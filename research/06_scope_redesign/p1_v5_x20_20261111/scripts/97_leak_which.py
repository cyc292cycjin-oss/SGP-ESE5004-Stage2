"""X20 C 段：审阅包泄露扫描命中定位。模式只从环境变量 X20_LEAK_PATTERNS 读取（本文件不含模式）；
对给定文件逐个备选项（按 | 顶层切分）检查，只打印备选项序号、文件名与行号，不打印命中内容。用法：python 97_leak_which.py <文件>..."""
import os
import re
import sys


def split_top(p):
    out, depth, cur, esc = [], 0, "", False
    for ch in p:
        if esc:
            cur += ch; esc = False; continue
        if ch == "\\":
            cur += ch; esc = True; continue
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "|" and depth == 0:
            out.append(cur); cur = ""
        else:
            cur += ch
    out.append(cur)
    return out


alts = split_top(os.environ["X20_LEAK_PATTERNS"])
for f in sys.argv[1:]:
    lines = open(f, encoding="utf-8", errors="replace").read().splitlines()
    for i, a in enumerate(alts):
        rx = re.compile(a, re.I)
        ln = [k + 1 for k, l in enumerate(lines) if rx.search(l)]
        if ln:
            print(f"alt#{i} len{len(a)} {os.path.basename(f)} lines {ln}")
