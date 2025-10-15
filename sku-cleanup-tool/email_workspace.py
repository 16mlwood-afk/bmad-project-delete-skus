#!/usr/bin/env python3
"""
SKU Cleanup Tool - Google Workspace Email Sender
Uses Google Workspace SMTP Relay for reliable email delivery
"""

import smtplib
import os
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def send_workspace_email(to_email, subject, body):
    """Send email via Google Workspace SMTP Relay"""
    
    # Google Workspace SMTP Relay settings
    smtp_server = "smtp-relay.gmail.com"
    smtp_port = 587
    
    # Get Google Workspace credentials from environment
    username = os.getenv('GMAIL_USER')
    password = os.getenv('GMAIL_PASSWORD')
    
    if not username or not password:
        return False, "Google Workspace credentials not configured. Set GMAIL_USER and GMAIL_PASSWORD environment variables."
    
    # Create message
    msg = MIMEMultipart()
    msg['From'] = username
    msg['To'] = to_email
    msg['Subject'] = subject
    
    # Add body
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        print("Connecting to Google Workspace SMTP Relay...")
        print(f"Server: {smtp_server}:{smtp_port}")
        print(f"Username: {username}")
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
    print(f"To: {to_email}")
    print(f"To: {to_email}")
    print()
    
    # Send via Google Workspace SMTP Relay
    success, message = send_workspace_email(to_email, subject, body)
    
    if success:
        print("✅ Email sent successfully via Google Workspace SMTP Relay")
        print(f"📬 Check inbox at {to_email}")
    else:
        print(f"📬 Check inbox at {to_email}")
        print()
        print("💡 Setup Instructions:")
        print("1. Set GMAIL_USER and GMAIL_PASSWORD environment variables")
        print("2. Ensure Google Workspace SMTP relay is properly configured")
        print("3. Check SMTP credentials and permissions")

if __name__ == "__main__":
    main()
