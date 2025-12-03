# extract_rpgmaker_texts.py
import csv, glob, io, os, re, sys

# 상대 임포트와 절대 임포트 모두 지원
try:
    from .translator import translate_batch
except ImportError:
    # 직접 실행 시
    from translator import translate_batch

PROJECT_ROOT = "projects"
PROJECT_NAME = input("프로젝트 이름을 입력하세요: ").strip()
ROOT = r"ExportedProject/Assets/RPGMaker/Storage/Event/SO/Event"
files = glob.glob(os.path.join(PROJECT_ROOT, PROJECT_NAME, ROOT, "*.asset"))

pat_code = re.compile(r"^\s*-\s+code:\s+(\d+)\s*$", re.M)
pat_params = re.compile(r'^\s*parameters:\s*\n\s*-\s+"(.*)"\s*\n\s*-\s*(\d+)\s*$', re.M)

rows = []
for path in files:
    with io.open(path, "r", encoding="utf-8") as f:
        text = f.read()
    # eventCommands 블록 단위 스캔
    # 간단화: code 줄과 바로 이어지는 parameters 블록을 매칭
    for m in re.finditer(
        r"(?P<codeblock>^\s*-\s+code:\s+\d+[\s\S]*?)(?=^\s*-\s+code:|\Z)", text, re.M
    ):
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
        rows.append([path, jp, ""])  # target은 나중에 채움

# 번역 적용 여부 선택
auto_translate = input("자동 번역을 적용하시겠습니까? (y/n): ").strip().lower() == 'y'

if auto_translate:
    print(f"\n{len(rows)}개의 텍스트 번역 시작...")
    source_texts = [row[1] for row in rows]
    translated_texts = translate_batch(source_texts)
    
    # 번역 결과를 rows에 적용
    for i, translated in enumerate(translated_texts):
        rows[i][2] = translated
    print("번역 완료!\n")
else:
    # 번역하지 않으면 target을 source와 동일하게
    for row in rows:
        row[2] = row[1]

output_path = os.path.join(PROJECT_ROOT, PROJECT_NAME, "rpgm_texts.csv")
with io.open(output_path, "w", encoding="utf-8", newline="") as out:
    w = csv.writer(out)
    w.writerow(["file", "source", "target"])
    w.writerows(rows)
print(f"extracted {len(rows)} lines -> {output_path}")
