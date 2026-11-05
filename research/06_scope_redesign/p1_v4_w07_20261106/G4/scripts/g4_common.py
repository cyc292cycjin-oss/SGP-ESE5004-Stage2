"""G4 (V4 W07, section B-G4: MM, KH, LA, BN, TL) shared helpers.

Paths, readers (UNdata export used by the model, the SDMX responses saved by g4_sdmx.py, FAOSTAT, GEM GIPT), the FAOSTAT base-year rule
('last year with new information', S2), the growth rule R2, the evidence list, and the scratch copy of the repository data chain OUTSIDE
the repository (/home/jin/v4w07_g4/chain). Several helpers are copies of S2 (work/p1_v4_data_20261105/scripts/v4s2_common.py) and W11
(work/p1_v4_ncv_20261106/scripts/v4ncv_chain.py) code, kept here so that G4 does not import from another session's worktree.

Chain edits (scratch copy only; the repository worktree /home/jin/wt_v4_g4 is never written):
  * NCV (decision 207, W11 section 4.2 item 5 order): the industry coal row of the ATS anchor table gets base_2019 + delta and
    value_2050 = base x multiplier_total (growth reading I, 'multiplier unchanged'); the coal cells of industry_cache.json are multiplied by
    new / v3 energy of the same UNSD rows (only within-carrier shares are read from the cache, s3_0_industry.py:158).
  * moves (S2 rule): an energy amount d leaves sub19[sub][carrier]: cache cell lowered by d x sum(cache) / e19 and e19 by d (current values).
  * cement correction (ii): one scratch-only line of s3_0_industry.py reads the 2019 cement tonnes for the grinding electricity from the
    environment variable G4_CEM_EL_T19_<cc>; without it the line is identical in effect (checked by the reproduction).
  * BN cement (iii): the BN 2.A.1 row of the EDGAR source in the scratch copy is set to 0 (no clinker kiln in BN).
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

G4 = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w07_20261106/G4")
S2W = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_data_20261105")        # S0 / S1 / S2 deliveries (read only)
NCVW = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_ncv_20261106")        # W11 delivery (read only)
INTAKE = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p2_data_intake")
REPO = Path("/home/jin/wt_v4_g4")                                              # G4 worktree (read only here)
MAIN = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model")    # regions_onshore.geojson (as S2)
CHAIN = Path("/home/jin/v4w07_g4/chain")
UNSD_DIR = Path("/home/jin/research/SGP_ESE5004_Stage2/pypsa-asean/data/demand/unsd/data")
C4 = ["MM", "KH", "LA", "BN"]
C5 = C4 + ["TL"]
NAME = {"MM": "Myanmar", "KH": "Cambodia", "LA": "Lao People's Dem. Rep.", "BN": "Brunei Darussalam", "TL": "Timor-Leste"}
ISO_UN = {v: k for k, v in NAME.items()}
FAO_AREA = {"MM": "Myanmar", "KH": "Cambodia", "LA": "Lao People's Democratic Republic", "BN": "Brunei Darussalam", "TL": "Timor-Leste"}
SUMMARY = "INDUSTRY_2050_SUMMARY_aeo8_ats_anchor_OTHER_USEFUL_HEAT_BANDS.csv"
CACHE_REL = "research_inputs/assembly_v1/sources/industry_cache.json"
ATS_REL = "research_inputs/demand_v5/DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv"
S30_REL = "scripts_project/s3_0_industry.py"
EDGAR_REL = "research_inputs/registry_v5/sources/EDGAR2025_IPPU_FUGITIVE_WASTE_ASEAN11_2019.csv"
S3_OUT = ["INDUSTRY_2050_SUMMARY_aeo8_ats_anchor.csv", SUMMARY, "INDUSTRY_2050_OTHER_BUCKET.csv", "INDUSTRY_2050_PYPSA_EUR_aeo8_ats_anchor.csv"]
OUTC = ("electricity", "heat", "heat_medium_a", "heat_medium_b", "heat_high", "coal", "oil", "gas", "biomass", "hydrogen", "ammonia", "methanol")
OUT_LABEL = {"electricity": "elec", "heat": "heat_lt150", "heat_medium_a": "heat_150_200", "heat_medium_b": "heat_200_400", "heat_high": "heat_gt400",
             "oil": "oil", "gas": "gas", "coal": "coal", "biomass": "biomass", "hydrogen": "H2", "ammonia": "ammonia", "methanol": "methanol"}
CARS19 = ("coal", "oil", "gas", "biomass", "electricity")
FUELS = ("coal", "oil", "gas", "biomass")
ELASTICITY = 0.5
FLAG_GRADE = {"A": "A", "X": "B", "E": "C", "I": "C", "M": "E"}
PATCH_OLD = 'el19 = float(ratios.at["elec", "Cement"]) * cem_t19'
PATCH_NEW = ('el19 = float(ratios.at["elec", "Cement"]) * float(__import__("os").environ.get(f"G4_CEM_EL_T19_{c}", cem_t19))'
             '   # V4 W07 G4 scratch-only patch (cement correction ii)')
GJ_PER_MWH = 3.6
FAO_FILES = {"FO": ("FAOSTAT_data_en_11-6-2026 (2).csv", "de61d07f1801c3f013c0f506c5da57a3c21ceda5cb53a5d094b1fa3bd8f5e027"),
             "QCL": ("FAOSTAT_data_en_11-6-2026.csv", "f340a9468f09d8a2325efaf7918e8eb2ea06031c9a0620ac13e8bc793d8b32a8")}
PY = "/home/jin/miniforge3/envs/pypsa-earth/bin/python"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


# ------------------------------------------------------------------ statistics readers ------------------------------------------------------
def unsd_export(isos=C5) -> pd.DataFrame:
    """UNdata export 2025-05-02 used by the repository chain (pypsa-asean data/demand/unsd/data), rows of the given countries, all years."""
    d = pd.concat((pd.read_csv(f, sep=";", dtype=str, on_bad_lines="skip") for f in sorted(glob.glob(str(UNSD_DIR / "*.txt")))), ignore_index=True)
    d = d[d["Country or Area"].isin([NAME[i] for i in isos])].copy()
    d["iso"] = d["Country or Area"].map(ISO_UN)
    sp = d["Commodity - Transaction"].str.split(" - ", n=1, expand=True)
    d["commodity"], d["transaction"] = sp[0].str.strip(), sp[1].fillna("").str.strip()
    d["q"] = pd.to_numeric(d.Quantity, errors="coerce"); d["year"] = pd.to_numeric(d.Year, errors="coerce")
    d["footnote"] = d["Quantity Footnotes"].fillna("")
    return d


def sdmx() -> pd.DataFrame:
    return pd.read_csv(G4 / "evidence/SDMX_COAL_BIOMASS_2015_2022.csv", dtype={"commodity_code": str, "transaction_code": str})


def conv_factors() -> dict:
    """pypsa-asean get_conv_factors (TWh per thousand t, fuelwood per thousand m3), via the S1 reader (read only)."""
    sys.path.insert(0, str(S2W / "scripts"))
    import v4s1_common as c1   # noqa: E402
    return c1.conv_factors()


def fao(domain: str) -> pd.DataFrame:
    name, sha = FAO_FILES[domain]
    p = S2W / "downloads/15_faostat" / name
    if sha256(p) != sha:
        raise ValueError(f"{name}: SHA256 differs from the S2 registration")
    d = pd.read_csv(p, dtype=str, encoding="utf-8-sig")
    d["year"] = d.Year.astype(int); d["value"] = pd.to_numeric(d.Value, errors="coerce"); d["flag"] = d.Flag.fillna("")
    return d


def fao_series(d: pd.DataFrame, cc: str, item: str, element: str = "Production") -> pd.DataFrame:
    s = d[(d.Area == FAO_AREA[cc]) & (d.Item == item) & (d.Element == element)].sort_values("year")
    if s.year.duplicated().any():
        raise ValueError(f"{cc} {item}: duplicated years")
    return s[["year", "value", "flag", "Unit"]].reset_index(drop=True)


def latest_actual(s: pd.DataFrame) -> dict:
    """S2 rule: base year = last year whose value differs from the year before (later equal values flagged E / I are carry-forwards);
    a series that never changes returns its first year with grade D."""
    s = s.dropna(subset=["value"]).reset_index(drop=True)
    yb = int(s.year.iloc[0]); i_b = 0
    for i in range(1, len(s)):
        if s.value.iloc[i] != s.value.iloc[i - 1]:
            yb = int(s.year.iloc[i]); i_b = i
    grade = FLAG_GRADE.get(str(s.flag.iloc[i_b]), "C") if (i_b > 0 or len(s) == 1) else "D"
    return dict(base_year=yb, value=float(s.value.iloc[i_b]), flag=str(s.flag.iloc[i_b]), grade=grade,
                carried_forward_years=[int(y) for y in s.year.iloc[i_b + 1:]], latest_year=int(s.year.iloc[-1]),
                latest_value=float(s.value.iloc[-1]), latest_flag=str(s.flag.iloc[-1]))


def gipt() -> pd.DataFrame:
    g = pd.read_csv(REPO / "research_inputs/registry_v5/sources/GEM_GIPT_2026-09_ASEAN11.csv", low_memory=False)
    g["sy"] = pd.to_numeric(g["Start year"], errors="coerce"); g["ry"] = pd.to_numeric(g["Retired year"], errors="coerce")
    g["op19"] = g.Status.isin(["operating", "retired", "mothballed"]) & (g.sy <= 2019) & ~(g.ry <= 2019)   # S1 / S2 operating rule
    return g


# ------------------------------------------------------------------ growth and ratios -------------------------------------------------------
def rule() -> pd.DataFrame:
    return pd.read_csv(REPO / "research_inputs/demand_v5/INDUSTRY_OUTPUT_2050_M08B.csv").set_index("country")


def growth(y_b: int, cc: str, y_t: int = 2050) -> float:
    """S0 R2 / R3: q(y_t) = q(y_b) x G^((y_t - y_b) / 28 x 0.5), G = AEO8 table D.2 real GDP 2050 / 2022 (v3 ammonia / non-ferrous rule)."""
    return float(rule().at[cc, "gdp_growth_2022_2050"]) ** ((y_t - y_b) / 28.0 * ELASTICITY)


def ratios_2050() -> pd.DataFrame:
    return pd.read_csv(REPO / "research_inputs/registry_v5/INDUSTRY_SECTOR_RATIOS_PYPSA_EUR_2050.csv", index_col=0)


def ratios_today() -> pd.DataFrame:
    return pd.read_csv(REPO / "research_inputs/registry_v5/INDUSTRY_SECTOR_RATIOS_TODAY_EU27_2019.csv").set_index("sector")


RATIO_TO_OUT = {"elec": "electricity", "coal": "coal", "coke": "coal", "biomass": "biomass", "methane": "gas", "hydrogen": "hydrogen", "heat": "heat",
                "ammonia": "ammonia", "methanol": "methanol"}   # = s3_0_industry.RATIO_TO_OUT (naphtha excluded: feedstock)


def vec2050(sector: str, t: float) -> dict:
    r = ratios_2050(); out = {k: 0.0 for k in OUTC}
    for k, oc in RATIO_TO_OUT.items():
        out[oc] += float(r.at[k, sector]) * t
    return out


def today_vec(sector: str, t: float) -> dict:
    """S1 / S2 convention for 2019 deductions: JRC-IDEES EU27 2019 today total (MWh/t) with the carrier structure of the PyPSA-Eur ratio column."""
    cars = ("elec", "coal", "coke", "methane", "biomass", "hydrogen", "heat")
    col = ratios_2050()[sector]; tf = float(sum(col[c] for c in cars)); T = float(ratios_today().at[sector, "today_total_mwh_per_t"])
    return {c: float(col[c]) / tf * T * t for c in cars}


# ------------------------------------------------------------------ evidence ----------------------------------------------------------------
class Ev:
    """Flat evidence list: every number with unit, source, status (EXACT / VERIFIED / INFERENCE / PROPOSED) and data grade (A-E or '-')."""

    def __init__(self, section: str):
        self.section, self.rows, self.extra = section, [], {}

    def put(self, key, value, unit, source, status, grade):
        if isinstance(value, (np.floating, np.integer)):
            value = float(value)
        if isinstance(value, float):
            value = round(value, 9)
        self.rows.append(dict(key=f"{self.section}.{key}", value=value, unit=unit, source=source, status=status, grade=grade))

    def write(self, p: Path):
        keys = [r["key"] for r in self.rows]
        if len(keys) != len(set(keys)):
            raise ValueError(f"duplicated evidence keys: {sorted(k for k in set(keys) if keys.count(k) > 1)[:5]}")
        jdump(dict(section=self.section, numbers=self.rows, extra=self.extra), p)


def jdump(obj, p: Path):
    p.write_text(json.dumps(obj, indent=1, ensure_ascii=False, default=lambda x: float(x) if isinstance(x, (np.floating, np.integer)) else str(x)) + "\n", encoding="utf-8")


# ------------------------------------------------------------------ scratch data chain --------------------------------------------------------
class Chain:
    def __init__(self, repo: Path = REPO, chain: Path = CHAIN):
        self.repo, self.chain = repo, chain
        self.orig = {rel: (repo / rel).read_bytes() for rel in (CACHE_REL, ATS_REL, S30_REL, EDGAR_REL)}
        self.patched = False

    def copy(self):
        if self.chain.exists():
            shutil.rmtree(self.chain)
        self.chain.mkdir(parents=True)
        shutil.copytree(self.repo / "research_inputs", self.chain / "research_inputs")
        shutil.copytree(self.repo / "scripts_project", self.chain / "scripts_project", ignore=shutil.ignore_patterns("__pycache__", "retired"))
        (self.chain / "scripts_project/retired").mkdir(exist_ok=True)

    def patch(self):
        src = self.orig[S30_REL].decode()
        if src.count(PATCH_OLD) != 1:
            raise ValueError("cement electricity line not found exactly once")
        (self.chain / S30_REL).write_text(src.replace(PATCH_OLD, PATCH_NEW)); self.patched = True

    def restore(self):
        for rel in (CACHE_REL, ATS_REL, EDGAR_REL):
            (self.chain / rel).write_bytes(self.orig[rel])

    def run(self, ncv: dict | None = None, moves: dict | None = None, cem_t19: dict | None = None, edgar_zero: list | None = None):
        """ncv: {cc: {'ats': {carrier: delta_mwh}, 'cache': {(carrier, sub): ratio}}}; moves: {cc: [(sub, carrier, d_mwh)]};
        cem_t19: {cc: t}; edgar_zero: [cc]. Returns (summary rows, other-bucket rows, PyPSA-Eur sub-sector rows, gaps)."""
        self.restore()
        cache = json.loads(self.orig[CACHE_REL])
        d = pd.read_csv(self.chain / ATS_REL, keep_default_na=False, dtype=str)
        recs = {(r["country"], r["carrier"]): r for r in cache["records"]}

        def ats_mask(cc, car):
            m = (d.country == cc) & (d.sector == "Industry") & (d.carrier == car)
            if m.sum() != 1:
                raise ValueError(f"{cc} Industry {car}: {m.sum()} rows")
            return m

        def set_base(m, b):
            d.loc[m, "base_2019_mwh"] = repr(b); d.loc[m, "value_2050_mwh"] = repr(b * float(d.loc[m, "multiplier_total"].iloc[0]))

        for cc, e in (ncv or {}).items():
            for (car, sub), f in e.get("cache", {}).items():
                r = recs[(cc, car)]; r[sub] = repr(float(r[sub]) * f)
            for car, dv in e.get("ats", {}).items():
                m = ats_mask(cc, car); set_base(m, float(d.loc[m, "base_2019_mwh"].iloc[0]) + dv)
        for cc, mv in (moves or {}).items():
            by_car = {}
            for sub, car, dv in mv:
                if abs(dv) > 0:
                    by_car.setdefault(car, {}); by_car[car][sub] = by_car[car].get(sub, 0.0) + dv
            for car, subs in by_car.items():
                r = recs[(cc, car)]
                tot = sum(float(v) for k, v in r.items() if k not in ("country", "carrier"))
                m = ats_mask(cc, car); e19 = float(d.loc[m, "base_2019_mwh"].iloc[0])
                for sub, dv in subs.items():
                    x = dv * tot / e19
                    if float(r.get(sub, 0.0)) - x < -1e-6:
                        raise ValueError(f"{cc} {sub} {car}: move {dv} MWh exceeds the cache cell {r.get(sub)}")
                    r[sub] = repr(float(r.get(sub, 0.0)) - x)
                set_base(m, e19 - sum(subs.values()))
        (self.chain / CACHE_REL).write_text(json.dumps(cache))
        d.to_csv(self.chain / ATS_REL, index=False)
        if edgar_zero:
            ed = pd.read_csv(self.chain / EDGAR_REL, dtype=str, keep_default_na=False)
            m = ed.iso.isin(edgar_zero) & (ed.ipcc_code_2006_for_standard_report == "2.A.1")
            ed.loc[m, "kt_CO2_2019"] = "0.0"
            ed.to_csv(self.chain / EDGAR_REL, index=False)
        env = {"PYTHONHASHSEED": "0", "PATH": "/usr/bin:/bin"}
        if cem_t19:
            if not self.patched:
                raise ValueError("cement correction needs the scratch patch")
            env.update({f"G4_CEM_EL_T19_{k}": repr(float(v)) for k, v in cem_t19.items()})
        r = subprocess.run([sys.executable, "s3_0_industry.py"], cwd=self.chain / "scripts_project", capture_output=True, text=True, env=env)
        if r.returncode:
            raise RuntimeError(r.stderr[-3000:])
        dd = self.chain / "research_inputs/demand_v5"
        s = pd.read_csv(dd / SUMMARY).set_index("country")
        ob = pd.read_csv(dd / "INDUSTRY_2050_OTHER_BUCKET.csv"); ob = ob[ob["mode"] == "aeo8_ats_anchor"].set_index("country")
        pz = pd.read_csv(dd / "INDUSTRY_2050_PYPSA_EUR_aeo8_ats_anchor.csv")
        gp = pd.read_csv(dd / "INDUSTRY_2050_GAPS.csv"); gp = gp[gp["mode"] == "aeo8_ats_anchor"]
        return s, ob, pz, gp


def import_v3(repo: Path = REPO):
    sys.path.insert(0, str(repo / "scripts_project"))
    import v3_industry as v3   # noqa: E402  (ROOT = repository worktree; read only)
    return v3
