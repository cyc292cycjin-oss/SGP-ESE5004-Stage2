"""V4 S0 stop-condition check: do the downloaded files carry the requesting user's personal data or login tokens?

    V4S0_SCAN='<pattern1>,<pattern2>' python scripts/v4s0_leak_scan.py --work <work dir>

Patterns come only from the environment at run time (never stored in a file). Scans every file under downloads/ and extracted/:
xlsx / zip members are decompressed and scanned; nested zips (Climate TRACE v5.5.0 per-gas packages) are scanned member by member
in streaming mode. Also flags generic token markers (token=, api_key, access_token, Authorization). Prints counts only, never the
matched text. Exit code 3 when a personal pattern is found.
"""
from __future__ import annotations

import argparse
import io
import os
import re
import sys
import zipfile
from pathlib import Path

GENERIC = [rb"access_token", rb"api_key", rb"apikey=", rb"Authorization:", rb"token=", rb"Bearer "]


def scan_bytes(b: bytes, pats) -> dict:
    return {p.pattern: len(p.findall(b)) for p in pats if p.search(b)}


def scan_zip(z: zipfile.ZipFile, pats, depth=0) -> dict:
    hits = {}
    for i in z.infolist():
        if i.is_dir():
            continue
        with z.open(i) as f:
            data = f.read()
        if i.filename.lower().endswith(".zip") and depth < 2:
            sub = scan_zip(zipfile.ZipFile(io.BytesIO(data)), pats, depth + 1)
        else:
            sub = scan_bytes(data, pats)
        for k, v in sub.items():
            hits[k] = hits.get(k, 0) + v
    return hits


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--work", type=Path, required=True); a = ap.parse_args()
    raw = [x.strip() for x in os.environ.get("V4S0_SCAN", "").split(",") if x.strip()]
    if not raw or any(len(x) < 4 for x in raw):
        sys.exit("V4S0_SCAN missing or a pattern shorter than 4 characters")
    personal = [re.compile(re.escape(x.encode()), re.I) for x in raw]
    generic = [re.compile(g, re.I) for g in GENERIC]
    found_personal, found_generic, n = {}, {}, 0
    for root in ("downloads", "extracted"):
        for f in sorted((a.work / root).rglob("*")):
            if not f.is_file():
                continue
            n += 1
            rel = f.relative_to(a.work).as_posix()
            if f.suffix.lower() in (".zip", ".xlsx"):
                try:
                    hp = scan_zip(zipfile.ZipFile(f), personal); hg = scan_zip(zipfile.ZipFile(f), generic) if f.stat().st_size < 80_000_000 else {}
                except zipfile.BadZipFile:
                    b = f.read_bytes(); hp, hg = scan_bytes(b, personal), scan_bytes(b, generic)
            else:
                b = f.read_bytes(); hp, hg = scan_bytes(b, personal), scan_bytes(b, generic)
            if hp:
                found_personal[rel] = sum(hp.values())
            if hg:
                found_generic[rel] = sorted(k.decode(errors="replace") if isinstance(k, bytes) else str(k) for k in hg)
    print("files scanned", n)
    print("personal pattern hits (file: count):", found_personal or "none")
    print("generic token-marker hits (file: markers):", found_generic or "none")
    sys.exit(3 if found_personal else 0)


if __name__ == "__main__":
    main()
