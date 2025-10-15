#!/usr/bin/env python3
"""
SKU Cleanup Tool - Email Sender
Supports both SMTP and Gmail OAuth 2.0 for reliable email delivery
"""

import smtplib
import os
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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

def get_cleanup_summary():
    """Extract summary information from log files"""
    try:
        # Read the main log file (last 100 lines for recent summary)
        log_file = 'logs/sku_cleanup.log'
        if not os.path.exists(log_file):
            return None, None, None

        # Get last 100 lines for summary
        with open(log_file, 'r') as f:
            lines = f.readlines()[-100:]

        # Extract key metrics from log
        total_processed = 0
        eligible_for_deletion = 0
        successfully_deleted = 0
        errors = 0
        execution_time = "0.00 seconds"

        for line in reversed(lines):
            if 'Total SKUs Processed:' in line:
                total_processed = int(line.split(':')[1].strip())
            elif 'Eligible for Deletion:' in line:
                eligible_for_deletion = int(line.split(':')[1].strip())
            elif 'Successfully Deleted:' in line:
                successfully_deleted = int(line.split(':')[1].strip())
            elif 'Errors:' in line:
                errors = int(line.split(':')[1].strip())
            elif 'Execution Time:' in line:
                execution_time = line.split(':')[1].strip()

        # Read processed SKUs file
        processed_skus_file = 'logs/processed_skus.txt'
        processed_skus_list = []
        if os.path.exists(processed_skus_file):
            with open(processed_skus_file, 'r') as f:
                processed_skus_list = f.read().strip().split('\n')

        # Get timestamp from most recent log entry
        timestamp = "Unknown"
        for line in reversed(lines[:20]):  # Check last 20 lines for timestamp
            if ' - ' in line and len(line.split(' - ')[0]) == 19:  # ISO timestamp format
                timestamp = line.split(' - ')[0]
                break

        return {
            'total_processed': total_processed,
            'eligible_for_deletion': eligible_for_deletion,
            'successfully_deleted': successfully_deleted,
            'errors': errors,
            'execution_time': execution_time,
            'timestamp': timestamp,
            'processed_skus_count': len(processed_skus_list),
            'processed_skus_preview': processed_skus_list[:10] if processed_skus_list else []
        }

    except Exception as e:
        print(f"Warning: Could not read log files: {e}")
        return None

