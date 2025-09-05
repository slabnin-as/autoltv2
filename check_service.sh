#!/bin/bash
# Script to check AutoLT v2 user service status and logs

echo "🔍 AutoLT v2 User Service Status Check"
echo "======================================"

USER_SERVICE_DIR="$HOME/.config/systemd/user"
SERVICE_FILE="$USER_SERVICE_DIR/autoltv2.service"

# Check if service exists
if [ ! -f "$SERVICE_FILE" ]; then
    echo "❌ AutoLT v2 user service is not installed"
    echo "Run ./install_service.sh to install it"
    exit 1
fi

# Service status
echo "📊 Service Status:"
systemctl --user status autoltv2 --no-pager -l

echo ""
echo "🔧 Service Configuration:"
echo "Service file: $SERVICE_FILE"
echo "Working directory: $(grep WorkingDirectory "$SERVICE_FILE" | cut -d'=' -f2)"
echo "Environment file: $(grep EnvironmentFile "$SERVICE_FILE" | cut -d'=' -f2)"

echo ""
echo "📝 Recent Logs (last 20 lines):"
journalctl --user -u autoltv2 -n 20 --no-pager

echo ""
echo "🔐 User Lingering Status:"
if command -v loginctl >/dev/null 2>&1; then
    if loginctl show-user "$(whoami)" | grep -q "Linger=yes"; then
        echo "✅ User lingering is enabled (service will start without login)"
    else
        echo "⚠️ User lingering is disabled (service only runs when logged in)"
        echo "To enable: sudo loginctl enable-linger $(whoami)"
    fi
else
    echo "ℹ️ loginctl not available"
fi

echo ""
echo "🌐 Network Check:"
if curl -s http://127.0.0.1:5000/ > /dev/null; then
    echo "✅ Application is responding on http://127.0.0.1:5000"
else
    echo "❌ Application is not responding on http://127.0.0.1:5000"
fi

echo ""
echo "📋 Useful Commands:"
echo "  View live logs:       journalctl --user -u autoltv2 -f"
echo "  Restart service:      systemctl --user restart autoltv2"
echo "  Stop service:         systemctl --user stop autoltv2" 
echo "  Start service:        systemctl --user start autoltv2"
echo "  Disable service:      systemctl --user disable autoltv2"
echo "  Enable lingering:     sudo loginctl enable-linger $(whoami)"