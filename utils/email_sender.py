import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from flask import current_app

def send_daily_report(pdf_bytes, filename, receiver_email):
    """Send daily PDF report via email"""
    sender_email = current_app.config.get('MAIL_USERNAME')
    sender_password = current_app.config.get('MAIL_PASSWORD')
    smtp_server = current_app.config.get('MAIL_SERVER', 'smtp.gmail.com')
    smtp_port = current_app.config.get('MAIL_PORT', 587)
    
    if not sender_email or not sender_password:
        print("Email configuration is missing. Cannot send daily report.")
        return False
        
    if not receiver_email:
        print("Receiver email is not configured. Cannot send daily report.")
        return False

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = f"Laporan Harian Smart Wash Laundry - {filename}"

    body = "Halo,\n\nBerikut adalah laporan harian dari Smart Wash Laundry yang terlampir pada email ini.\n\nTerima kasih."
    msg.attach(MIMEText(body, 'plain'))

    pdf_attachment = MIMEApplication(pdf_bytes.read(), _subtype="pdf")
    pdf_attachment.add_header('Content-Disposition', 'attachment', filename=filename)
    msg.attach(pdf_attachment)

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)
        server.quit()
        print(f"Daily report sent successfully to {receiver_email}")
        return True
    except Exception as e:
        print(f"Failed to send daily report email: {e}")
        return False
