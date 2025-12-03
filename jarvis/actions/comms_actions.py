import webbrowser
import os

def send_email(recipient, subject, body):
    print(f"Sending email to {recipient}...")
    # Basic implementation: Open default mail client
    # mailto:user@example.com?subject=Subject&body=Body
    webbrowser.open(f"mailto:{recipient}?subject={subject}&body={body}")
    return f"Opened mail client to send email to {recipient}"

def check_email():
    print("Checking email...")
    # Open Gmail or default webmail
    webbrowser.open("https://mail.google.com")
    return "Opened Gmail."

def send_whatsapp_message(number, message):
    print(f"Sending WhatsApp message to {number}: {message}")
    # Using WhatsApp Web
    # https://web.whatsapp.com/send?phone=NUMBER&text=MESSAGE
    webbrowser.open(f"https://web.whatsapp.com/send?phone={number}&text={message}")
    return f"Opened WhatsApp Web for {number}"

def open_whatsapp():
    print("Opening WhatsApp...")
    webbrowser.open("https://web.whatsapp.com")
    return "Opened WhatsApp Web."
