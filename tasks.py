from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import atexit

# This will hold the scheduler instance
scheduler = None

def run_daily_report_job(app):
    """Job function to generate and send the daily report"""
    # Need to run within app context
    with app.app_context():
        from routes.laporan import generate_pdf_bytes, _get_date_range
        from utils.email_sender import send_daily_report
        
        print(f"Running daily report job at {datetime.now()}")
        
        # Since it runs at 00:00 (midnight), we want the report for "yesterday"
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        dt_start, dt_end = _get_date_range('custom', yesterday, yesterday)
        
        pdf_bytes = generate_pdf_bytes('harian', dt_start, dt_end)
        
        # Format filename using yesterday's date
        filename_date = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
        filename = f"laporan_harian_{filename_date}.pdf"
        receiver_email = app.config.get('MAIL_RECEIVER')
        
        if receiver_email:
            send_daily_report(pdf_bytes, filename, receiver_email)
        else:
            print("No MAIL_RECEIVER configured, skipping email send.")


def init_scheduler(app):
    """Initialize and start the background scheduler"""
    global scheduler
    
    # Don't start scheduler multiple times in dev mode (reloader)
    import os
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true' and app.debug:
        return
        
    scheduler = BackgroundScheduler()
    
    # Schedule the job to run every day at 00:00 (midnight)
    scheduler.add_job(
        func=run_daily_report_job,
        trigger="cron",
        hour=0,
        minute=0,
        args=[app],
        id="daily_report_job",
        replace_existing=True
    )
    
    scheduler.start()
    print("Background scheduler started. Daily report scheduled for 00:00.")
    
    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())
