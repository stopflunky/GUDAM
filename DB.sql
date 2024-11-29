-- Tabella tickers
CREATE TABLE tickers 
(
	ticker_id SERIAL PRIMARY KEY,
    ticker_name VARCHAR(10) UNIQUE NOT NULL,  
    last_price float,          
    ticker_count INT NOT NULL DEFAULT 0  
);

-- Tabella utenti
CREATE TABLE users 
(
	user_id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
	password VARCHAR(255) NOT NULL,
    ticker VARCHAR(10) NOT NULL,         
    FOREIGN KEY (ticker) REFERENCES tickers(ticker_name) ON DELETE CASCADE
);

-- Funzione per incrementare il ticker_count
CREATE OR REPLACE FUNCTION increment_ticker_count()
RETURNS TRIGGER AS $$
BEGIN
    -- Incrementa il ticker_count
    UPDATE tickers
    SET ticker_count = ticker_count + 1
    WHERE ticker_name = NEW.ticker;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Funzione per gestire la modifica del ticker
CREATE OR REPLACE FUNCTION handle_ticker_update()
RETURNS TRIGGER AS $$
BEGIN
    -- Se il ticker è cambiato, aggiorna i contatori
    IF NEW.ticker != OLD.ticker THEN
        -- Decrementa il contatore del vecchio ticker
        UPDATE tickers
        SET ticker_count = ticker_count - 1
        WHERE ticker_name = OLD.ticker;

        -- Rimuove il vecchio ticker se il contatore è 0
        DELETE FROM tickers
        WHERE ticker_name = OLD.ticker AND ticker_count = 0;

        -- Incrementa il contatore del nuovo ticker
        UPDATE tickers
        SET ticker_count = ticker_count + 1
        WHERE ticker_name = NEW.ticker;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Funzione per decrementare il ticker_count e rimuovere il ticker se necessario
CREATE OR REPLACE FUNCTION decrement_ticker_count()
RETURNS TRIGGER AS $$
BEGIN
    -- Riduce il ticker_count
    UPDATE tickers
    SET ticker_count = ticker_count - 1
    WHERE ticker_name = OLD.ticker;

    -- Rimuove il ticker se il ticker_count è 0
    DELETE FROM tickers
    WHERE ticker_name = OLD.ticker AND ticker_count = 0;

    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

-- Trigger per incrementare il ticker_count quando un utente viene aggiunto
CREATE TRIGGER on_user_insert
AFTER INSERT ON users
FOR EACH ROW
EXECUTE FUNCTION increment_ticker_count();

-- Trigger associato alla cancellazione degli utenti
CREATE TRIGGER on_user_delete
AFTER DELETE ON users
FOR EACH ROW
EXECUTE FUNCTION decrement_ticker_count();

-- Trigger per gestire la modifica del ticker di un utente
CREATE TRIGGER on_user_update
AFTER UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION handle_ticker_update();