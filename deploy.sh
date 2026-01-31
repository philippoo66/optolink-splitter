#!/bin/bash
# Deployment script for optolink-splitter
# Syncs files and runs remote installation script
# Usage: REMOTE_USER=username REMOTE_HOST=hostname ./deploy.sh

set -e

# Configuration
REMOTE_PATH="/opt/optolink"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Test SSH connection
log_info "Testing SSH connection to ${REMOTE_USER}@${REMOTE_HOST}..."
if ! ssh "${REMOTE_USER}@${REMOTE_HOST}" "echo 'Connected successfully' > /dev/null"; then
    log_error "Cannot connect to ${REMOTE_USER}@${REMOTE_HOST}"
    exit 1
fi

# Detect Python version
log_info "Detecting Python version on remote host..."
PYTHON_VERSION=$(ssh "${REMOTE_USER}@${REMOTE_HOST}" "python3 --version 2>&1")
log_info "Remote Python: ${PYTHON_VERSION}"

# Detect serial port group
log_info "Detecting serial port access group..."
SERIAL_GROUP=$(ssh "${REMOTE_USER}@${REMOTE_HOST}" "
    if getent group dialout >/dev/null 2>&1; then
        echo 'dialout'
    elif getent group uucp >/dev/null 2>&1; then
        echo 'uucp'
    else
        echo 'dialout'
    fi
")
log_info "Using group: ${SERIAL_GROUP}"

# Create remote directory with proper permissions (world-writable for rsync)
log_info "Preparing remote directory..."
ssh -t "${REMOTE_USER}@${REMOTE_HOST}" "sudo mkdir -p ${REMOTE_PATH} && sudo rm -rf ${REMOTE_PATH}/* ${REMOTE_PATH}/.[!.]* 2>/dev/null || true && sudo chmod 777 ${REMOTE_PATH}"

# Sync files to remote host
log_info "Syncing files to remote host..."
rsync -avz --delete --no-times --no-perms --no-owner --no-group \
    --exclude='venv/' \
    --exclude='.venv/' \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    --exclude='*.pyo' \
    --exclude='*.pyd' \
    --exclude='.git/' \
    --exclude='.gitignore' \
    --exclude='*.log' \
    --exclude='*.csv' \
    --exclude='*.history' \
    --exclude='.vscode/' \
    --exclude='*.code-workspace' \
    --exclude='deploy.sh' \
    --exclude='DEPLOYMENT.md' \
    --exclude='README.md' \
    --exclude='old_test/' \
    --exclude='test.py' \
    --exclude='allupdate.sh' \
    --exclude='entities.json' \
    ./ "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/"

# Sync install script
rsync -az install.sh "${REMOTE_USER}@${REMOTE_HOST}:/tmp/install.sh"
ssh "${REMOTE_USER}@${REMOTE_HOST}" "chmod +x /tmp/install.sh"

# Run installation script (ONE sudo password prompt)
log_info "Running installation (you will be prompted for sudo password)..."
ssh -t "${REMOTE_USER}@${REMOTE_HOST}" "sudo /tmp/install.sh ${SERIAL_GROUP} ${REMOTE_USER}"

# Cleanup
ssh "${REMOTE_USER}@${REMOTE_HOST}" "rm -f /tmp/install.sh"

log_info ""
log_info "Deployment complete!"
log_info ""
log_info "Useful commands:"
log_info "  View logs:    ssh ${REMOTE_USER}@${REMOTE_HOST} 'sudo journalctl -u optolink -f'"
log_info "  Restart:      ssh ${REMOTE_USER}@${REMOTE_HOST} 'sudo systemctl restart optolink'"
log_info "  Stop:         ssh ${REMOTE_USER}@${REMOTE_HOST} 'sudo systemctl stop optolink'"
log_info "  Status:       ssh ${REMOTE_USER}@${REMOTE_HOST} 'sudo systemctl status optolink'"
