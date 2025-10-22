#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RPGMaker Unite 이벤트 에셋 → 번역용 CSV(source,target) 추출기
- code: 401(대사), 402(선택지) 등에서 parameters 내 모든 문자열을 수집(재귀)
- 기본 출력 헤더: source,target
- 기본 target은 빈칸(런타임/ dnSpy 번역용). --identity 옵션 시 target=source

의존성:
  pip install pyyaml
"""

import argparse, csv, io, sys
from pathlib import Path

# --- YAML 로더 ---
try:
    import yaml
except ImportError:
    sys.stderr.write("[ERROR] PyYAML 미설치. 설치: pip install pyyaml\n")
    sys.exit(1)


def load_mono_yaml(text: str):
    """
    Unity .asset YAML에서 'MonoBehaviour:' 이후만 파싱.
    상단의 %YAML / %TAG / --- !u! 라인은 버린다.
    """
    idx = text.find("MonoBehaviour:")
    if idx < 0:
        return None
    body = text[idx:]
    try:
        data = yaml.safe_load(body)
        return data.get("MonoBehaviour", None) if isinstance(data, dict) else None
    except Exception:
        return None


def normalize_newlines(s: str) -> str:
    return s.replace("\r\n", "\n").replace("\r", "\n")


def escape_visible(s: str) -> str:
    """편집 편의: 실제 개행/탭을 보이는 이스케이프로 바꿈 + 역슬래시 보존"""
    s = normalize_newlines(s)
    s = s.replace("\\", "\\\\")
    s = s.replace("\t", "\\t")
    s = s.replace("\n", "\\n")
    return s


def extract_strings(obj):
    """
    parameters 안에서 모든 문자열을 재귀적으로 수집.
    - 리스트/튜플/셋: 하위 순회
    - dict: 값들만 순회(키는 보통 의미 없는 인덱스/태그)
    - str: 그대로 수집
    - 그 외 타입은 무시
    """
    if obj is None:
        return
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, (list, tuple, set)):
        for x in obj:
            yield from extract_strings(x)
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from extract_strings(v)
    else:
        return


def iter_event_texts(mono: dict, target_codes: set[int], min_len: int):
    """
    dataModel.eventCommands[*]에서 code ∈ target_codes인 항목의
    parameters 내 모든 문자열을 뽑아 전달.
    """
    if not isinstance(mono, dict):
        return
    dm = mono.get("dataModel")
    if not isinstance(dm, dict):
        return
    cmds = dm.get("eventCommands")
    if not isinstance(cmds, list):
        return

    for cmd in cmds:
        if not isinstance(cmd, dict):
            continue
        code = cmd.get("code")
        if code not in target_codes:
            continue
        params = cmd.get("parameters")
        if params is None:
            continue
        for s in extract_strings(params):
            if not isinstance(s, str):
                continue
            s_norm = normalize_newlines(s)
            if len(s_norm.strip()) < min_len:
                continue
            yield s_norm


def collect_files(input_root: Path) -> list[Path]:
    if input_root.is_file() and input_root.suffix.lower() == ".asset":
        return [input_root]
    return list(input_root.rglob("*.asset"))


def main():
    ap = argparse.ArgumentParser(description="RPGMaker Unite 이벤트 텍스트 추출기(source,target)")
    ap.add_argument("-i", "--input",
                    default="ExportedProject/Assets/RPGMaker/Storage/Event/SO/Event",
                    help="입력 폴더(또는 단일 .asset 파일)")
    ap.add_argument("-o", "--output", default="translation.csv", help="출력 CSV 경로")
    ap.add_argument("--codes", default="401,402",
                    help="추출할 event code들(쉼표 구분). 기본: 401,402")
    ap.add_argument("--no-escape", action="store_true",
                    help="개행/탭을 \\n/\\t로 바꾸지 않음(실제 개행 유지)")
    ap.add_argument("--dedupe", action="store_true",
                    help="같은 source 중복 제거")
    ap.add_argument("--min-len", type=int, default=1,
                    help="추출 최소 글자수(양끝 공백 제거 후). 기본 1")
    ap.add_argument("--identity", action="store_true",
                    help="target=source 로 출력(테스트/검증용)")
    args = ap.parse_args()

    input_root = Path(args.input)
    out_path = Path(args.output)

    target_codes = {int(t.strip()) for t in args.codes.split(",") if t.strip().isdigit()}
    if not target_codes:
        target_codes = {401, 402}

    files = collect_files(input_root)
    if not files:
        sys.stderr.write(f"[WARN] 입력에서 .asset 파일을 찾지 못함: {input_root}\n")

    # 수집
    sources = []
    for f in files:
        try:
            with io.open(f, "r", encoding="utf-8") as fp:
                text = fp.read()
        except UnicodeDecodeError:
            continue

        mono = load_mono_yaml(text)
        if not mono:
            continue

        for s_norm in iter_event_texts(mono, target_codes, args.min_len):
            s_out = s_norm if args.no_escape else escape_visible(s_norm)
            sources.append(s_out)

    # 중복 제거(선택)
    if args.dedupe:
        seen = set()
        uniq = []
        for s in sources:
            if s in seen:
                continue
            seen.add(s)
            uniq.append(s)
        sources = uniq

    # 정렬(안정적 출력)
    sources.sort()

    # 출력: source,target
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with io.open(out_path, "w", encoding="utf-8", newline="") as fp:
        w = csv.writer(fp)
        w.writerow(["source", "target"])
        if args.identity:
            for s in sources:
                w.writerow([s, s])
        else:
            for s in sources:
                w.writerow([s, ""])

    print(f"[OK] extracted {len(sources)} lines → {out_path}")


if __name__ == "__main__":
    main()
