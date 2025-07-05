import schedule
import time
import json
import datetime
import smtplib
from email.mime.text import MIMEText
import logging
from services.viewdns_scanner import NetScanner
from config import settings

logging.basicConfig(level=logging.INFO)

scanner = NetScanner()

TARGET_FILE = "targets.txt"
RESULT_FILE = "scan_results.json"

# Load past results if file exists
try:
    with open(RESULT_FILE, "r") as f:
        all_results = json.load(f)
except FileNotFoundError:
    all_results = []

def read_targets():
    """Read targets from a file."""
    try:
        with open(TARGET_FILE, "r") as f:
            targets = [line.strip() for line in f if line.strip()]
        return targets
    except FileNotFoundError:
        logging.error(f"Target file {TARGET_FILE} not found.")
        return []

def scan_target():
    """Scan all targets and send email immediately."""
    logging.info("Starting scan for all targets...")
    targets = read_targets()
    scan_results = []

    for target in targets:
        result = scanner.scan_host(target)
        result["timestamp"] = datetime.datetime.now().isoformat()
        all_results.append(result)
        scan_results.append(result)
        logging.info(f"Scan result for {target}: {result}")

    # save results to file
    with open(RESULT_FILE, "w") as f:
        json.dump(all_results, f, indent=2)

    # generate and send report for this batch of scans
    report = generate_report(scan_results)
    if settings.email_from and settings.email_to:
        send_email(report)
    else:
        with open("latest_report.txt", "w") as f:
            f.write(report)
        logging.info("Saved latest report to latest_report.txt")

def generate_report(results):
    """Generate a report string from a list of results."""
    report = "\n=== Franks Scan Tool Report ===\n\n"
    for item in results:
        report += f"Timestamp: {item.get('timestamp')}\n"
        report += f"Target: {item.get('ip')}\n"
        report += f"Status: {item.get('status')}\n"

        if item.get("ports"):
            for p in item["ports"]:
                report += f"  - Port: {p['port']} | Status: {p['status']} | Service: {p['service']} | Banner: {p.get('banner')}\n"
        
        if item.get("error"):
            report += f"Error: {item['error']}\n"
        report += "\n"
    
    return report

def send_email(content: str):
    """Send email report."""
    msg = MIMEText(content)
    msg["Subject"] = "ViewDNS Scan Report"
    msg["From"] = settings.email_from
    msg["To"] = settings.email_to

    try:
        server = smtplib.SMTP(settings.smtp_server, int(settings.smtp_port))
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_pass)
        server.sendmail(settings.email_from, settings.email_to, msg.as_string())
        server.quit()
        logging.info("Email sent successfully!")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")

# Schedule jobs
schedule.every(10).minutes.do(scan_target)

if __name__ == "__main__":
    logging.info("Starting scheduler...")

    scan_target()

    while True:
        schedule.run_pending()
        time.sleep(1)




























# import schedule
# import time
# import json
# import datetime
# import smtplib
# from email.mime.text import MIMEText
# import logging
# from services.viewdns_scanner import NetScanner
# from config import settings

# logging.basicConfig(level=logging.INFO)

# scanner = NetScanner()

# TARGET_FILE = "targets.txt"
# RESULT_FILE = "scan_results.json"

# # Load past results if file exists
# try:
#     with open(RESULT_FILE, "r") as f:
#         all_results = json.load(f)
# except FileNotFoundError:
#     all_results = []

# def read_targets():
#     """Read targets from a file."""
#     try:
#         with open(TARGET_FILE, "r") as f:
#             targets = [line.strip() for line in f if line.strip()]
#         return targets
#     except FileNotFoundError:
#         logging.error(f"Target file {TARGET_FILE} not found.")
#         return []

# def scan_target():
#     """Scan all targets and store results."""
#     logging.info("Starting scan for all targets...")
#     targets = read_targets()
#     for target in targets:
#         result = scanner.scan_host(target)
#         result["timestamp"] = datetime.datetime.now().isoformat()
#         all_results.append(result)
#         logging.info(f"Scan result for {target}: {result}")

#     # save results to file
#     with open(RESULT_FILE, "w") as f:
#         json.dump(all_results, f, indent=2)

# def daily_report():
#     logging.info("Generating daily report...")

#     # Last ~24h of results if scanning every 10 minutes
#     last_24_hours = all_results[-144:] if len(all_results) > 144 else all_results

#     report = "\n=== Daily Scan Report ===\n\n"
#     for item in last_24_hours:
#         report += f"Timestamp: {item.get('timestamp')}\n"
#         report += f"Target: {item.get('ip')}\n"
#         report += f"Status: {item.get('status')}\n"

#         if item.get("ports"):
#             for p in item["ports"]:
#                 report += f"  - Port: {p['port']} | Status: {p['status']} | Service: {p['service']} | Banner: {p.get('banner')}\n"
        
#         if item.get("error"):
#             report += f"Error: {item['error']}\n"
#         report += "\n"

#     if settings.email_from and settings.email_to:
#         send_email(report)
#     else:
#         with open("daily_report.txt", "w") as f:
#             f.write(report)
#         logging.info("Daily report saved to daily_report.txt")

# def send_email(content: str):
#     """Send email report."""
#     msg = MIMEText(content)
#     msg["Subject"] = "ViewDNS Daily Scan Report"
#     msg["From"] = settings.email_from
#     msg["To"] = settings.email_to

#     try:
#         server = smtplib.SMTP(settings.smtp_server, int(settings.smtp_port))
#         server.starttls()
#         server.login(settings.smtp_user, settings.smtp_pass)
#         server.sendmail(settings.email_from, settings.email_to, msg.as_string())
#         server.quit()
#         logging.info("Email sent successfully!")
#     except Exception as e:
#         logging.error(f"Failed to send email: {e}")

# # Schedule jobs
# schedule.every(10).minutes.do(scan_target)
# schedule.every().day.at("08:00").do(daily_report)

# if __name__ == "__main__":
#     logging.info("Starting scheduler...")
#     while True:
#         schedule.run_pending()
#         time.sleep(1)
