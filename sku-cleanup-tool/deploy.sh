#!/bin/bash

# SKU Cleanup Tool - Production Deployment Script
# This script sets up automated daily execution and monitoring

echo "🚀 SKU Cleanup Tool - Production Deployment"
echo "============================================="

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create .env file from env.credentials first"
    exit 1
fi

# Check if Python requirements are installed
echo "📦 Checking Python dependencies..."
if ! python3 -c "import boto3, requests, schedule" 2>/dev/null; then
    echo "Installing Python dependencies..."
    pip3 install -r requirements.txt
fi

# Set up log rotation
echo "📝 Setting up log rotation..."
sudo tee /etc/logrotate.d/sku-cleanup >/dev/null <<EOF
/var/log/sku-cleanup.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 $(whoami) $(whoami)
    postrotate
        systemctl reload rsyslog >/dev/null 2>&1 || true
    endscript
}
EOF

# Create cron job for daily execution
echo "⏰ Setting up daily automation..."
CRON_JOB="0 2 * * * cd $(pwd) && /usr/bin/python3 main.py >> /var/log/sku-cleanup.log 2>&1"

# Check if cron job already exists
if crontab -l | grep -q "sku-cleanup"; then
    echo "✅ Cron job already exists"
else
    # Add to current crontab
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "✅ Daily execution scheduled for 2:00 AM"
fi

# Create monitoring script
echo "📊 Creating monitoring script..."
cat > monitor.sh <<'EOF'
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
EOF

chmod +x monitor.sh

# Create systemd service (optional, for more robust deployment)
echo "🔧 Creating systemd service (optional)..."
sudo tee /etc/systemd/system/sku-cleanup.service >/dev/null <<EOF
[Unit]
Description=SKU Cleanup Tool
After=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$(pwd)
ExecStart=/usr/bin/python3 $(pwd)/main.py
Restart=always
RestartSec=300

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service (optional)
echo "🔄 Service management:"
echo "   Enable: sudo systemctl enable sku-cleanup"
echo "   Start:  sudo systemctl start sku-cleanup"
echo "   Status: sudo systemctl status sku-cleanup"

echo ""
echo "🎯 Production Deployment Complete!"
echo "================================"
echo "✅ Daily automation scheduled (2:00 AM)"
echo "✅ Log rotation configured (30 days)"
echo "✅ Monitoring script created"
echo "✅ Systemd service available (optional)"
echo ""
echo "📋 Next Steps:"
echo "1. Review and test the setup: python3 main.py"
echo "2. Monitor execution: ./monitor.sh"
echo "3. Check logs: tail -f /var/log/sku-cleanup.log"
echo "4. Optional: Enable systemd service for better reliability"
echo ""
echo "⚠️  Remember to:"
echo "   - Add .env to .gitignore"
echo "   - Never commit credentials to version control"
echo "   - Monitor the first few automated runs"
