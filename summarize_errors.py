#!/usr/bin/env python3
"""Summarize error/fatal lines from vanilla_1_21_gaps.txt.

The file is UTF-16 LE with ANSI color codes. We strip ANSI and count only
error/fatal lines (ignoring warning/info/untidy/tips).
"""
import re
import sys
from collections import Counter

PATH = "vanilla_1_21_gaps.txt"
OUT = "gaps_summary.txt"

# ANSI escape sequence stripper
ANSI = re.compile(r"\x1b\[[0-9;]*m")

# Error/fatal line prefix pattern: e.g. "error(0)" or "fatal(...)"
SEVERITY = re.compile(r"(?m)^(error|fatal)\b")

# File path lines: "  --> path" (after stripping ANSI)
PATH_LINE = re.compile(r"^\s*-->\s*(.*)$")

# Normalize a message: strip leading file path/line info and trailing numbers
def normalize(msg: str) -> str:
    msg = ANSI.sub("", msg).strip()
    # Drop "file:line: " prefix if present
    msg = re.sub(r"^[^:]+:\d+:\s*", "", msg)
    # Collapse whitespace
    msg = re.sub(r"\s+", " ", msg)
    return msg

def main():
    with open(PATH, "r", encoding="utf-16", errors="replace") as f:
        raw = f.read()

    lines = raw.splitlines()
    # Show first 40 lines for format verification
    print("=== First 40 lines (raw, ANSI stripped) ===")
    for ln in lines[:40]:
        print(repr(ANSI.sub("", ln)))
    print()

    err_counter = Counter()
    path_counter = Counter()
    total_err = 0

    for ln in lines:
        clean = ANSI.sub("", ln)
        m = SEVERITY.match(clean)
        if m:
            total_err += 1
            err_counter[normalize(clean)] += 1
        else:
            pm = PATH_LINE.match(clean)
            if pm:
                path_counter[pm.group(1).strip()] += 1

    print(f"Total error+fatal: {total_err}")
    print("\nTop 20 error buckets:")
    for i, (msg, cnt) in enumerate(err_counter.most_common(20), 1):
        print(f"  {i:2d}. [{cnt:6d}] {msg}")

    print("\nTop 20 paths:")
    for i, (p, cnt) in enumerate(path_counter.most_common(20), 1):
        print(f"  {i:2d}. [{cnt:6d}] {p}")

    # Write summary
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(f"Total error+fatal count: {total_err}\n\n")
        f.write("Top 30 most frequent error messages:\n")
        f.write("-" * 60 + "\n")
        for i, (msg, cnt) in enumerate(err_counter.most_common(30), 1):
            f.write(f"{i:2d}. [{cnt:6d}] {msg}\n")
        f.write("\nTop 20 most affected game folders/paths:\n")
        f.write("-" * 60 + "\n")
        for i, (p, cnt) in enumerate(path_counter.most_common(20), 1):
            f.write(f"{i:2d}. [{cnt:6d}] {p}\n")

    print(f"\nWrote {OUT}")

if __name__ == "__main__":
    main()