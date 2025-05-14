import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from serpapi import GoogleSearch
import random
from database import *
from plan_zajec_c371 import get_plan_for_day, get_week_plan_text, get_week_plan_image_and_caption
from database import save_note
from telegram.ext import MessageHandler, filters
from telegram.request import HTTPXRequest

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

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
        await query.edit_message_text("📰 Funkcja 'Aktualności' w budowie... 🛠️")

    elif query.data == "przestrzen_robocza":
        await query.edit_message_text("📂 Funkcja 'Przestrzeń robocza' w budowie... 🛠️")

    elif query.data == "asystent_ai":
        await query.edit_message_text("🤖 Funkcja 'Asystent AI' w budowie... 🛠️")


    elif query.data == "dalej":

        keyboard = [
            [InlineKeyboardButton("Deadline tracker", callback_data="deadline"),
             InlineKeyboardButton("Notatki", callback_data="notatki")],
            [InlineKeyboardButton("Literatura", callback_data="literatura"),
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
        await query.edit_message_text("⏳ Funkcja 'Deadline tacker' w budowie... 🛠️")


    elif query.data == "notatki":

        keyboard = [
            [InlineKeyboardButton("📖 Moje notatki", callback_data="moje_notatki"),
             InlineKeyboardButton("➕ Dodaj notatkę", callback_data="dodaj_notatke")],
            [InlineKeyboardButton("<< Wstecz", callback_data="dalej"),
             InlineKeyboardButton("🧠 AI-notatki", callback_data="przepisnotatki")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text="🗂️ Notatki – wybierz opcję:",
            reply_markup=reply_markup

        )
    elif query.data == "dodaj_notatke":
        context.user_data.clear()
        context.user_data["dodaj_notatke"] = True

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Anuluj i wróć do notatek", callback_data="anuluj_dodawanie")]
        ])

        await context.bot.send_message(
            chat_id=query.from_user.id,
            text="**📎 Prześlij zdjęcie *lub plik PDF* swojej notatki jako wiadomość.**\n\n*Jeśli nie chcesz, kliknij przycisk anulowania poniżej 👇*",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )


    elif query.data == "anuluj_dodawanie":
        context.user_data.clear()

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📖 Moje notatki", callback_data="moje_notatki"),
             InlineKeyboardButton("➕ Dodaj notatkę", callback_data="dodaj_notatke")],
            [InlineKeyboardButton("<< Wstecz", callback_data="dalej"),
             InlineKeyboardButton("🔄 Na PDF", callback_data="konwertuj_pdf")]
        ])

        await query.edit_message_text(
            text="📂 Notatki – wybierz opcję:",
            reply_markup=keyboard
        )



    elif query.data == "moje_notatki":

        user_id = query.from_user.id
        notes = get_user_notes(user_id)

        if not notes:
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Dodaj notatkę", callback_data="dodaj_notatke")],
                [InlineKeyboardButton("⬅️ Powrót do menu notatek", callback_data="notatki")]
            ])

            await query.edit_message_text(
                text="📭 Nie masz jeszcze żadnych notatek.\n\nChcesz dodać swoją pierwszą?",
                reply_markup=keyboard
            )
            return

        for note in notes:
            note_id, file_id, podpis = note
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🗑 Usuń", callback_data=f"usun_{note_id}")]
            ])

            if file_id.startswith("AgAC"):  # Telegram photo file_id usually starts like this
                await context.bot.send_photo(
                    chat_id=user_id,
                    photo=file_id,
                    caption=f"📝 {podpis}",
                    reply_markup=keyboard
                )
            else:
                await context.bot.send_document(
                    chat_id=user_id,
                    document=file_id,
                    caption=f"📝 {podpis}",
                    reply_markup=keyboard
                )

        # 🔽 После цикла — кнопка вернуться в меню
        keyboard_back = InlineKeyboardMarkup([
            [InlineKeyboardButton("📂 Wróć do menu notatek", callback_data="notatki")]
        ])

        await context.bot.send_message(
            chat_id=user_id,
            text="📁 To wszystkie Twoje notatki.",
            reply_markup=keyboard_back
        )


    elif query.data.startswith("usun_"):
        note_id = int(query.data.split("_")[1])
        podpis = get_note_signature(note_id)

        if not podpis:
            await context.bot.send_message(
                chat_id=query.from_user.id,
                text="⚠️ Nie znaleziono notatki."
            )
            return

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Tak", callback_data=f"potwierdz_usun_{note_id}"),
             InlineKeyboardButton("❌ Nie", callback_data="notatki")]
        ])

        await context.bot.send_message(
            chat_id=query.from_user.id,
            text=f"Czy na pewno chcesz usunąć notatkę:\n\n„{podpis}”?",
            reply_markup=keyboard
        )


    elif query.data.startswith("potwierdz_usun_"):
        note_id = int(query.data.split("_")[2])
        podpis = get_note_signature(note_id)
        delete_note(note_id)

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📂 Wróć do menu notatek", callback_data="notatki")]
        ])

        await query.edit_message_text(
            text=f"🗑 Notatka „{podpis}” została usunięta.",
            reply_markup=keyboard
        )

    elif query.data == "przepisnotatki":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📂 Wróć do menu notatek", callback_data="notatki")]
        ])

        await context.bot.send_message(
            chat_id=query.from_user.id,
            text=(
                "🧠 *Zamień bałagan na porządek – dzięki AI!*\n\n"
                "Masz notatki z krzywym pismem, których sam już nie możesz odczytać?\n\n"
                "To narzędzie odczytuje Twoją notatkę i tworzy z niej czytelny, uporządkowany dokument – gotowy do nauki, PDF-a lub druku.\n\n"
                "👉 [Kliknij tutaj](https://www.revisely.com/quiz-generator)\n\n"
                "Działa w ponad 50 językach – w tym po polsku 🇵🇱"
            ),
            parse_mode="Markdown",
            reply_markup = keyboard
        )


    elif query.data == "literatura":
        await query.edit_message_text("📚 Funkcja 'Literatura' w budowie... 🛠️")

    elif query.data == "lista_funkcji":
        await query.edit_message_text("🧾 Funkcja 'Lista funkcji' w budowie... 🛠️")



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
        await query.edit_message_text("👤 Funkcja 'Konto' w budowie... 🛠️")

    elif query.data == "o_nas":
        await query.edit_message_text("ℹ️ Funkcja 'O nas' w budowie... 🛠️")

    elif query.data == "wsparcie":
        await query.edit_message_text("🤝 Funkcja 'Wsparcie' w budowie... 🛠️")

    elif query.data == "prywatnosc":
        await query.edit_message_text("🔐 Funkcja 'Prywatność' w budowie... 🛠️")

