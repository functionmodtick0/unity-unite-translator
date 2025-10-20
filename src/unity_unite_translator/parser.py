# extract_rpgmaker_texts.py
import csv, glob, io, os, re

PROJECT_ROOT = 'projects'
PROJECT_NAME = input("프로젝트 이름을 입력하세요: ").strip()
ROOT = r"ExportedProject/Assets/RPGMaker/Storage/Event/SO/Event"
files = glob.glob(os.path.join(PROJECT_ROOT, PROJECT_NAME, ROOT, "*.asset"))

pat_code = re.compile(r'^\s*-\s+code:\s+(\d+)\s*$', re.M)
pat_params = re.compile(r'^\s*parameters:\s*\n\s*-\s+"(.*)"\s*\n\s*-\s*(\d+)\s*$', re.M)

rows = []
for path in files:
    with io.open(path, "r", encoding="utf-8") as f:
        text = f.read()
    # eventCommands 블록 단위 스캔
    # 간단화: code 줄과 바로 이어지는 parameters 블록을 매칭
    for m in re.finditer(r'(?P<codeblock>^\s*-\s+code:\s+\d+[\s\S]*?)(?=^\s*-\s+code:|\Z)', text, re.M):
        block = m.group("codeblock")
        code_m = pat_code.search(block)
        if not code_m: 
            continue
        code = int(code_m.group(1))
        if code != 401:
            continue
        p = pat_params.search(block)
        if not p:
            continue
        jp = p.group(1)  # 원문
        # YAML 내부 \n 이스케이프는 그대로 둔다
        rows.append([path, jp])

with io.open("rpgm_texts.csv", "w", encoding="utf-8", newline="") as out:
    w = csv.writer(out)
    w.writerow(["file", "source"])
    w.writerows(rows)
print(f"extracted {len(rows)} lines")
