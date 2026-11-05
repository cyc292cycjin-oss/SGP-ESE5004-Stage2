"""I1-1c: truncation scan of every UNdata export file in the repository worktree and the upstream pypsa-asean checkout (instruction 1.3).

    PYTHONHASHSEED=0 /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/i1_trunc.py

A file is an UNdata web export when its first line is the UNdata header ("Country or Area";"Commodity - Transaction";... for the energy
database, or any header starting with "Country or Area"). Data rows = lines after the header up to the first blank line (the export appends
a footnote block after a blank line). A file is flagged when the data-row count equals a known web / tool limit (100,000 UNdata web export;
65,535 / 65,536 / 1,048,575 / 1,048,576 spreadsheet limits; 50,000 / 10,000 / 20,000 / 25,000 / 200,000 / 500,000 round page sizes) or is any
other multiple of 10,000. For a flagged file: the last country written, whether the countries are in alphabetical order, the ASEAN countries
after the cut, and (energy files) the SDMX 2019 quantity those countries have for the file's commodities (what the cut removed).
Writes EXPORT_TRUNCATION_SCAN.csv and evidence/I1_1c_trunc.json. Read only.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import i1_common as cm  # noqa: E402

LIMITS = {100000: "UNdata web export limit", 65535: "xls row limit - 1", 65536: "xls row limit", 1048575: "xlsx row limit - 1", 1048576: "xlsx row limit",
          50000: "round page size", 10000: "round page size", 20000: "round page size", 25000: "round page size", 200000: "round page size", 500000: "round page size"}
ROOTS = [cm.REPO, cm.UPSTREAM]
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".snakemake", "results_project", "networks"}


def candidates():
    for root in ROOTS:
        for dp, dns, fns in os.walk(root):
            dns[:] = [d for d in dns if d not in SKIP_DIRS]
            for fn in fns:
                if not fn.lower().endswith((".txt", ".csv")):
                    continue
                p = Path(dp) / fn
                try:
                    if p.stat().st_size > 400_000_000:
                        continue
                    with open(p, "r", encoding="utf-8", errors="replace") as f:
                        first = f.readline()
                except OSError:
                    continue
                if first.lstrip('﻿"').startswith("Country or Area") or "UNdata_Export" in fn:
                    yield p


def main():
    ev = cm.Evidence("I1_1c_trunc")
    sd = pd.read_csv(cm.BASE_OUT / "SDMX_2019_CAPSULE_RECORDS.csv", dtype=str)
    sd["q"] = pd.to_numeric(sd.Quantity, errors="coerce")
    rows, seen = [], {}
    for p in candidates():
        sha = cm.sha256(p)
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        hdr = lines[0] if lines else ""
        sep = ";" if hdr.count(";") >= hdr.count(",") else ","
        data = []
        for ln in lines[1:]:
            if not ln.strip():
                break
            data.append(ln)
        countries = [ln.split(sep)[0].strip('"') for ln in data]
        order_ok = all(a <= b for a, b in zip(countries, countries[1:]))
        n = len(data)
        flag = LIMITS.get(n, "multiple of 10,000" if n and n % 10000 == 0 else "")
        last = countries[-1] if countries else ""
        coms = sorted({ln.split(sep)[1].strip('"').split(" - ")[0] for ln in data if len(ln.split(sep)) > 1}) if data else []
        years = sorted({ln.split(sep)[2].strip('"') for ln in data if len(ln.split(sep)) > 2})
        # UNdata sorts with its own collation (accents, brackets), so the cut is judged by presence: an ASEAN country without any row in a
        # truncated file is cut off; the last country may be cut part-way (not ASEAN in this scan)
        present = set(countries)
        after = [cm.UNSD_NAMES[c] for c in sorted(cm.UNSD_NAMES) if flag and c not in present]
        lost = ""
        if flag and after:
            com_l = {c.lower() for c in coms}
            x = sd[sd.Country.isin(after) & sd.Commodity.str.lower().isin(com_l | {c.replace("/ ", "/") for c in com_l})]
            if len(x):
                lost = "; ".join(f"{r.Country} {r.Commodity} {r.Transaction}: {r.Quantity} {r.Unit}" for r in x[x.TransactionCode.isin(["12", "121", "1221", "1231", "1232", "1235", "1222", "11"])].itertuples())
        dup = seen.get(sha)
        seen.setdefault(sha, str(p))
        rows.append(dict(file=str(p), bytes=p.stat().st_size, sha256=sha, duplicate_of=dup or "", data_rows=n, limit_flag=flag, last_country=last,
                         last_country_is_asean=last in cm.UNSD_NAMES, countries_python_sorted=order_ok, asean_present=";".join(cm.UNSD_NAMES[c] for c in sorted(cm.UNSD_NAMES) if c in present),
                         asean_after_cut=";".join(after), years=";".join(years[:3]) + (";..." if len(years) > 3 else ""),
                         commodities=";".join(coms)[:400], sdmx_2019_lost_rows=lost[:1500]))
        if flag:
            ev.add(f"flag.{p.name}", dict(rows=n, limit=flag, last_country=last, asean_after_cut=after), "mixed", "VERIFIED", "A", str(p), f"sha256 {sha}; commodities {';'.join(coms)[:120]}")
    T = pd.DataFrame(rows).sort_values(["limit_flag", "data_rows"], ascending=[False, False])
    cm.write_csv(T.to_dict("records"), cm.I1 / "EXPORT_TRUNCATION_SCAN.csv")
    ev.add("scan.files", len(T), "count", "VERIFIED", "A", "os.walk over the worktree and the pypsa-asean checkout", f"distinct sha256 {T.sha256.nunique()}; flagged {int((T.limit_flag != '').sum())}")
    p = ev.write()
    pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 90)
    print(len(T), "files;", T.sha256.nunique(), "distinct")
    print(T[T.limit_flag != ""][["file", "data_rows", "limit_flag", "last_country", "last_country_is_asean", "asean_present", "asean_after_cut", "commodities"]].to_string())
    print(T.sort_values("data_rows", ascending=False).head(8)[["file", "data_rows", "limit_flag", "last_country"]].to_string())
    print(T[T.limit_flag != ""].sdmx_2019_lost_rows.to_string())
    print("evidence", p, len(ev.rows))


if __name__ == "__main__":
    main()
