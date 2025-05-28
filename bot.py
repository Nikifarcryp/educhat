import os, re
from dotenv import load_dotenv
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
from serpapi import GoogleSearch
import random
from database import *
from plan_zajec_c371 import get_plan_for_day, get_week_plan_text, get_week_plan_image_and_caption
from database import save_note
from telegram.ext import MessageHandler, filters
from telegram.request import HTTPXRequest
from deadline_tracker import (
    create_deadline_table, add_deadline, get_deadlines,
    delete_deadline, update_deadline, format_deadline_list,
    deadline_main_menu, get_deadline_by_index, edit_prompt, get_upcoming_deadlines
)
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

from database import init_workspace_db
init_workspace_db()
from database import save_link
from database import get_user_links
from database import delete_link
plik_states = {}  # user_id -> file_id

from database import create_files_table
create_files_table()


from mail_sender import wyslij_maila

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Przygotowujemy przyciski ReplyKeyboard (pod polem wiadomości)
    reply_keyboard = [
        ["/status"],
        ["/wyloguj"]
    ]
    reply_markup_keyboard = ReplyKeyboardMarkup(
        reply_keyboard,
        resize_keyboard=True
    )

    if is_logged_in(user_id):
        keyboard = [
            [InlineKeyboardButton("Plan zajęć", callback_data="plan_zajec"),
             InlineKeyboardButton("Aktualności", callback_data="aktualnosci")],
            [InlineKeyboardButton("Przestrzeń robocza", callback_data="przestrzen_robocza"),
             InlineKeyboardButton("Asystent AI", callback_data="asystent_ai")],
            [InlineKeyboardButton("Dalej >>", callback_data="dalej")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "🎉 Jesteś już zalogowany jako student USZ!\n\n✅ W czym mogę Ci pomóc?\n\n👇 Wybierz opcję z menu nawigacyjnego:",
            reply_markup=reply_markup
        )

    else:
        # Jeśli nie zalogowany → klasyczne przywitanie + szybkie komendy
        keyboard = [
            [InlineKeyboardButton("Zaloguj się", callback_data="zaloguj")]
        ]
        reply_markup_inline = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "Cześć! Tu EduChat – twój pomocnik na uczelni. 🎓 Gotowy? Kliknij przycisk „Zaloguj się” poniżej!",
            reply_markup=reply_markup_keyboard
        )

        await update.message.reply_text(
            "👇",
            reply_markup=reply_markup_inline
        )




