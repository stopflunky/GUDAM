from confluent_kafka import Consumer, KafkaException, KafkaError
import smtplib
from email.mime.text import MIMEText
import json
import time
import prometheus_client
import socket

# Definizione metriche di monitoraggio
HOSTNAME = socket.gethostname()
NODE_NAME = "alert_notifier_system"
APP_NAME = "alert_notifier_system_exporter"

ans_email_processing_time = prometheus_client.Gauge(
    'ans_email_processing_time', 
    'Tempo di invio di una email', 
    ["hostname", "node_name", "app_name"]
)
 
ans_sent_emails_count = prometheus_client.Counter(
    'ans_sent_emails_count', 
    'Numero di email inviate', 
    ["hostname", "node_name", "app_name"]
)

# Configurazione del consumer
consumer_config = {
    'bootstrap.servers': 'kafka-broker:9092',
    'group.id': 'notifier-system-group',
    'auto.offset.reset': 'earliest'
}

consumer = Consumer(consumer_config)
topic = 'to-notifier'

# Configurazione dell'email
smtp_config = {
    'host': 'smtp.gmail.com',
    'port': 587,              
    'user': 'daniloverde2001@gmail.com', 
    'password': 'kbpe tuzx feke psrn'      
}

# Dizionario per tracciare l'ultimo invio email
last_email_sent = {}

# Funzione per inviare email
def send_email(to, subject, body):
    try:
        startTime = time.time()
        # Crea il messaggio email
        msg = MIMEText(body)
        msg['From'] = smtp_config['user']
        msg['To'] = to
        msg['Subject'] = subject

        # Connessione al server SMTP
        with smtplib.SMTP(smtp_config['host'], smtp_config['port']) as server:
            server.starttls()
            server.login(smtp_config['user'], smtp_config['password'])
            server.sendmail(smtp_config['user'], to, msg.as_string())

        print(f"Email inviata con successo a {to}")
        ans_email_processing_time.labels(HOSTNAME, NODE_NAME, APP_NAME).set(time.time() - startTime)
        ans_sent_emails_count.labels(HOSTNAME, NODE_NAME, APP_NAME).inc() 
    except Exception as e:
        print(f"Errore durante l'invio dell'email a {to}: {e}")

# Funzione per consumare i messaggi
def consume_messages():
    consumer.subscribe([topic])
    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            elif msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    print(f"Raggiunto l'EOF per la partizione {msg.partition()} a offset {msg.offset()}")
                else:
                    raise KafkaException(msg.error())
            else:
                try:
                    # Parsing del messaggio JSON
                    message = json.loads(msg.value().decode('utf-8'))
                    email = message.get('email')
                    ticker = message.get('ticker')
                    condition = message.get('condition')

                    if email and ticker and condition:
                        subject = f"Alert: {ticker}"
                        body = f"Il valore del ticker {ticker} è {condition}."

                        # Controlla se possiamo inviare l'email
                        print(f"Invio email a {email} con oggetto: {subject} e corpo: {body}")
                        send_email(email, subject, body)

                except json.JSONDecodeError:
                    print("Errore nel parsing del messaggio JSON.")

    except KeyboardInterrupt:
        print("Interruzione del consumer.")
    finally:
        consumer.close()

# Esegui il consumer
if __name__ == "__main__":
    prometheus_client.start_http_server(50058)
    consume_messages()