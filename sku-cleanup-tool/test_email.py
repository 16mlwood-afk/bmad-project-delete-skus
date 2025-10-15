#!/usr/bin/env python3
"""
Simple test script to verify email delivery
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_email():
    """Test email delivery with minimal configuration"""
    
    # Get credentials
    username = os.getenv('GMAIL_USER')
    password = os.getenv('GMAIL_PASSWORD')
    to_email = "sales@bison.management"
    
    if not username or not password:
        print("❌ Gmail credentials not configured")
        return False
    
    print(f"📧 User: {username}")
    print(f"📧 User: {username}")
    print(f"📧 User: {username}")
    # Create simple email
    msg = MIMEMultipart()
    msg['From'] = username
    msg['To'] = to_email
    msg['Subject'] = "SKU Cleanup Test Email"
    
    body = f"""
🚀 SKU Cleanup System Test
=========================

✅ Email notification system is operational!

📅 Test sent: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🔧 System: BMAD SKU Management
📧 Delivery: Google Workspace SMTP Relay

---
This is a test email to verify the notification system.
Daily automated reports will be sent after each run at 2:00 AM.
"""
    
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        print("🔗 Connecting to smtp-relay.gmail.com:587...")
        
        # Connect to SMTP server
        server = smtplib.SMTP("smtp-relay.gmail.com", 587)
        server.starttls()
        server.login(username, password)
        
        print("📨 Sending email...")
        server.sendmail(username, to_email, msg.as_string())
        server.quit()
        
        print("✅ Email sent successfully!")
        print(f"📧 User: {username}")
        return True
        
    except smtplib.SMTPAuthenticationError:
        print("❌ Authentication failed - check username/password")
        return False
    except smtplib.SMTPConnectError:
        print("❌ Connection failed - check SMTP server settings")
        return False
    except Exception as e:
        print(f"❌ Email failed: {e}")
        return False

if __name__ == "__main__":
    success = test_email()
    exit(0 if success else 1)
