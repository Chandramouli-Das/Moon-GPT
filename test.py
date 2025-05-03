import smtplib
from email.message import EmailMessage

# Replace with your actual Gmail & app password
EMAIL_SENDER = "chandramoulidas39@gmail.com"
EMAIL_PASSWORD = "hemb iozb hdky gbbh"  # 16-character App Password from Google
EMAIL_RECEIVER = "chandramoulidas39@gmail.com"

msg = EmailMessage()
msg["Subject"] = "🚀 MoonGPT Email Test"
msg["From"] = EMAIL_SENDER
msg["To"] = EMAIL_RECEIVER
msg.set_content("Hello! This is a test email sent directly from a Python script using Gmail SMTP.")

try:
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
    print("✅ Email sent successfully!")
except Exception as e:
    print("❌ Failed to send email:")
    print(e)