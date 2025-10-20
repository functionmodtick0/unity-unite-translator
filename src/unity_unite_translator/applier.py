# apply_rpgmaker_texts.py
import csv, io, re

CSV_PATH = "rpgm_texts.csv"

# CSV: file,source,target
replacements = {}
with io.open(CSV_PATH, "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        if i == 0:
            header = line.strip().split(",")
            continue
        # 아주 단순 파서: CSV는 쉼표/따옴표 처리된 상태라고 가정
        # 파이썬 csv 모듈 쓰는 게 더 안전하지만 예시는 생략
with io.open(CSV_PATH, "r", encoding="utf-8", newline="") as f:
    import csv as _csv

    r = _csv.DictReader(f)
    for row in r:
        if not row.get("target"):
            continue
        replacements.setdefault(row["file"], []).append((row["source"], row["target"]))

for path, pairs in replacements.items():
    with io.open(path, "r", encoding="utf-8") as f:
        s = f.read()
    for src, tgt in pairs:
        # YAML 내부의 "src"를 정확히 치환(따옴표 포함 라인 보존)
        # src/tgt는 이미 \n, \" 등 이스케이프된 형태라고 가정
        s = s.replace(f'- "{src}"', f'- "{tgt}"')
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)
print("applied")
