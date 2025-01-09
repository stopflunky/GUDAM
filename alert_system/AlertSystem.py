from confluent_kafka import Consumer, Producer, KafkaException, KafkaError
from email.mime.text import MIMEText
import psycopg2
import json
import smtplib
import prometheus_client
import socket
import time

# Definizione metriche di monitoraggio
HOSTNAME = socket.gethostname()
NODE_NAME = "alert_system"
APP_NAME = "alert_system_exporter"

as_messages_processing_time = prometheus_client.Gauge(
    'as_message_processing_time', 
    'Numero di tickers letti dal DB', 
    ["hostname", "node_name", "app_name"]
)
 
as_messages_consumed_count = prometheus_client.Counter(
    'as_message_consumed_time', 
    'Numero di messaggi mandati al sistema di alert', 
    ["hostname", "node_name", "app_name"]
)

as_messages_produced_count = prometheus_client.Counter(
    'as_message_produced_time', 
    'Numero di messaggi mandati al sistema di notifica', 
    ["hostname", "node_name", "app_name"]
)

# Configurazione del database PostgreSQL
db_config = {
    "dbname": "Homework",
    "user": "postgres",
    "password": "Danilo2001",
    "host": "db",
    "port": "5432"
}

# Configurazione del consumer
consumer_config = {
    'bootstrap.servers': 'kafka-broker:9092',
    'group.id': 'alert-system-group',       
    'auto.offset.reset': 'earliest'       
}

# Configurazione del producer
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

# Funzione di report per la consegna del messaggio
def delivery_report(err, msg):
    if err:
        print(f"Errore nella lettura del messaggio: {err}")
    else:
        print(f"Messaggio ricevuto dal topic '{msg.topic()}', partizione {msg.partition()}, offset {msg.offset()}.")

# Funzione per verificare le soglie e inviare notifiche
def check_thresholds_and_notify(ticker, last_value):
    try:
        # Connessione al database
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # Query per verificare i valori high_value e low_value per il ticker specificato
        cursor.execute("SELECT email, low_value, high_value FROM users WHERE ticker = %s", (ticker,))
        rows = cursor.fetchall()

        for row in rows:
            email, high_value, low_value = row
            if high_value:
                high_value = float(high_value)
            if low_value:
                low_value = float(low_value)
            condition = None

            # Verifica delle condizioni di soglia
            if high_value is not None and last_value > high_value:
                condition = 'sopra la soglia'
            elif low_value is not None and last_value < low_value:
                condition = 'sotto la soglia'

            if condition:
                # Crea il messaggio di notifica
                notification = {
                    'email': email,
                    'ticker': ticker,
                    'condition': condition
                }

                # Invia il messaggio al topic Kafka to-notifier
                producer.produce(
                    topic2,
                    value=json.dumps(notification),
                    callback=delivery_report
                )
                producer.flush()

                as_messages_produced_count.labels(HOSTNAME, NODE_NAME, APP_NAME).inc()

        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Errore durante la verifica delle soglie: {e}")

# Funzione per consumare i messaggi dal topic
def consume_messages():
    consumer.subscribe([topic1])
    try:
        while True:
            # Consuma un messaggio
            msg = consumer.poll(timeout=1.0)

            if msg is None:
                # Nessun messaggio disponibile nel tempo specificato
                continue
            elif msg.error():
                # Gestione degli errori nel consumer
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    print(f"Raggiunto l'EOF per la partizione {msg.partition()} a offset {msg.offset()}")
                else:
                    raise KafkaException(msg.error())
            else:
                as_messages_consumed_count.labels(HOSTNAME, NODE_NAME, APP_NAME).inc()
                start_time = time.time()
                # Processa il messaggio
                print(f"Messaggio ricevuto: {msg.value().decode('utf-8')}")
                try:
                    message = json.loads(msg.value().decode('utf-8'))
                    print("Contenuto del messaggio:", message.get('message'))
                    
                    # Estrai il ticker e last_value dal messaggio
                    ticker = message.get('ticker')
                    last_value = message.get('last_value')
                    print(f"Controllo le soglie...")
                    check_thresholds_and_notify(ticker, last_value)
                    
                except json.JSONDecodeError:
                    print("Errore nel parsing del messaggio JSON.")

                processing_time = time.time() - start_time
                as_messages_processing_time.labels(HOSTNAME, NODE_NAME, APP_NAME).set(processing_time)

    except KeyboardInterrupt:
        print("Interruzione del consumer.")
    finally:
        consumer.close()

# Funzione principale per avviare il consumer
if __name__ == "__main__":
    prometheus_client.start_http_server(50057)
    consume_messages()