async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "zaloguj":
        keyboard = [
            [InlineKeyboardButton("Wpisz adres e-mail", callback_data="wpisz_email")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text="📧 Wpisz mail w domenie @stud.usz.edu.pl (tylko dla studentów USZ 💙)",
            reply_markup=reply_markup
        )

    elif query.data == "wpisz_email":
        await query.edit_message_text(
            text="🖊️ Teraz wpisz swój adres e-mail komendą:\n\n`/zaloguj twoj@stud.usz.edu.pl`",
            parse_mode="Markdown"
        )


    elif query.data == "plan_zajec":
        await query.edit_message_text(
            text="🚀 Super! \nTeraz wybierz odpowiednią dla siebie opcję:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Dzisiaj", callback_data="plan_dzisiaj"),
                 InlineKeyboardButton("Jutro", callback_data="plan_jutro")],
                [InlineKeyboardButton("Tydzień", callback_data="plan_tydzien")],
                [InlineKeyboardButton("<< Wróć", callback_data="menu_glowne")]
            ])
        )


    elif query.data == "plan_dzisiaj":
        today = datetime.today()
        text, markup = get_plan_for_day(today)
        await query.edit_message_text(text=text, reply_markup=markup, parse_mode="HTML")


    elif query.data == "plan_jutro":
        tomorrow = datetime.today() + timedelta(days=1)
        text, markup = get_plan_for_day(tomorrow)
        await query.edit_message_text(text=text, reply_markup=markup, parse_mode="HTML")



    elif query.data == "plan_tydzien":
        image_url, caption = get_week_plan_image_and_caption(datetime.today())

        sent_photo = await context.bot.send_photo(
            chat_id=query.message.chat_id,
            photo=image_url,
            caption=caption,
            parse_mode="HTML"
        )


        context.user_data["plan_image_message_id"] = sent_photo.message_id

        await query.edit_message_text(
            text="🖼️ Wyświetlono plan tygodnia. Możesz wrócić do menu:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("<< Wstecz", callback_data="plan_zajec_back")]
            ])
        )

    elif query.data == "plan_zajec_back":
        # Usuń wiadomość ze zdjęciem
        if "plan_image_message_id" in context.user_data:
            try:
                await context.bot.delete_message(
                    chat_id=query.message.chat_id,
                    message_id=context.user_data["plan_image_message_id"]
                )
            except:
                pass  # ignorujemy błędy przy usuwaniu
            del context.user_data["plan_image_message_id"]

        # Edytujemy obecną wiadomość – wracamy do wyboru opcji planu
        await query.edit_message_text(
            text="🚀 Super! \nTeraz wybierz odpowiednią dla siebie opcję:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Dzisiaj", callback_data="plan_dzisiaj"),
                 InlineKeyboardButton("Jutro", callback_data="plan_jutro")],
                [InlineKeyboardButton("Tydzień", callback_data="plan_tydzien")],
                [InlineKeyboardButton("<< Wróć", callback_data="menu_glowne")]
            ])
        )


    elif query.data == "menu_glowne":
        keyboard = [
            [InlineKeyboardButton("Plan zajęć", callback_data="plan_zajec"), InlineKeyboardButton("Aktualności", callback_data="aktualnosci")],
            [InlineKeyboardButton("Przestrzeń robocza", callback_data="przestrzen_robocza"), InlineKeyboardButton("Asystent AI", callback_data="asystent_ai")],
            [InlineKeyboardButton("Dalej >>", callback_data="dalej")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text="🎓 Menu główne:\n\nWybierz, co chcesz zrobić:",
            reply_markup=reply_markup
        )


    elif query.data == "aktualnosci":
        user_id = query.from_user.id
        upcoming = get_upcoming_deadlines(user_id)
        if not upcoming:
            await query.edit_message_text(
                "📭 Brak nadchodzących wydarzeń w ciągu 5 dni.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("<< Wstecz", callback_data="menu_glowne")]
                ])
            )

        else:
            message = "📰 <b>Twoje najbliższe wydarzenia:</b>\n\n"
            for task, date in upcoming:
                message += (
                    f"📌 <b>{task}</b>\n"
                    f"🗓️ <i>Wydarzenie odbędzie się {date}</i>\n"
                    f"<i>📅 Opublikowano: {datetime.today().strftime('%d.%m.%y')}</i>\n\n"
                )

            await query.edit_message_text(
                message,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("<< Wstecz", callback_data="menu_glowne")]
                ])
            )


    elif query.data == "przestrzen_robocza":
        keyboard = [
            [
                InlineKeyboardButton("📎 Linki", callback_data="workspace_links"),
                InlineKeyboardButton("📁 Pliki", callback_data="workspace_files")
            ],
            [
                InlineKeyboardButton("🔙 Wróć", callback_data="menu_glowne")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="📂 Wybierz czym chcesz pracować?",
            reply_markup=reply_markup
        )

    # ← вот здесь без отступа
    elif query.data == "workspace_links":
        keyboard = [
            [
                InlineKeyboardButton("➕ Dodaj link", callback_data="dodaj_link"),
                InlineKeyboardButton("👁 Zobacz linki", callback_data="zobacz_linki")
            ],
            [
                InlineKeyboardButton("❌ Usuń link", callback_data="usun_link"),
                InlineKeyboardButton("🔙 Wróć", callback_data="przestrzen_robocza")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="🔗 Co chcesz zrobić z linkami?",
            reply_markup=reply_markup
        )

    elif query.data == "dodaj_link":
        context.user_data["dodaj_link"] = True  # флаг: ждём линк

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Wstecz", callback_data="workspace_links")]
        ])

        await query.edit_message_text(
            text="📎 Super! Wklej link, który chcesz zapisać w swojej przestrzeni roboczej.",
            reply_markup=keyboard
        )

    elif query.data == "dodaj_notatke_do_linku":
        context.user_data["czekam_na_notatke"] = True

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Wstecz", callback_data="workspace_links")]
        ])

        await query.edit_message_text(
            text="📝 Wpisz notatkę, którą chcesz dodać do linku:",
            reply_markup=keyboard
        )
    elif query.data == "zapisz_link_bez_notatki":
        link = context.user_data.get("nowy_link")
        user_id = query.from_user.id

        from database import save_link
        save_link(user_id, link, notatka=None)
        context.user_data.clear()

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Dodaj kolejny", callback_data="dodaj_link"),
             InlineKeyboardButton("📂 Wróć do menu", callback_data="workspace_links")]
        ])

        await query.edit_message_text(
            text=f"✅ Link zapisany!\n\n🔗 Link: {link}\n📝 Notatka: brak",
            reply_markup=keyboard
        )

    elif query.data == "usun_link":
        from database import get_user_links
        user_id = query.from_user.id
        links = get_user_links(user_id)

        if not links:
            await query.edit_message_text(
                text="📭 Nie masz jeszcze żadnych zapisanych linków do usunięcia.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📂 Wróć do menu", callback_data="workspace_links")]
                ])
            )
            return

        # сохраняем ссылки во временное хранилище
        context.user_data["usun_links"] = links
        context.user_data["usun_etap"] = "czekam_na_numer"

        # 1 сообщение — список
        text = "🧾 *Twoje zapisane linki:*\n\n"
        for i, (id, link, notatka) in enumerate(links, start=1):
            text += f"*{i}. Link:* {link}\n"
            if notatka:
                text += f"📝 *Notatka:* {notatka}\n"
            text += "\n"

        await query.message.reply_text(text.strip(), parse_mode="Markdown")

        # 2 сообщение — просьба о номере
        await query.message.reply_text(
            text="✏️ *Napisz numer linku, który chcesz usunąć:*",
            parse_mode="Markdown"
        )
    elif query.data == "potwierdz_usun_link":
        from database import delete_link

        link_id = context.user_data.get("usun_wybrany")
        delete_link(link_id)

        context.user_data.pop("usun_etap", None)
        context.user_data.pop("usun_links", None)
        context.user_data.pop("usun_wybrany", None)

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🗑 Usuń kolejny", callback_data="usun_link")],
            [InlineKeyboardButton("📂 Wróć do menu", callback_data="workspace_links")]
        ])

        await query.edit_message_text(
            text="✅ Link został usunięty z Twojej przestrzeni roboczej.",
            reply_markup=keyboard
        )
    elif query.data == "anuluj_usuwanie":
        context.user_data.pop("usun_etap", None)
        context.user_data.pop("usun_links", None)
        context.user_data.pop("usun_wybrany", None)

        await query.edit_message_text(
            text="❎ Usuwanie anulowane.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📂 Wróć do menu", callback_data="workspace_links")]
            ])
        )
    elif query.data == "zobacz_linki":
        from database import get_user_links  # ← вот эта строчка нужна

        user_id = query.from_user.id
        links = get_user_links(user_id)

        if not links:
            await query.edit_message_text(
                text="📭 Nie masz jeszcze żadnych zapisanych linków.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Dodaj link", callback_data="dodaj_link")],
                    [InlineKeyboardButton("📂 Wróć", callback_data="workspace_links")]
                ])
            )
            return

        text = "📑 *Oto Twoje zapisane linki:*\n\n"
        for i, (id, link, notatka) in enumerate(links, start=1):
            text += f"*{i}. Link:* {link}\n"
            if notatka:
                text += f"📝 *Notatka:* {notatka}\n"
            else:
                text += f"📝 *Notatka:* brak\n"
            text += "\n"

        await query.edit_message_text(
            text=text.strip(),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📂 Wróć", callback_data="workspace_links")]
            ])
        )
    elif query.data == "workspace_files":
        await query.edit_message_text(
            text="📁Co chcesz zrobić z plikami?",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Dodaj plik", callback_data="dodaj_plik"),
                 InlineKeyboardButton("👁 Zobacz pliki", callback_data="zobacz_pliki")],
                [InlineKeyboardButton("❌ Usuń plik", callback_data="usun_plik"),
                 InlineKeyboardButton("🔙 Wróć", callback_data="przestrzen_robocza")]
            ])
        )


    elif query.data == "zobacz_pliki":
        from database import get_user_notes

        user_id = query.from_user.id
        notes = get_user_notes(user_id)

        if not notes:
            await query.edit_message_text(
                text="📭 Nie masz jeszcze żadnych zapisanych plików.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Dodaj plik", callback_data="dodaj_plik")],
                    [InlineKeyboardButton("📂 Wróć", callback_data="workspace_files")]
                ])
            )
            return

        for note in notes:
            note_id, file_id, podpis = note
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📂 Wróć", callback_data="workspace_files")]
            ])

            if file_id.startswith("AgAC"):  # jeśli zdjęcie
                await context.bot.send_photo(
                    chat_id=user_id,
                    photo=file_id,
                    caption=f"📝 {podpis}",

                )
            else:  # jeśli dokument lub inny plik
                await context.bot.send_document(
                    chat_id=user_id,
                    document=file_id,
                    caption=f"📝 {podpis}",

                )

        await context.bot.send_message(
            chat_id=user_id,
            text="📁 To wszystkie Twoje pliki.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📂 Wróć", callback_data="workspace_files")]
            ])
        )


    elif query.data == "usun_plik":
        from database import get_user_notes

        user_id = query.from_user.id
        notes = get_user_notes(user_id)

        if not notes:
            await query.edit_message_text(
                text="📭 Nie masz jeszcze żadnych plików do usunięcia.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📂 Wróć", callback_data="workspace_files")]
                ])
            )
            return

        context.user_data["usun_plik_lista"] = notes
        context.user_data["usun_plik_etap"] = "czekam_na_numer"

        text = "🧾 *Twoje pliki:*\n\n"
        for i, (note_id, file_id, podpis) in enumerate(notes, start=1):
            text += f"{i}. 📝 {podpis}\n"

        await context.bot.send_message(query.from_user.id, text=text, parse_mode="Markdown")
        await context.bot.send_message(query.from_user.id, text="✏️ Wpisz numer pliku, który chcesz usunąć:")


    elif query.data == "potwierdz_usun_plik":
        from database import delete_file
        file_id = context.user_data.get("usun_plik_wybrany")
        delete_file(file_id)

        context.user_data.pop("usun_plik_lista", None)
        context.user_data.pop("usun_plik_wybrany", None)
        context.user_data.pop("usun_plik_etap", None)

        await query.edit_message_text("✅ Plik został usunięty.",
                reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Wróć do menu", callback_data="workspace_files")]
            ]))


    elif query.data == "dodaj_plik":
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="📤 Wklej plik, który chcesz zapisać w przestrzeni roboczej.\n\n(Pamiętaj: zdjęcia *tylko jako plik*)",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Wróć", callback_data="workspace_files")]
            ])
        )
        context.user_data["plik_state"] = "awaiting_file"

    elif query.data == "plik_dodaj_notatke":
        await query.message.reply_text(
            "✍️ Wpisz notatkę do pliku:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Wróć", callback_data="workspace_files")]
            ])
        )
        context.user_data["state"] = "awaiting_file_note"

    elif query.data == "plik_bez_notatki":
        from database import save_file
        user_id = query.from_user.id
        file_id = plik_states.pop(user_id, None)
        if file_id:
            save_file(user_id, file_id, "")
            await query.message.reply_text(
                f"📂 Plik został zapisany:\nPlik: `{file_id}`\nNotatka: brak",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Dodaj kolejny", callback_data="plik_dodaj")],
                    [InlineKeyboardButton("🏠 Wróć do menu", callback_data="main_menu")]
                ])
            )
        context.user_data["state"] = None
    elif query.data == "plik_dodaj_notatke":
        await query.message.reply_text(
            "✍️ Wpisz notatkę do pliku:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Wróć", callback_data="workspace_files")]
            ])
        )
        context.user_data["state"] = "awaiting_file_note"











    elif query.data == "asystent_ai":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("<< Wstecz", callback_data="menu_glowne")]
        ])
        await query.edit_message_text("🤖 Funkcja 'Asystent AI' w budowie... 🛠️",
        reply_markup=keyboard)


    elif query.data == "dalej":

        keyboard = [
            [InlineKeyboardButton("Terminy", callback_data="deadline"),
            InlineKeyboardButton("Literatura", callback_data="literatura"),
             InlineKeyboardButton("Lista funkcji", callback_data="lista_funkcji")],
            [InlineKeyboardButton("<< Wstecz", callback_data="menu_glowne"),
             InlineKeyboardButton("Dalej >>", callback_data="dalej2")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(

            text="🧠 Menu główne:\n\nWybierz, co chcesz zrobić:",
            reply_markup=reply_markup

        )


    elif query.data == "deadline":
        await query.edit_message_text(
            text="🌸 Witaj w zarządzaniu terminami!\n\n"
                 "Tutaj możesz zapisywać wszystkie ważne terminy – oddania prac, kolokwia, egzaminy, a także osobiste zadania i przypomnienia.\n\n"
                 "Dzięki temu nic Ci nie umknie – wszystko w jednym miejscu, zawsze pod ręką.\n\nCo chcesz zrobić?",
            reply_markup=deadline_main_menu()
        )

    elif query.data == "add_deadline":
        await query.edit_message_text(
            text="✏️ Podaj nazwę wydarzenia i termin w formacie:\nnazwa – DD.MM.RRRR\n\nPrzykład:\nPrezentacja z marketingu - 16.05",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("<< Wstecz", callback_data="deadline")]])
        )
        context.user_data["awaiting_deadline"] = True

    elif query.data == "view_deadlines":
        user_id = query.from_user.id
        deadlines = get_deadlines(user_id)
        text = format_deadline_list(deadlines)
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("<< Wstecz", callback_data="deadline")]]),
            parse_mode="HTML"
        )

    elif query.data == "edit_deadline":
        user_id = query.from_user.id
        deadlines = get_deadlines(user_id)
        if not deadlines:
            await query.edit_message_text(
                "📭 Nie masz jeszcze żadnych terminów.",
                reply_markup=deadline_main_menu()
            )
        else:
            context.user_data["deadline_action"] = "edit"
            await query.edit_message_text(
                format_deadline_list(deadlines, with_instruction=True),
                reply_markup=deadline_main_menu()
            )

    elif query.data == "delete_deadline":
        user_id = query.from_user.id
        deadlines = get_deadlines(user_id)
        if not deadlines:
            await query.edit_message_text(
                "📭 Nie masz jeszcze żadnych terminów.",
                reply_markup=deadline_main_menu()
            )
        else:
            context.user_data["deadline_action"] = "delete"
            await query.edit_message_text(
                format_deadline_list(deadlines, with_instruction=True),
                reply_markup=deadline_main_menu()
            )


    elif query.data == "literatura":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("<< Wstecz", callback_data="menu_glowne")]
        ])
        await query.edit_message_text("📚 Funkcja 'Literatura' w budowie... 🛠️",
        reply_markup=keyboard)

    elif query.data == "lista_funkcji":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("<< Wstecz", callback_data="menu_glowne")]
        ])
        await query.edit_message_text("🧾 Funkcja 'Lista funkcji' w budowie... 🛠️",
        reply_markup=keyboard)



    elif query.data == "dalej2":

        keyboard = [
            [InlineKeyboardButton("Konto", callback_data="konto"),
             InlineKeyboardButton("O nas", callback_data="o_nas")],
            [InlineKeyboardButton("Wsparcie", callback_data="wsparcie"),
             InlineKeyboardButton("Prywatność", callback_data="prywatnosc")],
            [InlineKeyboardButton("<< Wstecz", callback_data="dalej")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(

            text="⚙️ Menu główne:\n\nWybierz, co chcesz zrobić:",
            reply_markup=reply_markup

        )


    elif query.data == "konto":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("<< Wstecz", callback_data="menu_glowne")]
        ])
        await query.edit_message_text("👤 Funkcja 'Konto' w budowie... 🛠️",
        reply_markup=keyboard)

    elif query.data == "o_nas":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("<< Wstecz", callback_data="menu_glowne")]
        ])
        await query.edit_message_text("ℹ️ Funkcja 'O nas' w budowie... 🛠️",
        reply_markup=keyboard
    )

    elif query.data == "wsparcie":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("<< Wstecz", callback_data="menu_glowne")]
        ])
        await query.edit_message_text("🤝 Funkcja 'Wsparcie' w budowie... 🛠️",
        reply_markup=keyboard
    )

    elif query.data == "prywatnosc":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("<< Wstecz", callback_data="menu_glowne")]
        ])
        await query.edit_message_text("🔐 Funkcja 'Prywatność' w budowie... 🛠️",
        reply_markup=keyboard
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("czekam_na_podpis"):
        podpis = update.message.text
        user_id = update.effective_user.id
        file_id = context.user_data.get("nowa_notatka_file_id")

        save_note(user_id, file_id, podpis)
        context.user_data.clear()

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Dodaj kolejną", callback_data="dodaj_notatke"),
             InlineKeyboardButton("📂 Wróć do menu notatek", callback_data="notatki")]
        ])

        await update.message.reply_text(
            "✅ Notatka została zapisana!\n\nCo teraz?",
            reply_markup=keyboard
        )

        # === DODAWANIE LINKU ===
        if context.user_data.get("dodaj_link"):
            link = update.message.text.strip()

            context.user_data["nowy_link"] = link
            context.user_data["dodaj_link"] = False

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Tak", callback_data="dodaj_notatke_do_linku"),
                 InlineKeyboardButton("❌ Nie", callback_data="zapisz_link_bez_notatki")],
                [InlineKeyboardButton("🔙 Wstecz", callback_data="workspace_links")]
            ])

            await update.message.reply_text(
                text=f"📝 Czy chcesz dodać notatkę do tego linku?\n\n🔗 {link}",
                reply_markup=keyboard
            )
            return


