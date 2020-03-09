CREATE TABLE settings (
                          id INTEGER PRIMARY KEY AUTOINCREMENT,
                          current_game_id TEXT NOT NULL,
                          created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
);

INSERT INTO settings(current_game_id) VALUES ("halo_3")
