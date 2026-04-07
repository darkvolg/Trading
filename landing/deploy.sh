#!/bin/bash
# Deploy TrendRider landing to Senko VPS (144.31.135.97)
# Usage: bash deploy.sh [domain]
# Example: bash deploy.sh trendrider.pro

set -euo pipefail

DOMAIN="${1:-trendrider.net}"
REMOTE_USER="root"
REMOTE_HOST="144.31.135.97"
REMOTE_PORT="2222"
REMOTE_DIR="/var/www/trendrider"
SSH_KEY="~/.ssh/senko_deploy"

# VPN proxy (vpn-b) — required, direct SSH doesn't work
VPN_HOST="84.201.178.73"
VPN_PORT="22"
VPN_USER="yc-user"
VPN_KEY="~/.ssh/yandex_vpn"

PROXY_CMD="ssh -i $VPN_KEY -p $VPN_PORT -o StrictHostKeyChecking=no -W %h:%p $VPN_USER@$VPN_HOST"
SSH_CMD="ssh -o ProxyCommand=\"$PROXY_CMD\" -i $SSH_KEY -p $REMOTE_PORT -o StrictHostKeyChecking=no $REMOTE_USER@$REMOTE_HOST"
SCP_CMD="scp -o ProxyCommand=\"$PROXY_CMD\" -i $SSH_KEY -P $REMOTE_PORT -o StrictHostKeyChecking=no"

echo "=== TrendRider Landing Deploy ==="
echo "Domain: $DOMAIN"
echo "Server: $REMOTE_HOST"
echo ""

# Step 1: Build
echo "[1/4] Building static site..."
cd "$(dirname "$0")"
npm run build
echo "Build complete. $(find out -name '*.html' | wc -l) HTML files."
echo ""

# Step 2: Create remote directory
echo "[2/4] Preparing server..."
eval $SSH_CMD "mkdir -p $REMOTE_DIR"
echo ""

# Step 3: Upload
echo "[3/4] Uploading to $REMOTE_HOST:$REMOTE_DIR ..."
eval $SCP_CMD -r out/* "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/"
echo "Upload complete."
echo ""

# Step 4: Set permissions + reload nginx
echo "[4/4] Setting permissions & reloading nginx..."
eval $SSH_CMD "chown -R www-data:www-data $REMOTE_DIR && nginx -t && systemctl reload nginx"
echo ""

echo "=== Done! ==="
echo "Check: https://$DOMAIN"
echo ""
echo "If nginx vhost not configured yet, copy nginx config:"
echo "  $SCP_CMD nginx-$DOMAIN.conf $REMOTE_USER@$REMOTE_HOST:/etc/nginx/sites-available/$DOMAIN"
echo "  $SSH_CMD \"ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/ && nginx -t && systemctl reload nginx\""
echo ""
echo "For SSL: $SSH_CMD \"certbot --nginx -d $DOMAIN -d www.$DOMAIN\""
