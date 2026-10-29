#!/usr/bin/env python3
"""交付驗證腳本（增量、配置驅動、嚴格攔截、精準行號、繁簡自動轉換）"""

import os
import re
import sys
import json
import subprocess
import fnmatch

# 嘗試載入 zhconv，若無則提示安裝（GitHub Actions 中需先 pip install zhconv）
try:
    import zhconv
except ImportError:
    print("[WARN] 未安裝 zhconv 模組，將跳過深度繁簡轉換檢查。請在環境中執行 'pip install zhconv'")
    zhconv = None

CONFIG_PATH = "AI-kernel/docs/r-rules/validate-config.json"
FORBIDDEN_PATH = "AI-kernel/docs/r-rules/forbidden_words.txt"

# 代碼檔案副檔名清單：這些檔案不做代碼塊跳過，逐行檢查禁用詞
CODE_FILE_EXTS = (".py", ".js", ".css", ".html", ".yml", ".yaml", ".json", ".sh")

DEFAULT_CONFIG = {
    "ignore_patterns": ["external/old-AI-WA-FAMILY/*", "external/AI-OS/*"],
    "file_specific_rules": {}
}

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"[WARN] 配置文件格式錯誤，使用預設配置。錯誤：{e}")
    return DEFAULT_CONFIG

