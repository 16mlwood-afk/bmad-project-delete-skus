#!/bin/bash

# SKU Cleanup Tool - Email Summary Generator
# Sends comprehensive email reports after each automated run

EMAIL="sales@bison.management"
LOG_FILE="/var/log/sku-cleanup.log"
PROJECT_DIR="/Users/masonwood/bmad-project-delete-skus/sku-cleanup-tool"
REPORTS_DIR="$PROJECT_DIR/reports"

# Function to send email with subject and body
send_email() {
    local subject="$1"
    local body="$2"

    # Use mail command if available, otherwise try alternative methods
    if command -v mail &> /dev/null; then
        echo "$body" | mail -s "$subject" "$EMAIL"
    else
        # Alternative: use sendmail directly or other methods
        echo "Subject: $subject
To: $EMAIL

$body" | sendmail -t
    fi
}

# Function to extract execution summary from logs
get_execution_summary() {
    local log_file="$1"

    if [ ! -f "$log_file" ]; then
        echo "❌ Log file not found: $log_file"
        return 1
    fi

    # Extract key metrics from recent logs
    local total_skus=$(tail -50 "$log_file" | grep "Total SKUs Processed:" | tail -1 | sed 's/.*Total SKUs Processed: \([0-9]*\).*/\1/')
    local eligible=$(tail -50 "$log_file" | grep "Eligible for Deletion:" | tail -1 | sed 's/.*Eligible for Deletion: \([0-9]*\).*/\1/')
    local deleted=$(tail -50 "$log_file" | grep "Successfully Deleted:" | tail -1 | sed 's/.*Successfully Deleted: \([0-9]*\).*/\1/')
    local errors=$(tail -50 "$log_file" | grep "Errors:" | tail -1 | sed 's/.*Errors: \([0-9]*\).*/\1/')
    local exec_time=$(tail -50 "$log_file" | grep "Execution Time:" | tail -1 | sed 's/.*Execution Time: \([0-9.]*\).*/\1/')

    echo "📊 EXECUTION SUMMARY"
    echo "=================="
    echo "Total SKUs Processed: ${total_skus:-0}"
    echo "Eligible for Deletion: ${eligible:-0}"
    echo "Successfully Deleted: ${deleted:-0}"
    echo "Errors: ${errors:-0}"
    echo "Execution Time: ${exec_time:-0.00} seconds"

    if [ "${errors:-0}" -gt 0 ]; then
        echo ""
        echo "🚨 RECENT ERRORS:"
        tail -20 "$log_file" | grep "ERROR\|CRITICAL\|FATAL" | head -5
    fi
}

# Function to check for recent reports
get_recent_reports() {
    local reports_dir="$1"

    if [ ! -d "$reports_dir" ]; then
        echo "❌ Reports directory not found: $reports_dir"
        return 1
    fi

    # Find most recent report
    local latest_report=$(ls -t "$reports_dir"/*.md 2>/dev/null | head -1)

    if [ -n "$latest_report" ]; then
        echo ""
        echo "📋 LATEST REPORT: $(basename "$latest_report")"
        echo "=================="
        head -20 "$latest_report"
    else
        echo "❌ No recent reports found"
    fi
}

# Main execution
echo "📧 Generating Email Summary for SKU Cleanup Run"
echo "=============================================="

# Check if we have recent execution data
if [ -f "$LOG_FILE" ]; then
    echo "✅ Found execution logs"

    # Generate summary
    SUMMARY=$(get_execution_summary "$LOG_FILE")
    REPORTS=$(get_recent_reports "$REPORTS_DIR")

    # Create email body
    EMAIL_BODY="
🚀 SKU Cleanup Execution Summary
================================

$SUMMARY

$REPORTS

📅 Generated: $(date)
🔗 Log Location: $LOG_FILE
📁 Reports Location: $REPORTS_DIR

---
Automated notification from SKU Cleanup Tool
Project: BMAD SKU Management System
"

    # Send email
    if send_email "SKU Cleanup Summary - $(date +%Y-%m-%d)" "$EMAIL_BODY"; then
        echo "✅ Email summary sent successfully to $EMAIL"
    else
        echo "❌ Failed to send email summary"
    fi

else
    echo "❌ No execution logs found - run may have failed"
    send_email "SKU Cleanup Alert - Execution Failed" "
⚠️ SKU Cleanup execution may have failed

No recent execution logs found in: $LOG_FILE

Please check:
1. Cron job execution
2. System logs for errors
3. Network connectivity for Amazon API

Last checked: $(date)
"
fi

echo "📧 Email summary generation complete"
