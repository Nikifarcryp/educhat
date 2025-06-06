import psycopg2
import sqlite3
from datetime import datetime

def add_fullname_column():
    conn = connect()
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE users ADD COLUMN fullname TEXT;")
        conn.commit()
    except Exception as e:
        print("Kolumna fullname już istnieje lub wystąpił błąd:", e)
    finally:
        cur.close()
        conn.close()

def save_name_and_surname(user_id: int, fullname: str):
    conn = connect()
    cur = conn.cursor()
    cur.execute("UPDATE users SET fullname = %s WHERE telegram_id = %s", (fullname, user_id))
    conn.commit()
    cur.close()
    conn.close()

def get_user_info(user_id: int):
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT email, fullname FROM users WHERE telegram_id = %s", (user_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result


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

def create_table_linki():
    conn = connect()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS linki (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            link TEXT,
            notatka TEXT,
            data_dodania TEXT
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()

def create_files_table():
    conn = sqlite3.connect("workspace.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            file_id TEXT,
            notatka TEXT
        )
    """)
    conn.commit()
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

def init_workspace_db():
    conn = connect()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS linki (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            link TEXT,
            notatka TEXT,
            data_dodania TEXT
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()

def save_link(user_id, link, notatka=None):
    conn = connect()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO linki (user_id, link, notatka, data_dodania)
        VALUES (%s, %s, %s, %s)
    ''', (user_id, link, notatka, datetime.now().isoformat()))
    conn.commit()
    cur.close()
    conn.close()

def get_user_links(user_id):
    conn = connect()
    cur = conn.cursor()
    cur.execute('''
        SELECT id, link, notatka FROM linki
        WHERE user_id = %s
        ORDER BY data_dodania DESC
    ''', (user_id,))
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results

def save_file(user_id, file_id, podpis):
    conn = connect()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO notatki (user_id, file_id, podpis, data_dodania)
        VALUES (%s, %s, %s, %s)
    ''', (user_id, file_id, podpis, datetime.now().isoformat()))
    conn.commit()
    cur.close()
    conn.close()



def delete_link(link_id):
    conn = connect()
    cur = conn.cursor()
    cur.execute("DELETE FROM linki WHERE id = %s", (link_id,))
    conn.commit()
    cur.close()
    conn.close()


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

def delete_file(file_id):
    conn = connect()
    cur = conn.cursor()
    cur.execute("DELETE FROM notatki WHERE id = %s", (file_id,))
    conn.commit()
    cur.close()
    conn.close()


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


def get_user_files(user_id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, file_id, notatka FROM files WHERE user_id = ?", (user_id,))
    result = cursor.fetchall()
    conn.close()
    return result

