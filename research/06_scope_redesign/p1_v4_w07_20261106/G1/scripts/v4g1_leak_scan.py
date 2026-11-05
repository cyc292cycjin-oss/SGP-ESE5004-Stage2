"""V4 W07 G1: privacy / licence scan of the deliverable folder before each commit (A8 stop condition). The search patterns (user name and e-mail
variants) are passed at run time in the environment variable V4G1_LEAK_PATTERNS (';'-separated) and never written to a file; the script refuses
patterns shorter than 4 characters. Text files and zip members are scanned case-insensitively; generic token markers are listed for manual review.

    V4G1_LEAK_PATTERNS='...' python scripts/v4g1_leak_scan.py <folder>
"""
import os
import re
import sys
import zipfile
from pathlib import Path

TOKENS = re.compile(r"(api[_-]?key|secret|password|passwd|bearer\s+[a-z0-9]|token=|licen[cs]e[_ ]?key|WLSACCESSID|WLSSECRET)", re.I)


def scan_bytes(name, b, pats, hits, toks):
    t = b.decode("utf-8", errors="ignore").lower()
    for p in pats:
        if p in t:
            hits.append((name, p[:2] + "***"))
    for m in TOKENS.finditer(t):
        toks.append((name, m.group(0)[:12]))


def main():
    pats = [p.strip().lower() for p in os.environ.get("V4G1_LEAK_PATTERNS", "").split(";") if p.strip()]
    if not pats or any(len(p) < 4 for p in pats):
        sys.exit("refused: V4G1_LEAK_PATTERNS empty or too short")
    root = Path(sys.argv[1]); hits, toks, n = [], [], 0
    for f in sorted(root.rglob("*")):
        if not f.is_file() or "__pycache__" in f.parts:
            continue
        n += 1
        if f.suffix.lower() == ".zip":
            with zipfile.ZipFile(f) as z:
                for m in z.namelist():
                    scan_bytes(f"{f.name}:{m}", z.read(m), pats, hits, toks)
        elif f.stat().st_size < 50_000_000:
            scan_bytes(str(f.relative_to(root)), f.read_bytes(), pats, hits, toks)
    print(f"files scanned: {n}; pattern hits: {len(hits)}; token markers: {len(toks)}")
    for h in hits:
        print("HIT", h)
    for t in sorted(set(toks)):
        print("token marker (review):", t)
    sys.exit(1 if hits else 0)


if __name__ == "__main__":
    main()
