import logging
import time
from apscheduler.schedulers.background import BackgroundScheduler
from scripts.calcCreditInterest import calculateCreditInterest
from scripts.calcInterest import accrue_interest
from scripts.billPayment import processScheduledBills, generate_monthly_credit_card_statements  # <- imported

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def monthly_interest_job():
    try:
        credit_results = calculateCreditInterest()
        accrue_interest('Savings')
        accrue_interest('Money Market')
        logging.info("Monthly interest calculations completed successfully.")
    except Exception as e:
        logging.error("Error running monthly interest job: %s", e)

def daily_bill_processing_job():
    try:
        results = processScheduledBills()
        for result in results:
            status = result.get("status")
            message = result.get("message")
            log_func = logging.info if status == "success" else logging.warning
            log_func(f"Bill Processing - {status.upper()}: {message}")
        logging.info("Daily bill processing completed.")
    except Exception as e:
        logging.error("Error running daily bill processing job: %s", e)

def daily_credit_statement_job():
    try:
        result = generate_monthly_credit_card_statements()
        status = result.get("status")
        message = result.get("message")
        log_func = logging.info if status == "success" else logging.warning
        log_func(f"Credit Statement - {status.upper()}: {message}")
    except Exception as e:
        logging.error("Error running daily credit card statement job: %s", e)

def start_scheduler():
    scheduler = BackgroundScheduler()

    # Monthly interest job — 1st of each month at midnight
    scheduler.add_job(monthly_interest_job, 'cron', day=1, hour=0, minute=0)

    # Daily bill processing job — every day at midnight
    scheduler.add_job(daily_bill_processing_job, 'cron', hour=0, minute=0)

    # Daily credit card statement generation — every day at 12:05 AM
    scheduler.add_job(daily_credit_statement_job, 'cron', hour=0, minute=5)


    # === TEST MODE: Run all jobs every 30 seconds ===
    # Uncomment the lines below to override the production schedule with test frequency
    #scheduler.add_job(monthly_interest_job, 'interval', seconds=30)
    #scheduler.add_job(daily_bill_processing_job, 'interval', seconds=30)
    #scheduler.add_job(daily_credit_statement_job, 'interval', seconds=30)


    scheduler.start()
    logging.info("Scheduler started: monthly interest, daily bill processing, and credit statement jobs scheduled.")
    return scheduler

if __name__ == "__main__":
    scheduler = start_scheduler()
    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logging.info("Scheduler shut down gracefully.")