async def clean_send(update_or_query, context, text, reply_markup=None, photo=None):
    chat_id = update_or_query.effective_chat.id if hasattr(update_or_query, 'effective_chat') else update_or_query.message.chat.id

    # Удалить предыдущее сообщение, если есть
    if "ostatnie_id" in context.user_data:
        try:
            await context.bot.delete_message(chat_id, context.user_data["ostatnie_id"])
        except:
            pass

    # Отправить фото или текст
    if photo:
        msg = await context.bot.send_photo(chat_id=chat_id, photo=photo, caption=text, reply_markup=reply_markup)
    else:
        if hasattr(update_or_query, "message"):
            msg = await update_or_query.message.reply_text(text, reply_markup=reply_markup)
        else:
            msg = await update_or_query.edit_message_text(text=text, reply_markup=reply_markup)

    # Сохранить ID
    context.user_data["ostatnie_id"] = msg.message_id



async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_logged_in(user_id):
        await update.message.reply_text("✅ Jesteś zalogowany jako student.")
    else:
        await update.message.reply_text("🔐 Nie jesteś zalogowany. Użyj /zaloguj aby uzyskać dostęp.")

async def zaloguj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if is_logged_in(user_id):
        await update.message.reply_text("✅ Już jesteś zalogowany jako student.")
        return

    if not context.args:
        await update.message.reply_text("📧 Podaj swój uczelniany mail: `/zaloguj twoj@stud.usz.edu.pl`", parse_mode="Markdown")
        return

    email = context.args[0]
    if not email.endswith("@stud.usz.edu.pl"):
        await update.message.reply_text("❌ Ten adres e-mail nie należy do domeny studenckiej USZ.")
        return

    kod = str(random.randint(100000, 999999))
    save_code_and_email(user_id, email, kod)
    wyslij_maila(email, kod)
    await update.message.reply_text(
        "📩 Wysłano kod weryfikacyjny na Twój adres e-mail.\n\n🖊️ Wpisz go komendą:\n\n`/kod `",
        parse_mode="Markdown"
    )