async def handle_note_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("dodaj_notatke"):
        file_id = None

        # Фото
        if update.message.photo:
            photo = update.message.photo[-1]
            file_id = photo.file_id

        # PDF-документ
        elif update.message.document:
            document = update.message.document
            if document.mime_type == 'application/pdf':
                file_id = document.file_id
            else:
                await update.message.reply_text("❌ Niewłaściwy format pliku. Możesz przesłać tylko zdjęcie lub plik PDF.")
                return

        # Ничего не отправил или странный тип файла
        else:
            await update.message.reply_text("❌ Musisz przesłać zdjęcie lub plik PDF. Inne formaty nie są obsługiwane.")
            return

        # Успешная обработка
        context.user_data["nowa_notatka_file_id"] = file_id
        context.user_data["dodaj_notatke"] = False
        context.user_data["czekam_na_podpis"] = True

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Anuluj i wróć do notatek", callback_data="anuluj_dodawanie")]
        ])

        await update.message.reply_text(
            "**✍️ Wpisz podpis do tej notatki.**\n\n*Jeśli nie chcesz, kliknij przycisk anulowania poniżej 👇*",
            parse_mode="Markdown",
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

    if query.data == "plan_zajec":
        await query.edit_message_text("📚 Funkcja 'Plan zajęć' w budowie... 🛠️")
    elif query.data == "aktualnosci":
        await query.edit_message_text("📰 Funkcja 'Aktualności' w budowie... 🛠️")
    elif query.data == "przestrzen_robocza":
        await query.edit_message_text("📂 Funkcja 'Przestrzeń robocza' w budowie... 🛠️")
    elif query.data == "asystent_ai":
        await query.edit_message_text("🤖 Funkcja 'Asystent AI' w budowie... 🛠️")
    elif query.data == "dalej":
        await query.edit_message_text("➡️ Funkcja 'Dalej' w budowie... 🛠️")

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

if __name__ == '__main__':
    init_db()
    app = ApplicationBuilder() \
        .token(BOT_TOKEN) \
        .request(HTTPXRequest(read_timeout=20)) \
        .build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("zaloguj", zaloguj))
    app.add_handler(CommandHandler("kod", code))
    app.add_handler(CommandHandler("szukaj", szukaj))
    app.add_handler(CommandHandler("wyloguj", wyloguj))

    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.PDF, handle_note_upload))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))  # ⬅️ поднимаем выше
    app.add_handler(MessageHandler(filters.Document.ALL | filters.TEXT, handle_invalid_upload))

    app.run_polling()
