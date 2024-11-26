# Import delle librerie necessarie
from concurrent import futures
from threading import Lock
import grpc
import file_pb2
import file_pb2_grpc
import psycopg2
import yfinance as yf
from datetime import datetime, timedelta

#------------------------------------------------------------

# Configurazione della connessione al DB
DATABASE_CONFIG = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "Danilo2001",
    "host": "localhost",
    "port": "5432"
}

#------------------------------------------------------------

request_cache = {}
cache_lock = Lock()

#------------------------------------------------------------

# Implementazione del server gRPC
class UserService(file_pb2_grpc.UserServiceServicer):
    def __init__(self):
        self.conn = psycopg2.connect(**DATABASE_CONFIG)
        self.cursor = self.conn.cursor()

#------------------------------------------------------------

    def Ping(self, request, context):
        # Risponde con "pong" quando riceve un "ping"
        return file_pb2.PingMessage(message="pong")

#------------------------------------------------------------

# Funzione di login per verificare se l'utente esiste nel DB
    def LoginUser(self, request, context):
        try:
            # Recupera l'utente dal database in base all'email
            self.cursor.execute("SELECT email, password FROM users WHERE email = %s", (request.email,))
            user = self.cursor.fetchone()

            if user is None:
                # Se l'utente non esiste, restituisci un messaggio di errore
                return file_pb2.UserResponse(message="Errore: utente non trovato. Devi registrarti.")

            # Recupera la password hashata dal database
            db_email, db_password = user

            # Confronta la password fornita con quella nel database
            if request.password == db_password:
                return file_pb2.UserResponse(message="Accesso riuscito!")
            else:
                return file_pb2.UserResponse(message="Errore: password errata.")

        # Eccezione generica
        except Exception as e:
            return file_pb2.UserResponse(message=f"Errore durante il login: {str(e)}")

#------------------------------------------------------------

    def CreateUser(self, request, context):
        # Controllo duplicati tramite cache
        with cache_lock:
            if request.requestID in request_cache:
                print(f"[CACHE HIT] La richiesta con ID {request.requestID} è già stata processata.")
                return request_cache[request.requestID]

        try:
            # Avvia una transazione
            self.cursor.execute("BEGIN")
            
            # Ottieni il prezzo dell'azione in modo sicuro
            try:
                stock = yf.Ticker(request.ticker)
                last_price = stock.history(period="1d")["Close"].iloc[-1]
                last_price = float(last_price)
            except Exception as yf_error:
                self.conn.rollback()
                return file_pb2.UserResponse(message=f"Errore nel recupero dei dati del ticker: {str(yf_error)}")

            # Inserisci i dati utili nel DB
            self.cursor.execute("INSERT INTO tickers (ticker_name, last_price) VALUES (%s, %s) ON CONFLICT (ticker_name) DO UPDATE SET last_price = EXCLUDED.last_price;", (request.ticker, last_price))
            self.cursor.execute("INSERT INTO users (email, password, ticker) VALUES (%s, %s, %s);", (request.email, request.password, request.ticker))
            self.conn.commit()

            response = file_pb2.UserResponse(message="Successo")

        # Gestione delle eccezioni
        except psycopg2.IntegrityError as e:
            self.conn.rollback()
            if "users_email_key" in str(e):
                response = file_pb2.UserResponse(message="Errore: email già registrata.")
        except Exception as e:
            self.conn.rollback()
            response = file_pb2.UserResponse(message=f"Errore durante la registrazione: {str(e)}")
        finally:
            # Memorizza nella cache il risultato della richiesta
            with cache_lock:
                request_cache[request.requestID] = response

        return response

