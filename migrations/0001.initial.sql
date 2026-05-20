CREATE TABLE watched_symbols (
    symbol TEXT PRIMARY KEY,
    tags   TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE app_config (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
