import psycopg2
#proverka na push
#proverka na push 3
#sdfgsdfsdf
#$sdfsdfsdfsdfsdfsd
#dsgfdsfgdfgdfgdfgdfgdfgdf
DB_HOST = "dpg-cvmlag3uibrs73bj4u6g-a.frankfurt-postgres.render.com"
DB_PORT = "5432"
DB_NAME = "educhat_9erf"
DB_USER = "educhat_9erf_user"
DB_PASSWORD = "Wq6byhOgtdbo0rMr3Upxn4EYelBC8oVN"

def connect():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

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