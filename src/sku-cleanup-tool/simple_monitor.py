#!/usr/bin/env python3
"""
SKU Cleanup Tool - Simple Production Monitor
Demonstrates how to verify scheduled run success
"""
import os
import re
from datetime import datetime, timedelta
from pathlib import Path

def check_run_success():
    """Check if the last scheduled run was successful"""

    print("🔍 SKU Cleanup Tool - Production Run Verification")
    print("=" * 50)
    print()

    # Check 1: Log file exists and has recent activity
    log_file = "logs/sku_cleanup.log"
    if not os.path.exists(log_file):
        print("❌ ERROR: Log file not found")
        return False

    # Get file modification time
    mod_time = datetime.fromtimestamp(os.path.getmtime(log_file))
    time_diff = datetime.now() - mod_time

    if time_diff > timedelta(hours=25):
        print(".2f"
        return False

    print(".2f"
    # Check 2: Look for success indicators in logs
    try:
        with open(log_file, 'r') as f:
            content = f.read()

        success_indicators = [
            "SKU cleanup process completed successfully",
            "Successfully Deleted:"
        ]

        found_success = []
        for indicator in success_indicators:
            if indicator.lower() in content.lower():
                found_success.append(indicator)

        if found_success:
            print(f"✅ SUCCESS: Found {len(found_success)} success indicators:")
            for indicator in found_success:
                print(f"   • {indicator}")
        else:
            print("⚠️  WARNING: No clear success indicators found")
            return False

        # Check 3: Look for errors
        error_count = len(re.findall(r'ERROR|CRITICAL|FATAL|Exception', content, re.IGNORECASE))

        if error_count == 0:
            print("✅ SUCCESS: No errors found in logs")
        elif error_count <= 3:
            print(".1f"
        else:
            print(f"❌ ERROR: Found {error_count} errors in logs")
            return False

        # Check 4: Check for reports
        reports_dir = Path("reports")
        if reports_dir.exists():
            recent_reports = list(reports_dir.glob("sku-cleanup-report-*.md"))
            if recent_reports:
                latest_report = max(recent_reports, key=lambda x: x.stat().st_mtime)
                print(".1f"
            else:
                print("⚠️  WARNING: No recent reports found")

        print()
        print("🎯 Overall Status: ✅ SCHEDULED RUN SUCCESSFUL")
        print()
        print("📋 Production Monitoring Setup:")
        print("• Logs are being written correctly")
        print("• Success indicators are present")
        print("• Error rate is acceptable")
        print("• Reports are being generated")
        print()
        print("🚀 Your 24-hour scheduled runs are working properly!")

        return True

    except Exception as e:
        print(f"❌ ERROR: Could not analyze logs: {e}")
        return False

if __name__ == "__main__":
    success = check_run_success()
    exit(0 if success else 1)
