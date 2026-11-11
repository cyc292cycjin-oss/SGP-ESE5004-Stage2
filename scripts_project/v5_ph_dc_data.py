"""V5 X20 revision 2-1 (decision 244; X20_SPEC.md 1.8; decision 246 Q8): Philippine inter-island DC stock table PH_DC_STOCK_V5.csv.

Frozen-base values = the author base inherited from PyPSA-Earth simplify_links (sum of every chain branch incl. the 2000 MW placeholder converters;
X10 REPORT section 1, PH_INTERISLAND_LINKS.csv). Corrected values from NGCP Transmission Development Plan 2025-2050 (downloaded by X20 B, SHA256
recorded in the source column; PDF page numbers):
  Leyte-Luzon HVDC 440 MW monopole (1998): the TDP lists the bipolar project "to provide an additional transfer capacity of 440 MW between Luzon
    and Visayas" (PDF p.43-44, ETC stage 1 2028-03 / stage 2 2030-12, p.51); the existing 440 MW monopole from the Hitachi Energy project page.
    The model splits the line at the Visayas10 DC junction: both segments get 440 MW; the parallel 2000 MW B2B placeholder gets 0 (kept, fixed).
  MVIP 450 MW (2024-01): "The MVIP has an initial transfer capacity of 450 MW" (PDF p.5).
  Mindoro links: Batangas-Mindoro interconnection ETC 2027-09 (stage 1, PDF p.35), BMIBP completion 2030-12 (p.72), Palawan-Mindoro stage 1 2033-02
    (p.40): no DC stock in 2025, the osm-plus 230 kV 'DC' rows are 0 MW and stay extendable candidates.
    python scripts_project/v5_ph_dc_data.py --tdp <NGCP_TDP_2025_2050_REPORT.pdf>
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research_inputs/corridors/PH_DC_STOCK_V5.csv"
TDP_URL = "https://www.ngcp.ph/Attachment-Uploads/TDP%202025-2050%20REPORT-2025-03-11-10-38-56.pdf"
HITACHI = "https://www.hitachienergy.com/news-and-events/customer-stories/leyte-luzon"
ROWS = [
    ("Link", "151018428-1_0+2", "set_capacity", 3146.6, 440.0, "B", "Leyte-Luzon HVDC (Visayas10 - Luzon5 segment): 440 MW monopole", "PDF p.43-44, 51 (bipole adds 440 MW); " + HITACHI),
    ("Link", "1006176982-1_0+1", "set_capacity", 2573.3, 440.0, "B", "Leyte-Luzon HVDC (Visayas10 - Visayas7 segment): 440 MW monopole", "PDF p.43-44, 51 (bipole adds 440 MW); " + HITACHI),
    ("Link", "convert_935_1501", "set_zero_fixed", 2000.0, 0.0, "A", "B2B placeholder converter (base_network.py:671 fixed 2000 MW), parallel to the Leyte-Luzon segment; kept at 0 for the DC/AC bus map", "X10 REPORT 1(b)"),
    ("Link", "100000087-1_0+1", "set_capacity", 2376.74, 0.0, "A", "Luzon5 - Luzon9 (Mindoro) osm-plus 230 kV 'DC' row: no link in 2025, extendable candidate", "PDF p.35 (ETC 2027-09), p.72 (BMIBP 2030-12)"),
    ("Link", "100000092-1_0+1", "set_capacity", 2376.74, 0.0, "A", "Visayas7 - Luzon9 (Mindoro) osm-plus 230 kV 'DC' row: no link in 2025, extendable candidate", "PDF p.35, p.40 (Palawan-Mindoro 2033-02)"),
    ("Link", "1076672675-1_0+4", "set_capacity", 5719.9, 450.0, "A", "Mindanao-Visayas Interconnection Project (MVIP): initial transfer capacity 450 MW", "PDF p.5"),
]


def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--tdp", type=Path, required=True); a = ap.parse_args(argv)
    h = hashlib.sha256(a.tdp.read_bytes()).hexdigest()
    t = pd.DataFrame(ROWS, columns=["component_type", "component", "action", "frozen_base_mw", "corrected_mw", "grade", "basis", "source_page"])
    t["source"] = f"NGCP TDP 2025-2050 {TDP_URL} (sha256 {h})"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    t.to_csv(OUT, index=False, lineterminator="\n")
    print(OUT.name, len(t), "frozen", round(t.frozen_base_mw.sum(), 2), "corrected", t.corrected_mw.sum())


if __name__ == "__main__":
    main()
