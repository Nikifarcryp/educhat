from datetime import datetime, timedelta
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

# Plan zajęć dla grupy C371
PLAN_C371 = {
    "poniedziałek": {
        "even": [
            {"godzina": "8:15", "przedmiot": "Testowanie oprogramowania (Wykład)", "prowadzący": "dr Artur Kulpa", "sala": "s. s.112 Lab. Cuk.8"},
            {"godzina": "10:00", "przedmiot": "Programowanie aplikacji chmurowych (LB)", "prowadzący": "dr Janusz Jakubiński", "sala": "s. 423 Lab. Cuk.8"},
            {"godzina": "12:00", "przedmiot": "Testowanie oprogramowania (LB)", "prowadzący": "dr Artur Kulpa", "sala": "SIL 137/138 Lab. Cuk.8"},
            {"godzina": "13:45", "przedmiot": "Testowanie oprogramowania (LB)", "prowadzący": "dr Janusz Jakubiński", "sala": "SIL 137/138 Lab. Cuk.8"}
        ],
        "odd": [
            {"godzina": "8:15", "przedmiot": "Programowanie aplikacji chmurowych (LB)", "prowadzący": "dr Janusz Jakubiński", "sala": " s. 423 Cuk.8"},
            {"godzina": "10:00", "przedmiot": "Programowanie aplikacji chmurowych (LB)", "prowadzący": "dr Janusz Jakubiński", "sala": " s. 423 Cuk.8"},
            {"godzina": "12:00", "przedmiot": "Testowanie oprogramowania (LB)", "prowadzący": "dr Artur Kulpa", "sala": "SIL 137/138 Cuk.8"}
        ]
    },
    "wtorek": {
        "even": [
            {"godzina": "12:00", "przedmiot": "Prawo w działalności gospodarczej (W)", "prowadzący": "dr Konrad Garnowski", "sala": "s. 307 Cuk.8"},
        ],
        "odd": [

        ]
    },
    "środa": {
        "even": [
            {"godzina": "10:00", "przedmiot": "Programowanie aplikacji chmurowych (Wykład)", "prowadzący": "Tomasz Zdziebko", "sala": "s. 307 Cuk.8"},
            {"godzina": "13:45", "przedmiot": "Zespołowy projekt z aplikacji internetowych (K)", "prowadzący": "dr inż. Mateusz Piwowarski", "sala": "s. SIL 204 Cuk.8"},
        ],
        "odd": [
            {"godzina": "10:00", "przedmiot": "Seminarium Dyplomowe (S)", "prowadzący": "dr hab. prof. US Ewa Krok", "sala": "gab. 418 Cuk.8"}
        ]
    },
    "czwartek": {
        "even": [
            {"godzina": "10:00", "przedmiot": "Język angielski (adv)", "prowadzący": "mgr Iwona Rokita-Lisiecka", "sala": "s. 046 Cukrowa 8"},
            {"godzina": "12:00", "przedmiot": "Język angielski", "prowadzący": "mgr Iwona Rokita-Lisiecka", "sala": "s. 046 Cukrowa 8"}
        ],
        "odd": [
            {"godzina": "10:00", "przedmiot": "Język angielski (adv)", "prowadzący": "mgr Iwona Rokita-Lisiecka", "sala": "s. 046 Cukrowa 8"},
            {"godzina": "12:00", "przedmiot": "Język angielski", "prowadzący": "mgr Iwona Rokita-Lisiecka", "sala": "s. 046 Cukrowa 8"}
        ]
    },
    "piątek": {
        "even": [

        ],
        "odd": [

        ]
    }
}

def is_even_week(date: datetime) -> bool:
    return date.isocalendar().week % 2 == 0

def get_plan_for_day(date: datetime) -> (str, InlineKeyboardMarkup):
    day_name = date.strftime('%A').lower()
    day_map = {
        "monday": "poniedziałek",
        "tuesday": "wtorek",
        "wednesday": "środa",
        "thursday": "czwartek",
        "friday": "piątek",
        "saturday": "sobota",
        "sunday": "niedziela"
    }
    polish_day = day_map.get(day_name, "")
    week_type = "even" if is_even_week(date) else "odd"

    plan_list = PLAN_C371.get(polish_day, {}).get(week_type, [])
    if not plan_list:
        return f"Brak zajęć na: {polish_day.capitalize()}", InlineKeyboardMarkup([[InlineKeyboardButton("<< Wstecz", callback_data="plan_zajec")]])

    formatted = f"✅ Świetnie, teraz możesz zobaczyć plan zajęć na {polish_day}, {date.strftime('%A %d.%m.%y')}\n"
    for entry in plan_list:
        formatted += f"\n⏰ {entry['godzina']} - <b>{entry['przedmiot']}</b>\n"
        formatted += f"Prowadzący: {entry['prowadzący']}\n"
        formatted += f"Sala: {entry['sala']}\n"
    keyboard = [[InlineKeyboardButton("<< Wstecz", callback_data="plan_zajec")]]
    return formatted, InlineKeyboardMarkup(keyboard)

def get_week_range(date: datetime) -> str:
    start = date - timedelta(days=date.weekday())
    end = start + timedelta(days=6)
    return f"{start.strftime('%d.%m.%y')} do {end.strftime('%d.%m.%y')}"

def get_week_label(date: datetime) -> str:
    return "parzysty" if is_even_week(date) else "nieparzysty"

def get_week_plan_text(date: datetime) -> (str, InlineKeyboardMarkup):
    label = get_week_label(date)
    week_range = get_week_range(date)
    formatted = f"✅ Świetnie, teraz możesz zobaczyć plan zajęć na tydzień od {week_range}\n\n<b>Tydzień {label}</b>\n\n(Obecnie widok graficzny jako zrzut lub grafika, funkcjonalność tekstowa w toku)"
    keyboard = [[InlineKeyboardButton("<< Wstecz", callback_data="plan_zajec")]]
    return formatted, InlineKeyboardMarkup(keyboard)

def get_week_plan_image_and_caption(date: datetime) -> (str, str):
    label = get_week_label(date)
    week_range = get_week_range(date)
    formatted = (
        f"✅ Świetnie, teraz możesz zobaczyć plan zajęć na tydzień od {week_range}"
        f"<b> Tydzień {label}</b>"
    )
    image_url = "https://imgur.com/a/0EL1olP"
    return image_url, formatted
