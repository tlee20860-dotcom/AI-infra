#!/bin/bash
# append_file.sh - 用於將源檔案合併到共享包中

if [ $# -ne 2 ]; then
    echo "Usage: $0 <source_file> <target_file>"
    exit 1
fi

SOURCE=$1
TARGET=$2

if [ ! -f "$SOURCE" ]; then
    echo "[WARN] Source file not found: $SOURCE"
    exit 0
fi

# 寫入標記與檔名
echo "" >> "$TARGET"
echo "<!-- === FILE START: $SOURCE === -->" >> "$TARGET"
echo "" >> "$TARGET"
echo "## 📄 $SOURCE" >> "$TARGET"
echo "" >> "$TARGET"

# 取得副檔名
EXT="${SOURCE##*.}"

# 寫入檔案內容（防呆：如果是 .md 檔且內部有三反引號，跳過包裹；其他副檔名一律強制包裹）
if [ "$EXT" = "md" ] && grep -q '\`\`\`' "$SOURCE"; then
    cat "$SOURCE" >> "$TARGET"
else
    echo "\`\`\`$EXT" >> "$TARGET"
    cat "$SOURCE" >> "$TARGET"
    echo "\`\`\`" >> "$TARGET"
fi

# 寫入結束標記
echo "" >> "$TARGET"
echo "<!-- === FILE END: $SOURCE === -->" >> "$TARGET"

# ═══ EOF ═══
# F: AI-infra/.github/workflows/append_file.sh
# V: 1792383600
# W: ai-system-20261019-011#004
# ═══ EOF ═══