from confluent_kafka import Consumer, KafkaException, KafkaError
import smtplib
from email.mime.text import MIMEText
import json

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
    'user': 'email@gmail.com', 
    'password': 'password'      
}

# Funzione per inviare email
def send_email(to, subject, body):
    try:
        # Crea il messaggio email
        msg = MIMEText(body)
        msg['From'] = smtp_config['user']
        msg['To'] = to
        msg['Subject'] = subject

        # Connessione al server SMTP
        with smtplib.SMTP(smtp_config['host'], smtp_config['port']) as server:
            server.starttls()  # Avvia la connessione sicura
            server.login(smtp_config['user'], smtp_config['password'])
            server.sendmail(smtp_config['user'], to, msg.as_string())

        print(f"Email inviata con successo a {to}")
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

                        print(f"Invio email a {email} con oggetto: {subject} e corpo: {body}")
                        # Invia l'email
                        send_email(email, subject, body)
                        
                except json.JSONDecodeError:
                    print("Errore nel parsing del messaggio JSON.")

    except KeyboardInterrupt:
        print("Interruzione del consumer.")
    finally:
        consumer.close()

# Esegui il consumer
if __name__ == "__main__":
    consume_messages()