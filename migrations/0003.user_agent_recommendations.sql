CREATE TABLE user_agent_recommendations (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at  TEXT    NOT NULL,
    agent       TEXT    NOT NULL,
    symbol      TEXT    NOT NULL,
    opcja       TEXT    NOT NULL,
    stop_loss   REAL,
    stop_profit REAL,
    target_date TEXT,
    outcome     TEXT
);
