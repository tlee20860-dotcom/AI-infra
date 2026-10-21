#!/usr/bin/env python3
"""交付驗證腳本（機器可驗的規則）"""

import os
import re
import sys

MODE = os.environ.get("VALIDATE_MODE", "report").strip().lower()
CHANGED = os.environ.get("CHANGED_FILES", "").strip()

def iter_targets():
    if CHANGED:
        for line in CHANGED.splitlines():
            path = line.strip()
            if path and path.endswith(".md") and os.path.exists(path):
                yield path
        return
    for root, _dirs, files in os.walk("docs"):
        for name in files:
            if name.endswith(".md"):
                yield os.path.join(root, name)

def check_eof(content):
    tail = content[-800:]
    m = re.search(r"F:\s*(\S+)\s*\nV:\s*(\d+)\s*\nW:\s*(\S+)", tail)
    if not m:
        return "EOF 缺 F/V/W 三行"
    _f, v, _w = m.groups()
    if len(v) != 10:
        return f"V 不是 10 位 Unix epoch（{v}）"
    return None

def check_file_boundary(path, content):
    if not path.endswith(".md"):
        return None
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    if not lines:
        return "檔案為空"
    
    first_line = lines[0]
    last_line = lines[-1]
    
    # 檢查是否以反引號開頭/結尾（防止整檔被包裹）
    if first_line.startswith("```") or first_line.startswith("````"):
        return "檔案第一行以反引號開頭（F-004）"
    if last_line.endswith("```") or last_line.endswith("````"):
        return "檔案最後一行以反引號結尾（F-004）"
    
    return None

def check_head(content):
    for line in content.splitlines()[:5]:
        s = line.strip()
        if not s:
            continue
        if s.startswith("#"):
            return None
        return f"檔案開頭不是 # 標題（首行為：{s[:40]}）"
    return "檔案為空或前 5 行皆空白"

def validate(path, content):
    problems = []
    for label, fn in (
        ("EOF", lambda c: check_eof(c)),
        ("檔案邊界", lambda c: check_file_boundary(path, c)),
        ("開頭標題", lambda c: check_head(c)),
    ):
        if label == "檔案邊界" and not path.endswith(".md"):
            continue
        err = fn(content)
        if err:
            problems.append(err)
    return problems

def main():
    total = 0
    bad = 0
    for path in iter_targets():
        total += 1
        try:
            with open(path, "r", encoding="utf-8") as fh:
                content = fh.read()
        except Exception as exc:
            print(f"[ERROR] {path}: 讀取失敗（{exc}）")
            bad += 1
            continue
        for msg in validate(path, content):
            print(f"[ERROR] {path}: {msg}")
            bad += 1

    print(f"[SUMMARY] 檢查 {total} 檔，問題 {bad} 項（模式：{MODE}）")
    if bad and MODE == "strict":
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()