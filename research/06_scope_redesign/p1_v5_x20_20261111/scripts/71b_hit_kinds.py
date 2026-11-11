"""泄露扫描命中的分类（只读）：对审阅包中命中的成员，按模式的第几个分支命中计数，并只打印每个命中的前 3 个字符与长度（不打印内容）。
模式来自环境变量 X20_LEAK_PATTERNS。用法：python 71b_hit_kinds.py <zip>"""
import os
import re
import sys
import zipfile

alts = os.environ["X20_LEAK_PATTERNS"].split("|")
z = zipfile.ZipFile(sys.argv[1])
for n in z.namelist():
    t = z.read(n).decode("utf-8", "replace")
    for i, a in enumerate(alts):
        for m in re.finditer(a, t, re.I):
            s = m.group(0); ln = t.count("\n", 0, m.start()) + 1
            print(n, "alt", i, "line", ln, "match", s[:3] + "...", "len", len(s), "context_prefix", repr(t[max(0, m.start() - 25):m.start()])[-30:])
