import re
from collections import Counter

# Strip ANSI codes
ansi_re = re.compile(r'\x1b\[[0-9;]*m')

errors = []  # list of (message, path)
current_path = None

with open('vanilla_1_21_gaps.txt', 'r', encoding='utf-16', errors='replace') as f:
    for line in f:
        clean = ansi_re.sub('', line).rstrip('\n')
        # Match error/warning/fatal lines
        m = re.match(r'^(error|warning|fatal)\([^)]+\):\s+(.+)$', clean)
        if m:
            msg = m.group(2).strip()
            errors.append((msg, current_path))
            continue
        # Match path lines like:     --> [CK3] common\bookmarks\bookmarks\00_bookmarks.txt
        pm = re.match(r'^\s*-->\s*\[CK3\]\s+(.+)$', clean)
        if pm:
            current_path = pm.group(1).strip()

# 1. Total count
total = len(errors)

# 2. Top 30 error messages
msg_counts = Counter(msg for msg, _ in errors)

# 3. Top 20 paths
path_counts = Counter(path for _, path in errors if path)

with open('gaps_summary.txt', 'w', encoding='utf-8') as out:
    out.write(f"Total error/warning count: {total}\n\n")

    out.write("Top 30 most frequent error messages:\n")
    out.write("-" * 60 + "\n")
    for i, (msg, cnt) in enumerate(msg_counts.most_common(30), 1):
        out.write(f"{i:2d}. [{cnt:5d}] {msg}\n")

    out.write("\nTop 20 most affected game folders/paths:\n")
    out.write("-" * 60 + "\n")
    for i, (path, cnt) in enumerate(path_counts.most_common(20), 1):
        out.write(f"{i:2d}. [{cnt:5d}] {path}\n")

print(f"Done. Total errors: {total}")