#!/bin/bash
# Marketing Autopilot Setup — installs cron jobs for automated posting
# Run on the server: bash setup.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Create logs directory
mkdir -p ~/logs

# Install cron jobs
# Twitter: 2x/day at 9:00 and 18:00 UTC
# Reddit: 1x/day at 14:00 UTC
# Reminders: 1x/day at 10:00 UTC (morning for user in Moscow timezone = UTC+3)

(crontab -l 2>/dev/null | grep -v "marketing/autopilot.py"; cat <<CRON
# === TrendRider Marketing Autopilot ===
0 9,18 * * * /usr/bin/python3 ${SCRIPT_DIR}/autopilot.py --twitter >> ~/logs/marketing_autopilot.log 2>&1
0 14 * * * /usr/bin/python3 ${SCRIPT_DIR}/autopilot.py --reddit >> ~/logs/marketing_autopilot.log 2>&1
0 7 * * * /usr/bin/python3 ${SCRIPT_DIR}/autopilot.py --remind >> ~/logs/marketing_autopilot.log 2>&1
CRON
) | crontab -

echo "Cron jobs installed:"
crontab -l | grep marketing

# Check env vars
echo ""
echo "Required env vars (add to ~/.bashrc or /etc/environment):"
for var in TWITTER_CONSUMER_KEY TWITTER_CONSUMER_SECRET TWITTER_ACCESS_TOKEN TWITTER_ACCESS_SECRET COMPOSIO_API_KEY TG_TOKEN ADMIN_CHAT_ID; do
    if [ -z "${!var}" ]; then
        echo "  MISSING: $var"
    else
        echo "  OK: $var"
    fi
done
