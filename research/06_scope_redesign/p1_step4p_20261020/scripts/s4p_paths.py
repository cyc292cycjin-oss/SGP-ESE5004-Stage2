"""S4P (decision 122 point 2): shared paths and helpers. Read-only on every input."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

WORK = Path("/mnt/d/ResearchWorkspaces/ASEAN/work")
STEP = WORK / "p1_step4p_20261020"
OUT = STEP
REPO = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model")

PILOT = WORK / "p1_step4n_20261019/cloud_results/20261019T072454Z_5125/unpacked/s4n_pilot_light_20261019T072454Z_5125/export_integrated"
BATCH = WORK / "p1_step4o_20261019/cloud_results/20261019T162951Z_6896/full/unpacked"
NETS = WORK / "p1_step4o_20261019/cloud_package_dist/networks"

RUNS = {
    "integrated": PILOT,                       # S4N pilot (optimal), light export only; solved network not downloaded
    "disconnected": BATCH / "disconnected",    # S4O-6 batch (SUBOPTIMAL, C1 passed)
    "disconnected_gap": BATCH / "disconnected_gap",
    "integrated_nze": BATCH / "integrated_nze",
}
SOLVED_NC = {
    "disconnected": BATCH / "disconnected/disconnected_FORMAL_TRIAL_365X24H_solved.nc",
    "disconnected_gap": BATCH / "disconnected_gap/disconnected_GAP_DIAGNOSTIC_solved.nc",
    "integrated_nze": BATCH / "integrated_nze/integrated_nze_FORMAL_TRIAL_365X24H_solved.nc",
}
UNSOLVED_NC = {
    "integrated": NETS / "integrated_365_24h_unsolved.nc",
    "disconnected": NETS / "disconnected_365_24h_unsolved.nc",
    "integrated_nze": NETS / "integrated_nze_365_24h_unsolved.nc",
}

COUNTRIES = ["BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN"]
ENTITIES = COUNTRIES + ["ASEAN_BUNKER", "ASEAN_POOL"]
BN_ = 1e9


def ledger_detail(run: str) -> pd.DataFrame:
    df = pd.read_csv(RUNS[run] / "COUNTRY_COST_LEDGER_DETAIL.csv")
    df["run"] = run
    return df


def ledger_total(run: str) -> pd.DataFrame:
    return pd.read_csv(RUNS[run] / "COUNTRY_COST_LEDGER.csv").set_index("entity")


def load_json(p: Path):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def dump_json(obj, p: Path):
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=False, default=_default)


def _default(o):
    import numpy as np
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, (pd.Timestamp,)):
        return str(o)
    raise TypeError(type(o))


def md_table(df: pd.DataFrame, floatfmt: str = "{:,.3f}") -> str:
    cols = list(df.columns)
    lines = ["| " + " | ".join(str(c) for c in cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            if isinstance(v, float):
                cells.append(floatfmt.format(v) if pd.notna(v) else "")
            else:
                cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)
