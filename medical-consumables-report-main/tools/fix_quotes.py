#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
from pathlib import Path
MAP = {
    """: '"', """: '"', """: '"', """: '"', """: '"',
    "'": "'", "'": "'", "'": "'", "'": "'", "'": "'",
    "-": "-", "-": "-", "*": "*", "...": "...",
    "\u00A0": " ",  # NBSP -> space
}
def fix_text(s: str) -> str:
    for k, v in MAP.items(): s = s.replace(k, v)
    return s
def main(paths):
    changed = False
    for p in paths:
        path = Path(p)
        if not path.is_file(): continue
        try: txt = path.read_text(encoding="utf-8")
        except Exception: continue
        fixed = fix_text(txt)
        if fixed != txt:
            path.write_text(fixed, encoding="utf-8")
            changed = True
            print(f"[fixed] {path}")
    return 0
if __name__ == "__main__":
    if len(sys.argv) == 1: sys.exit(0)
    sys.exit(main(sys.argv[1:]))
