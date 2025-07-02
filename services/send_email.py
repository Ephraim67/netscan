import smtplib
from email.mime.text import MIMEText
from config import settings
from models.database import SessionLocal, ScanHistory  # Make sure to import SessionLocal and ScanHistory from your db module

def send_daily_email():
    db = SessionLocal()
    try:
        all_scans = db.query(ScanHistory).all()
        body = "\n".join([f"Target: {s.target}, Status: {s.status}" for s in all_scans])

        msg = MIMEText(body)
        msg["Subject"] = "Daily Port Scan Report"
        msg["From"] = settings.email_sender
        msg["To"] = settings.email_receiver

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_username, settings.smtp_password)
            server.sendmail(settings.email_sender, [settings.email_receiver], msg.as_string())

        print("Daily scan email sent!")

    finally:
        db.close()

