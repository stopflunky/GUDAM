import time
import json
import psycopg2
import yfinance as yf
from circuit_breaker import CircuitBreaker, CircuitBreakerOpenException
from confluent_kafka import Producer
import prometheus_client
import socket

HOSTNAME = socket.gethostname()
NODE_NAME = "data_collector"
APP_NAME = "data_collector_exporter"

dc_tickers_count = prometheus_client.Gauge(
    'dc_tickers_count', 
    'Numero di tickers letti dal DB', 
    ["hostname", "node_name", "app_name"]
)

dc_messages_produced_count = prometheus_client.Counter(
    'dc_messages_count', 
    'Numero di messaggi mandati al sistema di alert', 
    ["hostname", "node_name", "app_name"]
)

# Configurazione della connessione al DB
DATABASE_CONFIG = {
    "dbname": "Homework",
    "user": "postgres",
    "password": "Danilo2001",
    "host": "postgres-db-service",
    "port": "5432"
}

producer_config = {
    'bootstrap.servers': 'kafka-broker:9092',
    'acks': 'all',
    'max.in.flight.requests.per.connection': 1,
    'batch.size': 500,
    'retries': 3
}

producer = Producer(producer_config)
topic = 'to-alert-system'


def delivery_report(err, msg):
    if err:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to topic '{msg.topic()}', partition {msg.partition()}, offset {msg.offset()}.")


# Modello Ticker
class Ticker:
    def __init__(self, ticker_name, last_price=None):
        self.ticker_name = ticker_name
        self.last_price = last_price

    def from_db_row(row):
        return Ticker(ticker_name=row[0], last_price=row[1] if len(row) > 1 else None)

    def to_dict(self):
        return {"ticker_name": self.ticker_name, "last_price": self.last_price}


# CQRS: Handler per le Query
class QueryHandler:
    def query_tickers():
        tickers = []
        try:
            conn = psycopg2.connect(**DATABASE_CONFIG)
            cursor = conn.cursor()

            query = f"SELECT ticker_name FROM tickers;"
            cursor.execute(query)

            rows = cursor.fetchall()
            dc_tickers_count.labels(HOSTNAME, NODE_NAME, APP_NAME).set(len(rows))

            for row in rows:
                tickers.append(Ticker.from_db_row(row))

            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Errore durante l'accesso al database: {e}")
        return tickers


# CQRS: Handler per i Comandi
class CommandHandler:
    def command_update_ticker_value(ticker_name, last_value):
        try:
            conn = psycopg2.connect(**DATABASE_CONFIG)
            cursor = conn.cursor()

            last_value = float(last_value)
            query = "UPDATE tickers SET last_price = %s WHERE ticker_name = %s;"
            cursor.execute(query, (last_value, ticker_name,))

            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Errore durante l'accesso al database: {e}")
            raise


# Funzione per recuperare i dati di un ticker da yfinance
def get_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="1d")
        if not data.empty:
            last_close = data['Close'].iloc[-1]
            return last_close
        else:
            print(f"Nessun dato trovato per {ticker}")
            return None
    except Exception as e:
        print(f"Errore durante il recupero dei dati per {ticker}: {e}")
        return None


def main():
    prometheus_client.start_http_server(50056)

    # Circuit Breakers
    get_data_circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=5)
    update_data_circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=5)

    while True:
        tickers = QueryHandler.query_tickers()
        dc_tickers_count.labels(HOSTNAME, NODE_NAME, APP_NAME).set(len(tickers))

        for ticker in tickers:
            try:
                last_value = get_data_circuit_breaker.call(lambda: get_stock_data(ticker.ticker_name))
                if last_value:
                    try:
                        CommandHandler.command_update_ticker_value(ticker.ticker_name, last_value)
                        message = {"message": f"Ticker {ticker.ticker_name} aggiornato a {last_value}!",
                                   "ticker": ticker.ticker_name,
                                   "last_value": last_value}
                        producer.produce(topic, json.dumps(message), callback=delivery_report)
                        producer.flush()
                        dc_messages_produced_count.labels(HOSTNAME, NODE_NAME, APP_NAME).inc()

                    except CircuitBreakerOpenException:
                        print(f"Circuito aperto durante l'aggiornamento del ticker {ticker.ticker_name}")
                    except Exception as e:
                        print(f"Errore durante l'aggiornamento del ticker {ticker.ticker_name}: {e}")

            except CircuitBreakerOpenException:
                print(f"Circuito aperto durante la raccolta dati per {ticker.ticker_name}")
            except Exception as e:
                print(f"Errore durante la raccolta dati per {ticker.ticker_name}: {e}")

        print("Update del ticker completato.")
        time.sleep(60)


if __name__ == "__main__":
    main()