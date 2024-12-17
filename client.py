import grpc
import hashlib
import file_pb2
import file_pb2_grpc
import uuid
import time
import os
import platform
from grpc import RpcError

is_authenticated = False # Variabile per memorizzare lo stato di autenticazione dell'utente
current_email = None  # Variabile per memorizzare l'email dell'utente autenticato
MAX_RETRIES = 3  # Numero massimo di tentativi
TIMEOUT = 5  # Timeout in secondi per ogni tentativo

#------------------------------------------------------------

# Funzione per pulire il terminale
def clear_terminal():
    
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")

#------------------------------------------------------------

# Funzione per criptare la password con SHA-256
def hash_password(password):
    sha256_hash = hashlib.sha256()
    sha256_hash.update(password.encode('utf-8'))
    return sha256_hash.hexdigest()

#------------------------------------------------------------

# Funzione per verificare se il server è attivo
def ping_server(query_stub):
    try:
        # Esegui il ping al server
        ping_request = file_pb2.PingMessage(message="ping")
        response = query_stub.Ping(ping_request)
        return True
    except RpcError as e:
        return False
    
#------------------------------------------------------------

# Funzione per effettuare il login di un utente
def login_user(query_stub):
    global is_authenticated, current_email

    # Controlla se l'utente è già autenticato
    if is_authenticated:
        print("Sei già autenticato!")
        time.sleep(2)
        clear_terminal()
        return

    email = input("Inserisci l'email dell'utente per il login: ")
    password = input("Inserisci la password: ")
    hashed_password = hash_password(password)
    request = file_pb2.LoginRequest(email=email, password=hashed_password)

    try:
        response = query_stub.LoginUser(request)
        if response.message == "Accesso riuscito!":
            print(response.message)
            time.sleep(2)
            clear_terminal()
            is_authenticated = True
            current_email = email
        else:
            print(response.message)
            time.sleep(2)
            clear_terminal()
    except RpcError as e:
        print(f"Errore RPC: {e.code()} - {e.details()}")
        
#------------------------------------------------------------

# Funzione per registrare un nuovo utente con retry e timeout
def create_user(command_stub):
    global is_authenticated, current_email

    if is_authenticated:
        print("Sei già autenticato!")
        time.sleep(2)
        clear_terminal()
        return

    email = input("Inserisci l'email dell'utente: ")
    password = input("Inserisci la password: ")
    hashed_password = hash_password(password)
    ticker = input("Inserisci il ticker dell'utente: ")
    request_id = str(uuid.uuid4())
    request = file_pb2.RegisterRequest(email=email, password=hashed_password, ticker=ticker, requestID=request_id)

    retries = 0
    while retries < MAX_RETRIES:
        try:
            response = command_stub.CreateUser(request, timeout=TIMEOUT)
            if response.message == "Successo":
                print("Registrazione riuscita!")
                time.sleep(2)
                clear_terminal()
                is_authenticated = True
                current_email = email
                return
            else:
                print(response.message)
            break
        
        except RpcError as e:
            print(f"Errore RPC: {e.code()} - {e.details()}")
            retries += 1
            if retries < MAX_RETRIES:
                print(f"Riprovo... Tentativo {retries}/{MAX_RETRIES}")
                time.sleep(2)
                clear_terminal()
            else:
                print("Numero massimo di tentativi raggiunto.")
                time.sleep(2)
                clear_terminal()
                break

#------------------------------------------------------------

# Funzione per aggiornare il ticker dell'utente con retry e timeout
def update_user(command_stub):
    if not is_authenticated:
        clear_terminal()
        print("Devi effettuare il login o la registrazione prima di aggiornare il ticker.")
        time.sleep(2)
        clear_terminal()
        return

    ticker = input("Inserisci il nuovo ticker: ")
    request_id = str(uuid.uuid4())
    request = file_pb2.UserRequest(email=current_email, ticker=ticker, requestID=request_id)

    retries = 0
    while retries < MAX_RETRIES:
        try:
            response = command_stub.UpdateUser(request, timeout=TIMEOUT)
            print(response.message)
            time.sleep(2)
            clear_terminal()
            return
        except RpcError as e:
            print(f"Errore RPC: {e.code()} - {e.details()}")
            retries += 1
            if retries < MAX_RETRIES:
                print(f"Riprovo... Tentativo {retries}/{MAX_RETRIES}")
                time.sleep(2)
                clear_terminal()
            else:
                print("Numero massimo di tentativi raggiunto.")
                time.sleep(2)
                clear_terminal()
                break

