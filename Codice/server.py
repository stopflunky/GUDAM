from concurrent import futures
import grpc
import file_pb2
import file_pb2_grpc
import psycopg2
import yfinance as yf

# Configura la connessione al database PostgreSQL
DATABASE_CONFIG = {
    "dbname": "provadata",
    "user": "postgres",
    "password": "1234",
    "host": "localhost",
    "port": "5432"
}

# Implementazione del server gRPC
class UserService(file_pb2_grpc.UserServiceServicer):
    def __init__(self):
        # Inizializza la connessione al database
        self.conn = psycopg2.connect(**DATABASE_CONFIG)
        self.cursor = self.conn.cursor()

    def CreateUser(self, request, context):
        try:

            print("Request: ", request)
            self.cursor.execute("SELECT ticker_name FROM tickers WHERE ticker_name = %s;", (request.ticker,))
            result = self.cursor.fetchone()

            if not result:
                
                stock = yf.Ticker(request.ticker)
                last_price = stock.history(period="1d")["Close"].iloc[-1]

                self.cursor.execute("INSERT INTO tickers (ticker_name, last_price) VALUES (%s, %s);", (request.ticker, last_price))
                self.conn.commit()



            self.cursor.execute(
                "INSERT INTO users (email, ticker) VALUES (%s, %s);",
                (request.email, request.ticker)
            )
            self.conn.commit()

            return file_pb2.UserResponse(message=f"Utente registrato con successo")
        

        except psycopg2.IntegrityError:
            self.conn.rollback()
            return file_pb2.UserResponse(message="Errore: l'email è già registrata.")
        except Exception as e:
            self.conn.rollback()
            return file_pb2.UserResponse(message=f"Errore durante la registrazione: {str(e)}")

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
