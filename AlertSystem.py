from confluent_kafka import Consumer, KafkaException, KafkaError
import json

# Configurazione del consumer
consumer_config = {
    'bootstrap.servers': 'localhost:29092',
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