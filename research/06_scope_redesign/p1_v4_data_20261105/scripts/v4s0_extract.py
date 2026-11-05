"""V4 S0 section 1: extract every archive under downloads/ into extracted/<subdir>/<archive stem>/ (originals untouched).

    python scripts/v4s0_extract.py --work /mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_data_20261105

Zip and tar members are checked before extraction (no absolute path, no '..', no links); .gzip / .gz single files are
decompressed to <stem>.csv. Writes evidence/EXTRACTED_MEMBERS.csv (archive, member, bytes, sha256). Read-only on downloads/.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import shutil
import tarfile
import zipfile
from pathlib import Path, PurePosixPath


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def safe(name: str) -> bool:
    p = PurePosixPath(name.replace("\\", "/"))
    return not p.is_absolute() and ".." not in p.parts and not name.startswith("/")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--work", type=Path, required=True); a = ap.parse_args()
    dl, ex = a.work / "downloads", a.work / "extracted"
    rows = []
    for f in sorted(dl.rglob("*")):
        if not f.is_file():
            continue
        sub = f.relative_to(dl).parts[0]
        rel = f.relative_to(dl).as_posix()
        if f.suffix == ".zip":
            dest = ex / sub / f.stem
            with zipfile.ZipFile(f) as z:
                bad = [i.filename for i in z.infolist() if not safe(i.filename)]
                if bad:
                    raise SystemExit(f"unsafe member in {rel}: {bad[:3]}")
                if dest.exists():
                    shutil.rmtree(dest)
                z.extractall(dest)
        elif f.name.endswith(".tar.gz"):
            dest = ex / sub / f.name[: -len(".tar.gz")]
            with tarfile.open(f, "r:gz") as t:
                bad = [m.name for m in t.getmembers() if not safe(m.name) or m.issym() or m.islnk()]
                if bad:
                    raise SystemExit(f"unsafe member in {rel}: {bad[:3]}")
                if dest.exists():
                    shutil.rmtree(dest)
                t.extractall(dest, filter="data")
        elif f.suffix in (".gzip", ".gz"):
            dest = ex / sub / (f.stem + "_decompressed")
            if dest.exists():
                shutil.rmtree(dest)
            dest.mkdir(parents=True)
            with gzip.open(f, "rb") as g, open(dest / (f.stem + ".csv"), "wb") as o:
                shutil.copyfileobj(g, o, 1 << 20)
        else:
            continue
        for m in sorted(dest.rglob("*")):
            if m.is_file():
                rows.append(dict(archive=rel, member=m.relative_to(ex).as_posix(), bytes=m.stat().st_size, sha256=sha256(m)))
        print(rel, "->", dest.relative_to(a.work), sum(1 for r in rows if r["archive"] == rel), "files", flush=True)
    (a.work / "evidence").mkdir(exist_ok=True)
    with open(a.work / "evidence" / "EXTRACTED_MEMBERS.csv", "w", newline="", encoding="utf-8") as o:
        w = csv.DictWriter(o, fieldnames=["archive", "member", "bytes", "sha256"]); w.writeheader(); w.writerows(rows)
    print("members", len(rows), "bytes", sum(r["bytes"] for r in rows))


if __name__ == "__main__":
    main()
