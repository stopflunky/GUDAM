import file_pb2
import yfinance as yf
from datetime import datetime, timedelta

class QueryService:

    # Funzione di login
    def _execute_login_user(self, command):
        try:
            self.cursor.execute("SELECT email, password FROM users WHERE email = %s", (command.email,))
            user = self.cursor.fetchone()

            if user is None:
                return file_pb2.UserResponse(message="Errore: utente non trovato. Devi registrarti.")

            db_email, db_password = user

            if command.password == db_password:
                return file_pb2.UserResponse(message="Successo")
            else:
                return file_pb2.UserResponse(message="Errore: password errata.")

        except Exception as e:
            return file_pb2.UserResponse(message=f"Errore durante il login: {str(e)}")
        
    # Funzione per ottenere il ticker di un utente
    def _execute_get_ticker_user(self, command):
        try:
            self.cursor.execute("SELECT ticker FROM users WHERE email = %s;", (command.email,))
            result = self.cursor.fetchone()
            if not result:
                return file_pb2.UserResponse(message="Errore: utente non trovato. Deve essere registrato.")
            
            ticker = result[0]
            print(f"Ticker: {ticker}")

            self.cursor.execute("SELECT last_price FROM tickers WHERE ticker_name = %s;", (ticker,))
            result = self.cursor.fetchone()
            if result:
                return file_pb2.UserResponse(message=f"Ticker: {ticker}, Valore: {result[0]}")
            else:
                return file_pb2.UserResponse(message="Errore: valore del titolo non trovato.")
            
        except Exception as e:
            return file_pb2.UserResponse(message=f"Errore durante la ricerca del valore del titolo: {str(e)}")

    # Funzione per ottenere la media degli ultimi X giorni di un ticker
    def _execute_get_average_price_of_x_days(self, command):
        try:
            days = int(command.days)

            self.cursor.execute("SELECT ticker FROM users WHERE email = %s;", (command.email,))
            result = self.cursor.fetchone()
            # Se non trovo l'utente, restituisco un messaggio di errore
            if not result:
                return file_pb2.UserResponse(message="Errore: utente non trovato. Deve essere registrato.")
            
            ticker = yf.Ticker(result[0])

            end_date = datetime.now()
            start_date = end_date - timedelta(days)

            data = ticker.history(start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))

            closing_price_average = data['Close'].mean()

            return file_pb2.UserResponse(message=f"Media degli ultimi {days} giorni: {closing_price_average}")

        except Exception as e:
            return file_pb2.UserResponse(message=f"Errore durante la ricerca del valore del titolo: {str(e)}") 
        
    # Funzione per ottenere le soglie (low_value e high_value) di un utente
    def _execute_get_thresholds(self, command):
        try:
            self.cursor.execute("SELECT low_value, high_value FROM users WHERE email = %s;", (command.email,))
            result = self.cursor.fetchone()

            if not result:
                return file_pb2.UserResponse(message="Errore: utente non trovato.")

            low_value, high_value = result
            return file_pb2.UserResponse(message=f"Soglie dell'utente: Low Value = {low_value}, High Value = {high_value}")

        except Exception as e:
            return file_pb2.UserResponse(message=f"Errore durante la ricerca delle soglie: {str(e)}")