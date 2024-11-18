import grpc
import file_pb2
import file_pb2_grpc

def register_user(stub):
    email = input("Inserisci l'email dell'utente: ")
    ticker = input("Inserisci il codice dell'azione (ticker): ")
    request = file_pb2.UserRequest(email=email, ticker=ticker)
    response = stub.CreateUser(request)
    print(f"Risultato della registrazione: {response}")

def update_user(stub):
    email = int(input("Inserisci l'email dell'utente da aggiornare: "))
    nuovo_codice_azione = input("Inserisci il nuovo codice dell'azione (ticker): ")
    request = file_pb2.UserUpdateRequest(email=email, codice_azione=nuovo_codice_azione)
    response = stub.UpdateUser(request)
    print(f"Risultato dell'aggiornamento: {response}")

def delete_user(stub):
    email = int(input("Inserisci l'email dell'utente da eliminare:"))
    request = file_pb2.DeleteUserRequest(email=email)
    response = stub.DeleteUser(request)
    print(f"Risultato dell'eliminazione: {response.message}")

def get_latest_stock_value(stub):
    email = int(input("Inserisci l'email dell'utente per cui vuoi ottenere il valore del titolo: "))
    request = file_pb2.UserId(email=email)
    response = stub.GetTicker(request)
    print(f"Ultimo valore del titolo: {response.valore}")

def main():
    # Connessione al server gRPC
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = file_pb2_grpc.UserServiceStub(channel)
        
        while True:
            # Menu di scelta
            print("\n--- Menu ---")
            print("1. Registra un nuovo utente")
            print("2. Aggiorna il codice dell'azione di un utente")
            print("3. Elimina un utente")
            print("4. Ottieni l'ultimo valore del titolo di un utente")
            print("5. Esci")
            
            scelta = input("Scegli un'opzione: ")

            if scelta == '1':
                register_user(stub)
            elif scelta == '2':
                update_user(stub)
            elif scelta == '3':
                delete_user(stub)
            elif scelta == '4':
                get_latest_stock_value(stub)
            elif scelta == '5':
                print("Uscita...")
                break
            else:
                print("Scelta non valida. Riprova.")

if __name__ == "__main__":
    main()
