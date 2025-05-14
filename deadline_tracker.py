from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import execute_query, fetch_all
from datetime import datetime

# Tabela w bazie danych:
# deadlines (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, task TEXT, date TEXT)

def create_deadline_table():
    query = '''
    CREATE TABLE IF NOT EXISTS deadlines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        task TEXT,
        date TEXT
    );
    '''
    execute_query(query)

def add_deadline(user_id: int, task: str, date: str):
    parts = date.strip().split('.')
    if len(parts) == 2:
        today = datetime.today()
        date = f"{parts[0]}.{parts[1]}.{today.year}"
    try:
        date_obj = datetime.strptime(date, "%d.%m.%Y")
        date = date_obj.strftime("%Y-%m-%d")
    except ValueError:
        pass

    query = "INSERT INTO deadlines (user_id, task, date) VALUES (?, ?, ?);"
    execute_query(query, (user_id, task, date))

def get_deadlines(user_id: int):
    query = "SELECT id, task, date FROM deadlines WHERE user_id = ? ORDER BY date;"
    return fetch_all(query, (user_id,))

def delete_deadline(user_id: int, task_id: int):
    query = "DELETE FROM deadlines WHERE user_id = ? AND id = ?;"
    execute_query(query, (user_id, task_id))

def update_deadline(user_id: int, task_id: int, new_task: str, new_date: str):
    parts = new_date.strip().split('.')
    if len(parts) == 2:
        today = datetime.today()
        new_date = f"{parts[0]}.{parts[1]}.{today.year}"
    try:
        date_obj = datetime.strptime(new_date, "%d.%m.%Y")
        new_date = date_obj.strftime("%Y-%m-%d")
    except ValueError:
        pass

    query = "UPDATE deadlines SET task = ?, date = ? WHERE user_id = ? AND id = ?;"
    execute_query(query, (new_task, new_date, user_id, task_id))

def get_deadline_by_index(user_id: int, index: int):
    deadlines = get_deadlines(user_id)
    if 0 <= index < len(deadlines):
        return deadlines[index]  # (id, task, date)
    return None

def format_deadline_list(deadlines, with_instruction: bool = False):
    if not deadlines:
        return "📭 Nie masz jeszcze żadnych terminów."
    result = "📋 Twoje nadchodzące terminy:\n"
    for i, (task_id, task, date) in enumerate(deadlines, start=1):
        try:
            formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%d.%m.%Y")
        except ValueError:
            formatted_date = date
        result += f"{i}. {task} – {formatted_date}\n"
    if with_instruction:
        result += "\n✏️ Wpisz numer, aby edytować lub usunąć."
    return result

def deadline_main_menu():
    keyboard = [
        [InlineKeyboardButton("➕ Dodaj", callback_data="add_deadline"),
         InlineKeyboardButton("📅 Zobacz terminy", callback_data="view_deadlines")],
        [InlineKeyboardButton("✏️ Edytuj", callback_data="edit_deadline"),
         InlineKeyboardButton("🗑️ Usuń", callback_data="delete_deadline")],
        [InlineKeyboardButton("<< Wstecz", callback_data="menu_glowne")]
    ]
    return InlineKeyboardMarkup(keyboard)

def error_message_with_back(text: str):
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ Dodaj deadline", callback_data="add_deadline"),
            InlineKeyboardButton("<< Wstecz", callback_data="deadline")
        ]
    ])
    return text, keyboard

def success_message_with_back(text: str):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("<< Wstecz", callback_data="deadline")]
    ])
    return text, keyboard

def edit_prompt():
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("<< Wstecz", callback_data="deadline")]
    ])
    text = "✏️ Wyślij nową treść i datę w formacie:\n\nNowy opis – 25.05 lub 25.05.2025"
    return text, keyboard

def get_upcoming_deadlines(user_id: int, days: int = 5):
    query = "SELECT task, date FROM deadlines WHERE user_id = ?;"
    all_deadlines = fetch_all(query, (user_id,))
    upcoming = []
    today = datetime.today()

    for task, date_str in all_deadlines:
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
            diff = (date - today).days
            if 0 <= diff <= days:
                upcoming.append((task, date.strftime("%d.%m.%Y")))
        except:
            continue
    return upcoming