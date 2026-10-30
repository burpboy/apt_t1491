#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STEG_DECRYPT.PY
Rootkit Payload Extractor - APT ELITE_BLACKHAT

Fungsi: Mengekstrak payload tersembunyi dari file carrier (Gambar/Audio) menggunakan teknik LSB Steganography.
Mendukung dekripsi AES-256 jika payload dibungkus enkripsi tambahan.

Author: ELITE BLACKHAT ROOTKIT TEAM
Version: 1.0.0
License: Proprietary / Internal Use Only

Usage:
    python3 steg_decrypt.py --input img_steg.png --output extracted_payload.bin --key "YOUR_SECRET_KEY"
    python3 steg_decrypt.py --input audio_hide.mp3 --output extracted_payload.bin --key "YOUR_SECRET_KEY" --mode audio

Dependencies:
    pip install Pillow pycryptodome wave
"""

import argparse
import sys
import os
import struct
import hashlib
from PIL import Image
import wave
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from Crypto.Random import get_random_bytes

# --- Constants ---
HEADER_MAGIC = b'ELITE_BH'  # Magic bytes to identify our stego payload
AES_BLOCK_SIZE = 16
DEFAULT_KEY = b"ELITE_BLACKHAT_ROOTKIT_KEY_1234567890"  # Default key for demo purposes

class StegoDecryptor:
    def __init__(self, input_file, output_file, key=None, mode='image'):
        self.input_file = input_file
        self.output_file = output_file
        self.key = key.encode() if isinstance(key, str) else key
        self.mode = mode.lower()
        
        # Ensure key is correct length for AES (16, 24, or 32 bytes)
        if len(self.key) < 16:
            self.key = self.key.ljust(16, b'\0')
        elif len(self.key) > 32:
            self.key = self.key[:32]
            
        self.decrypted_data = None

    def _extract_bits_from_image(self, img):
        """Extract LSB bits from a PIL Image object."""
        pixels = list(img.getdata())
        bits = []
        for pixel in pixels:
            for channel_value in pixel:
                # Get the least significant bit
                bits.append(str(channel_value & 1))
                # Stop if we have enough bits for a large payload (optimization)
                if len(bits) > 10 * 1024 * 1024: # 10MB max limit per extraction
                    break
            if len(bits) > 10 * 1024 * 1024:
                break
        
        # Convert bits to bytes
        byte_array = bytearray()
        for i in range(0, len(bits), 8):
            byte_str = bits[i:i+8]
            if len(byte_str) == 8:
                byte_val = int("".join(byte_str), 2)
                byte_array.append(byte_val)
            else:
                break # Incomplete byte at end
        
        return bytes(byte_array)

    def _extract_bits_from_audio(self, wav_file_path):
        """Extract LSB bits from a WAV file."""
        try:
            with wave.open(wav_file_path, 'rb') as wf:
                params = wf.getparams()
                frames = wf.readframes(wf.getnframes())
                samples = struct.unpack(f"{len(frames)//params.sampwidth}i", frames)
                
                bits = []
                for sample in samples:
                    # Get LSB of each sample
                    bits.append(str(sample & 1))
                    if len(bits) > 10 * 1024 * 1024:
                        break
                
                byte_array = bytearray()
                for i in range(0, len(bits), 8):
                    byte_str = bits[i:i+8]
                    if len(byte_str) == 8:
                        byte_val = int("".join(byte_str), 2)
                        byte_array.append(byte_val)
                    else:
                        break
                        
                return bytes(byte_array)
        except Exception as e:
            print(f"[!] Error extracting bits from audio: {e}")
            sys.exit(1)

    def _detect_and_extract_raw(self):
        """Detect type and extract raw hidden data."""
        print(f"[*] Opening carrier file: {self.input_file}")
        
        if self.mode == 'image':
            try:
                img = Image.open(self.input_file)
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                raw_data = self._extract_bits_from_image(img)
            except Exception as e:
                print(f"[!] Error processing image: {e}")
                sys.exit(1)
                
        elif self.mode == 'audio':
            if not self.input_file.endswith('.wav'):
                print("[!] Warning: Non-WAV audio format detected. Attempting raw extraction...")
                # Fallback for MP3 would require ffmpeg parsing, keeping it simple for now
                # Assume user converts to WAV or use raw binary extraction if needed
                pass
            
            raw_data = self._extract_bits_from_audio(self.input_file)
        else:
            raise ValueError(f"Unknown mode: {self.mode}")
            
        if not raw_data:
            print("[!] No hidden data found.")
            sys.exit(1)
            
        print(f"[*] Raw data extracted: {len(raw_data)} bytes")
        return raw_data

    def _verify_magic(self, data):
        """Check if the extracted data starts with our magic header."""
        if data.startswith(HEADER_MAGIC):
            return True
        return False

    def _decrypt_aes(self, encrypted_data):
        """Decrypt AES-256 CBC encrypted data."""
        try:
            # IV is stored in the first 16 bytes of the encrypted payload
            iv = encrypted_data[:AES_BLOCK_SIZE]
            ciphertext = encrypted_data[AES_BLOCK_SIZE:]
            
            cipher = AES.new(self.key, AES.MODE_CBC, iv)
            plaintext = unpad(cipher.decrypt(ciphertext), AES_BLOCK_SIZE)
            return plaintext
        except Exception as e:
            print(f"[!] Decryption failed: {e}")
            print("[*] Returning raw data anyway (might be unencrypted).")
            return encrypted_data

    def process(self):
        """Main processing pipeline."""
        print(f"[*] Mode: {self.mode.upper()}")
        print(f"[*] Key: {self.key.decode(errors='ignore')}")
        
        # Step 1: Extract raw bits
        raw_data = self._detect_and_extract_raw()
        
        # Step 2: Check for Magic Header
        if self._verify_magic(raw_data):
            print("[+] Magic header 'ELITE_BH' detected.")
            # Remove magic header
            payload_data = raw_data[len(HEADER_MAGIC):]
        else:
            print("[-] No magic header found. Data might be raw or corrupted.")
            payload_data = raw_data
            
        # Step 3: Decrypt if necessary
        # Heuristic: If data looks like it has an IV (first 16 bytes are random-looking)
        # Or if user specifies encryption mode
        decrypted_payload = self._decrypt_aes(payload_data)
        
        # Step 4: Write to output
        try:
            with open(self.output_file, 'wb') as f:
                f.write(decrypted_payload)
            print(f"[+] Payload successfully written to: {self.output_file}")
            print(f"[+] File size: {os.path.getsize(self.output_file)} bytes")
            
            # Optional: Verify integrity via hash
            import hashlib
            md5_hash = hashlib.md5(decrypted_payload).hexdigest()
            print(f"[+] MD5 Hash: {md5_hash}")
            
        except IOError as e:
            print(f"[!] Error writing output file: {e}")
            sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="APT ELITE_BLACKHAT Stego Payload Decryptor")
    parser.add_argument("--input", "-i", required=True, help="Path to the carrier file (PNG/WAV)")
    parser.add_argument("--output", "-o", required=True, help="Path to save the extracted payload")
    parser.add_argument("--key", "-k", default="ELITE_BLACKHAT_ROOTKIT_KEY_1234567890", help="AES decryption key")
    parser.add_argument("--mode", "-m", choices=['image', 'audio'], default='image', help="Processing mode")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"[!] Input file not found: {args.input}")
        sys.exit(1)
        
    decryptor = StegoDecryptor(
        input_file=args.input,
        output_file=args.output,
        key=args.key,
        mode=args.mode
    )
    
    decryptor.process()

if __name__ == "__main__":
    main()
