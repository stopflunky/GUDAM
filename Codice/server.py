from concurrent import futures
import grpc
import file_pb2
import file_pb2_grpc
import psycopg2

# Configura la connessione al database PostgreSQL
DATABASE_CONFIG = {
    "dbname": "nome_database",
    "user": "nome_utente",
    "password": "password",
    "host": "localhost",
    "port": "5432"
}

# Implementazione del server gRPC
class UserService(file_pb2_grpc.UserServiceServicer):
    def __init__(self):
        # Inizializza la connessione al database
        self.conn = psycopg2.connect(**DATABASE_CONFIG)
        self.cursor = self.conn.cursor()

    def RegisterUser(self, request, context):
        try:

            #### DA FARE una ricerca sull'esistenza o meno del ticker nel database


            self.cursor.execute(
                "INSERT INTO utenti (email, codice_azione) VALUES (%s, %s) RETURNING id;",
                (request.email, request.codice_azione)
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
                "UPDATE utenti SET codice_azione = %s WHERE email = %s;",
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
                "DELETE FROM utenti WHERE email = %s;",
                (request.email,)
            )
            self.conn.commit()
            if self.cursor.rowcount == 0:
                return file_pb2.UserResponse(message="Errore: utente non trovato.")
            return file_pb2.UserResponse(message="Utente eliminato con successo.")
        except Exception as e:
            self.conn.rollback()
            return file_pb2.UserResponse(message=f"Errore durante l'eliminazione: {str(e)}")


    def GetLatestStockValue(self, request, context):
        try:
            self.cursor.execute(
                "SELECT last_ptice FROM tickers WHERE email = %s;",
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
