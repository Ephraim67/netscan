from models.database import SessionLocal
from models.database import EmailLog
from datetime import datetime

def send_daily_email():
    db = SessionLocal()
    try:
        subject = "Daily Scan Summary"
        recipients = ["frankroyal10@gmail.com", "norbert.ephraim0@gmail.com"]
        body = "This is your daily scan summary. Please check the attached report for details."

        log = EmailLog(
            subject=subject,
            recipients=recipients,
            body=body,
            sent_at=datetime.utcnow(),
            status="sent"
        )

        db.add(log)
        db.commit()

    except Exception as e:
        db.add(EmailLog(
            subject=subject,
            recipients=",".join(recipients),
            body=body,
            sent_at=datetime.utcnow(),
            status="failed",
            error_message=str(e)
        ))

        db.commit()
    finally:
        db.close()
