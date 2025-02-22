# Import delle librerie necessarie
import grpc
import file_pb2
import file_pb2_grpc
import prometheus_client
import models.command_models as command_models
import models.query_models as query_models
import services.user_write_service as user_write_service
import services.user_read_service as user_read_service
import metrics
import user_db
import time
from concurrent import futures

#------------------------------------------------------------

# Implementazione del CommanServicer
class CommandService(file_pb2_grpc.CommandServiceServicer):

    def __init__(self):
        self.conn = user_db.getConnection()
        self.cursor = self.conn.cursor()

    # Funzione che monitora il tempo di risposta e gestisce gli errori
    @staticmethod
    def measure_latency(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                return func(*args, **kwargs)
            except Exception as e:
                metrics.s_errors_counter.labels(metrics.HOSTNAME, metrics.NODE_NAME, metrics.APP_NAME).inc()
                raise e
            finally:
                latency = time.time() - start_time
                metrics.s_request_latency.labels(metrics.HOSTNAME, metrics.NODE_NAME, metrics.APP_NAME).observe(latency)
        return wrapper

    # Funzione di creazione di un utente
    @measure_latency
    def CreateUser(self, request, context):
        metrics.s_requests_counter.labels(metrics.HOSTNAME, metrics.NODE_NAME, metrics.APP_NAME).inc()
        command = command_models.CreateUserCommand(request.email, request.password, request.ticker, request.lowValue, request.highValue, request.requestID)
        response = user_write_service.CommandService._execute_create_user(self, command)
        if response and response.message == "Successo":
            metrics.s_users_counter.labels(metrics.HOSTNAME, metrics.NODE_NAME, metrics.APP_NAME).inc()
        return response

    # Funzione di aggiornamento del ticker di un utente
    @measure_latency
    def UpdateUser(self, request, context):
        metrics.s_requests_counter.labels(metrics.HOSTNAME, metrics.NODE_NAME, metrics.APP_NAME).inc()
        command = command_models.UpdateUserCommand(request.email, request.ticker, request.requestID)
        return user_write_service.CommandService._execute_update_user(self, command)

    # Funzione di aggiornamento dei valori di basso e alto di un utente
    @measure_latency
    def UpdateHighLow(self, request, context):
        metrics.s_requests_counter.labels(metrics.HOSTNAME, metrics.NODE_NAME, metrics.APP_NAME).inc()
        command = command_models.UpdateThresholdsCommand(request.email, request.lowValue, request.highValue, request.requestID)
        return user_write_service.CommandService._execute_update_thresholds(self, command)

    # Funzione di cancellazione di un utente
    @measure_latency
    def DeleteUser(self, request, context):
        metrics.s_requests_counter.labels(metrics.HOSTNAME, metrics.NODE_NAME, metrics.APP_NAME).inc()
        command = command_models.DeleteUserCommand(request.email, request.requestID)
        response = user_write_service.CommandService._execute_delete_user(self, command)
        if response and response.message == "Successo":
            metrics.s_users_counter.labels(metrics.HOSTNAME, metrics.NODE_NAME, metrics.APP_NAME).dec()
        return response

#------------------------------------------------------------

# Implementazione del QueryServicer
class QueryService(file_pb2_grpc.QueryServiceServicer):

    def __init__(self):
        self.conn = user_db.getConnection()
        self.cursor = self.conn.cursor()

    # Funzione che monitora il tempo di risposta e gestisce gli errori
    @staticmethod
    def measure_latency(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            metrics.s_query_in_progress.labels(metrics.HOSTNAME, metrics.NODE_NAME, metrics.APP_NAME).inc()
            try:
                return func(*args, **kwargs)
            except Exception as e:
                metrics.s_errors_counter.labels(metrics.HOSTNAME, metrics.NODE_NAME, metrics.APP_NAME).inc()
                raise e
            finally:
                latency = time.time() - start_time
                metrics.s_request_latency.labels(metrics.HOSTNAME, metrics.NODE_NAME, metrics.APP_NAME).observe(latency)
                metrics.s_query_in_progress.labels(metrics.HOSTNAME, metrics.NODE_NAME, metrics.APP_NAME).dec()
        return wrapper

    # Funzione di ping per verificare se il server è attivo
    @measure_latency
    def Ping(self, request, context):
        metrics.s_requests_counter.labels(metrics.HOSTNAME, metrics.NODE_NAME, metrics.APP_NAME).inc()
        return file_pb2.PingMessage(message="pong")

    # Funzione di login per verificare se l'utente esiste nel DB
    @measure_latency
    def LoginUser(self, request, context):
        metrics.s_requests_counter.labels(metrics.HOSTNAME, metrics.NODE_NAME, metrics.APP_NAME).inc()
        query = query_models.LoginUserQuery(request.email, request.password)
        return user_read_service.QueryService._execute_login_user(self, query)

    # Funzione per ottenere il ticker di un utente
    @measure_latency
    def GetTicker(self, request, context):
        metrics.s_requests_counter.labels(metrics.HOSTNAME, metrics.NODE_NAME, metrics.APP_NAME).inc()
        query = query_models.GetTickerQuery(request.email)
        return user_read_service.QueryService._execute_get_ticker_user(self, query)

    # Funzione per ottenere la media degli ultimi X giorni di un ticker
    @measure_latency
    def GetAvaragePriceOfXDays(self, request, context):
        metrics.s_requests_counter.labels(metrics.HOSTNAME, metrics.NODE_NAME, metrics.APP_NAME).inc()
        query = query_models.GetAveragePriceQuery(request.email, request.days)
        return user_read_service.QueryService._execute_get_average_price_of_x_days(self, query)

    # Funzione per ottenere le soglie (low_value e high_value) di un utente
    @measure_latency
    def GetTresholds(self, request, context):
        metrics.s_requests_counter.labels(metrics.HOSTNAME, metrics.NODE_NAME, metrics.APP_NAME).inc()
        query = query_models.GetThresholdsQuery(request.email)
        return user_read_service.QueryService._execute_get_thresholds(self, query)

#------------------------------------------------------------

def serve():
    prometheus_client.start_http_server(9999)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    file_pb2_grpc.add_CommandServiceServicer_to_server(CommandService(), server)
    file_pb2_grpc.add_QueryServiceServicer_to_server(QueryService(), server)
    server.add_insecure_port('[::]:50051')
    print("Server gRPC in esecuzione sulla porta 50051...")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()