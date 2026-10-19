## FILE: `.github/workflows/setup-structure.yml`

<<<<<<< OLD
            if [ "$SAFE_NAME" == "AI-OS" ]; then
              for f in external/AI-OS/E-*.md; do
=======
            if [ -f "external/${SAFE_NAME}/meta.json" ]; then
              echo "" >> "$OUTPUT"
              echo "## meta.json" >> "$OUTPUT"
              bash .github/workflows/append_file.sh "external/${SAFE_NAME}/meta.json" "$OUTPUT" || true
            fi

            if [ "$SAFE_NAME" == "AI-OS" ]; then
              for f in external/AI-OS/E-*.md; do
>>>>>>> NEW

<<<<<<< OLD
            bash .github/workflows/append_file.sh ".github/workflows/setup-structure.yml" "$OUTPUT" || true
          fi
=======
            bash .github/workflows/append_file.sh ".github/workflows/setup-structure.yml" "$OUTPUT" || true
          fi

          if [ -f ".github/workflows/sync-repos.yml" ]; then 
            echo "" >> "$OUTPUT"
            echo "### 📄 檔案：sync-repos.yml (infra)" >> "$OUTPUT"
            bash .github/workflows/append_file.sh ".github/workflows/sync-repos.yml" "$OUTPUT" || true
          fi

          if [ -f ".github/workflows/update-index.yml" ]; then 
            echo "" >> "$OUTPUT"
            echo "### 📄 檔案：update-index.yml (infra)" >> "$OUTPUT"
            bash .github/workflows/append_file.sh ".github/workflows/update-index.yml" "$OUTPUT" || true
          fi

          if [ -f ".github/workflows/append_file.sh" ]; then 
            echo "" >> "$OUTPUT"
            echo "### 📄 檔案：append_file.sh (infra)" >> "$OUTPUT"
            bash .github/workflows/append_file.sh ".github/workflows/append_file.sh" "$OUTPUT" || true
          fi
>>>>>>> NEW