"""V4 W11 (NCV audit): page-by-page text of the local PDFs used as conversion-factor references, written to
extracted/<key>/pNNN.txt (layout mode) and pNNN_plain.txt (plain mode), plus extracted/PDF_TEXT_INDEX.csv (key, path, pages, SHA256, bytes).

    %USERPROFILE%/miniconda3/python.exe -I scripts/v4ncv_pdf_text.py --work <work dir> [--only key1,key2]

Windows miniconda interpreter (only it has pypdf; the WSL pypsa-earth environment has none). Read-only on the sources; nothing is downloaded.
The PDFs and their text are third-party publications: extracted/ stays out of git (only the index and the values used are committed).
Paths are relative to the workspace root D:/ResearchWorkspaces/ASEAN; the repository copies of UNSD_NCV.pdf, questionnaire_guidelines.pdf and
IPCC_2006_Vol2_Ch1_Introduction.pdf are byte-identical to the copies used here (SHA256 checked in the index).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path

from pypdf import PdfReader

ROOT = Path("D:/ResearchWorkspaces/ASEAN")
PDFS = {
    "unsd_ncv_05": "outputs/phase4_gate4_activation_20261005/repo/research_inputs/assembly_v1/sources/methodology/UNSD_NCV.pdf",
    "unsd_guidelines": "outputs/phase4_gate4_activation_20261005/repo/research_inputs/assembly_v1/sources/unsd_targeted/questionnaire_guidelines.pdf",
    "ipcc2006_v2c1": "work/p1_step2_20261015/research_inputs/registry_v5/sources/IPCC_2006_Vol2_Ch1_Introduction.pdf",
    "un_eb2019": "outputs/phase4_gate4_final_closure_20261006/repo/research/04_model_assembly/gate4/evidence/source_scope/UN_2019_balance_official.pdf",
    "heesi2019": "research/02_sector_coupling/buildings_heat/phase3a5/data/raw/buildings/heesi2019.pdf",
    "heesi2025": "work/p2_data_intake/v3_20261102/01_industry/content-handbook-of-energy-and-economic-statistics-of-indonesia-2025.pdf",
    "my_neb2019": "research/02_sector_coupling/buildings_heat/phase3a6/data/raw/malaysia-neb2019.pdf",
    "kh_stats": "research/02_sector_coupling/buildings_heat/phase3a5/data/raw/buildings/cambodia-energy-statistics.pdf",
    "th_eppo2564": "work/p2_data_intake/v3_20261102/01_industry/2564_รายงานสถิติพลังงาน_สนพ.pdf",
    "th_ebt2022": "work/p2_data_intake/v3_20261102/01_industry/EBT 2022 Table.pdf",
    "apec2022": "work/p2_data_intake/v3_20261102/01_industry/225_ewg_apec-energy-statistics-2022.pdf",
    "aeo8": "research/02_sector_coupling/buildings_heat/phase3a5/data/raw/buildings/aeo8.pdf",
    "mm_adb2016": "work/p1_step4_20261016/sources_s4a3/adb_myanmar_energy_assessment_2016.pdf",
    "iea_worldbal": "work/p1_v4_data_20261105/downloads/14_iea_worldbal/WORLDBAL_Documentation_July2026.pdf",
}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", type=Path, required=True)
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    only = {k for k in a.only.split(",") if k}
    out = a.work / "extracted"
    out.mkdir(exist_ok=True)
    idx_path = out / "PDF_TEXT_INDEX.csv"
    rows = {}
    if idx_path.exists():
        with idx_path.open(encoding="utf-8") as f:
            rows = {r["key"]: r for r in csv.DictReader(f)}
    for key, rel in PDFS.items():
        if only and key not in only:
            continue
        p = ROOT / rel
        r = PdfReader(str(p))
        d = out / key
        d.mkdir(exist_ok=True)
        chars = []
        for i, page in enumerate(r.pages, start=1):
            try:
                t = page.extract_text(extraction_mode="layout") or ""
            except Exception as e:   # noqa: BLE001  (record and continue: one bad page must not stop the dump)
                t = f"<<layout extraction failed: {type(e).__name__}>>"
            try:
                tp = page.extract_text() or ""
            except Exception as e:   # noqa: BLE001
                tp = f"<<plain extraction failed: {type(e).__name__}>>"
            (d / f"p{i:03d}.txt").write_text(t, encoding="utf-8")
            (d / f"p{i:03d}_plain.txt").write_text(tp, encoding="utf-8")
            chars.append(len(tp))
        rows[key] = dict(key=key, path=rel, pages=len(r.pages), sha256=sha256(p), bytes=p.stat().st_size,
                         chars_total=sum(chars), pages_without_text=sum(1 for c in chars if c < 20))
        print(key, len(r.pages), "pages", sum(chars), "chars", flush=True)
    with idx_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["key", "path", "pages", "sha256", "bytes", "chars_total", "pages_without_text"])
        w.writeheader()
        for k in sorted(rows):
            w.writerow(rows[k])


if __name__ == "__main__":
    main()
