import logging
import os
import time
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
from scripts.calcCreditInterest import calculateCreditInterest
from scripts.calcInterest import accrue_interest
from scripts.billPayment import processScheduledBills, generate_monthly_credit_card_statements

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Create a global scheduler instance to prevent duplicate schedulers
_scheduler = None

def monthly_interest_job():
    """Calculate monthly interest for savings and money market accounts."""
    try:
        # Calculate interest for savings accounts
        accrue_interest('Savings')
        logging.info("Monthly interest calculations for Savings accounts completed successfully.")
        
        # Calculate interest for money market accounts
        accrue_interest('Money Market')
        logging.info("Monthly interest calculations for Money Market accounts completed successfully.")
    except Exception as e:
        logging.error("Error running monthly interest job: %s", e)

def daily_credit_interest_job():
    """Calculate daily interest and process late bills for credit card and mortgage accounts."""
    try:
        credit_results = calculateCreditInterest()
        for result in credit_results:
            status = result.get("status")
            message = result.get("message")
            log_func = logging.info if status == "success" else logging.warning
            log_func(f"Credit Interest - {status.upper()}: {message}")
        logging.info("Daily credit interest and late bill processing completed.")
    except Exception as e:
        logging.error("Error running daily credit interest job: %s", e)

def daily_bill_processing_job():
    """Process scheduled bills due today - mark overdue bills as Late and handle auto payments."""
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
    """Generate monthly credit card statements for accounts without active bills."""
    try:
        result = generate_monthly_credit_card_statements()
        status = result.get("status")
        message = result.get("message")
        log_func = logging.info if status == "success" else logging.warning
        log_func(f"Credit Statement - {status.upper()}: {message}")
    except Exception as e:
        logging.error("Error running daily credit card statement job: %s", e)

def start_scheduler():
    """Initialize and start the APScheduler."""
    global _scheduler
    
    # Only create a new scheduler if one doesn't already exist
    if _scheduler is not None and _scheduler.running:
        logging.info("Scheduler already running. Not starting a new one.")
        return _scheduler
    
    _scheduler = BackgroundScheduler()
    
    # PRODUCTION SCHEDULE
    # Monthly interest job for savings and money market accounts - 1st of each month at midnight
    _scheduler.add_job(monthly_interest_job, 'cron', day=1, hour=0, minute=0)
    
    # Daily credit interest and late bill processing - every day at 1:00 AM
    _scheduler.add_job(daily_credit_interest_job, 'cron', hour=1, minute=0)
    
    # Daily bill processing job - every day at midnight
    _scheduler.add_job(daily_bill_processing_job, 'cron', hour=0, minute=0)
    
    # Daily credit card statement generation - every day at 12:05 AM
    _scheduler.add_job(daily_credit_statement_job, 'cron', hour=0, minute=5)

    # TEST MODE: Uncomment the lines below to override the production schedule with test frequency
    #_scheduler.add_job(monthly_interest_job, 'interval', seconds=30)
    #_scheduler.add_job(daily_credit_interest_job, 'interval', seconds=20)
    #_scheduler.add_job(daily_bill_processing_job, 'interval', seconds=40)
    #_scheduler.add_job(daily_credit_statement_job, 'interval', seconds=30)

    _scheduler.start()
    logging.info("Scheduler started with updated interest calculation jobs.")
    return _scheduler

if __name__ == "__main__":
    scheduler = start_scheduler()
    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logging.info("Scheduler shut down gracefully.")