def load_forbidden_words():
    words = []
    if os.path.exists(FORBIDDEN_PATH):
        try:
            with open(FORBIDDEN_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        words.append(line)
        except Exception as e:
            print(f"[WARN] 無法讀取禁用詞文件：{e}")
    return words

def get_changed_files():
    changed_env = os.environ.get("CHANGED_FILES", "").strip()
    if changed_env:
        return [f.strip() for f in changed_env.splitlines() if f.strip() and os.path.exists(f.strip())]
    try:
        out = subprocess.check_output(["git", "diff", "--name-only", "HEAD~1", "HEAD"], text=True, stderr=subprocess.DEVNULL)
        return [f.strip() for f in out.splitlines() if f.strip() and os.path.exists(f.strip())]
    except Exception:
        return []

def get_diff_stats():
    try:
        out = subprocess.check_output(["git", "diff", "--numstat", "HEAD~1", "HEAD"], text=True, stderr=subprocess.DEVNULL)
        stats = {}
        for line in out.splitlines():
            parts = line.split('\t')
            if len(parts) == 3:
                added, deleted, filename = parts
                stats[filename] = {"added": int(added) if added.isdigit() else 0, "deleted": int(deleted) if deleted.isdigit() else 0}
        return stats
    except Exception:
        return {}

def is_ignored(path, config):
    # 防自指：永遠忽略配置文件與禁用詞文件本身
    if path in [CONFIG_PATH, FORBIDDEN_PATH]:
        return True
    for pattern in config.get("ignore_patterns", []):
        if fnmatch.fnmatch(path, pattern):
            return True
    return False

def check_eof(content, filepath):
    if filepath.endswith(".json"):
        try:
            data = json.loads(content)
            if "_EOF" in data and "F" in data["_EOF"] and "V" in data["_EOF"] and "W" in data["_EOF"]:
                v = str(data["_EOF"]["V"])
                if len(v) != 10:
                    return f"_EOF.V 不是 10 位數（{v}）", data["_EOF"]["W"]
                return None, data["_EOF"]["W"]
            return "缺少 _EOF 鍵值對", "Unknown"
        except json.JSONDecodeError:
            return "JSON 語法錯誤", "Unknown"
    elif filepath.endswith(".txt"):
        # .txt 檔案使用 # 作為註解
        m = re.search(r"#\s*[═=]*\s*EOF\s*[═=]*\s*\n?#\s*F:\s*([^\s\n]+)\s*\n?#\s*V:\s*(\d+)\s*\n?#\s*W:\s*([^\s\n]+)", content[-500:])
        if m:
            if len(m.group(2)) != 10:
                return f"V 欄位不是 10 位數（{m.group(2)}）", m.group(3)
            return None, m.group(3)
        return "缺少註解包裹的 EOF（F/V/W）", "Unknown"
    elif filepath.endswith(".md"):
        m = re.search(r"F:\s*([^\s\n]+)\s*\nV:\s*(\d+)\s*\nW:\s*([^\s\n]+)", content[-1500:])
        if m:
            if len(m.group(2)) != 10:
                return f"V 欄位不是 10 位數（{m.group(2)}）", m.group(3)
            return None, m.group(3)
        return "缺少 EOF（F/V/W）", "Unknown"
    else:
        # 支援程式碼語言的註解
        tail = content[-500:]
        m = re.search(r"(?:/\*|#|<!--)\s*[═=]*\s*EOF\s*[═=]*\s*\n?.*?F:\s*([^\s\n]+)\s*\n?.*?V:\s*(\d+)\s*\n?.*?W:\s*([^\s\n]+)", tail, re.S)
        if m:
            if len(m.group(2)) != 10:
                return f"V 欄位不是 10 位數（{m.group(2)}）", m.group(3)
            return None, m.group(3)
        return "缺少註解包裹的 EOF（F/V/W）", "Unknown"

def check_content_lines(content, filepath, forbidden_words, specific_rule):
    """
    檢查檔案內容。
    - .md 檔案：跳過代碼塊內的檢查（避免規則範例被誤判）
    - 代碼檔案（.py/.js/.css/.html/.yml/.yaml/.json/.sh）：不跳過，逐行檢查
      （因為代碼檔案內的註解與字串也可能含禁用詞，需全量掃描）
    """
    problems = []
    lines = content.splitlines()

    is_code_file = filepath.endswith(CODE_FILE_EXTS)
    # 只有 .md 檔案才啟用代碼塊跳過
    skip_code_block = not is_code_file

    is_in_code_block = False

    for i, line in enumerate(lines, 1):
        if skip_code_block:
            if line.strip().startswith("```") or line.strip().startswith("~~~"):
                is_in_code_block = not is_in_code_block
                continue
            if is_in_code_block:
                continue

        # 禁用詞檢查
        if specific_rule.get("check_forbidden_words", True):
            for word in forbidden_words:
                if word in line:
                    problems.append(f"第 {i} 行：發現禁用詞彙「{word}」")

        # 繁簡檢查 (使用 zhconv)
        if specific_rule.get("check_simplified", True) and zhconv:
            if zhconv.convert(line, 'zh-hant') != line:
                problems.append(f"第 {i} 行：發現疑似簡體字（請檢查）")

    return problems

def main():
    config = load_config()
    forbidden_words = load_forbidden_words()
    targets = get_changed_files()

    if not targets:
        print("[SUMMARY] 無變更檔案，跳過檢查。")
        sys.exit(0)

    diff_stats = get_diff_stats()
    total = 0
    bad = 0
    warn = 0
    report = []

    allow_delete = os.environ.get("ALLOW_DELETE", "").lower() == "true"
    if not allow_delete:
        try:
            commit_msg = subprocess.check_output(["git", "log", "-1", "--pretty=%B"], text=True, stderr=subprocess.DEVNULL)
            if "[allow-delete]" in commit_msg:
                allow_delete = True
        except Exception:
            pass

    for path in targets:
        if is_ignored(path, config):
            print(f"[SKIP] 命中白名單或自指防護：{path}")
            continue

        stats = diff_stats.get(path, {})
        if stats.get("deleted", 0) > 30 and not allow_delete:
            report.append(f"[WARN] {path}: 異常減少 {stats['deleted']} 行，且無 [allow-delete] 標記。")
            warn += 1

        if not path.endswith((".md", ".py", ".js", ".css", ".html", ".yml", ".yaml", ".json", ".sh", ".txt")):
            continue

        total += 1
        try:
            with open(path, "r", encoding="utf-8") as fh:
                content = fh.read()
        except Exception as exc:
            report.append(f"[ERROR] {path}: 讀取失敗（{exc}）")
            bad += 1
            continue

        specific_rule = config.get("file_specific_rules", {}).get(path, {})

        eof_err, writer = check_eof(content, path)
        if eof_err:
            report.append(f"[ERROR] {path} (編寫者: {writer})\n  - {eof_err}")
            bad += 1

        content_errs = check_content_lines(content, path, forbidden_words, specific_rule)
        for err in content_errs:
            report.append(f"[ERROR] {path} (編寫者: {writer})\n  - {err}")
            bad += 1

    print(f"[SUMMARY] 增量檢查 {total} 檔，錯誤 {bad} 項，警告 {warn} 項。")
    if report:
        print("\n--- 檢查報告 ---")
        for r in report:
            print(r)

    mode = os.environ.get("VALIDATE_MODE", "strict").lower()
    if bad > 0 and mode == "strict":
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
/* ═══ EOF ═══
F: AI-infra/.github/scripts/validate_delivery.py
V: 1792913800
W: ai-system-005
═══ */