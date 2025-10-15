#!/usr/bin/env python3
"""
Gmail SMTP Setup Helper
Tests Gmail SMTP configuration and provides setup guidance
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_gmail_smtp():
    """Test Gmail SMTP with App Password"""

    username = os.getenv('GMAIL_USER')
    app_password = os.getenv('GMAIL_APP_PASSWORD')
    to_email = "sales@bison.management"

    if not username or not app_password:
        print("❌ Gmail SMTP credentials not configured")
        print("💡 Setup Instructions:")
        print("1. Set GMAIL_USER and GMAIL_APP_PASSWORD in .env file")
        print("2. Example: GMAIL_USER=your-email@gmail.com")
        print("3. Example: GMAIL_APP_PASSWORD=abcd-efgh-ijkl-mnop")
        return False

    print(f"📧 User: {os.getenv("GMAIL_USER", "Not set")}")
    print(f"📧 User: {os.getenv("GMAIL_USER", "Not set")}")
    print(f"📧 User: {os.getenv("GMAIL_USER", "Not set")}")
    msg = MIMEMultipart()
    msg['From'] = username
    msg['To'] = to_email
    msg['Subject'] = "SKU Cleanup Test - Gmail SMTP"

    body = f"""
🚀 SKU Cleanup System Test (Gmail SMTP)
=======================================

✅ Email notification system is operational!

📅 Test sent: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🔧 System: BMAD SKU Management
📧 Method: Gmail SMTP with App Password

---
This is a test email using Gmail SMTP.
Daily automated reports will be sent after each run at 2:00 AM.
"""
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(username, app_password)
        server.sendmail(username, to_email, msg.as_string())
        server.quit()

        print("✅ Gmail SMTP successful!")
        print(f"📧 User: {os.getenv("GMAIL_USER", "Not set")}")
        return True

    except smtplib.SMTPAuthenticationError:
        print("❌ Gmail authentication failed")
        print("💡 Check your App Password and Gmail 2FA settings")
        return False
    except Exception as e:
        print(f"❌ Gmail SMTP failed: {e}")
        return False

def main():
    """Main setup helper"""
    print("📧 Gmail SMTP Setup Helper")
    print("=" * 30)
    print()

    print("🔧 Current Configuration:")
    print(f"📧 User: {os.getenv("GMAIL_USER", "Not set")}")
    print(f"📧 User: {os.getenv("GMAIL_USER", "Not set")}")

    if not os.getenv('GMAIL_APP_PASSWORD'):
        print()
        print("💡 To set up Gmail SMTP:")
        print("1. Enable 2FA on your Gmail account")
        print("2. Generate App Password: https://myaccount.google.com/apppasswords")
        print("3. Add to .env file: GMAIL_APP_PASSWORD=your-16-char-password")
        print("4. Run this script again to test")
        return

    print()
    success = test_gmail_smtp()

    if success:
        print()
        print("🎉 Gmail SMTP is working!")
        print("✅ Ready for automated email notifications")
        print("📧 Emails will be sent to sales@bison.management")

if __name__ == "__main__":
    main()
