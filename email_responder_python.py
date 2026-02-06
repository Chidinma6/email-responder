
import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from huggingface_hub import InferenceClient
import os


# === CONFIGURATION ===
IMAP_SERVER = "imap.gmail.com"
SMTP_SERVER = "smtp.gmail.com"
EMAIL_ACCOUNT = "chiekuma24@gmail.com"
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
HF_TOKEN = os.getenv("HF_TOKEN")


def fetch_unread_emails(email_account: str, email_password: str):
    """Fetch unread emails and return list of (sender, subject, body)."""
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(email_account, email_password)
        mail.select("inbox")

        status, messages = mail.search(None, "UNSEEN")
        if status != "OK":
            return []

        email_ids = messages[0].split()
        emails = []

        for e_id in email_ids:
            status, msg_data = mail.fetch(e_id, "(RFC822)")
            if status != "OK":
                continue
            msg = email.message_from_bytes(msg_data[0][1])
            sender = email.utils.parseaddr(msg["From"])[1]
            subject = msg["Subject"] or "(No Subject)"
            body = ""

            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        payload = part.get_payload(decode=True)
                        if payload:
                            body = payload.decode(errors="ignore")
                            break
            else:
                payload = msg.get_payload(decode=True)
                if payload:
                    body = payload.decode(errors="ignore")

            emails.append((sender, subject, body))
            mail.store(e_id, "+FLAGS", "\\Seen")
        mail.logout()
        return emails
    except Exception as e:
        print(f"IMAP error: {e}")
        return []


def generate_ai_reply(email_body: str, hf_token: str) -> str:
    """Use Hugging Face Inference API to draft a reply, cleaned of unwanted prefixes."""
    try:
        client = InferenceClient(token=hf_token)
        """ask the model to write something"""
        response = client.chat_completion(
            model="meta-llama/Llama-3.1-8B-Instruct",
            messages=[
                {"role": "system", "content": "You are a polite email assistant. Reply directly, no preamble."},
                {"role": "user", "content": f"Draft a professional reply to this email: {email_body}"},
            ],
            max_tokens=300, 
            temperature=0.7,
        )
        """take the model's reply text from the response object, remove leading/trailing spaces"""
        text = response.choices[0].message["content"].strip()

        # Remove common unwanted prefixes
        bad_prefixes = [
            "Here is a polished and professional reply:",
            "Here’s a polished and professional reply:",
            "Here is the reply:",
            "Here’s the reply:",
        ]
        for prefix in bad_prefixes:
            if text.lower().startswith(prefix.lower()):
                text = text[len(prefix):].strip()
                break

        return text
    except Exception as e:
        print(f"Error generating AI reply: {e}")
        return "Thank you for your email. I'll get back to you soon."



def send_email_reply(
    email_account: str,
    email_password: str,
    to_address: str,
    subject: str,
    reply_body: str,
):
    """Send an email reply using SMTP."""
    try:
        msg = MIMEText(reply_body)
        msg["From"] = email_account
        msg["To"] = to_address
        msg["Subject"] = f"Re: {subject}"

        with smtplib.SMTP_SSL(SMTP_SERVER, 465) as server:
            server.login(email_account, email_password)
            server.sendmail(email_account, to_address, msg.as_string())
        print(f"Replied to: {to_address}")
    except Exception as e:
        print(f"SMTP error: {e}")


def process_emails(email_account: str, email_password: str, hf_token: str):
    """Main pipeline: fetch unread, generate replies, and send them."""
    emails = fetch_unread_emails(email_account, email_password)
    for sender, subject, body in emails:
        ai_reply = generate_ai_reply(body, hf_token)
        send_email_reply(email_account, email_password, sender, subject, ai_reply)


def main():
    if not EMAIL_PASSWORD:
        raise ValueError("EMAIL_PASSWORD not set.")
    if not HF_TOKEN:
        raise ValueError("HF_TOKEN not set.")

    process_emails(EMAIL_ACCOUNT, EMAIL_PASSWORD, HF_TOKEN)


if __name__ == "__main__":
    main()
