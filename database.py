import psycopg2
import sqlite3
from datetime import datetime


def connect():
    return psycopg2.connect(
        host="ep-proud-star-a2jggurn-pooler.eu-central-1.aws.neon.tech",
        database="neondb",
        user="neondb_owner",
        password="npg_mHiSW8NYr2uB",  # <- wklej hasło z Neona
        port="5432",
        sslmode="require"
    )

def create_table_notatki():
    conn = connect()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS notatki (
            id SERIAL PRIMARY KEY,
            user_id INTEGER,
            file_id TEXT,
            podpis TEXT,
            data_dodania TEXT
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()

def init_db():
    conn = connect()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            telegram_id BIGINT PRIMARY KEY,
            email TEXT,
            kod TEXT,
            czy_zalogowany BOOLEAN DEFAULT FALSE
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()

    create_table_notatki()

def save_note(user_id, file_id, podpis):
    conn = connect()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO notatki (user_id, file_id, podpis, data_dodania)
        VALUES (%s, %s, %s, %s)
    ''', (user_id, file_id, podpis, datetime.now().isoformat()))
    conn.commit()
    cur.close()
    conn.close()

def get_user_notes(user_id):
    conn = connect()
    cur = conn.cursor()
    cur.execute('''
        SELECT id, file_id, podpis FROM notatki
        WHERE user_id = %s
        ORDER BY data_dodania DESC
    ''', (user_id,))
    notes = cur.fetchall()
    cur.close()
    conn.close()
    return notes

def delete_note(note_id):
    conn = connect()
    cur = conn.cursor()
    cur.execute('DELETE FROM notatki WHERE id = %s', (note_id,))
    conn.commit()
    cur.close()
    conn.close()

def get_note_signature(note_id):
    conn = connect()
    cur = conn.cursor()
    cur.execute('SELECT podpis FROM notatki WHERE id = %s', (note_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result[0] if result else None





def save_code_and_email(telegram_id, email, kod):
    conn = connect()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO users (telegram_id, email, kod, czy_zalogowany)
        VALUES (%s, %s, %s, FALSE)
        ON CONFLICT (telegram_id) DO UPDATE
        SET email = EXCLUDED.email,
            kod = EXCLUDED.kod,
            czy_zalogowany = FALSE
    ''', (telegram_id, email, kod))
    conn.commit()
    cur.close()
    conn.close()

def confirm_code(telegram_id, wpisany_kod):
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT kod FROM users WHERE telegram_id = %s", (telegram_id,))
    wynik = cur.fetchone()
    if wynik and wynik[0] == wpisany_kod:
        cur.execute("UPDATE users SET czy_zalogowany = TRUE WHERE telegram_id = %s", (telegram_id,))
        conn.commit()
        cur.close()
        conn.close()
        return True
    cur.close()
    conn.close()
    return False

def is_logged_in(telegram_id):
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT czy_zalogowany FROM users WHERE telegram_id = %s", (telegram_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result is not None and result[0]

def logged_out(telegram_id):
    conn = connect()
    cur = conn.cursor()
    cur.execute("UPDATE users SET czy_zalogowany = FALSE WHERE telegram_id = %s", (telegram_id,))
    conn.commit()
    cur.close()
    conn.close()

DB_PATH = "neondb"

def execute_query(query: str, params: tuple = ()):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()

def fetch_all(query: str, params: tuple = ()):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()