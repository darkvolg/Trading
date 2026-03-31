#!/usr/bin/env bash
# deploy_marketing.sh — Deploy marketing automation scripts to Senko + Yandex servers
# Usage: bash deploy_marketing.sh
# Safe to run multiple times (idempotent)

set -euo pipefail

# ── Colors ──────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

ok()   { echo -e "${GREEN}[OK]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; }
info() { echo -e "${CYAN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

# ── Paths ───────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AUTOPILOT="$SCRIPT_DIR/autopilot.py"
CONTENT_BANK="$SCRIPT_DIR/content_bank.json"
SERVER_MONITOR="$SCRIPT_DIR/server_monitor.py"

# ── SSH config ──────────────────────────────────────────────────────────────
YANDEX_HOST="yc-user@84.201.178.73"
YANDEX_KEY="$HOME/.ssh/yandex_vpn"

SENKO_HOST="root@144.31.135.97"
SENKO_PORT="2222"
SENKO_KEY="$HOME/.ssh/senko_deploy"

SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=15"

SENKO_SSH="ssh $SSH_OPTS -p $SENKO_PORT -i $SENKO_KEY -J $YANDEX_HOST root@144.31.135.97"
SENKO_SCP="scp $SSH_OPTS -P $SENKO_PORT -i $SENKO_KEY -o ProxyJump=$YANDEX_HOST"

YANDEX_SSH="ssh $SSH_OPTS -i $YANDEX_KEY $YANDEX_HOST"
YANDEX_SCP="scp $SSH_OPTS -i $YANDEX_KEY"

# ── Remote paths ────────────────────────────────────────────────────────────
SENKO_REMOTE_DIR="/opt/freqtrade/scripts/marketing"
YANDEX_REMOTE_DIR="/opt/scripts/marketing"

# ── Cron blocks ─────────────────────────────────────────────────────────────
CRON_MARKER_START="# === TrendRider Marketing START ==="
CRON_MARKER_END="# === TrendRider Marketing END ==="

SENKO_CRON_BLOCK="$CRON_MARKER_START
# === TrendRider Marketing Autopilot ===
0 9,18 * * * /usr/bin/python3 $SENKO_REMOTE_DIR/autopilot.py --twitter >> ~/logs/marketing.log 2>&1
0 14 * * * /usr/bin/python3 $SENKO_REMOTE_DIR/autopilot.py --reddit >> ~/logs/marketing.log 2>&1
0 7 * * * /usr/bin/python3 $SENKO_REMOTE_DIR/autopilot.py --remind >> ~/logs/marketing.log 2>&1
# === Server Cross-Monitor ===
*/5 * * * * /usr/bin/python3 $SENKO_REMOTE_DIR/server_monitor.py >> ~/logs/server_monitor.log 2>&1
0 8 * * * /usr/bin/python3 $SENKO_REMOTE_DIR/server_monitor.py --daily-report >> ~/logs/server_monitor.log 2>&1
$CRON_MARKER_END"

YANDEX_CRON_BLOCK="$CRON_MARKER_START
# === Server Cross-Monitor ===
*/5 * * * * /usr/bin/python3 $YANDEX_REMOTE_DIR/server_monitor.py >> ~/logs/server_monitor.log 2>&1
0 8 * * * /usr/bin/python3 $YANDEX_REMOTE_DIR/server_monitor.py --daily-report >> ~/logs/server_monitor.log 2>&1
$CRON_MARKER_END"

# ── Pre-flight checks ──────────────────────────────────────────────────────
echo ""
echo "=========================================="
echo "  TrendRider Marketing Deploy Script"
echo "=========================================="
echo ""

# Check local files exist
MISSING=0
for f in "$AUTOPILOT" "$CONTENT_BANK" "$SERVER_MONITOR"; do
    if [[ ! -f "$f" ]]; then
        fail "Missing local file: $f"
        MISSING=1
    fi
done
if [[ $MISSING -eq 1 ]]; then
    fail "Cannot proceed without all source files."
    exit 1
fi
ok "All local source files found"

# Check SSH keys exist
for key in "$SENKO_KEY" "$YANDEX_KEY"; do
    if [[ ! -f "$key" ]]; then
        fail "SSH key not found: $key"
        exit 1
    fi
done
ok "SSH keys found"

# ── Step 1: Test SSH connectivity ───────────────────────────────────────────
echo ""
info "Step 1: Testing SSH connectivity..."

if $YANDEX_SSH "echo ok" >/dev/null 2>&1; then
    ok "Yandex Cloud (84.201.178.73) — connected"
else
    fail "Cannot connect to Yandex Cloud (84.201.178.73)"
    exit 1
fi

if $SENKO_SSH "echo ok" >/dev/null 2>&1; then
    ok "Senko Digital (144.31.135.97) — connected"
else
    fail "Cannot connect to Senko Digital (144.31.135.97) via ProxyJump"
    exit 1
fi

# ── Step 2: Create remote directories + logs ────────────────────────────────
echo ""
info "Step 2: Creating remote directories..."

$SENKO_SSH "mkdir -p $SENKO_REMOTE_DIR ~/logs" 2>/dev/null
ok "Senko: $SENKO_REMOTE_DIR + ~/logs created"

$YANDEX_SSH "mkdir -p $YANDEX_REMOTE_DIR ~/logs" 2>/dev/null
ok "Yandex: $YANDEX_REMOTE_DIR + ~/logs created"

# ── Step 3: Deploy files ────────────────────────────────────────────────────
echo ""
info "Step 3: Deploying files..."

# Senko — all files
$SENKO_SCP "$AUTOPILOT" "$SENKO_HOST:$SENKO_REMOTE_DIR/autopilot.py"
ok "Senko: autopilot.py deployed"

$SENKO_SCP "$CONTENT_BANK" "$SENKO_HOST:$SENKO_REMOTE_DIR/content_bank.json"
ok "Senko: content_bank.json deployed"

$SENKO_SCP "$SERVER_MONITOR" "$SENKO_HOST:$SENKO_REMOTE_DIR/server_monitor.py"
ok "Senko: server_monitor.py deployed"

# Yandex — only monitor
$YANDEX_SCP "$SERVER_MONITOR" "$YANDEX_HOST:$YANDEX_REMOTE_DIR/server_monitor.py"
ok "Yandex: server_monitor.py deployed"

# Make scripts executable
$SENKO_SSH "chmod +x $SENKO_REMOTE_DIR/autopilot.py $SENKO_REMOTE_DIR/server_monitor.py" 2>/dev/null
ok "Senko: scripts marked executable"

$YANDEX_SSH "chmod +x $YANDEX_REMOTE_DIR/server_monitor.py" 2>/dev/null
ok "Yandex: scripts marked executable"

# ── Step 4: Install cron jobs ───────────────────────────────────────────────
echo ""
info "Step 4: Installing cron jobs..."

# Function to install cron block on a remote server
# Args: $1=SSH command, $2=cron block, $3=server label
install_cron() {
    local ssh_cmd="$1"
    local cron_block="$2"
    local label="$3"

    # Get existing crontab, strip old marketing block, append new one
    $ssh_cmd bash -s <<REMOTE_SCRIPT
# Get existing crontab (ignore "no crontab" error)
existing=\$(crontab -l 2>/dev/null || true)

# Remove old marketing block (between markers)
cleaned=\$(echo "\$existing" | sed "/$CRON_MARKER_START/,/$CRON_MARKER_END/d")

# Remove any trailing blank lines from cleaned crontab
cleaned=\$(echo "\$cleaned" | sed -e :a -e '/^\n*$/{\$d;N;ba}')

# Build new crontab
if [[ -n "\$cleaned" ]]; then
    new_crontab="\$cleaned

$cron_block"
else
    new_crontab="$cron_block"
fi

# Install
echo "\$new_crontab" | crontab -

echo "CRON_INSTALLED"
REMOTE_SCRIPT

    if [[ $? -eq 0 ]]; then
        ok "$label: cron jobs installed"
    else
        fail "$label: failed to install cron jobs"
        return 1
    fi
}

install_cron "$SENKO_SSH" "$SENKO_CRON_BLOCK" "Senko"
install_cron "$YANDEX_SSH" "$YANDEX_CRON_BLOCK" "Yandex"

# ── Step 5: Verify cron jobs ────────────────────────────────────────────────
echo ""
info "Step 5: Verifying cron jobs..."

echo ""
info "Senko crontab:"
$SENKO_SSH "crontab -l" 2>/dev/null | grep -A20 "TrendRider" || warn "No TrendRider entries found on Senko"

echo ""
info "Yandex crontab:"
$YANDEX_SSH "crontab -l" 2>/dev/null | grep -A20 "TrendRider" || warn "No TrendRider entries found on Yandex"

# ── Step 6: Test server_monitor on Senko ────────────────────────────────────
echo ""
info "Step 6: Testing server_monitor.py --daily-report on Senko..."

if $SENKO_SSH "cd $SENKO_REMOTE_DIR && /usr/bin/python3 server_monitor.py --daily-report" 2>&1; then
    ok "server_monitor.py --daily-report executed successfully"
else
    warn "server_monitor.py --daily-report returned non-zero (may need .env or deps)"
fi

# ── Summary ─────────────────────────────────────────────────────────────────
echo ""
echo "=========================================="
echo -e "  ${GREEN}Deployment Complete${NC}"
echo "=========================================="
echo ""
echo "  Senko Digital (144.31.135.97):"
echo "    - autopilot.py        → $SENKO_REMOTE_DIR/"
echo "    - content_bank.json   → $SENKO_REMOTE_DIR/"
echo "    - server_monitor.py   → $SENKO_REMOTE_DIR/"
echo "    - Cron: twitter 2x/day, reddit 1x/day, remind 1x/day"
echo "    - Cron: server monitor every 5 min + daily report 08:00"
echo ""
echo "  Yandex Cloud (84.201.178.73):"
echo "    - server_monitor.py   → $YANDEX_REMOTE_DIR/"
echo "    - Cron: server monitor every 5 min + daily report 08:00"
echo ""
echo "  Logs:"
echo "    - Senko:  ~/logs/marketing.log, ~/logs/server_monitor.log"
echo "    - Yandex: ~/logs/server_monitor.log"
echo ""