async def code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if is_logged_in(user_id):
        await update.message.reply_text("✅ Już jesteś zalogowany.")
        return

    if not context.args:
        await update.message.reply_text("🔢 Wpisz kod, który otrzymałeś e-mailem: `/kod 123456`", parse_mode="Markdown")
        return

    wpisany_kod = context.args[0]
    if confirm_code(user_id, wpisany_kod):
        # Sukces – wyświetlamy menu główne
        keyboard = [
            [InlineKeyboardButton("Plan zajęć", callback_data="plan_zajec"), InlineKeyboardButton("Aktualności", callback_data="aktualnosci")],
            [InlineKeyboardButton("Przestrzeń robocza", callback_data="przestrzen_robocza"), InlineKeyboardButton("Asystent AI", callback_data="asystent_ai")],
            [InlineKeyboardButton("Dalej >>", callback_data="dalej")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "🎉 Zalogowano pomyślnie jako student USZ!\n\nW czym mogę Ci pomóc?\n\n✅ Sprawdź plan, salę, zadaj pytanie...\n👇 Wybierz opcję lub przejdź dalej:",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text("❌ Nieprawidłowy kod. Sprawdź jeszcze raz.")

async def menu_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    #if query.data == "plan_zajec":
       #await query.edit_message_text("📚 Funkcja 'Plan zajęć' w budowie... 🛠️")
    #elif query.data == "aktualnosci":
#await query.edit_message_text("📰 Funkcja 'Aktualności' w budowie... 🛠️")
    #elif query.data == "przestrzen_robocza":
     #   await query.edit_message_text("📂 Funkcja 'Przestrzeń robocza' w budowie... 🛠️")
  #  elif query.data == "asystent_ai":
#        await query.edit_message_text("🤖 Funkcja 'Asystent AI' w budowie... 🛠️")
#    elif query.data == "dalej":
 #       await query.edit_message_text("➡️ Funkcja 'Dalej' w budowie... 🛠️")

async def wyloguj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if is_logged_in(user_id):
        logged_out(user_id)
        await update.message.reply_text("👋 Zostałeś wylogowany. Do zobaczenia wkrótce!")
    else:
        await update.message.reply_text("🔐 Nie jesteś aktualnie zalogowany.")

async def szukaj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_logged_in(user_id):
        await update.message.reply_text("🔐 Najpierw musisz się zalogować przez /zaloguj.")
        return

    zapytanie = ' '.join(context.args)
    if not zapytanie:
        await update.message.reply_text("Napisz, czego mam poszukać 🧐")
        return

    search = GoogleSearch({
        "q": zapytanie,
        "api_key": SERPAPI_KEY
    })
    results = search.get_dict()
    if "organic_results" in results:
        odpowiedzi = [res["title"] + "\n" + res["link"] for res in results["organic_results"][:3]]
        await update.message.reply_text("\n\n".join(odpowiedzi))
    else:
        await update.message.reply_text("Niestety, nic nie znalazłam 😢")

async def handle_invalid_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("dodaj_notatke"):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📂 Wróć do menu notatek", callback_data="notatki")]
        ])

        await update.message.reply_text(
            "❌ Możesz przesłać tylko zdjęcie lub plik PDF. Inne formaty i wiadomości tekstowe nie są obsługiwane.",
            reply_markup=keyboard
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    # 📎 Dodawanie linku (obsługuje tylko wklejony link)
    if context.user_data.get("dodaj_link"):
        import re
        link = text
        link_pattern = re.compile(r'(https?://)?([a-zA-Z0-9\-]+\.)+[a-zA-Z]{2,}(/.*)?')

        if not link_pattern.fullmatch(link):
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Wstecz", callback_data="workspace_links")]
            ])
            await update.message.reply_text(
                text="❗ To nie wygląda jak prawidłowy link.\n\n🧠 Sprawdź pisownię lub upewnij się, że to naprawdę adres strony (np. google.com)",
                reply_markup=keyboard
            )
            return

        context.user_data["nowy_link"] = link
        context.user_data["dodaj_link"] = False

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Tak", callback_data="dodaj_notatke_do_linku"),
             InlineKeyboardButton("❌ Nie", callback_data="zapisz_link_bez_notatki")],
            [InlineKeyboardButton("🔙 Wstecz", callback_data="workspace_links")]
        ])

        await update.message.reply_text(
            text=f"📝 Czy chcesz dodać notatkę do tego linku?\n\n🔗 {link}",
            reply_markup=keyboard
        )
        return

    # 🔥 ДОДАНО: obsługa notatki do pliku
    if context.user_data.get("plik_state") == "czekaj_na_notatke":
        podpis = text
        file_id = context.user_data.get("plik_file_id")

        if not file_id:
            await update.message.reply_text("❌ Nie znaleziono pliku. Spróbuj jeszcze raz.")
            return

        from database import save_file
        save_file(user_id, file_id, podpis)

        await update.message.reply_text(
            f"✅ Plik został zapisany!\n📎 Plik ID: `{file_id}`\n📝 Notatka: {podpis}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Dodaj kolejny", callback_data="plik_dodaj")],
                [InlineKeyboardButton("🏠 Wróć do menu", callback_data="workspace_files")]
            ])
        )
        context.user_data.pop("plik_state", None)
        context.user_data.pop("plik_file_id", None)

    elif context.user_data.get("usun_etap") == "czekam_na_numer":
        numer = update.message.text.strip()

        if not numer.isdigit():
            await update.message.reply_text("⚠️ Wpisz tylko numer linku (np. 1, 2, 3...)")
            return

        index = int(numer) - 1
        links = context.user_data.get("usun_links", [])
        if index < 0 or index >= len(links):
            await update.message.reply_text("❌ Nie ma linku o takim numerze.")
            return

        # znaleziono link
        link_id, link, notatka = links[index]
        context.user_data["usun_wybrany"] = link_id
        context.user_data["usun_etap"] = "potwierdz_usuniecie"

        text = f"🔐 *Czy na pewno chcesz usunąć ten link?*\n\n🔗 {link}"
        if notatka:
            text += f"\n📝 {notatka}"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Tak", callback_data="potwierdz_usun_link")],
            [InlineKeyboardButton("❌ Anuluj", callback_data="anuluj_usuwanie")]
        ])

        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=keyboard)
        return


    # 🔽 Poniżej — pozostałe rzeczy, które już były
    # ✏️ Dodawanie notatki do linku
    if context.user_data.get("czekam_na_notatke"):
        notatka = text
        link = context.user_data.get("nowy_link")
        user_id = update.effective_user.id

        from database import save_link
        save_link(user_id, link, notatka)

        context.user_data.clear()

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Dodaj kolejny", callback_data="dodaj_link")],
            [InlineKeyboardButton("📂 Wróć do menu", callback_data="workspace_links")]
        ])

        await update.message.reply_text(
            text=f"✅ Link zapisany!\n\n🔗 Link: {link}\n📝 Notatka: {notatka}",
            reply_markup=keyboard
        )
        return

    # ➕ Dodawanie deadline'u
    if context.user_data.get("awaiting_deadline"):
        try:
            if "-" not in text:
                raise ValueError("Brak separatora")

            task, raw_date = [s.strip() for s in text.split("-", 1)]

            # Dodaj bieżący rok, jeśli nie został podany
            parts = raw_date.split(".")
            if len(parts) == 2:
                raw_date = f"{parts[0]}.{parts[1]}.{datetime.today().year}"

            date_obj = datetime.strptime(raw_date, "%d.%m.%Y")
            formatted_date = date_obj.strftime("%Y-%m-%d")

            add_deadline(user_id, task, formatted_date)

            await update.message.reply_text(
                f"✅ Dodano do listy!\n📌 <b>{task}</b> – {date_obj.strftime('%d %B %Y')}\n\nCo chcesz zrobić teraz?",
                reply_markup=deadline_main_menu(),
                parse_mode="HTML"
            )
        except Exception:
            await update.message.reply_text(
                "❌ Ups! Nie udało się dodać deadline'u.\nUpewnij się, że używasz formatu `Nazwa – data` i spróbuj jeszcze raz.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Dodaj deadline", callback_data="add_deadline")],
                    [InlineKeyboardButton("<< Wstecz", callback_data="deadline")]
                ]),
                parse_mode="Markdown"
            )
        finally:
            context.user_data["awaiting_deadline"] = False
        return

    # ✏️ Edycja / usuwanie – wybór numeru
    if "deadline_action" in context.user_data:
        action = context.user_data["deadline_action"]
        if not text.isdigit():
            await update.message.reply_text("❗ Wpisz poprawny numer zadania.")
            return

        index = int(text) - 1
        selected = get_deadline_by_index(user_id, index)

        if not selected:
            await update.message.reply_text("❌ Nie znaleziono zadania o tym numerze.")
            return

        task_id, task, date = selected
        context.user_data["selected_deadline_id"] = task_id

        if action == "delete":
            delete_deadline(user_id, task_id)
            await update.message.reply_text("🗑️ Deadline usunięty!", reply_markup=deadline_main_menu())
        else:  # edit
            context.user_data["editing"] = True
            await update.message.reply_text("✏️ Wyślij nową treść i datę w formacie:\n\nNowy opis – 25.05 lub 25.05.2025")

        del context.user_data["deadline_action"]
        return

    # ✏️ Edycja konkretnego terminu – nowa treść
    if context.user_data.get("editing"):
        if "-" not in text:
            await update.message.reply_text("❗ Użyj formatu `Nowy opis – data`.")
            return

        task_text, raw_date = [s.strip() for s in text.split("-", 1)]

        # Dodaj bieżący rok, jeśli brak
        parts = raw_date.split(".")
        if len(parts) == 2:
            raw_date = f"{parts[0]}.{parts[1]}.{datetime.today().year}"

        try:
            date_obj = datetime.strptime(raw_date, "%d.%m.%Y")
            formatted_date = date_obj.strftime("%Y-%m-%d")
        except:
            await update.message.reply_text("❗ Niepoprawna data. Użyj formatu `25.05` lub `25.05.2025`.")
            return

        update_deadline(user_id, context.user_data["selected_deadline_id"], task_text, formatted_date)
        await update.message.reply_text("✅ Deadline zaktualizowany!", reply_markup=deadline_main_menu())

        del context.user_data["editing"]
        del context.user_data["selected_deadline_id"]
        return

    if context.user_data.get("usun_plik_etap") == "czekam_na_numer":
        numer = text.strip()
        if not numer.isdigit():
            await update.message.reply_text("❌ Wpisz numer jako liczbę (np. 1, 2, 3...)")
            return

        index = int(numer) - 1
        pliki = context.user_data.get("usun_plik_lista", [])
        if index < 0 or index >= len(pliki):
            await update.message.reply_text("❌ Nie ma pliku o takim numerze.")
            return

        file_id, telegram_file_id, podpis = pliki[index]
        context.user_data["usun_plik_wybrany"] = file_id
        context.user_data["usun_plik_etap"] = "potwierdz"

        await update.message.reply_text(
            f"🔐 Czy na pewno chcesz usunąć ten plik?\n\n📝 {podpis}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Tak", callback_data="potwierdz_usun_plik")],
                [InlineKeyboardButton("❌ Nie", callback_data="workspace_files")]
            ])
        )
        return


