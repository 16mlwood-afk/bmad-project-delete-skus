#!/usr/bin/env python3
"""
Gmail OAuth 2.0 Email Sender
Uses Gmail API with OAuth 2.0 for sending emails from company accounts
"""

import os
import base64
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Gmail API scope for sending emails
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def get_credentials():
    """Get or create OAuth 2.0 credentials"""
    creds = None

    # Check if token.json exists (from previous successful auth)
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If no valid credentials, run OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Run OAuth flow for first-time setup
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Save credentials for next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return creds

def create_message(sender, to, subject, body):
    """Create email message"""
    message = MIMEMultipart()
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject

    # Add body as HTML for better formatting
    msg = MIMEText(body, 'html')
    message.attach(msg)

    # Encode message
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    return {'raw': raw_message}

def send_email(to_email, subject, body, sender_email='sales@bison.management'):
    """
    Send email using Gmail API with OAuth 2.0

    Args:
        to_email (str): Recipient email address
        subject (str): Email subject
        body (str): Email body (can be HTML)
        sender_email (str): Sender email address (must match OAuth account)

    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        # Get OAuth credentials
        creds = get_credentials()

        # Build Gmail API service
        service = build('gmail', 'v1', credentials=creds)

        # Create email message
        message = create_message(sender_email, to_email, subject, body)

        # Send email
        sent_message = service.users().messages().send(
            userId='me',
            body=message
        ).execute()

        message_id = sent_message['id']
        print(f"✅ Email sent successfully! Message ID: {message_id}")
        return True, f"Email sent successfully to {to_email}"

    except HttpError as error:
        print(f"❌ Gmail API error: {error}")
        return False, f"Gmail API error: {error}"
    except Exception as error:
        print(f"❌ Unexpected error: {error}")
        return False, f"Unexpected error: {error}"

def test_gmail_oauth():
    """Test Gmail OAuth setup"""
    print("🔐 Testing Gmail OAuth 2.0 Setup...")
    print("=" * 40)

    # Test credentials
    try:
        creds = get_credentials()
        print("✅ OAuth credentials loaded successfully")

        # Test API connection
        service = build('gmail', 'v1', credentials=creds)
        profile = service.users().getProfile(userId='me').execute()

        print(f"✅ Connected to Gmail API")
        print(f"📧 Email address: {profile['emailAddress']}")
        print(f"📊 Messages total: {profile['messagesTotal']}")
        print(f"📊 Threads total: {profile['threadsTotal']}")

        return True

    except Exception as e:
        print(f"❌ OAuth setup failed: {e}")
        print()
        print("💡 Setup Instructions:")
        print("1. Ensure credentials.json exists in the current directory")
        print("2. Run this script - it will open a browser for OAuth consent")
        print("3. Log in with your Google account (sales@bison.management)")
        print("4. Grant permissions for Gmail API access")
        print("5. Token will be saved automatically for future runs")
        return False

if __name__ == "__main__":
    # Test the OAuth setup
    success = test_gmail_oauth()

    if success:
        print()
        print("🎉 Gmail OAuth is working!")
        print("✅ Ready for automated email notifications")

        # Send a test email
        print()
        print("📧 Sending test email...")
        test_subject = "SKU Cleanup Test - Gmail OAuth 2.0"
        test_body = """
        <h2>🚀 SKU Cleanup System Test (Gmail OAuth 2.0)</h2>
        <p><strong>Test sent:</strong> {}</p>
        <p><strong>System:</strong> BMAD SKU Management</p>
        <p><strong>Method:</strong> Gmail API with OAuth 2.0</p>
        <hr>
        <p>This is a test email using Gmail OAuth 2.0.</p>
        <p>Daily automated reports will be sent after each run at 2:00 AM.</p>
        """.format(__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        success, message = send_email("sales@bison.management", test_subject, test_body)

        if success:
            print("✅ Test email sent successfully!")
        else:
            print(f"❌ Test email failed: {message}")
    else:
        print("❌ Gmail OAuth setup needs to be completed")
