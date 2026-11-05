import re, sys, os, pathlib
root = pathlib.Path(sys.argv[1])
pats = {
 "ipv4": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
 "wls_keys": re.compile(r"WLSACCESSID|WLSSECRET|LICENSEID|GRB_LICENSE_FILE\s*=\s*\S+"),
 "user_at_host": re.compile(r"\b[A-Za-z0-9_.-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+"),
 "ssh_scp_host": re.compile(r"\b(ssh|scp|rsync)\s+[^\s]*@?[A-Za-z0-9.-]+\.(edu|sg|com|net|cn)\b"),
 "port_flag": re.compile(r"\s-p\s*\d{2,5}\b|\s-P\s*\d{2,5}\b|:\d{4,5}\b"),
 "hostnames": re.compile(r"\b[a-z0-9-]+\.(nus\.edu\.sg|autodl\.com|seetacloud\.com|gurobi\.com)\b", re.I),
 "instance_like": re.compile(r"autodl-container-[a-z0-9-]+|\bWest-B\b|region-\d+", re.I),
}
skip_ext = {".nc", ".gz", ".tar", ".zip", ".pyc"}
hits = {}
nfiles = 0
for p in root.rglob("*"):
    if not p.is_file() or p.suffix.lower() in skip_ext: continue
    nfiles += 1
    try: txt = p.read_text(encoding="utf-8", errors="replace")
    except Exception: continue
    for i, line in enumerate(txt.splitlines(), 1):
        for k, rx in pats.items():
            for m in rx.finditer(line):
                s = m.group(0)
                mask = s[:4] + "…" + s[-3:] if len(s) > 8 else s
                hits.setdefault(k, []).append((str(p.relative_to(root)), i, mask))
print("files scanned:", nfiles)
for k, v in hits.items():
    print(f"\n[{k}] {len(v)} hits")
    seen = set()
    for f, i, m in v:
        key = (f, m)
        if key in seen: continue
        seen.add(key)
        print(f"  {f}:{i}  {m}")
        if len(seen) > 25: print("  ..."); break
