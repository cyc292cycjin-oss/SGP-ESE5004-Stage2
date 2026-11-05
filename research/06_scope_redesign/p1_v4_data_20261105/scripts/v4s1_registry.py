"""V4 S1 section 5: add the three PDFs that the user put into downloads/12-14 on 2026-11-05 to DATA_REGISTRY_V4_DOWNLOADS.csv.

    python scripts/v4s1_registry.py --work <work dir>      (any Python 3; standard library only)

Bytes and SHA256 are computed here. Version, licence and content were read from the files themselves in S1 (copyright page, report front matter,
documentation header; text dumps in extracted/, not in git). Rows with the same relative_path are replaced, so the script can be re-run.
None of the three PDFs enters the repository; the IEA document is cited by page number only and none of its data is used.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path

ROWS = {
    "downloads/12_bps_indonesia/BPS0000-statistik_industri_manufaktur_indonesia_2019.pdf": dict(
        source="BPS-Statistics Indonesia, Statistik Industri Manufaktur Indonesia 2019 (Statistics of Indonesia Manufacturing Industry 2019; IBS large and medium industry)",
        source_url="https://www.bps.go.id (watermark on every page; the publication page address is not in the file)",
        version_or_release="ISSN 2338-0934, publication number 05300.2113, catalogue 6103019; PDF created 2021-09-28 (FPDF 1.81); 348 PDF pages (xvi + 330 printed)",
        licence="(c) BPS-Statistics Indonesia; commercial use needs written permission",
        licence_basis="copyright page (PDF p.3): announcing, distributing, communicating or copying the book in part or whole for commercial purposes is prohibited without written permission of BPS",
        content="IBS 2019 tables by industrial code (KBLI 2015) and province: firms, workers, wages, electricity generated / purchased / sold (table 5.1), fuel and lubricant quantities (6a.1) and values (6b.1), inputs, output, capital",
        extracted_to="extracted/12_bps_indonesia/ (page text, glyph tokens; not in git)",
        note="vector text inside one Form XObject per page (ToUnicode present); tables 5.1 and 6a.1 parsed by scripts/v4s1_bps_*.py, check s1/ID_BPS_PARSE_CHECK.csv"),
    "downloads/13_crea_captive_coal/EN-CREA_GEM_Indonesia-captive-coal-in-2025_REV.pdf": dict(
        source="CREA and GEM, 'Out of sight, out of control: 31 GW of captive coal is jeopardizing Indonesia's economic and emissions goals' (third joint captive-coal briefing)",
        source_url="https://energyandcleanair.org (CREA publication; the address of this report is not stated in the file)",
        version_or_release="27 January 2026, revised (editorial note of 4 February 2026 on p.iii); based on GEM GCPT releases July 2023 / July 2024 / July 2025",
        licence="not stated",
        licence_basis="no licence statement in the file; p.ii holds only a disclaimer (views of the authors, no liability)",
        content="Indonesian captive coal capacity 2023-2025 by status, province and industry (nickel 7.16 / 11.6 / 15.4 GW operating), sub-30 MW units (722 MW), comparison with the JETP captive power study; no capacity factors, heat rates or coal tonnages",
        extracted_to="extracted/13_crea_captive_coal/ (page text; not in git)", note="used only as a trend and plant-list cross-check, not for 2019 values"),
    "downloads/14_iea_worldbal/WORLDBAL_Documentation_July2026.pdf": dict(
        source="IEA, World Energy Balances database documentation, July 2026 edition",
        source_url="https://www.iea.org (the file says it is online but gives no address in text; terms https://www.iea.org/terms)",
        version_or_release="July 2026 edition; 700 PDF pages",
        licence="IEA, all rights reserved; IEA data under the IEA terms and conditions",
        licence_basis="p.3 (and every page header): 'IEA. All rights reserved.'; p.3 refers all IEA data to https://www.iea.org/terms",
        content="database documentation: flows, products, conversion conventions and country notes; Indonesia note on PDF p.471 (captive-plant coal in HEESI sales removed from consumption from 2010 in the 2025 edition, estimated from GEM captive capacity; blast furnace and coke oven estimates added; 2022 coal increase in non-ferrous metals)",
        extracted_to="extracted/14_iea_worldbal/ (page text; not in git)", note="decision 202 item 5: cited by page as a method reference only; no IEA data used"),
}
FIELDS = ["relative_path", "bytes", "sha256", "source", "source_url", "version_or_release", "licence", "licence_basis", "content", "extracted_to", "note"]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--work", type=Path, required=True); a = ap.parse_args()
    reg = a.work / "DATA_REGISTRY_V4_DOWNLOADS.csv"
    with reg.open(encoding="utf-8", newline="") as f:
        r = csv.DictReader(f); fields = r.fieldnames; rows = [x for x in r if x["relative_path"] not in ROWS]
    if fields != FIELDS:
        raise ValueError(f"registry columns changed: {fields}")
    for rel, meta in ROWS.items():
        p = a.work / rel
        rows.append(dict(relative_path=rel, bytes=p.stat().st_size, sha256=sha256(p), **meta))
    with reg.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS); w.writeheader(); w.writerows(rows)
    for x in rows[-3:]:
        print(x["relative_path"], x["bytes"], x["sha256"][:16])


if __name__ == "__main__":
    main()
