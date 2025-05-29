import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

GOOGLE_BOOKS_API_URL = "https://www.googleapis.com/books/v1/volumes"

async def szukaj_ksiazek(temat: str):
    params = {
        "q": temat,
        "maxResults": 3,
        "langRestrict": "pl",
        "printType": "books"
    }
    response = requests.get(GOOGLE_BOOKS_API_URL, params=params)
    if response.status_code == 200:
        return response.json().get("items", [])
    return []

async def komenda_literatura(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        temat = " ".join(context.args)
        ksiazki = await szukaj_ksiazek(temat)

        if not ksiazki:
            await update.message.reply_text("😕 Nie znaleziono książek dla podanego tematu.")
            return

        for ksiazka in ksiazki:
            info = ksiazka.get('volumeInfo', {})
            tytul = info.get('title', 'Brak tytułu')
            autorzy = ", ".join(info.get('authors', ['Nieznani autorzy']))
            rok = info.get('publishedDate', 'Brak roku')[:4]
            isbn_list = info.get('industryIdentifiers', [])
            isbn = next((i['identifier'] for i in isbn_list if 'ISBN' in i.get('type', '')), 'Brak ISBN')
            opis = info.get('description', 'Brak opisu')
            if len(opis) > 400:
                opis = opis[:400] + "..."

            link = info.get('infoLink', '#')

            tekst = (
                f"📘 *{tytul}*\n"
                f"✍️ Autor: {autorzy}\n"
                f"📅 Rok wydania: {rok}\n"
                f"📖 ISBN: {isbn}\n"
                f"📝 Opis: _{opis}_\n"
                f"🔗 [Zobacz w Google Books]({link})"
            )

            await update.message.reply_markdown(tekst)

        await update.message.reply_text(
            "↩️ Wróć do menu:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("<< Wróć", callback_data="menu_glowne")]
            ])
        )

    else:
        await update.message.reply_text("📘 Użyj komendy w formacie:\n`/literatura temat_książki`", parse_mode="Markdown")
