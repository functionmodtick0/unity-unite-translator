#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RPGMaker Unite 이벤트 에셋에서 문자열 추출 → CSV 생성
헤더: file,name,code,idx,indent,source,target
- file/name/idx/indent는 디버깅/추적용
- 실제 적용엔 file/name + source + target만 쓰면 됨
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
    parameters[0]이 문자열이면 뽑는다.
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
            txt = par[0]
            if isinstance(txt, str):
                yield idx, int(code), indent, txt, name


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
        "--dedupe", action="store_true", help="같은 file+name+source 중복행 제거"
    )
    ap.add_argument(
        "--no-escape",
        action="store_true",
        help="개행/탭을 \\n/\\t로 바꾸지 않음(실제 개행 유지)",
    )
    args = ap.parse_args()

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

            rel = str(f).replace("\\", "/")
            key = (rel, name, src_out)
            if args.dedupe and key in seen:
                continue
            seen.add(key)

            rows.append(
                {
                    "file": rel,
                    "name": name,
                    "code": code,
                    "idx": idx,
                    "indent": indent,
                    "source": src_out,
                    "target": src_out,  # 번역 채울 자리
                }
            )

    # 정렬(파일명→idx)
    rows.sort(key=lambda r: (r["file"], r["idx"]))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with io.open(out_path, "w", encoding="utf-8", newline="") as fp:
        w = csv.writer(fp)
        w.writerow(["file", "name", "code", "idx", "indent", "source", "target"])
        for r in rows:
            w.writerow(
                [
                    r["file"],
                    r["name"],
                    r["code"],
                    r["idx"],
                    r["indent"],
                    r["source"],
                    r["target"],
                ]
            )

    print(f"[OK] extracted {len(rows)} lines → {out_path}")


if __name__ == "__main__":
    main()