async def handle_workspace_link_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not (context.user_data.get("dodaj_link") or context.user_data.get("czekam_na_notatke")):
        return
    if context.user_data.get("dodaj_link"):
        link = update.message.text.strip()

        # мягкая проверка на ссылку
        import re
        link_pattern = re.compile(r'(https?://)?([a-zA-Z0-9\-]+\.)+[a-zA-Z]{2,}(/.*)?')

        if not link_pattern.fullmatch(link):
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Wstecz", callback_data="workspace_links")]
            ])
            await update.message.reply_text(
                text="❗ To nie wygląda jak prawidłowy link.\n\n🧠 Sprawdź pisownię lub upewnij się, że to naprawdę adres strony (np. google.com)",
                reply_markup=keyboard
            )
            return

        context.user_data["nowy_link"] = link
        context.user_data["dodaj_link"] = False

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Tak", callback_data="dodaj_notatke_do_linku"),
             InlineKeyboardButton("❌ Nie", callback_data="zapisz_link_bez_notatki")],
            [InlineKeyboardButton("🔙 Wstecz", callback_data="workspace_links")]
        ])

        await update.message.reply_text(
            text=f"📝 Czy chcesz dodać notatkę do tego linku?\n\n🔗 {link}",
            reply_markup=keyboard
        )
        return


    elif context.user_data.get("czekam_na_notatke"):
        notatka = update.message.text.strip()
        link = context.user_data.get("nowy_link")
        user_id = update.effective_user.id

        from database import save_link  # ← если ещё не импортировал
        save_link(user_id, link, notatka)
        context.user_data.clear()

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Dodaj kolejny", callback_data="dodaj_link"),
             InlineKeyboardButton("📂 Wróć do menu", callback_data="workspace_links")]
        ])

        await update.message.reply_text(
            text=f"✅ Link zapisany!\n\n🔗 Link: {link}\n📝 Notatka: {notatka}",
            reply_markup=keyboard
        )
        return


