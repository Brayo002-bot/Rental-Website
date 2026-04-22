import sqlite3
import os

path = 'db.sqlite3'
if not os.path.exists(path):
    raise SystemExit('db.sqlite3 not found')

con = sqlite3.connect(path)
cur = con.cursor()

# Create users_user table if missing
cur.execute(
    '''CREATE TABLE IF NOT EXISTS users_user (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        password VARCHAR(128) NOT NULL,
        last_login DATETIME NULL,
        is_superuser BOOLEAN NOT NULL,
        username VARCHAR(150) NOT NULL UNIQUE,
        first_name VARCHAR(150) NOT NULL,
        last_name VARCHAR(150) NOT NULL,
        email VARCHAR(254) NOT NULL,
        is_staff BOOLEAN NOT NULL,
        is_active BOOLEAN NOT NULL,
        date_joined DATETIME NOT NULL,
        role VARCHAR(10) NOT NULL,
        phone VARCHAR(15)
    );'''
)

# Ensure migration record exists so Django sees it as applied
cur.execute(
    "INSERT OR IGNORE INTO django_migrations(app, name, applied) VALUES ('users','0001_initial', datetime('now'))"
)

con.commit()
con.close()
print('Ensured users_user table exists and users.0001_initial is recorded.')
