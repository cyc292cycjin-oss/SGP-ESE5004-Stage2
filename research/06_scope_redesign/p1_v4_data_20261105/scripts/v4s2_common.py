"""V4 S2 shared helpers: paths, FAOSTAT readers with flags and the 'latest actual year' rule, the growth rule R2, and the scratch copy of the
repository data chain (outside the repository) with input edits, one documented scratch-only patch (cement correction ii) and the v3 conservation layer.

Nothing here writes into the repository worktree. The scratch copy is /home/jin/v4s2/chain (research_inputs + scripts_project of the worktree).

Chain edits (all in the scratch copy only):
  * cache / D1 base: an energy amount d (MWh, per carrier) moved out of one UNSD sub-sector of ID ('other' or 'chemical and petrochemical').
    s3_0_industry.py splits the D1 2019 base e19 of a carrier by the cache shares, sub19[s] = e19 * cache[s] / sum(cache). For coal, biomass and
    electricity the cache sum equals e19; for gas and oil it does not (ID: 133.52 vs 120.17 TWh, 95.21 vs 90.89 TWh). The cache cell is therefore
    lowered by x = d * sum(cache) / e19 and e19 by d, which lowers sub19 of that sub-sector by exactly d and leaves every other sub-sector unchanged.
  * electricity added (captive option b): the same rule with a negative d.
  * cement correction (ii): one line of the scratch s3_0_industry.py reads the 2019 cement tonnes used for the grinding electricity from an
    environment variable (V4S2_CEM_EL_T19_<country>); without the variable the line is identical in effect, which the reproduction check verifies.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

WORK = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_data_20261105")
REPO = Path("/home/jin/wt_v4_data")
CHAIN = Path("/home/jin/v4s2/chain")
MAIN = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model")   # regions_onshore.geojson (as in S1)
FAO_DIR = WORK / "downloads/15_faostat"
FAO_FILES = {"FO": ("FAOSTAT_data_en_11-6-2026 (2).csv", "de61d07f1801c3f013c0f506c5da57a3c21ceda5cb53a5d094b1fa3bd8f5e027"),
             "QCL": ("FAOSTAT_data_en_11-6-2026.csv", "f340a9468f09d8a2325efaf7918e8eb2ea06031c9a0620ac13e8bc793d8b32a8")}
FLAG_GRADE = {"A": "A", "X": "B", "E": "C", "I": "C", "M": "E"}   # FAO flag -> data grade (A official, X external organisation, E estimate, I imputed)
FLAG_TEXT = {"A": "official value", "X": "value from external organisation", "E": "estimated value", "I": "imputed by a receiving agency", "M": "missing"}
SUMMARY = "INDUSTRY_2050_SUMMARY_aeo8_ats_anchor_OTHER_USEFUL_HEAT_BANDS.csv"
OUTC = ("electricity", "heat", "heat_medium_a", "heat_medium_b", "heat_high", "coal", "oil", "gas", "biomass", "hydrogen", "ammonia", "methanol")
CARS19 = ("coal", "oil", "gas", "biomass", "electricity")
FUELS = ("coal", "oil", "gas", "biomass")
ELASTICITY = 0.5
PATCH_OLD = 'el19 = float(ratios.at["elec", "Cement"]) * cem_t19'
PATCH_NEW = 'el19 = float(ratios.at["elec", "Cement"]) * float(__import__("os").environ.get(f"V4S2_CEM_EL_T19_{c}", cem_t19))   # V4 S2 scratch-only patch (cement correction ii)'


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


# ---------------------------------------------------------------- FAOSTAT -------------------------------------------------------------------
def fao(domain: str) -> pd.DataFrame:
    name, sha = FAO_FILES[domain]
    p = FAO_DIR / name
    if sha256(p) != sha:
        raise ValueError(f"{name}: SHA256 differs from the instruction")
    d = pd.read_csv(p, dtype=str, encoding="utf-8-sig")
    d["year"] = d.Year.astype(int)
    d["value"] = pd.to_numeric(d.Value, errors="coerce")
    d["flag"] = d.Flag.fillna("")
    return d


def series(d: pd.DataFrame, area: str, item: str, element: str = "Production") -> pd.DataFrame:
    s = d[(d.Area == area) & (d.Item == item) & (d.Element == element)].sort_values("year")
    if s.year.duplicated().any():
        raise ValueError(f"{area} {item}: duplicated years")
    return s[["year", "value", "flag", "Unit"]].reset_index(drop=True)


def value(d, area, item, year, element="Production"):
    s = series(d, area, item, element)
    z = s[s.year == year]
    if len(z) != 1:
        raise KeyError((area, item, year, element))
    return float(z.value.iloc[0]), str(z.flag.iloc[0])


def latest_actual(s: pd.DataFrame) -> dict:
    """Last year that carries new information: the last year whose value differs from the year before (a later run of equal values flagged
    E / I is a carry-forward). A series that never changes returns its first year. Also returns the literal latest year."""
    s = s.dropna(subset=["value"]).reset_index(drop=True)
    yb = int(s.year.iloc[0]); i_b = 0
    for i in range(1, len(s)):
        if s.value.iloc[i] != s.value.iloc[i - 1]:
            yb = int(s.year.iloc[i]); i_b = i
    carry = [int(y) for y in s.year.iloc[i_b + 1:]]
    grade = FLAG_GRADE.get(str(s.flag.iloc[i_b]), "C") if (i_b > 0 or len(s) == 1) else "D"   # a series that never changes carries no dated information
    return dict(base_year=yb, value=float(s.value.iloc[i_b]), flag=str(s.flag.iloc[i_b]), grade=grade,
                carried_forward_years=carry, latest_year=int(s.year.iloc[-1]), latest_value=float(s.value.iloc[-1]), latest_flag=str(s.flag.iloc[-1]))


# ---------------------------------------------------------------- growth rule ---------------------------------------------------------------
def gdp_growth(country: str = "ID") -> float:
    rule = pd.read_csv(REPO / "research_inputs/demand_v5/INDUSTRY_OUTPUT_2050_M08B.csv").set_index("country")
    return float(rule.at[country, "gdp_growth_2022_2050"])


def growth(y_b: int, country: str = "ID") -> float:
    """S0 R2: q(2050) = q(y_b) x G^((2050 - y_b) / 28 x 0.5), G = AEO8 table D.2 real GDP 2050 / 2022 (same as the v3 ammonia / non-ferrous rule)."""
    return gdp_growth(country) ** ((2050 - y_b) / 28.0 * ELASTICITY)


def ratios_2050() -> pd.DataFrame:
    return pd.read_csv(REPO / "research_inputs/registry_v5/INDUSTRY_SECTOR_RATIOS_PYPSA_EUR_2050.csv", index_col=0)


def ratios_today() -> pd.DataFrame:
    return pd.read_csv(REPO / "research_inputs/registry_v5/INDUSTRY_SECTOR_RATIOS_TODAY_EU27_2019.csv").set_index("sector")


RATIO_TO_OUT = {"elec": "electricity", "coal": "coal", "coke": "coal", "biomass": "biomass", "methane": "gas", "hydrogen": "hydrogen", "heat": "heat",
                "ammonia": "ammonia", "methanol": "methanol"}   # = s3_0_industry.RATIO_TO_OUT (naphtha excluded: feedstock)


def vec2050(sector: str, t: float) -> dict:
    """PyPSA-Eur 2050 ratio column x tonnes -> {v3 carrier: MWh} (naphtha excluded, as in s3_0_industry / v3_industry)."""
    r = ratios_2050(); out = {k: 0.0 for k in OUTC}
    for k, oc in RATIO_TO_OUT.items():
        out[oc] += float(r.at[k, sector]) * t
    return out


# ---------------------------------------------------------------- scratch data chain --------------------------------------------------------
CACHE_REL = "research_inputs/assembly_v1/sources/industry_cache.json"
D1_REL = "research_inputs/demand_v5/DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv"
S30_REL = "scripts_project/s3_0_industry.py"


class Chain:
    def __init__(self, repo: Path = REPO, chain: Path = CHAIN):
        self.repo, self.chain = repo, chain
        self.orig = {"cache": (repo / CACHE_REL).read_bytes(), "d1": (repo / D1_REL).read_bytes(), "s30": (repo / S30_REL).read_bytes()}
        self.patched = False

    def copy(self):
        if self.chain.exists():
            shutil.rmtree(self.chain)
        self.chain.mkdir(parents=True)
        shutil.copytree(self.repo / "research_inputs", self.chain / "research_inputs")
        shutil.copytree(self.repo / "scripts_project", self.chain / "scripts_project", ignore=shutil.ignore_patterns("__pycache__", "retired"))
        (self.chain / "scripts_project/retired").mkdir(exist_ok=True)

    def patch(self):
        """Scratch-only patch for cement correction (ii); identical in effect without the environment variable."""
        src = self.orig["s30"].decode()
        if src.count(PATCH_OLD) != 1:
            raise ValueError("cement electricity line not found exactly once")
        (self.chain / S30_REL).write_text(src.replace(PATCH_OLD, PATCH_NEW))
        self.patched = True

    def unpatch(self):
        (self.chain / S30_REL).write_bytes(self.orig["s30"]); self.patched = False

    def restore(self):
        (self.chain / CACHE_REL).write_bytes(self.orig["cache"]); (self.chain / D1_REL).write_bytes(self.orig["d1"])

    def run(self, moves: list | None = None, cem_el_t19: dict | None = None, country: str = "ID"):
        """moves: list of (subsector, carrier, d_mwh): d leaves sub19[subsector][carrier] of `country` (negative d adds energy). Returns the
        heat-band summary row, the other-bucket row and the s3_0 sub-sector rows of the country."""
        self.restore()
        moves = [m for m in (moves or []) if abs(m[2]) > 0]
        if moves:
            cache = json.loads(self.orig["cache"])
            d = pd.read_csv(self.chain / D1_REL, keep_default_na=False, dtype=str)
            recs = {r["carrier"]: r for r in cache["records"] if r["country"] == country}
            by_car = {}
            for sub, car, dv in moves:
                by_car.setdefault(car, {}); by_car[car][sub] = by_car[car].get(sub, 0.0) + dv
            for car, subs in by_car.items():
                r = recs[car]
                tot = sum(float(v) for k, v in r.items() if k not in ("country", "carrier"))   # original cache sum of the carrier
                m = (d.country == country) & (d.sector == "Industry") & (d.carrier == car)
                if m.sum() != 1:
                    raise ValueError(f"{country} Industry {car}: {m.sum()} rows")
                e19 = float(d.loc[m, "base_2019_mwh"].iloc[0])   # original D1 base of the carrier
                for sub, dv in subs.items():
                    x = dv * tot / e19   # lowers sub19[sub][car] by exactly dv and leaves the other sub-sectors unchanged
                    if float(r[sub]) - x < -1e-6:
                        raise ValueError(f"{country} {sub} {car}: move {dv} MWh exceeds the cache cell {r[sub]}")
                    r[sub] = repr(float(r[sub]) - x)
                b = e19 - sum(subs.values())
                d.loc[m, "base_2019_mwh"] = repr(b)
                d.loc[m, "value_2050_mwh"] = repr(b * float(d.loc[m, "multiplier_total"].iloc[0]))
            (self.chain / CACHE_REL).write_text(json.dumps(cache))
            d.to_csv(self.chain / D1_REL, index=False)
        env = {"PYTHONHASHSEED": "0", "PATH": "/usr/bin:/bin"}
        if cem_el_t19:
            if not self.patched:
                raise ValueError("cement correction needs the scratch patch")
            env.update({f"V4S2_CEM_EL_T19_{k}": repr(float(v)) for k, v in cem_el_t19.items()})
        r = subprocess.run([sys.executable, "s3_0_industry.py"], cwd=self.chain / "scripts_project", capture_output=True, text=True, env=env)
        if r.returncode:
            raise RuntimeError(r.stderr[-3000:])
        dd = self.chain / "research_inputs/demand_v5"
        row = pd.read_csv(dd / SUMMARY).set_index("country").loc[country]
        ob = pd.read_csv(dd / "INDUSTRY_2050_OTHER_BUCKET.csv")
        ob = ob[(ob["mode"] == "aeo8_ats_anchor") & (ob.country == country)].iloc[0]
        pz = pd.read_csv(dd / "INDUSTRY_2050_PYPSA_EUR_aeo8_ats_anchor.csv")
        pz = pz[pz.country == country]
        return row, ob, pz


def v3_layer(v3, row, fut, nf: dict, extra: dict | None = None) -> dict:
    """v3 conservation (D163-6 a) on one chain row: T = route total of the row + new explicit sub-sectors (pulp / paper, ethylene) that the chain
    does not contain; explicit = steel + cement + ammonia + dispersed + non-ferrous + new; Other = T - explicit, carriers scaled uniformly."""
    extra = extra or {}
    T_chain = float(sum(row[v3.col(x)] for x in v3.CARRIERS))
    parts = v3.decompose(row, fut); parts.update(nf); parts.update(extra)
    T = T_chain + sum(sum(v.values()) for v in extra.values())
    expl = sum(sum(v.values()) for k, v in parts.items() if k != "other")
    so = sum(parts["other"].values()); f = (T - expl) / so
    other = {k: v * f for k, v in parts["other"].items()}
    by_sub = {k: sum(v.values()) for k, v in parts.items() if k != "other"}
    return dict(T=T, T_chain=T_chain, other=other, other_total=sum(other.values()), scale=f, explicit=expl, by_sub=by_sub,
                explicit_carriers={k: dict(v) for k, v in parts.items() if k != "other"})


def import_v3(repo: Path = REPO):
    sys.path.insert(0, str(repo / "scripts_project"))
    import v3_industry as v3   # noqa: E402  (ROOT = repository worktree; read only)
    return v3


class Ev:
    """Flat evidence list: every number with unit, source, status (EXACT / VERIFIED / INFERENCE / PROPOSED) and data grade (A-E)."""

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