async def plik_dodaj_notatke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["plik_state"] = "czekaj_na_notatke"
    await query.edit_message_text(
        "✏️ Wpisz notatkę do pliku.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Wróć", callback_data="workspace_files")]
        ])
    )

async def handle_file_note_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("plik_state") == "czekaj_na_notatke":
        podpis = update.message.text
        file_id = context.user_data.get("plik_file_id")
        user_id = update.effective_user.id

        if not file_id:
            await update.message.reply_text("❌ Nie znaleziono pliku. Spróbuj jeszcze raz.")
            return

        from database import save_file
        save_file(user_id, file_id, podpis)

        await update.message.reply_text(
            f"✅ Plik został zapisany!\n📎 Plik ID: `{file_id}`\n📝 Notatka: {podpis}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Dodaj kolejny", callback_data="plik_dodaj")],
                [InlineKeyboardButton("🏠 Wróć do menu", callback_data="workspace_files")]
            ])
        )
        context.user_data.pop("plik_state", None)
        context.user_data.pop("plik_file_id", None)
        return  # ← ОБЯЗАТЕЛЬНО




async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("plik_state") != "awaiting_file":
        return

    document = update.message.document or update.message.video or update.message.audio
    if not document:
        await update.message.reply_text("❌ To nie jest plik. Wyślij plik jako *plik*, nie zdjęcie.", parse_mode="Markdown")
        return

    file_id = document.file_id
    user_id = update.effective_user.id

    context.user_data["plik_file_id"] = file_id
    context.user_data["plik_state"] = "czekaj_na_notatke"

    await update.message.reply_text(
        "📝 Chcesz dodać notatkę do tego pliku?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🟢 Tak", callback_data="plik_dodaj_notatke"),
             InlineKeyboardButton("🔴 Nie", callback_data="plik_bez_notatki")],
            [InlineKeyboardButton("🔙 Wróć", callback_data="workspace_files")]
        ])
    )

