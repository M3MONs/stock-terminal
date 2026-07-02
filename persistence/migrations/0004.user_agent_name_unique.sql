DELETE FROM user_agents
WHERE id NOT IN (
    SELECT MIN(id) FROM user_agents GROUP BY name
);

ALTER TABLE user_agents RENAME TO user_agents_old;

CREATE TABLE user_agents (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    name      TEXT    NOT NULL UNIQUE,
    file_path TEXT    NOT NULL,
    enabled   INTEGER NOT NULL DEFAULT 1
);

INSERT INTO user_agents (id, name, file_path, enabled)
SELECT id, name, file_path, enabled FROM user_agents_old;

DROP TABLE user_agents_old;
