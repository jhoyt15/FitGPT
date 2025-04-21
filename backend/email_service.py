
import smtplib
import os
from email.mime.text import MIMEText

def send_otp_email(to_email, otp):
    msg = MIMEText(f'Your 2FA code is: {otp}')
    msg['Subject'] = 'Your FitGPT 2FA Code'
    msg['From'] = os.getenv("SMTP_EMAIL")
    msg['To'] = to_email

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(os.getenv("SMTP_EMAIL"), os.getenv("SMTP_APP_PASSWORD"))
            smtp.send_message(msg)
    except Exception as e:
        print("Failed to send OTP email:", e)
        raise
