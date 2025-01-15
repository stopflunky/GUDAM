from confluent_kafka import Consumer, Producer, KafkaException, KafkaError
import psycopg2
import json
import prometheus_client
import socket
import time
from datetime import datetime
from typing import List, Optional

# Definizione delle metriche di monitoraggio
HOSTNAME = socket.gethostname()
NODE_NAME = "alert_system"
APP_NAME = "alert_system_exporter"

as_messages_processing_time = prometheus_client.Gauge(
    'as_message_processing_time', 
    'Tempo di elaborazione dei messaggi', 
    ["hostname", "node_name", "app_name"]
)

as_messages_consumed_count = prometheus_client.Counter(
    'as_message_consumed_count', 
    'Numero di messaggi consumati', 
    ["hostname", "node_name", "app_name"]
)

as_messages_produced_count = prometheus_client.Counter(
    'as_message_produced_count', 
    'Numero di messaggi prodotti', 
    ["hostname", "node_name", "app_name"]
)

# Configurazione database PostgreSQL
db_config = {
    "dbname": "Homework",
    "user": "postgres",
    "password": "Danilo2001",
    "host": "postgres-db-service",
    "port": "5432"
}

# Configurazione consumer e producer
consumer_config = {
    'bootstrap.servers': 'kafka-broker:9092',
    'group.id': 'alert-system-group',       
    'auto.offset.reset': 'earliest'       
}

producer_config = {
    'bootstrap.servers': 'kafka-broker:9092',
    'acks': 'all',  
    'max.in.flight.requests.per.connection': 1,  
    'batch.size': 500,  
    'retries': 3
}

consumer = Consumer(consumer_config)
producer = Producer(producer_config)
topic1 = 'to-alert-system' 
topic2 = 'to-notifier'

# Modelli

class UserThreshold:
    def __init__(self, email: str, low_value: Optional[float], high_value: Optional[float], last_notification_time: Optional[datetime]):
        self.email = email
        self.low_value = low_value
        self.high_value = high_value
        self.last_notification_time = last_notification_time

    def from_db_row(row):
        return UserThreshold(
            email=row[0],
            low_value=float(row[1]) if row[1] is not None else None,
            high_value=float(row[2]) if row[2] is not None else None,
            last_notification_time=row[3]
        )

class Notification:
    def __init__(self, email: str, ticker: str, condition: str):
        self.email = email
        self.ticker = ticker
        self.condition = condition

    def to_json(self):
        return json.dumps({
            'email': self.email,
            'ticker': self.ticker,
            'condition': self.condition
        })

# CQRS: Handler per i Comandi
class CommandHandler:

    def update_notification_time(email, timestamp):
        try:
            conn = psycopg2.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users 
                SET last_notification_time = %s 
                WHERE email = %s
            """, (timestamp, email))
            conn.commit()
        finally:
            cursor.close()
            conn.close()

    def send_notification(notification: Notification):
        producer.produce(
            topic2,
            value=notification.to_json(),
            callback=CommandHandler.delivery_report
        )
        producer.flush()
        as_messages_produced_count.labels(HOSTNAME, NODE_NAME, APP_NAME).inc()

    def delivery_report(err, msg):
        if err:
            print(f"Errore nella consegna del messaggio: {err}")
        else:
            print(f"Messaggio inviato al topic '{msg.topic()}', offset {msg.offset()}.")

# CQRS: Handler per le Query
class QueryHandler:

    def get_user_thresholds(ticker: str) -> List[UserThreshold]:
        try:
            conn = psycopg2.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT email, low_value, high_value, last_notification_time 
                FROM users 
                WHERE ticker = %s
            """, (ticker,))
            rows = cursor.fetchall()
            return [UserThreshold.from_db_row(row) for row in rows]
        finally:
            cursor.close()
            conn.close()

# Funzione principale di elaborazione dei messaggi
def process_message(ticker, last_value):
    user_thresholds = QueryHandler.get_user_thresholds(ticker)
    for user in user_thresholds:
        condition = None

        if user.high_value is not None and last_value > user.high_value:
            condition = 'sopra la soglia'
        elif user.low_value is not None and last_value < user.low_value:
            condition = 'sotto la soglia'

        if condition:
            now = datetime.now()
            if user.last_notification_time and (now - user.last_notification_time).total_seconds() < 1800:
                print(f"Notifica non inviata a {user.email}. Ultima notifica troppo recente.")
                continue

            notification = Notification(user.email, ticker, condition)
            CommandHandler.send_notification(notification)
            CommandHandler.update_notification_time(user.email, now)

# Funzione per consumare i messaggi dal topic
def consume_messages():
    consumer.subscribe([topic1])
    try:
        while True:
            msg = consumer.poll(timeout=1.0)

            if msg is None:
                continue
            elif msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    print(f"EOF per la partizione {msg.partition()} a offset {msg.offset()}")
                else:
                    raise KafkaException(msg.error())
            else:
                as_messages_consumed_count.labels(HOSTNAME, NODE_NAME, APP_NAME).inc()
                start_time = time.time()
                try:
                    message = json.loads(msg.value().decode('utf-8'))
                    ticker = message.get('ticker')
                    last_value = message.get('last_value')
                    process_message(ticker, last_value)
                except json.JSONDecodeError:
                    print("Errore nel parsing del messaggio JSON.")

                processing_time = time.time() - start_time
                as_messages_processing_time.labels(HOSTNAME, NODE_NAME, APP_NAME).set(processing_time)

    except KeyboardInterrupt:
        print("Interruzione del consumer.")
    finally:
        consumer.close()

if __name__ == "__main__":
    prometheus_client.start_http_server(50057)
    consume_messages()