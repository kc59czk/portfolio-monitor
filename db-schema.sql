CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE sqlite_sequence(name,seq);
CREATE TABLE tickers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT UNIQUE NOT NULL,
    name TEXT,
    sector TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
, nazwa1 text);
CREATE TABLE prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume REAL,
    volume_avg_20 REAL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (ticker_id, date),
    FOREIGN KEY (ticker_id) REFERENCES tickers (id)
);
CREATE TABLE indicators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    rsi REAL,
    macd REAL,
    macd_signal REAL,
    vwma REAL,
    UNIQUE (ticker_id, date),
    FOREIGN KEY (ticker_id) REFERENCES tickers (id)
);
CREATE TABLE trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    ticker_id INTEGER NOT NULL,
    trade_date TEXT NOT NULL,
    action TEXT NOT NULL CHECK (action IN ('BUY', 'SELL')),
    quantity REAL NOT NULL,
    price REAL NOT NULL,
    fees REAL DEFAULT 0,
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (ticker_id) REFERENCES tickers (id)
);
CREATE TABLE alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    ticker_id INTEGER NOT NULL,
    indicator TEXT NOT NULL, -- e.g. 'RSI', 'MACD', 'PRICE'
    operator TEXT NOT NULL, -- e.g. '<', '>', 'crosses'
    value REAL,
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (ticker_id) REFERENCES tickers (id)
);
CREATE TABLE alert_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    alert_id INTEGER NOT NULL,
    ticker_id INTEGER NOT NULL,
    triggered_at TEXT NOT NULL,
    indicator_value REAL,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (alert_id) REFERENCES alerts (id),
    FOREIGN KEY (ticker_id) REFERENCES tickers (id)
);
CREATE TABLE volume_spikes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    volume REAL,
    avg_volume REAL,
    spike_multiplier REAL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticker_id) REFERENCES tickers (id)
);
CREATE TABLE news (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    content TEXT,
    source TEXT,
    published_at TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticker_id) REFERENCES tickers (id)
);
CREATE TABLE watchlists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
CREATE TABLE watchlist_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    watchlist_id INTEGER NOT NULL,
    ticker_id INTEGER NOT NULL,
    added_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (watchlist_id) REFERENCES watchlists (id),
    FOREIGN KEY (ticker_id) REFERENCES tickers (id)
);
CREATE TABLE portfolio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    ticker_id INTEGER NOT NULL,
    quantity REAL NOT NULL,
    average_price REAL NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (ticker_id) REFERENCES tickers (id)
);
CREATE TABLE settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    key TEXT NOT NULL,
    value TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, key),
    FOREIGN KEY (user_id) REFERENCES users (id)
); 