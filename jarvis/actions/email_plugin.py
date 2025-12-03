import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(to_email, subject, body):
    # Placeholder credentials - User must update these
    sender_email = "your_email@gmail.com"
    sender_password = "your_app_password"
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        # SMTP Server for Gmail
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        # server.login(sender_email, sender_password) # Uncomment when credentials are set
        # server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
        
        print(f"Email sent to {to_email}")
        return "Email sent successfully (Simulated)."
    except Exception as e:
        print(f"Failed to send email: {e}")
        return f"Failed to send email: {e}"
