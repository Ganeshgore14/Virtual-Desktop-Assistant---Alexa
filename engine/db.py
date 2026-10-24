import csv
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = str(BASE_DIR / "jarvis.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS sys_command (
        id INTEGER PRIMARY KEY,
        name VARCHAR(100),
        path VARCHAR(1000)
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS web_command (
        id INTEGER PRIMARY KEY,
        name VARCHAR(100),
        url VARCHAR(1000)
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS contacts (
        id INTEGER PRIMARY KEY,
        name VARCHAR(200),
        mobile_no VARCHAR(255),
        email VARCHAR(255) NULL
    )''')
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE contacts SET name = 'omkar' WHERE mobile_no = '87885 70359'")
        conn.commit()
        print("Database initialized and updated.")
    except Exception as e:
        print(f"DB update error: {e}")
    finally:
        conn.close()