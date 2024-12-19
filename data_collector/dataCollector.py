import time
import json
import psycopg2
import yfinance as yf
from circuit_breaker import CircuitBreaker, CircuitBreakerOpenException
from confluent_kafka import Producer

#----------------------------------------

# Configurazione della connessione al DB
DATABASE_CONFIG = {
    "dbname": "Homework",
    "user": "postgres",
    "password": "Danilo2001",
    "host": "db",
    "port": "5432"
}

#----------------------------------------

producer_config = {
    'bootstrap.servers': 'kafka-broker:9092',  # List of Kafka brokers
    'acks': 'all',  # Ensure all in-sync replicas acknowledge the message
    'max.in.flight.requests.per.connection': 1,  # Ensure ordering of messages
    'batch.size': 500,  # Maximum size of a batch in bytes
    'retries': 3  # Number of retries for failed messages
}

producer = Producer(producer_config)
topic = 'to-alert-system'
message = {"message": "Stock data has been updated!"}

def delivery_report(err, msg):
    """
    Callback to report the result of message delivery.
    :param err: Error during delivery (None if successful).
    :param msg: The message metadata.
    """
    if err:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to topic '{msg.topic()}', partition {msg.partition()}, offset {msg.offset()}.")

#----------------------------------------

# Funzione Query: recupera i ticker, da aggiornare, dal DB
def query_tickers():

    tickers = []

    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        cursor = conn.cursor()

        # Query per recuperare i ticker
        query = f"SELECT ticker_name FROM tickers;"
        cursor.execute(query)

        # Recupera tutti i risultati
        rows = cursor.fetchall()

        # Inserisce ogni ticker nella lista
        for row in rows:
            tickers.append(row[0])  # row[0] contiene il valore del ticker

        # Chiude il cursore e la connessione
        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Errore durante l'accesso al database: {e}")

    return tickers

# Funzione Command: aggiorna il valore di un ticker nel DB
def command_update_ticker_value(ticker, last_value):

    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        cursor = conn.cursor()

        last_value = float(last_value)
        query = "UPDATE tickers SET last_price = %s WHERE ticker_name = %s;"
        cursor.execute(query, (last_value, ticker,))

        conn.commit()

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Errore durante l'accesso al database: {e}")
        raise

#----------------------------------------

# Funzione per recuperare i dati di un ticker da yfinance
def get_stock_data(ticker):

    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="1d")
        if not data.empty:
            # Ritorna il prezzo di chiusura più recente
            last_close = data['Close'].iloc[-1]
            return last_close
        else:
            print(f"Nessun dato trovato per {ticker}")
            return None
    except Exception as e:
        print(f"Errore durante il recupero dei dati per {ticker}: {e}")
        return None

#----------------------------------------

# Funzione principale
def main():

    # Configurazione iniziale, ad esempio istanze di circuit breaker
    get_data_circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=5)
    update_data_circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=5)

    while True:

        tickers = query_tickers()

        for ticker in tickers:
            try:
                last_value = get_data_circuit_breaker.call(lambda: get_stock_data(ticker))
                if last_value:
                    try:
                        update_data_circuit_breaker.call(lambda: command_update_ticker_value(ticker, last_value))
                        producer.produce(topic, json.dumps(message), callback = delivery_report)
                        producer.flush()

                    except CircuitBreakerOpenException:
                        print(f"Circuito aperto durante l'aggiornamento del ticker {ticker}")
                    except Exception as e:
                        print(f"Errore durante l'aggiornamento del ticker {ticker}: {e}")

            except CircuitBreakerOpenException:
                print(f"Circuito aperto durante la raccolta dati per {ticker}")
            except Exception as e:
                print(f"Errore durante la raccolta dati per {ticker}: {e}")
        
        print("Update del ticker completato.")
        time.sleep(60)

#----------------------------------------

if __name__ == "__main__":
    main()