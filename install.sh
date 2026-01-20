#!/bin/bash
# Installation script for optolink-splitter
# Can be run locally or remotely via deploy.sh
# Usage: sudo ./install.sh [SERIAL_GROUP] [DEPLOYING_USER]

set -e

INSTALL_PATH="${INSTALL_PATH:-/opt/optolink}"
SERVICE_NAME="optolink"
SERIAL_GROUP="${1:-uucp}"
DEPLOYING_USER="${2:-}"
PYTHON_CMD="python3"

# Get the group of the deploying user
if [ -n "$DEPLOYING_USER" ]; then
    DEPLOY_GROUP=$(id -gn "$DEPLOYING_USER" 2>/dev/null || echo "optolink")
else
    DEPLOY_GROUP="optolink"
fi

echo "=== Optolink Installation ==="
echo "Install path: $INSTALL_PATH"
echo "Serial group: $SERIAL_GROUP"
echo "File group: $DEPLOY_GROUP"
echo ""

# Create optolink user if not exists
if ! id -u optolink >/dev/null 2>&1; then
    echo "[1/7] Creating optolink system user..."
    useradd -r -s /usr/sbin/nologin -M optolink
    echo "✓ User created"
else
    echo "[1/7] User optolink already exists"
fi

# Add optolink to serial port group
if ! groups optolink 2>/dev/null | grep -q "$SERIAL_GROUP"; then
    echo "[2/7] Adding optolink to $SERIAL_GROUP group..."
    usermod -a -G "$SERIAL_GROUP" optolink
    echo "✓ User added to group"
else
    echo "[2/7] User already in $SERIAL_GROUP group"
fi

# Set ownership and permissions
echo "[3/7] Setting ownership and permissions..."
chown -R optolink:${DEPLOY_GROUP} "$INSTALL_PATH"
chmod -R u+rwX,g+rX,o-rwx "$INSTALL_PATH"
chmod o+x "$INSTALL_PATH"  # Allow others to cd into directory
echo "✓ Ownership set"

# Remove old venv and create new one
echo "[4/7] Setting up Python virtual environment..."
if [ -d "$INSTALL_PATH/venv" ]; then
    rm -rf "$INSTALL_PATH/venv"
fi
sudo -u optolink $PYTHON_CMD -m venv "$INSTALL_PATH/venv"
echo "✓ Virtual environment created"

# Install dependencies
echo "[5/7] Installing Python dependencies..."
sudo -u optolink bash -c "source $INSTALL_PATH/venv/bin/activate && pip install -q --upgrade pip setuptools wheel && pip install -q pyserial paho-mqtt"
echo "✓ Dependencies installed"

# Create systemd service file
echo "[6/7] Creating systemd service..."
cat > "/etc/systemd/system/${SERVICE_NAME}.service" << EOF
[Unit]
Description=Optolink Splitter Service
After=network.target

[Service]
Type=simple
User=optolink
Group=optolink
SupplementaryGroups=${SERIAL_GROUP}
WorkingDirectory=${INSTALL_PATH}
Environment="PATH=${INSTALL_PATH}/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=${INSTALL_PATH}/venv/bin/python ${INSTALL_PATH}/optolinkvs2_switch.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
echo "✓ Service file created"

# Enable and start service
echo "[7/7] Starting service..."
systemctl daemon-reload
systemctl enable "${SERVICE_NAME}.service"
systemctl restart "${SERVICE_NAME}.service"
sleep 2
echo "✓ Service started"

echo ""
echo "=== Installation Complete ==="
systemctl status "${SERVICE_NAME}.service" --no-pager || true