def send_oauth_email(to_email, subject, body, force_send=False):
    """Send email via Gmail OAuth 2.0 with smart frequency logic"""
    try:
        # Import here to avoid errors if OAuth libraries aren't installed
        from gmail_oauth_sender import send_email_with_recipients, should_send_email, send_error_alert

        # Check if email should be sent (unless forced)
        if not force_send:
            should_send, reason, _ = should_send_email()
            if not should_send:
                print(f"📧 Email not sent: {reason}")
                return True, f"Email skipped: {reason}"

        # Get configuration from environment
        sender_email = os.getenv('GMAIL_USER', 'sales@bison.management')

        # Get recipients from environment (support multiple)
        primary_recipients = [to_email]
        cc_recipients = os.getenv('EMAIL_CC', '').split(',') if os.getenv('EMAIL_CC') else []
        bcc_recipients = os.getenv('EMAIL_BCC', '').split(',') if os.getenv('EMAIL_BCC') else []

        # Filter out empty strings
        cc_recipients = [email.strip() for email in cc_recipients if email.strip()]
        bcc_recipients = [email.strip() for email in bcc_recipients if email.strip()]

        recipients = {
            'to': primary_recipients,
            'cc': cc_recipients,
            'bcc': bcc_recipients
        }

        # Get actual cleanup summary from logs
        summary = get_cleanup_summary()

        if summary:
            # Create HTML body with actual data
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0;">
                    <h1>🚀 BMAD SKU Cleanup Report</h1>
                    <p style="margin: 0; opacity: 0.9;">Automated Daily Execution Summary</p>
                </div>

                <div style="background: #f8f9fa; padding: 30px; border: 1px solid #dee2e6; border-radius: 0 0 10px 10px;">
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px;">
                        <div style="background: #e3f2fd; padding: 20px; border-radius: 8px; text-align: center; border-left: 4px solid #2196f3;">
                            <h3 style="margin: 0 0 10px 0; color: #1976d2;">📊 Total Processed</h3>
                            <p style="font-size: 24px; font-weight: bold; margin: 0; color: #1976d2;">{summary['total_processed']:,}</p>
                            <p style="margin: 5px 0 0 0; font-size: 12px; color: #666;">SKUs analyzed</p>
                        </div>

                        <div style="background: #fff3e0; padding: 20px; border-radius: 8px; text-align: center; border-left: 4px solid #ff9800;">
                            <h3 style="margin: 0 0 10px 0; color: #f57c00;">⚠️ Eligible for Deletion</h3>
                            <p style="font-size: 24px; font-weight: bold; margin: 0; color: #f57c00;">{summary['eligible_for_deletion']:,}</p>
                            <p style="margin: 5px 0 0 0; font-size: 12px; color: #666;">FBA-verified safe to remove</p>
                        </div>

                        <div style="background: #e8f5e8; padding: 20px; border-radius: 8px; text-align: center; border-left: 4px solid #4caf50;">
                            <h3 style="margin: 0 0 10px 0; color: #388e3c;">✅ Successfully Deleted</h3>
                            <p style="font-size: 24px; font-weight: bold; margin: 0; color: #388e3c;">{summary['successfully_deleted']:,}</p>
                            <p style="margin: 5px 0 0 0; font-size: 12px; color: #666;">Removed from inventory</p>
                        </div>

                        <div style="background: #ffebee; padding: 20px; border-radius: 8px; text-align: center; border-left: 4px solid #f44336;">
                            <h3 style="margin: 0 0 10px 0; color: #d32f2f;">❌ Errors</h3>
                            <p style="font-size: 24px; font-weight: bold; margin: 0; color: #d32f2f;">{summary['errors']:,}</p>
                            <p style="margin: 5px 0 0 0; font-size: 12px; color: #666;">Issues encountered</p>
                        </div>
                    </div>

                    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #dee2e6;">
                        <h3 style="margin-top: 0; color: #495057;">📋 Execution Details</h3>
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr style="background: #e9ecef;">
                                <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">Timestamp</td>
                                <td style="padding: 12px; border: 1px solid #dee2e6;">{summary['timestamp']}</td>
                            </tr>
                            <tr>
                                <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">Execution Time</td>
                                <td style="padding: 12px; border: 1px solid #dee2e6;">{summary['execution_time']}</td>
                            </tr>
                            <tr style="background: #e9ecef;">
                                <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">Processed SKUs Count</td>
                                <td style="padding: 12px; border: 1px solid #dee2e6;">{summary['processed_skus_count']:,}</td>
                            </tr>
                        </table>
                    </div>

                    {f'''
                    <div style="background: #fff3cd; padding: 20px; border-radius: 8px; border: 1px solid #ffeaa7;">
                        <h3 style="margin-top: 0; color: #856404;">📦 Recently Processed SKUs (Preview)</h3>
                        <div style="max-height: 200px; overflow-y: auto; font-family: monospace; font-size: 12px;">
                            {'<br>'.join(f"<code style='background: #f8f9fa; padding: 2px 4px; border-radius: 3px;'>{sku}</code>" for sku in summary['processed_skus_preview'])}
                            {f"<p style='color: #856404; font-style: italic; margin: 10px 0 0 0;'>... and {summary['processed_skus_count'] - 10:,} more SKUs</p>" if summary['processed_skus_count'] > 10 else ""}
                        </div>
                    </div>
                    ''' if summary['processed_skus_preview'] else ''}

                    <div style="margin-top: 30px; padding: 20px; background: #d1ecf1; border-radius: 8px; border-left: 4px solid #17a2b8;">
                        <h3 style="margin-top: 0; color: #0c5460;">🔗 System Information</h3>
                        <p style="margin: 0;"><strong>System:</strong> BMAD SKU Management Platform</p>
                        <p style="margin: 5px 0 0 0;"><strong>Method:</strong> Automated FBA inventory verification</p>
                    </div>
                </div>

                <div style="text-align: center; margin-top: 20px; color: #6c757d; font-size: 12px;">
                    <p>This report was generated automatically by the BMAD SKU Cleanup System.</p>
                    <p>Next scheduled run: Daily at 2:00 AM</p>
                </div>
            </body>
            </html>
            """
        else:
            # Fallback to simple text if no log data available
            html_body = f"""
            <html>
            <body>
            <h2>🚀 SKU Cleanup Execution Summary</h2>
            <pre>{body}</pre>
            <p><em>Note: Could not read log files for detailed summary</em></p>
            </body>
            </html>
            """

        return send_email_with_recipients(recipients, subject, html_body, sender_email)
    except ImportError:
        return False, "Gmail OAuth libraries not installed. Install with: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client"
    except Exception as e:
        return False, f"OAuth email failed: {e}"

def main():
    """Main email sending function"""

    # Get configuration from environment
    to_email = os.getenv('DEFAULT_EMAIL_RECIPIENT', 'sales@bison.management')
    email_method = os.getenv('EMAIL_METHOD', 'oauth').lower()

    # Get recipients from environment (support multiple)
    cc_recipients = os.getenv('EMAIL_CC', '').split(',') if os.getenv('EMAIL_CC') else []
    bcc_recipients = os.getenv('EMAIL_BCC', '').split(',') if os.getenv('EMAIL_BCC') else []

    # Filter out empty strings
    cc_recipients = [email.strip() for email in cc_recipients if email.strip()]
    bcc_recipients = [email.strip() for email in bcc_recipients if email.strip()]

    # Email content (now dynamically generated from logs)
    subject = f"BMAD SKU Cleanup Report - {datetime.now().strftime('%Y-%m-%d')}"

    # The body is now generated dynamically in send_oauth_email()
    body = "Dynamic report generated from log files"

    print("📧 Sending Email via {}...".format(email_method.upper()))
    print("=" * 30)
    print(f"To: {to_email}")
    print(f"Subject: {subject}")
    print()

    # Try email method based on configuration
    if email_method == 'oauth':
        success, message = send_oauth_email(to_email, subject, body, force_send=False)
        if success:
            print("✅ Email sent successfully via Gmail OAuth 2.0")
            if "skipped" not in message.lower():
                print(f"📬 Check inbox at {to_email}")
                if cc_recipients or bcc_recipients:
                    print(f"📬 CC: {', '.join(cc_recipients)}" if cc_recipients else "")
                    print(f"📬 BCC: {', '.join(bcc_recipients)}" if bcc_recipients else "")
        else:
            print(f"❌ OAuth failed: {message}")
            print()
            print("💡 OAuth Setup Instructions:")
            print("1. Ensure credentials.json exists in the current directory")
            print("2. Run this script - it will open a browser for OAuth consent")
            print("3. Log in with your Google account (sales@bison.management)")
            print("4. Grant permissions for Gmail API access")

        # Test error alerting if requested
        if "--test-error-alert" in sys.argv:
            print("\n🧪 Testing error alert system...")
            from gmail_oauth_sender import send_error_alert
            alert_success, alert_message = send_error_alert(
                "Test error alert",
                "This is a test of the error alerting system. If you receive this, error alerts are working correctly."
            )
            if alert_success:
                print("✅ Error alert test successful")
            else:
                print(f"❌ Error alert test failed: {alert_message}")

    elif email_method == 'smtp':
        # Try Gmail SMTP first (legacy method)
        success, message = send_gmail_email(to_email, subject, body)

        if success:
            print("✅ Email sent successfully via Gmail SMTP")
            print(f"📬 Check inbox at {to_email}")
        else:
            print(f"❌ Gmail SMTP failed: {message}")

            # Try SendGrid as alternative
            print("🔄 Trying SendGrid...")
            success, message = send_sendgrid_email(to_email, subject, body)

            if success:
                print("✅ Email sent successfully via SendGrid SMTP")
                print(f"📬 Check inbox at {to_email}")
            else:
                print(f"❌ SendGrid failed: {message}")
                print()
                print("💡 Setup Instructions:")
                print("1. For Gmail: Set GMAIL_USER and GMAIL_APP_PASSWORD environment variables")
                print("2. For SendGrid: Set SENDGRID_API_KEY environment variable")
                print("3. Or configure local Postfix to relay external emails")

    else:
        print(f"❌ Unknown email method: {email_method}")
        print("💡 Valid methods: oauth, smtp")
        return

if __name__ == "__main__":
    main()
