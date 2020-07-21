CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  uid TEXT NOT NULL,
  token TEXT NOT NULL,
  client TEXT NOT NULL,
  expiry TEXT NOT NULL,
  token_type TEXT DEFAULT "Bearer" NOT NULL 
);

INSERT INTO users(uid, token, client, expiry) VALUES ("", "", "", "")
