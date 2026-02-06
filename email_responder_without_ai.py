import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.header import decode_header
import time
import os

# Email account credentials
EMAIL_ADDRESS = "name@gmail.com"
# EMAIL_PASSWORD = "password"  # Use Gmail App Password
IMAP_SERVER = "imap.gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

def connect_to_email():
    # Connect to IMAP server for reading emails
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    mail.select("inbox")
    return mail

def send_reply(to_email, subject, body):
    # Create the email message
    msg = MIMEText(body)
    msg["Subject"] = f"Re: {subject}"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email

    # Connect to SMTP server for sending emails
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
    print(f"Reply sent to {to_email}")

def check_emails():
    mail = connect_to_email()
    while True:
        try:
            # Search for unread emails
            mail.select("inbox")
            _, data = mail.search(None, "UNSEEN")
            email_ids = data[0].split()

            for email_id in email_ids:
                # Fetch email data
                _, msg_data = mail.fetch(email_id, "(RFC822)")
                email_body = msg_data[0][1]
                msg = email.message_from_bytes(email_body)

                # Decode email subject
                subject, encoding = decode_header(msg["subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding or "utf-8")

                # Get sender's email
                from_email = email.utils.parseaddr(msg["from"])[1]

                # Define auto-reply message
                reply_body = (
                    "Thank you for your email!\n\n"
                    "This is an automated response. I will get back to you soon.\n"
                    "Best regards,\nYour Name"
                )

                # Send reply
                send_reply(from_email, subject, reply_body)

                # Mark email as read
                mail.store(email_id, "+FLAGS", "\\Seen")

            # Wait before checking again
            time.sleep(60)  # Check every 60 seconds
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(60)  # Wait before retrying on error

if __name__ == "__main__":
    print("Starting email autoresponder...")
    check_emails()