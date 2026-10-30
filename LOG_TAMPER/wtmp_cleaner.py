#!/usr/bin/env python3
"""
wtmp_cleaner_termux.py - Versi aman untuk Termux & User-Level.
Tidak membutuhkan sudo jika targetnya adalah file lokal/simulasi.
Jika dijalankan di Linux biasa tanpa sudo, ia akan membuat backup & file bersih lokal.
"""

import os
import sys
import struct
import stat

# Konfigurasi Path
# Di Termux, path wtmp mungkin tidak ada, jadi kita gunakan default lokal
DEFAULT_WTMP = "wtmp_clean.dat"
SYSTEM_WTMP = "/var/run/wtmp"

# Struktur utmp standar
UTMP_ENTRY_SIZE = 384
UT_TYPE_OFFSET = 17
UT_TYPE_EMPTY = 7

def clean_wtmp(target_path):
    """
    Membersihkan file wtmp dengan membuat record EMPTY.
    Jika file tidak ada, buat file baru yang valid.
    """
    
    # Cek apakah file sudah ada
    if not os.path.exists(target_path):
        print(f"[+] File {target_path} tidak ditemukan. Membuat file baru yang bersih...")
        # Buat file kosong dengan ukuran kelipatan UTMP_ENTRY_SIZE
        with open(target_path, 'wb') as f:
            pass  # File kosong 0 byte adalah valid untuk wtmp baru
        print(f"[+] {target_path} berhasil dibuat.")
        return True

    try:
        # Baca isi file
        with open(target_path, 'rb') as f:
            data = f.read()

        if len(data) == 0:
            print(f"[*] {target_path} sudah kosong.")
            return True

        # Validasi ukuran
        remainder = len(data) % UTMP_ENTRY_SIZE
        if remainder != 0:
            print(f"[!] Warning: Ukuran file ({len(data)}) tidak kelipatan {UTMP_ENTRY_SIZE}. Memotong sisa corrupt...")
            data = data[:-(remainder)]

        # Bersihkan setiap record
        cleaned_data = bytearray()
        num_records = len(data) // UTMP_ENTRY_SIZE
        
        for i in range(num_records):
            start = i * UTMP_ENTRY_SIZE
            end = start + UTMP_ENTRY_SIZE
            record = bytearray(data[start:end])
            
            # Set field ut_type menjadi EMPTY
            record[UT_TYPE_OFFSET] = UT_TYPE_EMPTY
            record[UT_TYPE_OFFSET + 1] = 0
            
            cleaned_data.extend(record)

        # Tulis kembali
        # Gunakan mode 'wb' untuk overwrite
        with open(target_path, 'wb') as f:
            f.write(cleaned_data)

        print(f"[+] Berhasil membersihkan {num_records} record di {target_path}")
        return True

    except PermissionError:
        # Jika tidak bisa write ke sistem (misal /var/run/wtmp tanpa sudo)
        # Kita buat alternatif di folder lokal
        alt_path = "local_wtmp_clean.dat"
        print(f"[!] Gagal write ke {target_path} (mungkin butuh sudo?).")
        print(f"    -> Mencoba menyimpan ke {alt_path} ...")
        try:
            # Salin data asli dulu
            with open(target_path, 'rb') as f:
                original_data = f.read()
            
            # Bersihkan data tersebut
            if len(original_data) > 0:
                remainder = len(original_data) % UTMP_ENTRY_SIZE
                if remainder != 0:
                    original_data = original_data[:-(remainder)]
                
                cleaned_data = bytearray()
                num_records = len(original_data) // UTMP_ENTRY_SIZE
                
                for i in range(num_records):
                    start = i * UTMP_ENTRY_SIZE
                    end = start + UTMP_ENTRY_SIZE
                    record = bytearray(original_data[start:end])
                    record[UT_TYPE_OFFSET] = UT_TYPE_EMPTY
                    record[UT_TYPE_OFFSET + 1] = 0
                    cleaned_data.extend(record)
                
                with open(alt_path, 'wb') as f:
                    f.write(cleaned_data)
                print(f"[+] File bersih disimpan di: {alt_path}")
            else:
                # Buat file kosong
                with open(alt_path, 'wb') as f:
                    pass
                print(f"[+] File kosong dibuat di: {alt_path}")
            return True
        except Exception as e:
            print(f"[!] Error saat membuat fallback: {e}")
            return False
    except Exception as e:
        print(f"[!] Error umum: {e}")
        return False

if __name__ == "__main__":
    # Tentukan target
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        # Default: Gunakan file lokal jika di Termux, atau system jika di Linux dengan hak akses
        if os.geteuid() == 0:
            target = SYSTEM_WTMP
        else:
            # Di Termux/user biasa, gunakan file lokal agar tidak perlu sudo
            target = DEFAULT_WTMP
    
    print(f"[*] Menargetkan: {target}")
    clean_wtmp(target)
