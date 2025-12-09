#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pip install pycryptodome
import argparse, os, sys
from base64 import b64decode
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

# !!! 배포 전 교체 !!!
KEY_B64 = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="  # 32바이트 키(Base64). 예시: 전부 0.
MAGIC = b"TCSV1"

def pkcs7_pad(b, block=16):
    pad = block - (len(b) % block)
    return b + bytes([pad])*pad

def main():
    ap = argparse.ArgumentParser(description="translation.csv → translation.csv.enc (AES-256-CBC)")
    ap.add_argument("-i", "--input", default="translation.csv", help="입력 CSV 경로")
    ap.add_argument("-o", "--output", default="translation.csv.enc", help="출력 ENC 경로")
    args = ap.parse_args()

    key = b64decode(KEY_B64)
    if len(key) != 32:
        print("ERROR: KEY_B64는 32바이트(Base64)여야 합니다.", file=sys.stderr)
        sys.exit(1)

    with open(args.input, "rb") as f:
        plain = f.read()

    iv = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_CBC, iv=iv)
    ct = cipher.encrypt(pkcs7_pad(plain, 16))

    with open(args.output, "wb") as f:
        f.write(MAGIC + iv + ct)

    print(f"[OK] {args.output} 생성, IV={iv.hex()}")

if __name__ == "__main__":
    main()
