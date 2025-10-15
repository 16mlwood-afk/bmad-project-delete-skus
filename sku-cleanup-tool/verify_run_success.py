#!/usr/bin/env python3
"""
SKU Cleanup Tool - Scheduled Run Success Verification
Demonstrates how to verify if your scheduled runs are successful
"""
import os
import sys
import re
from datetime import datetime, timedelta
from pathlib import Path

class RunSuccessVerifier:
    """Verifies scheduled run success through multiple indicators"""

    def __init__(self, log_file='logs/sku_cleanup.log'):
        self.log_file = log_file
        self.log_path = Path(log_file)

    def check_log_exists(self) -> bool:
        """Check if log file exists"""
        return self.log_path.exists()

    def check_recent_activity(self, hours=25) -> dict:
        """Check for recent activity in logs"""
        if not self.check_log_exists():
            return {'status': 'ERROR', 'message': 'Log file not found'}

        try:
            # Get timestamp from last modification
            last_modified = datetime.fromtimestamp(self.log_path.stat().st_mtime)
            time_since_modified = datetime.now() - last_modified

            # Check if modified within expected timeframe (24 hours + buffer)
            if time_since_modified > timedelta(hours=hours):
                return {
                    'status': 'WARNING',
                    'message': '.2f'
                }

            return {
                'status': 'SUCCESS',
                'message': '.2f'
            }

        except Exception as e:
            return {'status': 'ERROR', 'message': f'Error reading log file: {e}'}

    def check_completion_indicators(self) -> dict:
        """Check for successful completion indicators in logs"""
        if not self.check_log_exists():
            return {'status': 'ERROR', 'message': 'Log file not found'}

        try:
            with open(self.log_file, 'r') as f:
                content = f.read()

            # Check for successful completion
            success_patterns = [
                r'SKU cleanup process completed successfully',
                r'Successfully Deleted: \d+',
                r'Verification complete'
            ]

            found_indicators = []
            for pattern in success_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    found_indicators.append(pattern)

            if found_indicators:
                return {
                    'status': 'SUCCESS',
                    'message': f'Found {len(found_indicators)} success indicators',
                    'indicators': found_indicators
                }

            return {'status': 'WARNING', 'message': 'No success indicators found'}

        except Exception as e:
            return {'status': 'ERROR', 'message': f'Error reading log content: {e}'}

    def check_error_indicators(self) -> dict:
        """Check for error indicators in logs"""
        if not self.check_log_exists():
            return {'status': 'ERROR', 'message': 'Log file not found'}

        try:
            with open(self.log_file, 'r') as f:
                content = f.read()

            # Check for error patterns
            error_patterns = [
                r'ERROR',
                r'CRITICAL',
                r'FATAL',
                r'Exception',
                r'Traceback'
            ]

            error_count = 0
            for pattern in error_patterns:
                error_count += len(re.findall(pattern, content, re.IGNORECASE))

            if error_count == 0:
                return {'status': 'SUCCESS', 'message': 'No errors found in logs'}
            elif error_count <= 5:
                return {'status': 'WARNING', 'message': f'Found {error_count} minor errors'}
            else:
                return {'status': 'ERROR', 'message': f'Found {error_count} errors - review required'}

        except Exception as e:
            return {'status': 'ERROR', 'message': f'Error analyzing logs: {e}'}

    def check_report_generation(self) -> dict:
        """Check if reports were generated"""
        reports_dir = Path('reports')
        if not reports_dir.exists():
            return {'status': 'WARNING', 'message': 'Reports directory not found'}

        try:
            # Look for recent report files
            recent_reports = []
            for report_file in reports_dir.glob('sku-cleanup-report-*.md'):
                if (datetime.now() - datetime.fromtimestamp(report_file.stat().st_mtime)) < timedelta(hours=25):
                    recent_reports.append(report_file.name)

            if recent_reports:
                return {
                    'status': 'SUCCESS',
                    'message': f'Found {len(recent_reports)} recent report(s)',
                    'reports': recent_reports
                }

            return {'status': 'WARNING', 'message': 'No recent reports found'}

        except Exception as e:
            return {'status': 'ERROR', 'message': f'Error checking reports: {e}'}

    def get_comprehensive_status(self) -> dict:
        """Get comprehensive status of scheduled runs"""
        checks = {
            'log_activity': self.check_recent_activity(),
            'completion': self.check_completion_indicators(),
            'errors': self.check_error_indicators(),
            'reports': self.check_report_generation()
        }

        # Determine overall status
        error_checks = [checks['log_activity'], checks['completion'], checks['errors']]
        warning_checks = [checks['reports']]

        if any(check['status'] == 'ERROR' for check in error_checks):
            overall_status = 'ERROR'
            message = 'Critical issues detected - immediate attention required'
        elif any(check['status'] == 'WARNING' for check in error_checks):
            overall_status = 'WARNING'
            message = 'Some issues detected - review recommended'
        elif any(check['status'] == 'WARNING' for check in warning_checks):
            overall_status = 'WARNING'
            message = 'Minor issues detected - monitoring recommended'
        else:
            overall_status = 'SUCCESS'
            message = 'All checks passed - runs appear successful'

        return {
            'overall_status': overall_status,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'checks': checks
        }

def main():
    """Main verification function"""
    print("🔍 SKU Cleanup Tool - Scheduled Run Success Verification")
    print("=" * 60)
    print()

    verifier = RunSuccessVerifier()

    # Run comprehensive verification
    status = verifier.get_comprehensive_status()

    # Display results
    print(f"📊 Overall Status: {status['overall_status']}")
    print(f"📝 Message: {status['message']}")
    print(f"🕐 Checked: {status['timestamp']}")
    print()

    # Show detailed check results
    print("📋 Detailed Check Results:")
    print("-" * 40)

    for check_name, check_result in status['checks'].items():
        status_icon = {
            'SUCCESS': '✅',
            'WARNING': '⚠️',
            'ERROR': '❌'
        }.get(check_result['status'], '❓')

        print(".1f"
        if 'indicators' in check_result:
            for indicator in check_result['indicators'][:3]:  # Show first 3 indicators
                print(f"      • {indicator}")
        if 'reports' in check_result:
            for report in check_result['reports'][:3]:  # Show first 3 reports
                print(f"      • {report}")

    print()
    print("🎯 Production Monitoring Recommendations:")
    print("-" * 45)
    print("• Run this verification script after each scheduled execution")
    print("• Set up automated alerts for ERROR status")
    print("• Monitor WARNING status for potential issues")
    print("• Use logs/ and reports/ for detailed troubleshooting")
    print("• Implement email/Slack notifications for failures")

if __name__ == "__main__":
    main()
