## FILE: `.github/workflows/apply-patch.yml`

<<<<<<< OLD
      - name: Checkout
        uses: actions/checkout@v4
=======
      - name: Checkout
        uses: actions/checkout@v4
        with:
          token: ${{ secrets.CROSS_REPO_PAT }}
>>>>>>> NEW