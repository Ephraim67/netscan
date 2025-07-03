from apscheduler.schedulers.background import BackgroundScheduler
from services.viewdns_scanner import NetScanner
from models.database import ScanTarget, ScanHistory, SessionLocal
from datetime import datetime
from services.send_email import send_daily_email
from typing import List

scheduler = None

scanner = NetScanner()

def start_scheduler(selected_targets: List[str]):
    global scheduler
    if scheduler and scheduler.running:
        print("Scheduler already running.")
        return

    def run_scheduled_scans():
        db = SessionLocal()
        try:
            targets = db.query(ScanTarget).filter(ScanTarget.target.in_(selected_targets)).all()
            for target in targets:
                result = scanner.scan_host(target.target)

                history = ScanHistory(
                    target=target.target,
                    status=result.get("status", "error"),
                    ports=result.get("ports", []),
                    error_message=result.get("error"),
                    scan_time=datetime.utcnow()
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
    print("Scheduler started.")


def shutdown_scheduler():
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown()
        print("Scheduler stopped.")
