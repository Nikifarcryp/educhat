import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ADRES_NADAWCY = "uszeduchat@gmail.com"
HASLO_APLIKACJI = "raxrhtyhoytohwrd"  # Bez spacji!

def wyslij_maila(email_docelowy, kod):
    temat = "Kod weryfikacyjny - EduChat"
    tresc = f"Cześć! Twój kod weryfikacyjny do EduChatu to: {kod}\n\nMiłego dnia! 😊"

    msg = MIMEMultipart()
    msg["From"] = ADRES_NADAWCY
    msg["To"] = email_docelowy
    msg["Subject"] = temat

    msg.attach(MIMEText(tresc, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(ADRES_NADAWCY, HASLO_APLIKACJI)
        server.sendmail(ADRES_NADAWCY, email_docelowy, msg.as_string())
        server.quit()
        print(f"✅ Mail wysłany do {email_docelowy}")
    except Exception as e:
        print("❌ Błąd podczas wysyłania maila:", e)
