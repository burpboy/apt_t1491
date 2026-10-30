#!/bin/bash
#
# bash_history_clean.sh
# Versi: 1.0.0
# Deskripsi: Membersihkan riwayat perintah Bash (history) secara agresif namun aman.
# Fitur:
#   - Mengosongkan history buffer memori saat ini
#   - Menghapus file .bash_history utama
#   - Menghapus file history rotasi (.bash_history.old, .bash_history1, dll)
#   - Menghapus variabel history dari environment
#   - Opsional: Menghapus juga .lesshst, .mysql_history, .psql_history jika diminta
#
# Penggunaan:
#   ./bash_history_clean.sh [--all-system-users] [--verbose]
#

set -euo pipefail # Exit on error, undefined vars, and pipe failures

# --- Konfigurasi ---
VERBOSE=false
CLEAN_ALL_USERS=false
LOG_FILE="/tmp/history_cleaner_$(date +%Y%m%d_%H%M%S).log"

# --- Fungsi Log ---
log_info() {
    echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log_warn() {
    echo "[WARN] $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1" >&2
}

# --- Fungsi Pembersihan User Saat Ini ---
clean_current_user() {
    local user_home="$HOME"
    local user_name="$(whoami)"
    
    log_info "Memulai pembersihan untuk user: $user_name ($user_home)"

    # 1. Hapus History Buffer Memori
    # Ini menghapus command yang diketik tapi belum di-save ke file
    history -c
    log_info "History buffer memori telah dikosongkan."

    # 2. Hapus File History Utama
    if [ -f "${user_home}/.bash_history" ]; then
        > "${user_home}/.bash_history" # Cara paling aman: kosongkan isi file daripada hapus filenya
        log_info "File .bash_history telah dikosongkan."
    fi

    # 3. Hapus File History Rotasi
    for hist_file in "${user_home}/.bash_history"[0-9]*; do
        if [ -e "$hist_file" ]; then
            > "$hist_file"
            log_info "File history rotasi $hist_file telah dikosongkan."
        fi
    done

    # 4. Hapus Variabel Environment History
    unset HISTFILE HISTSIZE HISTFILESIZE HISTCONTROL
    log_info "Variabel environment history telah dihapus."

    # 5. Hapus History Tambahan Lainnya (Opsional tapi disarankan untuk forensics)
    local extra_histories=(
        ".zsh_history"
        ".fish_history"
        ".lesshst"
        ".mysql_history"
        ".psql_history"
        ".python_history"
        ".node_repl_history"
        ".ruby_history"
        ".irb_history.rb"
    )

    for hist in "${extra_histories[@]}"; do
        if [ -f "${user_home}/${hist}" ]; then
            > "${user_home}/${hist}"
            log_info "File ${hist} telah dikosongkan."
        fi
    done

    log_info "Pembersihan user $user_name selesai."
}

# --- Fungsi Pembersihan Semua User (Root Only) ---
clean_all_users() {
    log_info "Mode 'Semua User' diaktifkan. Membutuhkan hak akses root/sudo."
    
    # Dapatkan daftar semua user yang memiliki home directory
    while IFS=: read -r username _ uid _ _ homedir _; do
        # Skip user system jika tidak ada home dir atau home dir bukan /home/*
        if [[ -n "$homedir" && -d "$homedir" ]]; then
            # Simpan HOME asli
            local original_home="$HOME"
            
            # Ubah HOME sementara untuk fungsi clean_current_user
            export HOME="$homedir"
            
            # Jalankan pembersihan
            # Kita perlu menjalankan fungsi dalam subshell atau konteks user ini
            # Karena kita bukan user tersebut, kita langsung manipulasi file
            
            log_info "Membersihkan user: $username ($homedir)"
            
            # Kosongkan file history
            for f in "${homedir}/.bash_history" "${homedir}/.bash_history."[0-9]*; do
                if [ -f "$f" ]; then
                    > "$f"
                    log_info "  - File $f dikosongkan."
                fi
            done
            
            # Kosongkan history tambahan
            for f in "${homedir}/.zsh_history" "${homedir}/.lesshst" "${homedir}/.mysql_history" "${homedir}/.psql_history"; do
                if [ -f "$f" ]; then
                    > "$f"
                    log_info "  - File $f dikosongkan."
                fi
            done
            
            # Kembalikan HOME
            export HOME="$original_home"
        fi
    done < /etc/passwd
}

# --- Parse Argumen ---
while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --all-system-users|-a)
            CLEAN_ALL_USERS=true
            shift
            ;;
        *)
            log_error "Argumen tidak dikenali: $1"
            echo "Gunakan: $0 [--verbose] [--all-system-users]"
            exit 1
            ;;
    esac
done

# --- Eksekusi Utama ---
main() {
    log_info "Script bash_history_clean.sh dimulai."
    
    if [ "$CLEAN_ALL_USERS" = true ]; then
        # Cek apakah kita root
        if [ "$(id -u)" -ne 0 ]; then
            log_warn "Anda bukan root. Hanya akan membersihkan user saat ini."
            log_warn "Gunakan sudo $0 $0 untuk membersihkan semua user."
            CLEAN_ALL_USERS=false
        else
            clean_all_users
        fi
    else
        clean_current_user
    fi
    
    log_info "Script selesai."
}

main
