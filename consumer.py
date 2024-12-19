from confluent_kafka import Consumer, KafkaException, KafkaError
import json

# Configurazione del consumer
consumer_config = {
    'bootstrap.servers': 'localhost:29092',  # Lista di broker Kafka
    'group.id': 'alert-system-group',          # Identificatore del gruppo consumer
    'auto.offset.reset': 'earliest'            # Imposta la lettura dei messaggi dal primo messaggio disponibile se non ci sono offset salvati
}

# Crea il consumer
consumer = Consumer(consumer_config)

topic = 'to-alert-system'  # Nome del topic da cui il consumer leggerà i messaggi

def delivery_report(err, msg):
    """
    Callback per la consegna dei messaggi. Può essere utilizzata anche nel consumer
    per segnalare se ci sono errori durante la lettura dei messaggi.
    """
    if err:
        print(f"Errore nella lettura del messaggio: {err}")
    else:
        print(f"Messaggio ricevuto dal topic '{msg.topic()}', partizione {msg.partition()}, offset {msg.offset()}.")

def consume_messages():
    # Iscriviti al topic
    consumer.subscribe([topic])

    try:
        while True:
            # Consuma un messaggio
            msg = consumer.poll(timeout=1.0)  # Tempo di attesa per il messaggio in secondi

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
                    # Puoi aggiungere qui il codice per elaborare il messaggio
                except json.JSONDecodeError:
                    print("Errore nel parsing del messaggio JSON.")

    except KeyboardInterrupt:
        print("Interruzione del consumer.")
    finally:
        # Assicurati di chiudere il consumer quando finito
        consumer.close()

# Funzione principale per avviare il consumer
if __name__ == "__main__":
    consume_messages()