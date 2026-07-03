#!/usr/bin/env bash
# Server hardening script for scm-mcp-mssp on a traditional Linux VM.
# Run once as root after deploying the application.
# Tested on Ubuntu 22.04 / 24.04 and RHEL 9.
set -euo pipefail

APP_USER="scm-mcp"
APP_GROUP="scm-mcp"
APP_DIR="/opt/scm-mcp-mssp"
SECRETS_DIR="/etc/scm-mcp-mssp"

echo "[1/7] Creating dedicated service account..."
if ! id "$APP_USER" &>/dev/null; then
    useradd --system --no-create-home --shell /usr/sbin/nologin \
        --comment "scm-mcp-mssp service account" "$APP_USER"
fi

echo "[2/7] Locking down application directory..."
install -d -m 750 -o "$APP_USER" -g "$APP_GROUP" "$APP_DIR"
install -d -m 700 -o "$APP_USER" -g "$APP_GROUP" "$SECRETS_DIR"
# .secrets.toml lives here, not in the repo working directory
chown -R "$APP_USER:$APP_GROUP" "$APP_DIR"
chmod -R o= "$APP_DIR"

echo "[3/7] Applying sysctl kernel hardening..."
install -m 644 "$(dirname "$0")/sysctl-hardening.conf" \
    /etc/sysctl.d/99-scm-mcp.conf
sysctl --system

echo "[4/7] Applying SSH hardening..."
install -m 644 "$(dirname "$0")/ssh-hardening.conf" \
    /etc/ssh/sshd_config.d/99-scm-mcp-hardening.conf
sshd -t && systemctl reload sshd

echo "[5/7] Installing systemd service unit..."
install -m 644 "$(dirname "$0")/scm-mcp.service" \
    /etc/systemd/system/scm-mcp.service
systemctl daemon-reload
systemctl enable scm-mcp.service

echo "[6/7] Configuring firewall (ufw)..."
if command -v ufw &>/dev/null; then
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow ssh
    # Only open SSE port if you run HTTP transport; remove if using stdio only
    # ufw allow from 127.0.0.1 to any port 8000 proto tcp
    ufw --force enable
else
    echo "  ufw not found — configure your firewall manually."
    echo "  Block all inbound except SSH. The MCP SSE port (8000)"
    echo "  should bind to 127.0.0.1 only (already the default)."
fi

echo "[7/7] Restricting secrets file..."
SECRETS_FILE="$SECRETS_DIR/.secrets.toml"
if [ -f "$SECRETS_FILE" ]; then
    chown "$APP_USER:$APP_GROUP" "$SECRETS_FILE"
    chmod 600 "$SECRETS_FILE"
else
    echo "  $SECRETS_FILE not found — copy .secrets.toml.example and populate it."
fi

echo ""
echo "Hardening complete. Next steps:"
echo "  1. Populate $SECRETS_DIR/.secrets.toml with tenant credentials"
echo "  2. Start service: systemctl start scm-mcp"
echo "  3. Check logs:    journalctl -u scm-mcp -f"
