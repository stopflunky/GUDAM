from threading import Lock
import yfinance as yf
import psycopg2
import file_pb2

# Inizializzazione della cache
request_cache = {}
cache_lock = Lock()

# Definizione della classe CommandService
class CommandService:

    # Funzione di inserimento utente ottimizzata
    def _execute_create_user(self, command):
        with cache_lock:
            if command.requestID in request_cache:
                print(f"[CACHE HIT] La richiesta con ID {command.requestID} è già stata processata.")
                return request_cache[command.requestID]

        try:
            try:
                stock = yf.Ticker(command.ticker)
                history = stock.history(period="1d")
                if history.empty:
                    return file_pb2.UserResponse(message="Errore: ticker non trovato.")
                
                last_price = stock.history(period="1d")["Close"].iloc[-1]
                last_price = float(last_price)
            except Exception as yf_error:
                return file_pb2.UserResponse(message=f"Errore nel recupero dei dati del ticker: {str(yf_error)}")

            with self.conn:
                self.cursor.execute(
                    """
                    INSERT INTO tickers (ticker_name, last_price)
                    VALUES (%s, %s)
                    ON CONFLICT (ticker_name)
                    DO UPDATE SET last_price = EXCLUDED.last_price;
                    """,
                    (command.ticker, last_price)
                )

                self.cursor.execute(
                    """
                    INSERT INTO users (email, password, ticker, low_value, high_value)
                    VALUES (%s, %s, %s, %s, %s);
                    """,
                    (command.email, command.password, command.ticker, command.lowValue, command.highValue)
                )

            response = file_pb2.UserResponse(message="Successo")
        
        except psycopg2.IntegrityError as e:
            if "users_email_key" in str(e):
                response = file_pb2.UserResponse(message="Errore: email già registrata.")
            else:
                response = file_pb2.UserResponse(message=f"Errore d'integrità: {str(e)}")
        except Exception as e:
            response = file_pb2.UserResponse(message=f"Errore durante la registrazione: {str(e)}")

        with cache_lock:
            request_cache[command.requestID] = response

        return response

    
    # Funzione di aggiornamento utente
    def _execute_update_user(self, command):
        with cache_lock:
            if command.requestID in request_cache:
                print(f"[CACHE HIT] La richiesta con ID {command.requestID} è già stata processata.")
                return request_cache[command.requestID]

        try:
            # Recupero ticker con cache HTTP
            stock = yf.Ticker(command.ticker)
            last_price = stock.history(period="1d")["Close"].iloc[-1]
            last_price = float(last_price)

            # Transazione ridotta
            self.cursor.execute("""
                INSERT INTO tickers (ticker_name, last_price)
                VALUES (%s, %s)
                ON CONFLICT (ticker_name) DO NOTHING;
            """, (command.ticker, last_price))

            self.cursor.execute("""
                UPDATE users SET ticker = %s WHERE email = %s;
            """, (command.ticker, command.email))

            self.conn.commit()

            response = file_pb2.UserResponse(message="Ticker aggiornato con successo")
        except Exception as e:
            self.conn.rollback()
            response = file_pb2.UserResponse(message=f"Errore durante l'aggiornamento: {str(e)}")
        finally:
            with cache_lock:
                request_cache[command.requestID] = response

        return response
    
    # Funzione di aggiornamento soglie
    def _execute_update_thresholds(self, command):
        # Controllo nella cache
        with cache_lock:
            if command.requestID in request_cache:
                print(f"[CACHE HIT] La richiesta con ID {command.requestID} è già stata processata.")
                return request_cache[command.requestID]

        try:
            # Inizio della transazione
            self.cursor.execute("BEGIN")

            # Aggiorna direttamente i valori, controllando prima l'esistenza
            self.cursor.execute("""
                UPDATE users
                SET low_value = %s, high_value = %s
                WHERE email = %s
                RETURNING email;
            """, (command.lowValue, command.highValue, command.email))
            
            # Verifica se l'utente esiste
            updated_user = self.cursor.fetchone()
            if not updated_user:
                response = file_pb2.UserResponse(message="Errore: utente non trovato.")
            else:
                self.conn.commit()
                response = file_pb2.UserResponse(message="Valori aggiornati con successo.")
        
        except psycopg2.IntegrityError:
            self.conn.rollback()
            response = file_pb2.UserResponse(message="Errore di integrità: impossibile aggiornare le soglie.")
        except Exception as e:
            self.conn.rollback()
            response = file_pb2.UserResponse(message=f"Errore durante l'aggiornamento: {str(e)}")
        finally:
            # Memorizza il risultato nella cache
            with cache_lock:
                request_cache[command.requestID] = response

        return response

    # Funzione di eliminazione utente
    def _execute_delete_user(self, command):
        try:
            self.cursor.execute("DELETE FROM users WHERE email = %s;",(command.email,))
            self.conn.commit()
            if self.cursor.rowcount == 0:
                return file_pb2.UserResponse(message="Errore: utente non trovato.")
            else:
                return file_pb2.UserResponse(message="Successo")

        except Exception as e:
            self.conn.rollback()
            return file_pb2.UserResponse(message=f"Errore durante l'eliminazione: {str(e)}")