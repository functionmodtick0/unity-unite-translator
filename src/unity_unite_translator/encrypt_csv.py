#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pip install pycryptodome
import argparse, sys
from base64 import b64decode, b64encode
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

MAGIC = b"TCSV1"  # 헤더: MAGIC(5) + IV(16) + CIPHERTEXT

def pkcs7_pad(data: bytes, block: int = 16) -> bytes:
    pad = block - (len(data) % block)
    return data + bytes([pad]) * pad

def main():
    ap = argparse.ArgumentParser(description="translation.csv → translation.csv.enc (AES-256-CBC)")
    ap.add_argument("-i", "--input", default="translation.csv", help="입력 CSV 경로")
    ap.add_argument("-o", "--output", default="translation.csv.enc", help="출력 ENC 경로")
    ap.add_argument("--key-b64", default="", help="Base64 인코딩된 32바이트 키. 비우면 랜덤 생성")
    args = ap.parse_args()

    # 키 준비
    if args.key_b64.strip():
        try:
            key = b64decode(args.key_b64.strip(), validate=True)
        except Exception as e:
            print(f"ERROR: 잘못된 Base64 키: {e}", file=sys.stderr)
            sys.exit(1)
        if len(key) != 32:
            print("ERROR: 키 길이는 32바이트여야 합니다(AES-256).", file=sys.stderr)
            sys.exit(1)
        key_b64 = args.key_b64.strip()
        generated = False
    else:
        key = get_random_bytes(32)
        key_b64 = b64encode(key).decode("ascii")
        generated = True

    # 암호화
    try:
        with open(args.input, "rb") as f:
            plain = f.read()
    except FileNotFoundError:
        print(f"ERROR: 입력 파일 없음: {args.input}", file=sys.stderr)
        sys.exit(1)

    iv = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_CBC, iv=iv)
    ct = cipher.encrypt(pkcs7_pad(plain, 16))

    with open(args.output, "wb") as f:
        f.write(MAGIC + iv + ct)

    print(f"[OK] {args.output} 생성")
    print(f"IV: {iv.hex()}")
    print(f"KEY_B64: {key_b64}")
    if generated:
        print("※ 새 키가 생성되었습니다. 위 KEY_B64를 C# CsvTranslator의 KEY_B64 상수에 복사하세요.")

if __name__ == "__main__":
    main()
