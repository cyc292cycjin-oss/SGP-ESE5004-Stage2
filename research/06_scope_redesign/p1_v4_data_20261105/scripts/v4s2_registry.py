"""V4 S2 section 7: add the two FAOSTAT exports that the user put into downloads/15_faostat on 2026-11-06 to DATA_REGISTRY_V4_DOWNLOADS.csv.

    python scripts/v4s2_registry.py --work <work dir>      (any Python 3; standard library only)

Bytes and SHA256 are computed here and must equal the values in V4_S2_INSTRUCTION.md. Content (domain, areas, years, elements, flags, row count)
is read from the files. The csv files carry no licence or release text; the FAO terms could not be checked on this machine, so the licence is
recorded as 'to be checked' (待核) for the reviewer. Rows with the same relative_path are replaced, so the script can be re-run. The two csv files
stay out of the repository (downloads/); only derived tables in s2/ are committed.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path

EXPECTED = {"downloads/15_faostat/FAOSTAT_data_en_11-6-2026 (2).csv": "de61d07f1801c3f013c0f506c5da57a3c21ceda5cb53a5d094b1fa3bd8f5e027",
            "downloads/15_faostat/FAOSTAT_data_en_11-6-2026.csv": "f340a9468f09d8a2325efaf7918e8eb2ea06031c9a0620ac13e8bc793d8b32a8"}
COMMON = dict(licence="待核 (to be checked): FAO terms of use for FAOSTAT data; not verifiable on this machine",
              licence_basis="the csv export holds no licence, citation or release text; the FAO website terms were not opened (no download in S2)",
              extracted_to="(none; read directly by scripts/v4s2_common.py fao())")
META = {"downloads/15_faostat/FAOSTAT_data_en_11-6-2026 (2).csv": dict(
            source="FAO, FAOSTAT domain FO 'Forestry Production and Trade' (bulk csv export by the user)",
            source_url="https://www.fao.org/faostat/en/#data/FO (export page; the address is not in the file)",
            note="S2 section 2.1 (pulp and paper base years), section 3 (wood fuel, residues, trade); file name date 11-6-2026 = 2026-11-06, put into downloads at 00:24 SGT"),
        "downloads/15_faostat/FAOSTAT_data_en_11-6-2026.csv": dict(
            source="FAO, FAOSTAT domain QCL 'Crops and livestock products' (bulk csv export by the user)",
            source_url="https://www.fao.org/faostat/en/#data/QCL (export page; the address is not in the file)",
            note="S2 sections 2.3-2.4 (sugar cane, oil palm fruit, palm oil, palm kernels) and section 3; put into downloads at 00:27 SGT")}


def describe(p: Path) -> tuple[str, str]:
    with open(p, encoding="utf-8-sig", newline="") as f:
        r = list(csv.DictReader(f))
    dom = sorted({x["Domain Code"] for x in r}); areas = sorted({x["Area"] for x in r}); yrs = sorted({int(x["Year"]) for x in r})
    els = sorted({x["Element"] for x in r}); flags = sorted({f"{x['Flag']} {x['Flag Description']}" for x in r})
    items_id = len({x["Item"] for x in r if x["Area"] == "Indonesia"})
    content = (f"domain {', '.join(dom)}; {len(areas)} areas (ASEAN 11); years {yrs[0]}-{yrs[-1]}; elements {', '.join(els)}; {len(r)} data rows; "
               f"{items_id} items for Indonesia; flags {'; '.join(flags)}")
    return content, f"FAOSTAT bulk export of 2026-11-06 (no release date in the file); years {yrs[0]}-{yrs[-1]}"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--work", type=Path, required=True); a = ap.parse_args()
    reg = a.work / "DATA_REGISTRY_V4_DOWNLOADS.csv"
    with open(reg, encoding="utf-8", newline="") as f:
        rd = csv.DictReader(f); cols = rd.fieldnames; rows = [r for r in rd if r["relative_path"] not in EXPECTED]
    n0 = len(rows)
    for rel, sha in EXPECTED.items():
        p = a.work / rel; b = p.read_bytes(); h = hashlib.sha256(b).hexdigest()
        if h != sha:
            raise SystemExit(f"STOP: {rel} SHA256 {h} differs from the instruction")
        content, version = describe(p)
        rows.append(dict(relative_path=rel, bytes=str(len(b)), sha256=h, version_or_release=version, content=content, **META[rel], **COMMON))
    with open(reg, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, quoting=csv.QUOTE_MINIMAL); w.writeheader(); w.writerows(rows)
    print(f"registry rows {n0} kept + {len(EXPECTED)} FAOSTAT rows = {len(rows)}")
    for r in rows[-2:]:
        print(r["relative_path"], r["bytes"], r["sha256"][:16], r["content"][:160])


if __name__ == "__main__":
    main()
