from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from serpapi import GoogleSearch
import random
from baza import zapisz_email_i_kod, potwierdz_kod, is_logged_in, init_db, wyloguj_user

from mailer import wyslij_maila

BOT_TOKEN = '7596922139:AAH0_bPKSTV_HeAzKdk146ghQAW17RXhJvc'
SERPAPI_KEY = '3179bee341901ba51d3263c1a9dc6d87e656c80b9f157463c38b0f7f7b7e1a80'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hejka! Jestem EduChat – jak mogę Ci pomóc? 😊")

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
    zapisz_email_i_kod(user_id, email, kod)
    wyslij_maila(email, kod)
    await update.message.reply_text("📩 Wysłano kod weryfikacyjny na Twój adres e-mail. Wpisz go komendą: `/kod 123456`")

async def kod(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if is_logged_in(user_id):
        await update.message.reply_text("✅ Już jesteś zalogowany.")
        return

    if not context.args:
        await update.message.reply_text("🔢 Wpisz kod, który otrzymałeś e-mailem: `/kod 123456`", parse_mode="Markdown")
        return

    wpisany_kod = context.args[0]
    if potwierdz_kod(user_id, wpisany_kod):
        await update.message.reply_text("🎉 Sukces! Jesteś teraz zalogowany jako student.")
    else:
        await update.message.reply_text("❌ Nieprawidłowy kod. Sprawdź jeszcze raz.")

async def wyloguj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if is_logged_in(user_id):
        wyloguj_user(user_id)
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

if __name__ == '__main__':
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("zaloguj", zaloguj))
    app.add_handler(CommandHandler("kod", kod))
    app.add_handler(CommandHandler("szukaj", szukaj))
    app.add_handler(CommandHandler("wyloguj", wyloguj))
    app.run_polling()
