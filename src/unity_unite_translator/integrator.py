#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
원문 텍스트 파일과 번역문 텍스트 파일을 합쳐서 CSV 생성
입력: original.txt, translated.txt
출력: source,target CSV
"""

import argparse
import csv
import sys
from pathlib import Path

def main():
    ap = argparse.ArgumentParser(description="RPGMaker Unite 텍스트 병합기 (TXT + TXT -> CSV)")
    ap.add_argument("original", help="원문 텍스트 파일 경로", default="source.txt")
    ap.add_argument("translated", help="번역문 텍스트 파일 경로", default="translated.txt")
    ap.add_argument("-o", "--output", default="rpgm_texts-translated.csv", help="출력 CSV 경로")
    
    args = ap.parse_args()
    
    orig_path = Path(args.original)
    trans_path = Path(args.translated)
    out_path = Path(args.output)
    
    if not orig_path.exists():
        sys.stderr.write(f"[ERROR] 원문 파일이 없습니다: {orig_path}\n")
        sys.exit(1)
        
    if not trans_path.exists():
        sys.stderr.write(f"[ERROR] 번역문 파일이 없습니다: {trans_path}\n")
        sys.exit(1)

    with open(orig_path, "r", encoding="utf-8") as f:
        orig_lines = [line.rstrip('\n') for line in f]
        
    with open(trans_path, "r", encoding="utf-8") as f:
        trans_lines = [line.rstrip('\n') for line in f]
        
    if len(orig_lines) != len(trans_lines):
        print(f"[WARN] 줄 수가 다릅니다! 원문: {len(orig_lines)}, 번역문: {len(trans_lines)}")
        
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(out_path, "w", encoding="utf-8", newline="") as fp:
        w = csv.writer(fp)
        w.writerow(["source", "target"])
        
        for src, tgt in zip(orig_lines, trans_lines):
            w.writerow([src, tgt])
            
    print(f"[OK] Merged {min(len(orig_lines), len(trans_lines))} lines → {out_path}")

if __name__ == "__main__":
    main()
