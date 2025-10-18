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
    script_dir = os.path.dirname(os.path.abspath(__file__))
    token_file = os.path.join(script_dir, 'token.json')
    if not os.path.exists(token_file):
        token_file = os.path.join(script_dir, '..', 'token.json')

    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    # If no valid credentials, run OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Run OAuth flow for first-time setup
            script_dir = os.path.dirname(os.path.abspath(__file__))
            # Look for credentials.json in the email_utils directory first, then in parent directory
            credentials_file = os.path.join(script_dir, 'credentials.json')
            if not os.path.exists(credentials_file):
                credentials_file = os.path.join(script_dir, '..', 'credentials.json')

            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save credentials for next run
        script_dir = os.path.dirname(os.path.abspath(__file__))
        token_file = os.path.join(script_dir, '..', 'token.json')
        with open(token_file, 'w') as token:
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

def should_send_email(force_send=False):
    """
    Determine if an email should be sent based on recent activity

    Args:
        force_send (bool): If True, always send email regardless of activity

    Returns:
        tuple: (should_send: bool, reason: str, summary: dict or None)
    """
    if force_send:
        return True, "Force send requested - sending notification", None

    try:
        # Read the main log file (last 100 lines for recent summary)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        log_file = os.path.join(script_dir, 'logs', 'sku_cleanup.log')
        if not os.path.exists(log_file):
            return True, "No log file found - possible cleanup failure", None  # Force send if no logs

        # Get last 100 lines for summary
        with open(log_file, 'r') as f:
            lines = f.readlines()[-100:]

        # Extract key metrics from log
        total_processed = 0
        eligible_for_deletion = 0
        successfully_deleted = 0
        errors = 0

        for line in reversed(lines):
            if 'Total SKUs Processed:' in line:
                total_processed = int(line.split(':')[1].strip())
            elif 'Eligible for Deletion:' in line:
                eligible_for_deletion = int(line.split(':')[1].strip())
            elif 'Successfully Deleted:' in line:
                successfully_deleted = int(line.split(':')[1].strip())
            elif 'Errors:' in line:
                errors = int(line.split(':')[1].strip())

        # Check for critical failure patterns
        critical_errors = []
        for line in reversed(lines[-20:]):  # Check last 20 lines for critical errors
            if any(pattern in line.upper() for pattern in [
                'CRITICAL', 'FATAL', 'EXCEPTION', 'ERROR', 'FAILED',
                'COULD NOT', 'UNABLE TO', 'CONNECTION FAILED'
            ]):
                critical_errors.append(line.strip())

        # Check if there were any meaningful changes
        has_deletions = successfully_deleted > 0
        has_eligible_skus = eligible_for_deletion > 0
        has_errors = errors > 0 or len(critical_errors) > 0
        has_activity = total_processed > 0

        # Determine if email should be sent
        if has_deletions:
            return True, f"SKUs were successfully deleted ({successfully_deleted} deletions)", None
        elif has_eligible_skus:
            return True, f"SKUs eligible for deletion found ({eligible_for_deletion} eligible)", None
        elif has_errors:
            error_text = f"Errors occurred during execution ({errors} errors)"
            if critical_errors:
                error_text += f" - Critical issues: {len(critical_errors)} found"
            return True, error_text, None
        elif has_activity:
            # Always send email if there's activity and it's been more than 24 hours since last email
            # This ensures users know the system is running even when no deletions occur
            script_dir = os.path.dirname(os.path.abspath(__file__))
            last_email_file = os.path.join(script_dir, 'logs', 'last_email_sent.txt')
            if os.path.exists(last_email_file):
                with open(last_email_file, 'r') as f:
                    last_email_time = float(f.read().strip())
                current_time = __import__('time').time()
                hours_since_last_email = (current_time - last_email_time) / 3600

                if hours_since_last_email < 24:
                    return False, f"System running normally, last email sent {hours_since_last_email:.1f} hours ago", None

            return True, f"System running normally ({total_processed} SKUs processed, no deletions needed)", None
        else:
            # Check if cleanup process actually ran today by looking for today's timestamp
            today = __import__('datetime').datetime.now().strftime('%Y-%m-%d')
            has_today_activity = any(today in line for line in lines)

            if not has_today_activity:
                return True, "No activity detected for today - possible cleanup failure", None

            return False, "No activity detected in logs", None

    except Exception as e:
        # If we can't read logs, send email to be safe
        return True, f"Unable to analyze logs ({e}), sending precautionary email", None

