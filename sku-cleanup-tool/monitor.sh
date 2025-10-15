#!/bin/bash
# SKU Cleanup Monitor - Check daily execution status

LOG_FILE="/var/log/sku-cleanup.log"
EMAIL="your-email@example.com"  # Change this to your email

# Check if log file exists and has recent entries
if [ -f "$LOG_FILE" ]; then
    LAST_RUN=$(tail -5 "$LOG_FILE" | grep -E "(Starting|Completed|Error)" | tail -1)

    if [ -n "$LAST_RUN" ]; then
        echo "✅ Last run: $LAST_RUN"
    else
        echo "⚠️  No recent activity found in logs"
        # Uncomment to enable email alerts:
        # echo "SKU Cleanup may have failed" | mail -s "SKU Cleanup Alert" $EMAIL
    fi
else
    echo "❌ Log file not found: $LOG_FILE"
fi

# Check for errors in recent logs
ERROR_COUNT=$(tail -100 "$LOG_FILE" | grep -c "ERROR")
if [ "$ERROR_COUNT" -gt 0 ]; then
    echo "⚠️  Found $ERROR_COUNT errors in recent logs"
    # Uncomment to enable email alerts:
    # tail -20 "$LOG_FILE" | grep "ERROR" | mail -s "SKU Cleanup Errors" $EMAIL
fi
