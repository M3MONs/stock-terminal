CREATE TABLE user_agents (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    name      TEXT    NOT NULL,
    file_path TEXT    NOT NULL UNIQUE,
    enabled   INTEGER NOT NULL DEFAULT 1
);
