# Import delle librerie necessarie
from concurrent import futures
import grpc
import file_pb2
import file_pb2_grpc
import psycopg2
import yfinance as yf

# Configurazione della connessione al DB
DATABASE_CONFIG = {
    "dbname": "provadata",
    "user": "postgres",
    "password": "Danilo2001",
    "host": "localhost",
    "port": "5432"
}

# Implementazione del server gRPC
class UserService(file_pb2_grpc.UserServiceServicer):
    def __init__(self):
        self.conn = psycopg2.connect(**DATABASE_CONFIG)
        self.cursor = self.conn.cursor()

#------------------------------------------------------------

    # Funzione di creazione utente
    def CreateUser(self, request, context):
        try:
            # Avvio di una transazione atomica
            self.cursor.execute("BEGIN")

            # Ottiene il prezzo dell'azione
            stock = yf.Ticker(request.ticker)
            last_price = stock.history(period="1d")["Close"].iloc[-1]
            last_price = float(last_price)

            # Tenta di inserire il ticker
            self.cursor.execute("INSERT INTO tickers (ticker_name, last_price) VALUES (%s, %s) ON CONFLICT (ticker_name) DO NOTHING;",(request.ticker, last_price))

            # Tenta di inserire l'utente
            self.cursor.execute("INSERT INTO users (email, ticker) VALUES (%s, %s)",(request.email, request.ticker))

            # Conferma la transazione
            self.conn.commit()

            return file_pb2.UserResponse(message="Utente registrato con successo")

        # Eccezione in caso di problemi di integrità del DB
        except psycopg2.IntegrityError as e:
            self.conn.rollback()
            error_message = str(e)
            if "users_email_key" in error_message:
                return file_pb2.UserResponse(message="Errore: email già registrata.")
            elif "tickers_pkey" in error_message:
                return file_pb2.UserResponse(message="Errore: ticker già presente.")
            else:
                return file_pb2.UserResponse(message="Errore di integrità: impossibile registrare l'utente.")

        # Eccezione generica
        except Exception as e:
            self.conn.rollback()
            return file_pb2.UserResponse(message=f"Errore durante la registrazione: {str(e)}")

#------------------------------------------------------------

    # Funzione di aggiornamento del ticker di un utente
    def UpdateUser(self, request, context):
        try:
            # Verifica se l'utente esiste
            self.cursor.execute("SELECT * FROM users WHERE email = %s;", (request.email,))
            if self.cursor.rowcount == 0:
                return file_pb2.UserResponse(message="Errore: utente non trovato.")

            # Verifica se il ticker è presente nella tabella tickers
            self.cursor.execute("SELECT * FROM tickers WHERE ticker_name = %s;", (request.ticker,))
            if self.cursor.rowcount == 0:
                # Se il ticker non esiste, lo cerca su yfinance e lo inserisce nel DB
                stock = yf.Ticker(request.ticker)
                last_price = stock.history(period="1d")["Close"].iloc[-1]
                last_price = float(last_price)
                self.cursor.execute(
                    "INSERT INTO tickers (ticker_name, last_price) VALUES (%s, %s) ON CONFLICT (ticker_name) DO NOTHING;",
                    (request.ticker, last_price)
                )

            # A questo punto il ticker è garantito essere presente, quindi aggiorno il ticker dell'utente
            self.cursor.execute("UPDATE users SET ticker = %s WHERE email = %s;", (request.ticker, request.email))
            
            # Commit delle modifiche
            self.conn.commit()

            return file_pb2.UserResponse(message="Codice azione aggiornato con successo.")

        except Exception as e:
            self.conn.rollback()
            return file_pb2.UserResponse(message=f"Errore durante l'aggiornamento: {str(e)}")

        
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
            return file_pb2.UserResponse(message="Utente eliminato con successo.")
        # Eccezione generica
        except Exception as e:
            self.conn.rollback()
            return file_pb2.UserResponse(message=f"Errore durante l'eliminazione: {str(e)}")

#------------------------------------------------------------

    def GetTicker(self, request, context):
        try:
            # Cerca l'utente nel DB e ottiene il suo ticker
            self.cursor.execute("SELECT ticker FROM users WHERE email = %s;", (request.email,))
            result = self.cursor.fetchone()
            # Se non trovo l'utente, restituisco un messaggio di errore
            if not result:
                return file_pb2.UserResponse(message="Errore: utente non trovato. Deve essere registrato.")
            
            ticker = result[0]

            # Cerca il valore del ticker nel DB
            self.cursor.execute("SELECT last_price FROM tickers WHERE ticker_name = %s;", (ticker,))
            result = self.cursor.fetchone()
            if result:
                # Se il valore del ticker è trovato, restituisci il messaggio con il nome e il valore del titolo
                return file_pb2.UserResponse(message=f"Ticker: {ticker}, Valore: {result[0]}")
            else:
                return file_pb2.UserResponse(message="Errore: valore del titolo non trovato.")
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