async def handle_file_note_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    file_id = context.user_data.get("plik_file_id")

    if query.data == "plik_dodaj_notatke":
        context.user_data["plik_state"] = "awaiting_note"
        await query.message.reply_text(
            "✍️ Wpisz notatkę do tego pliku:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Wróć", callback_data="workspace_files")]
            ])
        )
    elif query.data == "plik_bez_notatki":
        save_file(user_id, file_id, "")  # без подписи
        await query.message.reply_text(
            f"✅ Plik został zapisany!\n📎 Plik ID: `{file_id}`\n📝 Notatka: brak",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Dodaj kolejny", callback_data="plik_dodaj")],
                [InlineKeyboardButton("🏠 Wróć do menu", callback_data="workspace_files")]
            ])
        )
        context.user_data.pop("plik_state", None)
        context.user_data.pop("plik_file_id", None)


if __name__ == '__main__':
    init_db()
    app = ApplicationBuilder() \
        .token(BOT_TOKEN) \
        .request(HTTPXRequest(read_timeout=20)) \
        .build()
    create_deadline_table()
    create_files_table()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("zaloguj", zaloguj))
    app.add_handler(CommandHandler("kod", code))
    app.add_handler(CommandHandler("szukaj", szukaj))
    app.add_handler(CommandHandler("wyloguj", wyloguj))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.ATTACHMENT & ~filters.PHOTO, handle_file))
    app.add_handler(CallbackQueryHandler(handle_file_note_decision, pattern="^plik_dodaj_notatke|plik_bez_notatki$"))

    app.add_handler(MessageHandler(filters.Document.ALL | filters.TEXT, handle_invalid_upload))

    app.run_polling()
