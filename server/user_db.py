import psycopg2

# Configurazione della connessione al DB
DATABASE_CONFIG = {
    "dbname": "Homework",
    "user": "postgres",
    "password": "Danilo2001",
    "host": "postgres-db-service",
    "port": "5432"
}

# Connessione effettiva al DB
conn = psycopg2.connect(**DATABASE_CONFIG)
cursor = conn.cursor()

# Ritorna la connessione se andata a buon fine
def getConnection():
    return conn