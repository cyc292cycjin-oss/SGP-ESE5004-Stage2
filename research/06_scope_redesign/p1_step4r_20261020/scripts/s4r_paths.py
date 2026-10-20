"""S4R shared paths (read-only on every input)."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

WORK = Path("/mnt/d/ResearchWorkspaces/ASEAN/work")
STEP = WORK / "p1_step4r_20261020"
OUT = STEP
EV = STEP / "evidence"
S4P = WORK / "p1_step4p_20261020"
REPO = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model")
TMP = Path("/home/jin/s4r_tmp")
COUNTRIES = ["BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN"]
NAMES = {"BN": "Brunei", "ID": "Indonesia", "KH": "Cambodia", "LA": "Lao PDR", "MM": "Myanmar", "MY": "Malaysia", "PH": "Philippines", "SG": "Singapore", "TH": "Thailand", "TL": "Timor-Leste", "VN": "Vietnam"}
ISO3 = {"BN": "BRN", "ID": "IDN", "KH": "KHM", "LA": "LAO", "MM": "MMR", "MY": "MYS", "PH": "PHL", "SG": "SGP", "TH": "THA", "TL": "TLS", "VN": "VNM"}
MWH_PER_MTOE = 11.63e6
MWH_PER_T_LNG = 13.333333333333334   # GEM table conversion used by the registry (lng_mwh_per_t)


def load_json(p):
    return json.load(open(p, encoding="utf-8"))


def dump_json(obj, p):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    json.dump(obj, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2, default=lambda o: float(o) if hasattr(o, "__float__") else str(o))


def md_table(df: pd.DataFrame, fmt="{:,.2f}"):
    cols = list(df.columns)
    out = ["| " + " | ".join(str(c) for c in cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            cells.append(fmt.format(v) if isinstance(v, float) and pd.notna(v) else ("" if (isinstance(v, float) and pd.isna(v)) else str(v)))
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)