#------------------------------------------------------------

# Funzione per eliminare un utente
def delete_user(command_stub):
    if not is_authenticated:
        print("Devi effettuare il login o la registrazione prima di eliminare un utente.")
        time.sleep(2)
        clear_terminal()
        return

    request_id = str(uuid.uuid4())
    request = file_pb2.UserRequest(email=current_email, requestID=request_id)

    try:
        response = command_stub.DeleteUser(request)
        print(response.message)
        time.sleep(2)
        clear_terminal()
    except RpcError as e:
        print(f"Errore RPC: {e.code()} - {e.details()}")
        time.sleep(2)
        clear_terminal()

#------------------------------------------------------------

# Funzione per ottenere il ticker di un utente
def get_ticker(stub):
    if not is_authenticated:
        print("Devi effettuare il login o la registrazione prima di ottenere il ticker.")
        time.sleep(2)
        clear_terminal()
        return

    request_id = str(uuid.uuid4())
    request = file_pb2.UserRequest(email=current_email, requestID=request_id)

    try:
        response = stub.GetTicker(request)
        print(response.message)
        time.sleep(2)
        clear_terminal()
    except RpcError as e:
        print(f"Errore RPC: {e.code()} - {e.details()}")
        time.sleep(2)
        clear_terminal()

#------------------------------------------------------------

# Funzione per ottenere la media degli ultimi X giorni di un ticker
def GetAvaragePriceOfXDays(query_stub):
    if not is_authenticated:
        print("Devi effettuare il login o la registrazione prima di ottenere il ticker.")
        time.sleep(2)
        clear_terminal()
        return

    days = input("Inserisci il numero di valori: ")
    request = file_pb2.GetAvarageXDaysRequest(days=days, email=current_email)

    try:
        response = query_stub.GetAvaragePriceOfXDays(request)
        print(response.message)
        time.sleep(2)
        clear_terminal()
    except RpcError as e:
        print(f"Errore RPC: {e.code()} - {e.details()}")
        time.sleep(2)
        clear_terminal()

#------------------------------------------------------------

def run():
    global is_authenticated
    channel = grpc.insecure_channel('localhost:50051')
    command_stub = file_pb2_grpc.CommandServiceStub(channel)
    query_stub = file_pb2_grpc.QueryServiceStub(channel)

    # Verifica se il server è attivo prima di proseguire
    if not ping_server(query_stub):
        print("Il server non è disponibile. Uscita.")
        return

    # Menu principale
    while True:
        if is_authenticated:
            print("\n1. Aggiorna ticker utente")
            print("2. Elimina utente")
            print("3. Ottieni ticker utente")
            print("4. Ottieni la media degli ultimi X valori del ticker: ")
            print("5. Esci (torna al login)")
        else:
            print("\n1. Login utente")
            print("2. Crea nuovo utente")
            print("3. Esci (chiudi il programma)")

        choice = input("Scegli un'opzione: ")

        if choice == '1':
            if is_authenticated:
                update_user(command_stub)
            else:
                login_user(query_stub)
        elif choice == '2':
            if is_authenticated:
                delete_user(command_stub)
                is_authenticated = False
                current_email = None
            else:
                create_user(command_stub)
        elif choice == '3':
            if is_authenticated:
                get_ticker(query_stub)
            else:
                if is_authenticated:
                    print("Uscita...")
                    break
                else:
                    print("Uscita dal programma...")
                    break
        elif choice == '2':
            print("Torna al login")
        elif choice == '4' and is_authenticated:
            GetAvaragePriceOfXDays(query_stub)
        elif choice == '5' and is_authenticated:
            is_authenticated = False
            current_email = None
            print("Sei stato disconnesso. Torna al login.")
            time.sleep(1)
            clear_terminal()
        elif choice == '3' and not is_authenticated:
            print("Uscita dal programma...")
            break
        else:
            print("Opzione non valida.")

if __name__ == "__main__":
    run()