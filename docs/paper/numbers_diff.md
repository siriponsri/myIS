# Numeric Diff Audit

Compared against `tmp/selection_goal_before.txt` after the final build.

- Semantic reported values: unchanged.
- New or changed numeric claims: none.
- The standalone-token extractor reports four count-only differences (`0`, `03`, `64`, and `872`) caused by Poppler text extraction joining hyphenated forms such as `64-token` and `Final-872`; the rendered PDF retains the same values and labels.
- Classification: no `VALUE_CHANGED`, `NEW_STAT`, `DISPLAY_ROUNDING`, or `REMOVED` numeric result.
