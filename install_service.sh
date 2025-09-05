#!/bin/bash
# Script to install AutoLT v2 as user systemd service (no sudo required)

set -e

echo "🔧 Installing AutoLT v2 user systemd service..."

# Get current directory and user
CURRENT_DIR=$(pwd)
CURRENT_USER=$(whoami)
USER_SERVICE_DIR="$HOME/.config/systemd/user"

echo "📁 Working directory: $CURRENT_DIR"
echo "👤 User: $CURRENT_USER"

# Create user systemd directory if it doesn't exist
echo "📂 Creating user systemd directory..."
mkdir -p "$USER_SERVICE_DIR"

# Create user service file with correct paths
echo "📝 Creating user service file..."
cat > "$USER_SERVICE_DIR/autoltv2.service" << EOF
[Unit]
Description=AutoLT v2 - JIRA and Jenkins Task Scheduler
After=network.target

[Service]
Type=exec
WorkingDirectory=$CURRENT_DIR
Environment=PATH=$CURRENT_DIR/venv/bin
Environment=FLASK_ENV=production
EnvironmentFile=$CURRENT_DIR/.env
ExecStart=$CURRENT_DIR/venv/bin/gunicorn --config $CURRENT_DIR/gunicorn.conf.py run:app
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
Restart=on-failure
RestartSec=10

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=autoltv2

[Install]
WantedBy=default.target
EOF

# Reload user systemd
echo "🔄 Reloading user systemd..."
systemctl --user daemon-reload

# Enable service
echo "✅ Enabling AutoLT v2 user service..."
systemctl --user enable autoltv2

# Enable lingering to start services without login
echo "🔐 Enabling user lingering..."
if command -v loginctl >/dev/null 2>&1; then
    if ! loginctl show-user "$CURRENT_USER" | grep -q "Linger=yes"; then
        echo "Note: To start service without login, run:"
        echo "  sudo loginctl enable-linger $CURRENT_USER"
    fi
else
    echo "Note: loginctl not available, service will only run when user is logged in"
fi

echo ""
echo "🎉 AutoLT v2 user service installed successfully!"
echo ""
echo "📋 Available commands:"
echo "  Start service:    systemctl --user start autoltv2"
echo "  Stop service:     systemctl --user stop autoltv2"
echo "  Restart service:  systemctl --user restart autoltv2"
echo "  Check status:     systemctl --user status autoltv2"
echo "  View logs:        journalctl --user -u autoltv2 -f"
echo "  Enable lingering: sudo loginctl enable-linger $CURRENT_USER"
echo ""
echo "🚀 To start the service now:"
echo "  systemctl --user start autoltv2"