"""I1 shared helpers (v4 integration step 1; read-only for the repository: nothing is solved, no model code / config / network /
registry / T_v2 in the repository is written).

Run with the WSL pypsa-earth python:  PYTHONHASHSEED=0 /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/i1_<item>.py
Outputs go to the I1 delivery folder (BASE2019_SDMX/, tables/, evidence/), written with LF line endings.
Scratch copies of the data chain live OUTSIDE the repository in /home/jin/v4i1/.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

I1 = Path(__file__).resolve().parents[1]
TABLES = I1 / "tables"
EVID = I1 / "evidence"
BASE_OUT = I1 / "BASE2019_SDMX"
REPO = Path("/home/jin/wt_v4_i1")          # branch codex/v4-i1-20261106 from 07e08f38 (= codex/v4-data-20261105 head)
SP = REPO / "scripts_project"
SRC = REPO / "research_inputs/assembly_v1/sources"
DEMAND = REPO / "research_inputs/demand_v5"
UPSTREAM = Path("/home/jin/research/SGP_ESE5004_Stage2/pypsa-asean")
UNSD_DIR = UPSTREAM / "data" / "demand" / "unsd" / "data"
W07 = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w07_20261106")
W12 = W07 / "W12"
SDMX_DIR = W12 / "sdmx"                     # W12 raw SDMX responses (11 countries, 2019, all commodities / transactions); read only
W11 = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_ncv_20261106")
SCRATCH = Path("/home/jin/v4i1")

ASEAN = ["BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN"]
ASEAN10 = [c for c in ASEAN if c != "TL"]
AREAS = {"BN": "096", "KH": "116", "ID": "360", "LA": "418", "MY": "458", "MM": "104", "PH": "608", "SG": "702", "TH": "764", "TL": "626", "VN": "704"}
UNSD_NAMES = {"Brunei Darussalam": "BN", "Cambodia": "KH", "Indonesia": "ID", "Lao People's Dem. Rep.": "LA", "Malaysia": "MY",
              "Myanmar": "MM", "Philippines": "PH", "Singapore": "SG", "Thailand": "TH", "Timor-Leste": "TL", "Viet Nam": "VN"}
CC_NAME = {v: k for k, v in UNSD_NAMES.items()}

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
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in cols})
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
        assert grade in {"A", "B", "C", "D", "E"}, grade
        self.rows.append(dict(id=f"{self.item}.{key}", value=value, unit=unit, status=status, grade=grade, source=source, locator=locator, note=note))

    def write(self) -> Path:
        return write_json(dict(item=self.item, n=len(self.rows), entries=self.rows), EVID / f"{self.item}.json")
