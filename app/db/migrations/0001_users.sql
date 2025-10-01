PRAGMA foreign_keys = ON;

-------------- USUARIOS ------------
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password_hash BLOB NOT NULL,
  tentativas INTEGER NOT NULL DEFAULT 0,
  bloqueado INTEGER NOT NULL DEFAULT 0, -- 0=false, 1=true
  must_change_password INTEGER NOT NULL DEFAULT 1,
  criado_em TEXT NOT NULL DEFAULT (datetime('now'))
);




