#!/usr/bin/env python3
"""
SKU Cleanup Tool - Robust Wrapper with Error Notifications
Ensures email notifications are sent regardless of cleanup success/failure
"""

import subprocess
import sys
import os
import time
import logging
from datetime import datetime

# Configure logging - use absolute paths to ensure correct location
script_dir = os.path.dirname(os.path.abspath(__file__))
log_file = os.path.join(script_dir, 'logs', 'sku_cleanup.log')

# Ensure log directory exists
os.makedirs(os.path.dirname(log_file), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_cleanup_process():
    """Run the main cleanup process and return exit code"""
    logger.info("🚀 Starting SKU cleanup process...")

    try:
        # Run the main cleanup script
        result = subprocess.run([
            sys.executable, 'main.py'
        ], capture_output=True, text=True, cwd=os.getcwd())

        logger.info(f"Cleanup process exited with code: {result.returncode}")

        if result.returncode == 0:
            logger.info("✅ Cleanup completed successfully")
        else:
            logger.error(f"❌ Cleanup failed with exit code: {result.returncode}")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")

        return result.returncode, result.stdout, result.stderr

    except Exception as e:
        logger.error(f"❌ Failed to run cleanup process: {e}")
        return 1, "", str(e)

def send_notification_email(cleanup_success, stdout, stderr):
    """Send appropriate email notification based on cleanup result"""
    logger.info("📧 Preparing email notification...")

    try:
        # Import here to avoid issues if email modules aren't available
        from email_utils.email_external import main as send_email_main

        if cleanup_success:
            logger.info("✅ Cleanup successful - sending success notification")
            # Run email script normally for successful cleanup
            send_email_main()
        else:
            logger.warning("❌ Cleanup failed - sending error notification")
            # Run email script with force flag to ensure notification is sent
            sys.argv.append('--force-error')
            send_email_main()

        logger.info("📬 Email notification sent")

    except ImportError as e:
        logger.error(f"❌ Email modules not available: {e}")
        logger.error("💡 Install required packages: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    except Exception as e:
        logger.error(f"❌ Failed to send email notification: {e}")

def create_error_log_file(stdout, stderr):
    """Create a detailed error log file for debugging"""
    try:
        error_log_dir = 'logs/errors'
        os.makedirs(error_log_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        error_log_file = f'{error_log_dir}/cleanup_error_{timestamp}.log'

        with open(error_log_file, 'w') as f:
            f.write(f"SKU Cleanup Error Report - {datetime.now().isoformat()}\n")
            f.write("=" * 60 + "\n\n")
            f.write("STDOUT:\n")
            f.write("-" * 20 + "\n")
            f.write(stdout or "No output\n")
            f.write("\nSTDERR:\n")
            f.write("-" * 20 + "\n")
            f.write(stderr or "No errors\n")

        logger.info(f"📝 Error details saved to: {error_log_file}")
        return error_log_file

    except Exception as e:
        logger.error(f"❌ Failed to create error log file: {e}")
        return None

def cleanup_temp_files():
    """Clean up temporary files used for email notifications"""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        temp_files = [
            os.path.join(script_dir, 'logs', 'current_run_deleted.txt')
        ]

        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)
                logger.debug(f"🧹 Cleaned up temp file: {temp_file}")

    except Exception as e:
        logger.warning(f"⚠️ Could not clean up temp files: {e}")

def main():
    """Main wrapper function"""
    logger.info("=" * 60)
    logger.info("🔄 BMAD SKU Cleanup with Guaranteed Notifications")
    logger.info("=" * 60)

    start_time = time.time()

    # Run cleanup process
    exit_code, stdout, stderr = run_cleanup_process()

    # Calculate execution time
    execution_time = time.time() - start_time

    # Determine if cleanup was successful
    cleanup_success = (exit_code == 0)

    logger.info(f"📊 Execution Summary:")
    logger.info(f"   Duration: {execution_time:.2f} seconds")
    logger.info(f"   Exit Code: {exit_code}")
    logger.info(f"   Success: {cleanup_success}")

    # Create error log if cleanup failed
    if not cleanup_success:
        error_log_file = create_error_log_file(stdout, stderr)
        logger.error(f"📝 Error details logged to: {error_log_file}")

    # Always send notification email (success or error)
    send_notification_email(cleanup_success, stdout, stderr)

    # Clean up temporary files after email is sent
    cleanup_temp_files()

    logger.info("=" * 60)

    # Return appropriate exit code
    return 0 if cleanup_success else 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("🛑 Process interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"💥 Fatal error in wrapper: {e}")
        sys.exit(1)
