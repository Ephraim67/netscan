from apscheduler.schedulers.background import BackgroundScheduler
from services.viewdns_scanner import NetScanner
from models import ScanTarget, ScanHistory, SessionLocal
import datetime
from email import send_daily_email  

scanner = NetScanner()

def run_scheduled_scans():

    db = SessionLocal()
    try:
        targets = db.query(ScanTarget).all()
        for target in targets:
            result = scanner.scan_host(target.target)

            history = ScanHistory(
                target=target.target,
                status=result.get("status", "error"),
                ports=result.get("ports", []),
                error_message=result.get("error"),
                scan_time=datetime.datetime.now(),
            )

            db.add(history)

            target.status = result["status"]
            target.result = str(result)
            db.commit()

    except Exception as e:
        print(f"Error during scheduled scan: {e}")
    finally:
        db.close()


scheduler = BackgroundScheduler()
scheduler.add_job(run_scheduled_scans, 'interval', minutes=10)
scheduler.add_job(send_daily_email, 'interval', hours=24)
scheduler.start()

