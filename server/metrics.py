import socket
import prometheus_client

# Configurazione di Prometheus
HOSTNAME = socket.gethostname()
NODE_NAME = "server"
APP_NAME = "server-exporter"

# Definizione delle metriche
s_requests_counter = prometheus_client.Counter(
    "s_request_counter",
    "Contatore delle richieste",
    ["hostname", "node_name", "app_name"]
)

s_users_counter = prometheus_client.Gauge(
    "s_user_counter",
    "Contatore degli utenti attualmente connessi",
    ["hostname", "node_name", "app_name"]
)