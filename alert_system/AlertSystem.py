from confluent_kafka import Consumer, KafkaException, KafkaError
import json
import smtplib
from email.mime.text import MIMEText

# Configurazione del consumer
consumer_config = {
    'bootstrap.servers': 'kafka-broker:9092',
    'group.id': 'alert-system-group',       
    'auto.offset.reset': 'earliest'       
}

consumer = Consumer(consumer_config)
topic = 'to-alert-system' 

def delivery_report(err, msg):
    if err:
        print(f"Errore nella lettura del messaggio: {err}")
    else:
        print(f"Messaggio ricevuto dal topic '{msg.topic()}', partizione {msg.partition()}, offset {msg.offset()}.")

# Funzione per consumare i messaggi dal topic
def consume_messages():


    smtp_server = 'smtp.gmail.com'
    smtp_port = 587  # Porta per TLS
    sender_email = "sdapallino@gmail.com"  # Inserisci il tuo indirizzo email
    password = "7A&U2iOtIppzYVb"  # Inserisci la tua password


    # Creazione dell'oggetto messaggio
    receiver_email = "russo.t.o.d@gmail.com"  # Inserisci l'email del destinatario
    message = MIMEText("This is a plain text email sent from a Python script.")
    message['Subject'] = 'Plain Text Email from Python'
    message['From'] = sender_email
    message['To'] = receiver_email


    consumer.subscribe([topic])

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
                # Processa il messaggio
                print(f"Messaggio ricevuto: {msg.value().decode('utf-8')}")
                try:
                    message = json.loads(msg.value().decode('utf-8'))
                    print("Contenuto del messaggio:", message)

                    with smtplib.SMTP(smtp_server, smtp_port) as server:
                        server.starttls()  # Avvia la connessione TLS
                        server.login(sender_email, password)
                        server.send_message(message)  # send_message è un metodo conveniente quando si usa MIMEText
                        print("Email sent successfully!")
                    
                    # Estrai il ticker e last_value dal messaggio
                    ticker = message.get('ticker')
                    last_value = message.get('last_value')
                    
                    # Verifica se i valori sono presenti e successivamente esegui operazioni future
                    if ticker and last_value:
                        print(f"Ticker: {ticker}, Last Value: {last_value}")
                        # Puoi aggiungere qui il codice per ulteriori operazioni, ad esempio:
                        # Esegui operazioni basate su ticker e last_value
                        # Ad esempio, salvataggio su database, invio di alert, etc.
                except json.JSONDecodeError:
                    print("Errore nel parsing del messaggio JSON.")

    except KeyboardInterrupt:
        print("Interruzione del consumer.")
    finally:
        consumer.close()

# Funzione principale per avviare il consumer
if __name__ == "__main__":
    consume_messages()