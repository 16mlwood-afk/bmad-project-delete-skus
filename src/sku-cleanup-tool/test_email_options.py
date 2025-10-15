#!/usr/bin/env python3
"""
Email delivery test with multiple options
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_workspace_smtp():
    """Test Google Workspace SMTP Relay"""
    print("🧪 Testing Google Workspace SMTP Relay...")

    username = os.getenv('GMAIL_USER')
    password = os.getenv('GMAIL_PASSWORD')
    to_email = "sales@bison.management"

    if not username or not password:
        print("❌ Google Workspace credentials not configured")
        return False

    msg = MIMEMultipart()
    msg['From'] = username
    msg['To'] = to_email
    msg['Subject'] = "SKU Cleanup Test - Workspace SMTP"

    body = f"""
🚀 SKU Cleanup System Test (Google Workspace)
=============================================

✅ Email notification system is operational!

📅 Test sent: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🔧 System: BMAD SKU Management
📧 Method: Google Workspace SMTP Relay

---
This is a test email using Google Workspace SMTP relay.
"""
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP("smtp-relay.gmail.com", 587)
        server.starttls()
        server.login(username, password)
        server.sendmail(username, to_email, msg.as_string())
        server.quit()
        print("✅ Google Workspace SMTP relay successful!")
        return True
    except Exception as e:
        print(f"❌ Google Workspace SMTP failed: {e}")
        return False

def test_gmail_smtp():
    """Test regular Gmail SMTP"""
    print("🔄 Testing regular Gmail SMTP...")

    username = os.getenv('GMAIL_USER')
    app_password = os.getenv('GMAIL_APP_PASSWORD')
    to_email = "sales@bison.management"

    if not username or not app_password:
        print("❌ Gmail credentials not configured")
        return False

    msg = MIMEMultipart()
    msg['From'] = username
    msg['To'] = to_email
    msg['Subject'] = "SKU Cleanup Test - Gmail SMTP"

    body = f"""
🚀 SKU Cleanup System Test (Gmail)
===================================

✅ Email notification system is operational!

📅 Test sent: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🔧 System: BMAD SKU Management
📧 Method: Regular Gmail SMTP

---
This is a test email using regular Gmail SMTP with App Password.
"""
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(username, app_password)
        server.sendmail(username, to_email, msg.as_string())
        server.quit()
        print("✅ Regular Gmail SMTP successful!")
        return True
    except Exception as e:
        print(f"❌ Regular Gmail SMTP failed: {e}")
        return False

def main():
    """Test both email methods"""
    print("📧 Testing Email Delivery Options...")
    print("=" * 40)

    # Try Google Workspace SMTP Relay first
    workspace_success = test_workspace_smtp()

    if not workspace_success:
        print()
        # Try regular Gmail SMTP as fallback
        gmail_success = test_gmail_smtp()

        if gmail_success:
            print()
            print("💡 Recommendation:")
            print("Use regular Gmail SMTP with App Password for reliable delivery")
            print("Configure GMAIL_APP_PASSWORD in .env file")
        else:
            print()
            print("💡 Setup Instructions:")
            print("1. For Google Workspace: Verify SMTP relay configuration in Google Admin")
            print("2. For Gmail: Enable 2FA and generate App Password")
            print("3. Update .env file with correct credentials")

if __name__ == "__main__":
    main()
