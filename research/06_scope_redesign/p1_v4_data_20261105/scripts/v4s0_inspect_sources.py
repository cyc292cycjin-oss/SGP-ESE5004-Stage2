"""V4 S0 sections 1 and 4: structure of every tabular source (sheet names, dimensions, header row, about / licence text lines).

    python scripts/v4s0_inspect_sources.py --work <work dir>

Read-only. Writes evidence/SOURCE_STRUCTURE.json. Personal data guard: text lines that look like an e-mail address are replaced by
'<redacted e-mail>' before they are written (download forms may stamp the requesting user into a file).
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import openpyxl
import pandas as pd

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
ABOUT_HINT = re.compile(r"about|read ?me|licen|copyright|terms|citation|version|metadata|notes|info", re.I)


def clean(v):
    s = "" if v is None else str(v)
    return EMAIL.sub("<redacted e-mail>", s)[:400]


def xlsx(path: Path, max_header_rows: int = 12) -> dict:
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    out = {}
    for ws in wb.worksheets:
        rows = []
        for i, r in enumerate(ws.iter_rows(values_only=True)):
            if i >= (60 if ABOUT_HINT.search(ws.title) else max_header_rows):
                break
            vals = [clean(x) for x in r if x not in (None, "")]
            if vals:
                rows.append(vals[:40])
        out[ws.title] = dict(max_row=ws.max_row, max_column=ws.max_column, first_rows=rows)
    wb.close()
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--work", type=Path, required=True); a = ap.parse_args()
    dl, ex = a.work / "downloads", a.work / "extracted"
    files = sorted(set(dl.rglob("*.xlsx")) | set(ex.rglob("*.xlsx")))
    res = {}
    for f in files:
        if "Ownership-Tracker" in f.name:   # 60 MB ownership tables, not used (header only)
            wb = openpyxl.load_workbook(f, read_only=True); res[f.relative_to(a.work).as_posix()] = {ws.title: dict(max_row=ws.max_row, max_column=ws.max_column) for ws in wb.worksheets}; wb.close()
            continue
        try:
            res[f.relative_to(a.work).as_posix()] = xlsx(f)
        except Exception as e:   # noqa: BLE001
            res[f.relative_to(a.work).as_posix()] = dict(error=repr(e))
        print(f.relative_to(a.work), flush=True)
    for f in sorted(ex.rglob("*.csv")):
        if f.stat().st_size < 50_000_000 and "timeseries_data" not in f.as_posix():
            try:
                d = pd.read_csv(f, nrows=5, sep=None, engine="python")
                res[f.relative_to(a.work).as_posix()] = dict(columns=[clean(c) for c in d.columns][:60], first_row=[clean(x) for x in d.iloc[0].tolist()][:60] if len(d) else [])
            except Exception as e:   # noqa: BLE001
                res[f.relative_to(a.work).as_posix()] = dict(error=repr(e))
    for f in sorted(ex.rglob("*.parquet")):
        if "NAICS=" in f.as_posix() and not f.as_posix().endswith(("NAICS=3111/" + f.name, "NAICS=331110/" + f.name)):
            continue
        import pyarrow.parquet as pq
        m = pq.ParquetFile(f)
        res[f.relative_to(a.work).as_posix()] = dict(rows=m.metadata.num_rows, columns=m.schema.names)
    (a.work / "evidence").mkdir(exist_ok=True)
    (a.work / "evidence" / "SOURCE_STRUCTURE.json").write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print("entries", len(res))


if __name__ == "__main__":
    main()
