CREATE TABLE achievements
(
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    medal_id   TEXT    NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deck_id    INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS achievements_created_at ON achievements(created_at);
CREATE INDEX IF NOT EXISTS achievements_deck_id ON achievements(deck_id)
