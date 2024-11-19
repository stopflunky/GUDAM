# Import delle librerie necessarie
from concurrent import futures
import grpc
import file_pb2
import file_pb2_grpc
import psycopg2
import yfinance as yf

# Configurazione della connessione al DB
DATABASE_CONFIG = {
    "dbname": "postgres",
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
            self.cursor.execute("INSERT INTO tickers (ticker_name, last_price) VALUES (%s, %s) ON CONFLICT (ticker_name) DO NOTHING;",
            (request.ticker, last_price))

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

    def UpdateUser(self, request, context):
        try:
            self.cursor.execute(
                "UPDATE users SET ticker = %s WHERE email = %s;",
                (request.codice_azione, request.email)
            )
            self.conn.commit()
            if self.cursor.rowcount == 0:
                return file_pb2.UserResponse(message="Errore: utente non trovato.")
            return file_pb2.UserResponse(message="Codice dell'azione aggiornato con successo.")
        except Exception as e:
            self.conn.rollback()
            return file_pb2.UserResponse(message=f"Errore durante l'aggiornamento: {str(e)}")
        
    def DeleteUser(self, request, context):
        try:
            self.cursor.execute(
                "DELETE FROM users WHERE email = %s;",
                (request.email,)
            )
            self.conn.commit()
            if self.cursor.rowcount == 0:
                return file_pb2.UserResponse(message="Errore: utente non trovato.")
            return file_pb2.UserResponse(message="Utente eliminato con successo.")
        except Exception as e:
            self.conn.rollback()
            return file_pb2.UserResponse(message=f"Errore durante l'eliminazione: {str(e)}")


    def GetTicker(self, request, context):
        try:
            self.cursor.execute(
                "SELECT last_price FROM tickers WHERE email = %s;",
                (request.email,)
            )
            result = self.cursor.fetchone()
            if result:
                valore = result
                return file_pb2.StockValueResponse(valore=valore)
            return file_pb2.StockValueResponse(valore=0.0)
        except Exception as e:
            return file_pb2.StockValueResponse(valore=0.0)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    file_pb2_grpc.add_UserServiceServicer_to_server(UserService(), server)
    server.add_insecure_port('[::]:50051')
    print("Server gRPC in esecuzione sulla porta 50051...")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
