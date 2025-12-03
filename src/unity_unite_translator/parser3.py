#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RPGMaker Unite 이벤트 에셋에서 문자열 추출 → CSV 생성
출력 헤더: source,target
"""

import argparse, csv, io, os, re, sys
from pathlib import Path

# --- YAML 로더 준비 ---
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
        # data = {'MonoBehaviour': {...}}
        return data.get("MonoBehaviour", None) if isinstance(data, dict) else None
    except Exception as e:
        return None


def normalize_newlines(s: str) -> str:
    return s.replace("\r\n", "\n").replace("\r", "\n")


def escape_visible(s: str) -> str:
    """편집 편의: 실제 개행/탭을 보이는 이스케이프로 바꿈"""
    s = normalize_newlines(s)
    s = s.replace("\\", "\\\\")  # 역슬래시 보존
    s = s.replace("\t", "\\t")
    s = s.replace("\n", "\\n")
    return s


def iter_event_texts(mono: dict, target_codes: set[int]):
    """
    dataModel.eventCommands[*]에서 code ∈ target_codes인 항목의
    parameters 배열에 들어있는 **모든 문자열 요소**를 뽑는다.
    """
    if not isinstance(mono, dict):
        return
    name = mono.get("m_Name", "")
    dm = mono.get("dataModel")
    if not isinstance(dm, dict):
        return
    cmds = dm.get("eventCommands")
    if not isinstance(cmds, list):
        return
    for idx, cmd in enumerate(cmds):
        if not isinstance(cmd, dict):
            continue
        code = cmd.get("code")
        if code not in target_codes:
            continue
        indent = cmd.get("indent", "")
        par = cmd.get("parameters")
        if isinstance(par, list) and par:
            for item in par:
                if isinstance(item, str):
                    yield idx, int(code), indent, item, name


def collect_files(input_root: Path) -> list[Path]:
    if input_root.is_file() and input_root.suffix.lower() == ".asset":
        return [input_root]
    # 기본적으로 Unite 샘플 경로 패턴에 맞춤
    candidates = list(input_root.rglob("*.asset"))
    return candidates


def main():
    ap = argparse.ArgumentParser(description="RPGMaker Unite 이벤트 텍스트 추출기")
    ap.add_argument(
        "-i",
        "--input",
        default="ExportedProject/Assets/RPGMaker/Storage/Event/SO/Event",
        help="입력 폴더(또는 단일 .asset 파일)",
    )
    ap.add_argument("-o", "--output", default="rpgm_texts.csv", help="출력 CSV 경로")
    ap.add_argument(
        "--codes",
        default="401,402",
        help="추출할 event code들(쉼표 구분). 기본: 401,402",
    )
    ap.add_argument(
        "--dedupe", action="store_true", help="중복된 source 텍스트 제거"
    )
    ap.add_argument(
        "--no-escape",
        action="store_true",
        help="개행/탭을 \\n/\\t로 바꾸지 않음(실제 개행 유지)",
    )
    ap.add_argument(
        "--gui", action="store_true", help="입력 폴더를 GUI 창으로 선택 (tkinter 필요)"
    )
    args = ap.parse_args()

    if args.gui:
        try:
            import tkinter as tk
            from tkinter import filedialog

            root = tk.Tk()
            root.withdraw()  # 메인 윈도우 숨김
            print("[INFO] 폴더 선택 창을 띄웁니다...")
            selected = filedialog.askdirectory(title="입력 폴더 선택", initialdir=os.getcwd())
            if selected:
                args.input = selected
                print(f"[INFO] 선택된 경로: {args.input}")
            else:
                print("[INFO] 폴더 선택이 취소되었습니다. 기존 설정을 사용합니다.")
        except ImportError:
            sys.stderr.write("[ERROR] tkinter 모듈이 없습니다. GUI 기능을 사용할 수 없습니다.\n")

    input_root = Path(args.input)
    out_path = Path(args.output)
    target_codes = set()
    for tok in args.codes.split(","):
        tok = tok.strip()
        if tok.isdigit():
            target_codes.add(int(tok))
    if not target_codes:
        target_codes = {401, 402}

    files = collect_files(input_root)
    if not files:
        sys.stderr.write(f"[WARN] 입력에서 .asset 파일을 찾지 못함: {input_root}\n")

    rows = []
    seen = set()  # dedupe용 (file,name,source)
    for f in files:
        try:
            with io.open(f, "r", encoding="utf-8") as fp:
                text = fp.read()
        except UnicodeDecodeError:
            # 일부 파일이 바이너리일 수 있음 → 스킵
            continue

        mono = load_mono_yaml(text)
        if not mono:
            continue

        for idx, code, indent, txt, name in iter_event_texts(mono, target_codes):
            src = normalize_newlines(txt)
            src_out = src if args.no_escape else escape_visible(src)

            # 기준: 최종 csv 출력문에서 동일한 원문이 두 번 이상 등장해서는 안됨
            key = src_out
            if args.dedupe and key in seen:
                continue
            seen.add(key)

            rows.append({"source": src_out, "target": src_out})  # dnSpy용 매핑

    # 정렬(문자열 기준)
    rows.sort(key=lambda r: r["source"])

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with io.open(out_path, "w", encoding="utf-8", newline="") as fp:
        w = csv.writer(fp)
        w.writerow(["source", "target"])
        for r in rows:
            w.writerow([r["source"], r["target"]])

    print(f"[OK] extracted {len(rows)} lines → {out_path}")


if __name__ == "__main__":
    main()