def send_email_with_recipients(recipients, subject, body, sender_email='sales@bison.management', priority='normal'):
    """
    Send email using Gmail API with OAuth 2.0 to multiple recipients

    Args:
        recipients (dict): {'to': [...], 'cc': [...], 'bcc': [...]}
        subject (str): Email subject
        body (str): Email body (can be HTML)
        sender_email (str): Sender email address (must match OAuth account)
        priority (str): 'high', 'normal', or 'low' for email priority

    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        # Get OAuth credentials
        creds = get_credentials()

        # Build Gmail API service
        service = build('gmail', 'v1', credentials=creds)

        # Create email message
        message = MIMEMultipart()
        message['from'] = sender_email
        message['subject'] = subject

        # Add priority headers
        if priority == 'high':
            message['X-Priority'] = '1'
            message['Importance'] = 'high'
        elif priority == 'low':
            message['X-Priority'] = '5'
            message['Importance'] = 'low'

        # Add recipients
        if recipients.get('to'):
            message['to'] = ', '.join(recipients['to'])
        if recipients.get('cc'):
            message['cc'] = ', '.join(recipients['cc'])
        if recipients.get('bcc'):
            message['bcc'] = ', '.join(recipients['bcc'])

        # Add body as HTML for better formatting
        msg = MIMEText(body, 'html')
        message.attach(msg)

        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

        # Send email
        sent_message = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()

        message_id = sent_message['id']
        print(f"✅ Email sent successfully! Message ID: {message_id}")

        # Track when email was sent to prevent spam
        script_dir = os.path.dirname(os.path.abspath(__file__))
        last_email_file = os.path.join(script_dir, 'logs', 'last_email_sent.txt')
        os.makedirs(os.path.dirname(last_email_file), exist_ok=True)
        with open(last_email_file, 'w') as f:
            f.write(str(__import__('time').time()))

        return True, f"Email sent successfully to {len(recipients.get('to', []))} recipients"

    except HttpError as error:
        print(f"❌ Gmail API error: {error}")
        return False, f"Gmail API error: {error}"
    except Exception as error:
        print(f"❌ Unexpected error: {error}")
        return False, f"Unexpected error: {error}"

def send_email(to_email, subject, body, sender_email='sales@bison.management'):
    """
    Send email using Gmail API with OAuth 2.0 (legacy single recipient method)

    Args:
        to_email (str): Recipient email address
        subject (str): Email subject
        body (str): Email body (can be HTML)
        sender_email (str): Sender email address (must match OAuth account)

    Returns:
        tuple: (success: bool, message: str)
    """
    recipients = {'to': [to_email], 'cc': [], 'bcc': []}
    return send_email_with_recipients(recipients, subject, body, sender_email)

def send_error_alert(error_message, error_details=None, priority='high'):
    """
    Send immediate error alert email for critical issues

    Args:
        error_message (str): Brief error description
        error_details (str): Detailed error information
        priority (str): 'high', 'normal', or 'low' for email priority

    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        # Get OAuth credentials
        creds = get_credentials()

        # Build Gmail API service
        service = build('gmail', 'v1', credentials=creds)

        # Create email message
        message = MIMEMultipart()
        message['from'] = 'sales@bison.management'
        message['to'] = 'sales@bison.management'
        message['subject'] = f"🚨 CRITICAL: SKU Cleanup System Error Alert"

        # Set high priority
        message['X-Priority'] = '1'
        message['Importance'] = 'high'

        # Create error email body
        timestamp = __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S WITA')

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="background: #ffebee; border: 2px solid #f44336; border-radius: 8px; padding: 20px; margin: 20px 0;">
                <h2 style="color: #d32f2f; margin-top: 0;">🚨 CRITICAL SYSTEM ERROR</h2>
                <p style="font-size: 16px; color: #d32f2f; font-weight: bold;">{error_message}</p>

                <div style="background: #fff; border: 1px solid #ffcdd2; border-radius: 5px; padding: 15px; margin: 15px 0;">
                    <h3 style="color: #d32f2f; margin-top: 0;">Error Details:</h3>
                    <p style="font-family: monospace; background: #f8f8f8; padding: 10px; border-radius: 3px; font-size: 14px;">
                        {error_details or 'No additional details available'}
                    </p>
                </div>

                <div style="background: #e3f2fd; border-left: 4px solid #2196f3; padding: 15px; margin: 15px 0;">
                    <h3 style="color: #1976d2; margin-top: 0;">System Information:</h3>
                    <p><strong>Timestamp:</strong> {timestamp}</p>
                    <p><strong>System:</strong> BMAD SKU Cleanup Tool</p>
                    <p><strong>Priority:</strong> CRITICAL - Immediate attention required</p>
                </div>

                <div style="background: #fff3e0; border-left: 4px solid #ff9800; padding: 15px; margin: 15px 0;">
                    <h3 style="color: #f57c00; margin-top: 0;">Recommended Actions:</h3>
                    <ul>
                        <li>Check system logs for detailed error information</li>
                        <li>Verify API credentials and connectivity</li>
                        <li>Review recent changes that may have caused the issue</li>
                        <li>Contact system administrator if issue persists</li>
                    </ul>
                </div>

                <p style="color: #666; font-size: 12px; margin-top: 20px;">
                    This is an automated error alert from the BMAD SKU Cleanup System.
                </p>
            </div>
        </body>
        </html>
        """

        # Add body as HTML
        msg = MIMEText(html_body, 'html')
        message.attach(msg)

        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

        # Send email
        sent_message = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()

        message_id = sent_message['id']
        print(f"🚨 Critical error alert sent! Message ID: {message_id}")

        return True, f"Error alert sent successfully"

    except Exception as error:
        print(f"❌ Failed to send error alert: {error}")
        return False, f"Failed to send error alert: {error}"

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
