import time
import psycopg2
import yfinance as yf
from circuit_breaker import CircuitBreaker, CircuitBreakerOpenException


DATABASE_CONFIG = {
    "dbname": "provadata",
    "user": "postgres",
    "password": "1234",
    "host": "localhost",
    "port": "5432"
}





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





def get_tickers():

    tickers = []


    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        cursor = conn.cursor()

        # Query per recuperare i ticker
        query = f"SELECT ticker_name FROM tickers;"
        cursor.execute(query)

        # Recupera tutti i risultati
        rows = cursor.fetchall()

        # Inserisce ogni ticker nella pila
        for row in rows:
            tickers.append(row[0])  # row[0] contiene il valore del ticker

        # Chiude il cursore e la connessione
        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Errore durante l'accesso al database: {e}")

    return tickers





def update_ticker_value(ticker, last_value):

    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        cursor = conn.cursor()

        query = "UPDATE tickers SET last_price = %s WHERE ticker_name = %s;"
        cursor.execute(query, (last_value, ticker,))

        conn.commit()

        cursor.close()
        conn.close()


    except Exception as e:
        print(f"Errore durante l'accesso al database: {e}")
        raise


def main():

    # Configurazione iniziale, ad esempio istanze di circuit breaker
    get_data_circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=5)
    update_data_circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=5)

    while True:
        tickers = get_tickers()
        for ticker in tickers:

            try:

                last_value = get_data_circuit_breaker.call(lambda: get_stock_data(ticker))

                if last_value:

                    try:

                        update_data_circuit_breaker.call(lambda: update_ticker_value(ticker, last_value))

                    except CircuitBreakerOpenException:

                        print(f"Circuito aperto durante l'aggiornamento del ticker {ticker}")

                    except Exception as e:

                        print(f"Errore durante l'aggiornamento del ticker {ticker}: {e}")

            except CircuitBreakerOpenException:

                print(f"Circuito aperto durante la raccolta dati per {ticker}")

            except Exception as e:

                print(f"Errore durante la raccolta dati per {ticker}: {e}")
        
        
        print("update completato")
        time.sleep(60)

if __name__ == "__main__":
    main()