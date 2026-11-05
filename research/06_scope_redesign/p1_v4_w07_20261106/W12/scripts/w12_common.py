"""W12 shared helpers (read-only verification of network-layer issues; nothing is solved, the repository is not written).

Run with the WSL pypsa-earth python:  PYTHONHASHSEED=0 /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/w12_<item>.py
All outputs go to the W12 delivery folder (tables/, evidence/), written with LF line endings.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

W12 = Path(__file__).resolve().parents[1]
TABLES = W12 / "tables"
EVID = W12 / "evidence"
REPO = Path("/home/jin/wt_v4_w12")                      # branch codex/v4-w07-w12-20261106 = 07e08f38; code = v3.1 d3b9a3bc outside research/
UPSTREAM = Path("/home/jin/research/SGP_ESE5004_Stage2/pypsa-asean")
UNSD_DIR = UPSTREAM / "data" / "demand" / "unsd" / "data"
D = Path("/mnt/d/ResearchWorkspaces/ASEAN/work")
SCREEN = D / "p1_v3_20261102/cloud_results/final_20261103T063207Z/full_unpacked/export"
SUPP07 = D / "p1_v3_20261102/cloud_results/final_20261103T160537Z/full_unpacked/export"
SMOKE31 = Path("/home/jin/v3fix/drill_pkg_13ebce95/runs/smoke56_v31")
HPC31 = D / "p1_v3_20261102/hpc_package_v3_1/networks"
W11 = D / "p1_v4_ncv_20261106"

ASEAN = ["BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN"]
UNSD_NAMES = {"Brunei Darussalam": "BN", "Cambodia": "KH", "Indonesia": "ID", "Lao People's Dem. Rep.": "LA", "Malaysia": "MY",
              "Myanmar": "MM", "Philippines": "PH", "Singapore": "SG", "Thailand": "TH", "Timor-Leste": "TL", "Viet Nam": "VN"}

# solved runs available on this machine (label -> (folder, scenario, resolution, model version))
SOLVED = {
    "S56_F1": (SMOKE31 / "F1", "integrated", "56x3h smoke", "v3.1 (d3b9a3bc code; drill package 13ebce95)"),
    "S56_F2": (SMOKE31 / "F2", "no_new_xb", "56x3h smoke", "v3.1 (d3b9a3bc code; drill package 13ebce95)"),
    "SCR_V1": (SCREEN / "V1", "integrated", "365x24h screening", "v3 (screening 2026-11-03)"),
    "SCR_V2": (SCREEN / "V2", "no_new_xb", "365x24h screening", "v3 (screening 2026-11-03)"),
    "SCR_V3": (SCREEN / "V3", "disconnected", "365x24h screening", "v3 (screening 2026-11-03)"),
    "SCR_V4": (SCREEN / "V4", "integrated bridge 160-162", "365x24h screening", "v3 (screening 2026-11-03)"),
    "SCR_V5": (SCREEN / "V5", "integrated bridge 160-164", "365x24h screening", "v3 (screening 2026-11-03)"),
    "S07_V1": (SUPP07 / "V1", "integrated", "365x24h supplement 07 (dmax)", "v3 (supplement 07 2026-11-04)"),
    "S07_V2": (SUPP07 / "V2", "no_new_xb", "365x24h supplement 07 (dmax)", "v3 (supplement 07 2026-11-04)"),
    "S07_V3": (SUPP07 / "V3", "disconnected", "365x24h supplement 07 (dmax)", "v3 (supplement 07 2026-11-04)"),
}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def solved_nc(folder: Path) -> Path:
    c = sorted(x for x in folder.glob("*_solved.nc"))
    if len(c) != 1:
        raise FileNotFoundError(f"{folder}: {len(c)} solved nc files")
    return c[0]


def write_csv(rows: list[dict], path: Path, cols: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cols = cols or (list(rows[0].keys()) if rows else [])
    with open(path, "w", newline="\n", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n", extrasaction="raise")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in cols})


def write_json(obj, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="\n", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False, sort_keys=False, default=float)
        f.write("\n")


class Evidence:
    """One evidence list per item; every number carries status (EXACT / VERIFIED / INFERENCE / PROPOSED) and grade (A-E)."""

    def __init__(self, item: str):
        self.item = item
        self.rows: list[dict] = []

    def add(self, key: str, value, unit: str, status: str, grade: str, source: str, locator: str = "", note: str = "") -> None:
        assert status in {"EXACT", "VERIFIED", "INFERENCE", "PROPOSED"}, status
        assert grade in {"A", "B", "C", "D", "E"}, grade
        self.rows.append(dict(id=f"{self.item}.{key}", value=value, unit=unit, status=status, grade=grade, source=source, locator=locator, note=note))

    def write(self) -> Path:
        p = EVID / f"{self.item}.json"
        write_json(dict(item=self.item, n=len(self.rows), entries=self.rows), p)
        return p


def nc_meta(ds) -> dict:
    """PyPSA stores n.meta as a JSON string in the netCDF attribute 'meta'."""
    m = ds.attrs.get("meta")
    return json.loads(m) if isinstance(m, str) else (m or {})


def load_unsd_2019() -> "pd.DataFrame":
    import glob

    import pandas as pd
    rows = []
    for f in sorted(glob.glob(str(UNSD_DIR / "UNdata_Export_*.txt"))):
        d = pd.read_csv(f, sep=";", dtype=str, low_memory=False)
        d = d[d["Country or Area"].isin(UNSD_NAMES) & (d["Year"] == "2019")]
        if len(d):
            rows.append(d.assign(file=Path(f).name, sha=sha256(Path(f))))
    u = pd.concat(rows, ignore_index=True)
    u["ISO"] = u["Country or Area"].map(UNSD_NAMES)
    parts = u["Commodity - Transaction"].str.split(" - ", n=1, expand=True)
    u["commodity"] = parts[0].str.strip()
    u["transaction"] = parts[1].str.strip().str.lower()
    u["q"] = u["Quantity"].astype(float)
    return u