#------------------------------------------------------------

    # Funzione di aggiornamento del ticker di un utente
    def UpdateUser(self, request, context):
        with cache_lock:
            if request.requestID in request_cache:
                print(f"[CACHE HIT] La richiesta con ID {request.requestID} è già stata processata.")
                return request_cache[request.requestID]

        try:
            self.cursor.execute("BEGIN")

            # Verifica se l'utente esiste nel database
            self.cursor.execute("SELECT * FROM users WHERE email = %s", (request.email,))
            user = self.cursor.fetchone()

            if user is None:
                response = file_pb2.UserResponse(message="Errore: utente non trovato.")
            else:
                # Ottieni il prezzo dell'azione
                stock = yf.Ticker(request.ticker)
                last_price = stock.history(period="1d")["Close"].iloc[-1]
                last_price = float(last_price)

                # Aggiorna il ticker dell'utente
                self.cursor.execute("INSERT INTO tickers (ticker_name, last_price) VALUES (%s, %s) ON CONFLICT (ticker_name) DO NOTHING;",(request.ticker, last_price))
                self.cursor.execute("UPDATE users SET ticker = %s WHERE email = %s", (request.ticker, request.email))
                self.conn.commit()

                response = file_pb2.UserResponse(message="Ticker aggiornato con successo")

        # Gestione delle eccezioni
        except psycopg2.IntegrityError as e:
            self.conn.rollback()
            response = file_pb2.UserResponse(message="Errore di integrità: impossibile aggiornare il ticker.")
        except Exception as e:
            self.conn.rollback()
            response = file_pb2.UserResponse(message=f"Errore durante l'aggiornamento: {str(e)}")
        finally:
            # Memorizza nella cache il risultato della richiesta
            with cache_lock:
                request_cache[request.requestID] = response

        return response

#------------------------------------------------------------

    # Funzione di cancellazione di un utente
    def DeleteUser(self, request, context):         
        try:
            # Cerca l'utente nel DB
            self.cursor.execute("DELETE FROM users WHERE email = %s;",(request.email,))
            self.conn.commit()
            # Se non trova l'utente, restituisce un messaggio di errore, altrimenti conferma l'eliminazione
            if self.cursor.rowcount == 0:
                return file_pb2.UserResponse(message="Errore: utente non trovato.")
            response = file_pb2.UserResponse(message="Utente eliminato con successo.")

        # Gestione delle eccezioni
        except Exception as e:
            self.conn.rollback()
            return file_pb2.UserResponse(message=f"Errore durante l'eliminazione: {str(e)}")

#------------------------------------------------------------

    # Funzione per ottenere il ticker di un utente
    def GetTicker(self, request, context):
        try:
            # Cerca l'utente nel DB e ottiene il suo ticker
            self.cursor.execute("SELECT ticker FROM users WHERE email = %s;", (request.email,))
            result = self.cursor.fetchone()
            # Se non trovo l'utente, restituisco un messaggio di errore
            if not result:
                return file_pb2.UserResponse(message="Errore: utente non trovato. Deve essere registrato.")
            
            ticker = result[0]
            print(f"Ticker: {ticker}")

            # Cerca il valore del ticker nel DB
            self.cursor.execute("SELECT last_price FROM tickers WHERE ticker_name = %s;", (ticker,))
            result = self.cursor.fetchone()
            if result:
                response = file_pb2.UserResponse(message=f"Ticker: {ticker}, Valore: {result[0]}")
            else:
                response =  file_pb2.UserResponse(message="Errore: valore del titolo non trovato.")
            
        # Gestione delle eccezioni
        except Exception as e:
            return file_pb2.UserResponse(message=f"Errore durante la ricerca del valore del titolo: {str(e)}")

#------------------------------------------------------------

    # Funzione per ottenere la media degli ultimi X giorni di un ticker
    def GetAvaragePriceOfXDays(self, request, contest):

        try:
            days = int(request.days)

            self.cursor.execute("SELECT ticker FROM users WHERE email = %s;", (request.email,))
            result = self.cursor.fetchone()
            # Se non trovo l'utente, restituisco un messaggio di errore
            if not result:
                return file_pb2.UserResponse(message="Errore: utente non trovato. Deve essere registrato.")
            
            ticker = yf.Ticker(result[0])

            end_date = datetime.now()
            start_date = end_date - timedelta(days)

            data = ticker.history(start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))

            closing_price_average = data['Close'].mean()

            response =  file_pb2.UserResponse(message=f"Media degli ultimi {days} giorni: {closing_price_average}")

        # Gestione delle eccezioni
        except Exception as e:
            return file_pb2.UserResponse(message=f"Errore durante la ricerca del valore del titolo: {str(e)}")

#------------------------------------------------------------

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    file_pb2_grpc.add_UserServiceServicer_to_server(UserService(), server)
    server.add_insecure_port('[::]:50051')
    print("Server gRPC in esecuzione sulla porta 50051...")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()