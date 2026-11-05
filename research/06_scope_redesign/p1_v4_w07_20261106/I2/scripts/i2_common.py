"""I2 shared helpers (v4 integration step 2; the repository is read only: nothing is solved, no model code / config / network / registry /
T_v2 in the repository is written; every recompute runs in the scratch copy /home/jin/v4i2/ outside the repository).

Run with the WSL pypsa-earth python:  PYTHONHASHSEED=0 /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/i2_<item>.py
Outputs go to the I2 delivery folder (work/p1_v4_w07_20261106/I2/), written with LF line endings.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

I2 = Path(__file__).resolve().parents[1]
TABLES = I2 / "tables"
EVID = I2 / "evidence"
FIGS = I2 / "figures"
W07 = I2.parent
REPO = Path("/home/jin/wt_v4_i2")                     # branch codex/v4-i2-20261106 (07e08f38 + merges of the nine W07 / I1 branches)
SP = REPO / "scripts_project"
SRC = REPO / "research_inputs/assembly_v1/sources"
DEMAND = REPO / "research_inputs/demand_v5"
IND_V3 = REPO / "research_inputs/industry_v3"
BIO = REPO / "research_inputs/biomass_v5"
SCRATCH = Path("/home/jin/v4i2")                      # scratch copies (instruction section 7)
S2D = REPO / "research/06_scope_redesign/p1_v4_data_20261105"   # S0 / S1 / S2 deliverables as committed (read only)
S2W = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_data_20261105")   # downloads / evidence of S0-S2 (not in git; read only)
W11 = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_ncv_20261106")
G = {k: W07 / k for k in ("G0", "G1", "G2", "G3", "G4", "G5", "W12", "I1")}
PY = "/home/jin/miniforge3/envs/pypsa-earth/bin/python"
ENV = {"PYTHONHASHSEED": "0", "PATH": "/usr/bin:/bin"}

ASEAN = ["BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN"]
ASEAN10 = [c for c in ASEAN if c != "TL"]
SECTORS = ["Industry", "Transport", "Residential", "Commercial", "AgricultureOthers"]
TCARS = ("coal", "oil", "gas", "biomass", "electricity", "hydrogen", "heat", "ammonia", "methanol", "heat_medium_a", "heat_medium_b", "heat_high")
OUTC = ("electricity", "heat", "heat_medium_a", "heat_medium_b", "heat_high", "coal", "oil", "gas", "biomass", "hydrogen", "ammonia", "methanol")
CARS19 = ("coal", "oil", "gas", "biomass", "electricity")
FUELS = ("coal", "oil", "gas", "biomass")
FOSSIL = ("coal", "oil", "gas")
COLMAP = {"electricity": "elec", "heat": "heat_lt150", "heat_medium_a": "heat_150_200", "heat_medium_b": "heat_200_400", "heat_high": "heat_gt400",
          "oil": "oil", "gas": "gas", "coal": "coal", "biomass": "biomass", "hydrogen": "H2", "ammonia": "ammonia", "methanol": "methanol"}

if str(SP) not in sys.path:
    sys.path.insert(0, str(SP))


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def write_csv(rows: list[dict], path: Path, cols: list[str] | None = None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if cols is None:
        cols = []
        for r in rows:
            for k in r:
                if k not in cols:
                    cols.append(k)
    with open(path, "w", newline="\n", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n", extrasaction="raise")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if r.get(k) is None else (f"{r[k]:.9g}" if isinstance(r.get(k), float) else r.get(k))) for k in cols})
    return path


def write_json(obj, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="\n", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False, sort_keys=False, default=float)
        f.write("\n")
    return path


class Evidence:
    """One evidence list per item; every number carries status (EXACT / VERIFIED / INFERENCE / PROPOSED) and data grade (A-E)."""

    def __init__(self, item: str):
        self.item = item
        self.rows: list[dict] = []

    def add(self, key: str, value, unit: str, status: str, grade: str, source: str, locator: str = "", note: str = "") -> None:
        assert status in {"EXACT", "VERIFIED", "INFERENCE", "PROPOSED"}, status
        assert grade in {"A", "B", "C", "D", "E", "-"}, grade
        if isinstance(value, float):
            value = round(value, 9)
        self.rows.append(dict(id=f"{self.item}.{key}", value=value, unit=unit, status=status, grade=grade, source=source, locator=locator, note=note))

    def write(self) -> Path:
        ids = [r["id"] for r in self.rows]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate evidence ids: " + str(sorted({i for i in ids if ids.count(i) > 1})[:5]))
        return write_json(dict(item=self.item, n=len(self.rows), entries=self.rows), EVID / f"{self.item}.json")
