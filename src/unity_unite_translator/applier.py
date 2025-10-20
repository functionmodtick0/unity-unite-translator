# apply_rpgmaker_texts.py
import csv, io, os, sys

# 프로젝트 루트 설정
PROJECT_ROOT = "projects"
PROJECT_NAME = input("프로젝트 이름을 입력하세요: ").strip()
CSV_PATH = os.path.join(PROJECT_ROOT, PROJECT_NAME, "rpgm_texts.csv")

# CSV: file,source,target
replacements = {}

# CSV 파일 확인
if not os.path.exists(CSV_PATH):
    print(f"오류: CSV 파일을 찾을 수 없습니다: {CSV_PATH}")
    sys.exit(1)

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
