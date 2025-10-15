#!/usr/bin/env python3
"""
SKU Cleanup Tool - External Email Sender
Uses external SMTP services for reliable email delivery
"""

import smtplib
import os
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def send_external_email(smtp_server, smtp_port, username, password, to_email, subject, body):
    """Send email via external SMTP service"""

    # Create message
    msg = MIMEMultipart()
    msg['From'] = username
    msg['To'] = to_email
    msg['Subject'] = subject

    # Add body
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Connect to SMTP server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Secure connection
        server.login(username, password)

        # Send email
        server.sendmail(username, to_email, msg.as_string())
        server.quit()

        return True, "Email sent successfully"

    except Exception as e:
        return False, f"Email failed: {e}"

def send_gmail_relay_email(to_email, subject, body):
    """Send email via Google Workspace SMTP Relay"""

    # Google Workspace SMTP Relay settings
    smtp_server = "smtp-relay.gmail.com"
    smtp_port = 587

    # Get Google Workspace credentials from environment
    gmail_user = os.getenv('GMAIL_USER')
    gmail_password = os.getenv('GMAIL_PASSWORD')

    if not gmail_user or not gmail_password:
        return False, "Google Workspace credentials not configured. Set GMAIL_USER and GMAIL_PASSWORD environment variables."

    print(".2f"
    print(".1f"
    print(".1f"
    return send_external_email(smtp_server, smtp_port, gmail_user, gmail_password, to_email, subject, body)

def send_gmail_email(to_email, subject, body):
    """Send email via Gmail SMTP (legacy method)"""

    # Gmail SMTP settings
    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    # Get Gmail credentials from environment or prompt
    gmail_user = os.getenv('GMAIL_USER')
    gmail_password = os.getenv('GMAIL_APP_PASSWORD')

    if not gmail_user or not gmail_password:
        return False, "Gmail credentials not configured. Set GMAIL_USER and GMAIL_APP_PASSWORD environment variables."

    return send_external_email(smtp_server, smtp_port, gmail_user, gmail_password, to_email, subject, body)

def send_sendgrid_email(to_email, subject, body):
    """Send email via SendGrid SMTP"""

    # SendGrid SMTP settings
    smtp_server = "smtp.sendgrid.net"
    smtp_port = 587

    # Get SendGrid credentials from environment
    sendgrid_user = os.getenv('SENDGRID_USER', 'apikey')
    sendgrid_password = os.getenv('SENDGRID_API_KEY')

    if not sendgrid_password:
        return False, "SendGrid API key not configured. Set SENDGRID_API_KEY environment variable."

    return send_external_email(smtp_server, smtp_port, sendgrid_user, sendgrid_password, to_email, subject, body)

def main():
    """Main email sending function"""

    # Default recipient
    to_email = "sales@bison.management"

    # Email content - summary of SKU cleanup execution
    subject = ".1f"

    body = """
🚀 SKU Cleanup Execution Summary
================================

📊 EXECUTION SUMMARY
==================
Total SKUs Processed: 186
Eligible for Deletion: 0
Successfully Deleted: 0
Errors: 0
Execution Time: 0.00 seconds

📅 Generated: {}
🔗 System: BMAD SKU Management
📧 Delivery: Google Workspace SMTP Relay

---
Automated notification from SKU Cleanup Tool
Next run: Daily at 2:00 AM
""".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    print("📧 Sending Email via Google Workspace SMTP Relay...")
    print("=" * 50)
    print(".1f"
    print(".1f"
    print()

    # Try Google Workspace SMTP Relay first (user's configuration)
    success, message = send_gmail_relay_email(to_email, subject, body)

    if success:
        print("✅ Email sent successfully via Google Workspace SMTP Relay")
        print(".1f"
    else:
        print(".1f"
        print()

        # Try SendGrid as fallback
        print("🔄 Trying SendGrid as fallback...")
        success, message = send_sendgrid_email(to_email, subject, body)

        if success:
            print("✅ Email sent successfully via SendGrid SMTP")
            print(".1f"
        else:
            print(".1f"
            print()
            print("💡 Setup Instructions:")
            print("1. For Google Workspace: Set GMAIL_USER and GMAIL_PASSWORD environment variables")
            print("2. For SendGrid: Set SENDGRID_API_KEY environment variable")
            print("3. Or configure local Postfix to relay external emails")

if __name__ == "__main__":
    main()
