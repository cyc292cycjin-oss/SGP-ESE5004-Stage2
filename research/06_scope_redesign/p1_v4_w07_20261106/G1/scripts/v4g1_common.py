"""V4 W07 G1 (Malaysia) shared helpers: paths, evidence list, FAOSTAT readers, the growth rule R2, PyPSA-Eur ratio vectors and the scratch copy of
the repository data chain (outside the repository) with input edits and the v3 conservation layer.

Adapted from the S2 helpers (work/p1_v4_data_20261105/scripts/v4s2_common.py, read only) with three changes: the repository is this session's
worktree (/home/jin/wt_v4_g1, branch codex/v4-w07-g1-20261106 from codex/v4-data-20261105 07e08f38); the scratch copy is /home/jin/v4w07_g1/chain;
every chain call takes the country (MY). Nothing here writes into the repository worktree.

Chain edits (scratch copy only):
  * move d (MWh, per carrier) out of one UNSD sub-sector of a country: s3_0_industry.py splits the D1 2019 base e19 of a carrier by the cache
    shares, sub19[s] = e19 * cache[s] / sum(cache). The cache cell is lowered by x = d * sum(cache) / e19 and e19 by d, which lowers sub19 of that
    sub-sector by exactly d and leaves the other sub-sectors unchanged (MY gas: cache sum 99.58 vs D1 89.62 TWh, so x != d).
  * a negative d adds energy (captive option b electricity; a higher coal NCV: decision 207 changes the MY non-metallic-minerals hard coal row).
  * D1 value_2050 = new base x multiplier_total (growth mode I, 'ATS multiplier unchanged').
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

G1 = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w07_20261106/G1")
S2W = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_data_20261105")       # S0-S2 deliverables (read only)
W11 = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_ncv_20261106")        # W11 deliverables (read only)
REPO = Path("/home/jin/wt_v4_g1")
CHAIN = Path("/home/jin/v4w07_g1/chain")
MAIN = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model")   # regions_onshore.geojson (as in S1 / S2)
UNSD_DIR = Path("/home/jin/research/SGP_ESE5004_Stage2/pypsa-asean/data/demand/unsd/data")   # UNdata export 2025-05-02 (model source)
NETWORK = Path("/home/jin/v3fix/drill_pkg_13ebce95/networks/integrated_2920_3h_unsolved.nc")   # v3.1 F1 network (read only)
NEB_PDF = Path("/mnt/d/ResearchWorkspaces/ASEAN/research/02_sector_coupling/buildings_heat/phase3a6/data/raw/malaysia-neb2019.pdf")
NEB_PDF_SHA = "141f20588ead46a942526a1e6c0a7f730a67cd586f071868f68294492aad3009"   # W11 extracted/PDF_TEXT_INDEX.csv
NEB_TXT = W11 / "extracted/my_neb2019"
CC = "MY"
AREA = "Malaysia"
FAO_DIR = S2W / "downloads/15_faostat"
FAO_FILES = {"FO": ("FAOSTAT_data_en_11-6-2026 (2).csv", "de61d07f1801c3f013c0f506c5da57a3c21ceda5cb53a5d094b1fa3bd8f5e027"),
             "QCL": ("FAOSTAT_data_en_11-6-2026.csv", "f340a9468f09d8a2325efaf7918e8eb2ea06031c9a0620ac13e8bc793d8b32a8")}
FLAG_GRADE = {"A": "A", "X": "B", "E": "C", "I": "C", "M": "E"}
SUMMARY = "INDUSTRY_2050_SUMMARY_aeo8_ats_anchor_OTHER_USEFUL_HEAT_BANDS.csv"
OUTC = ("electricity", "heat", "heat_medium_a", "heat_medium_b", "heat_high", "coal", "oil", "gas", "biomass", "hydrogen", "ammonia", "methanol")
CARS19 = ("coal", "oil", "gas", "biomass", "electricity")
FUELS = ("coal", "oil", "gas", "biomass")
ELASTICITY = 0.5
TWH_PER_KT_HARD_COAL_V3 = 0.007167   # FROZEN_UPSTREAM_CONVERSIONS.json (pypsa-asean get_conv_factors), = 25.8012 GJ/t
MWH_PER_TOE = 11.63


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
        raise ValueError(f"{name}: SHA256 differs from the S2 instruction")
    d = pd.read_csv(p, dtype=str, encoding="utf-8-sig")
    d["year"] = d.Year.astype(int); d["value"] = pd.to_numeric(d.Value, errors="coerce"); d["flag"] = d.Flag.fillna("")
    return d


def series(d, area, item, element="Production"):
    s = d[(d.Area == area) & (d.Item == item) & (d.Element == element)].sort_values("year")
    if s.year.duplicated().any():
        raise ValueError(f"{area} {item}: duplicated years")
    return s[["year", "value", "flag", "Unit"]].reset_index(drop=True)


def value(d, area, item, year, element="Production"):
    s = series(d, area, item, element); z = s[s.year == year]
    if len(z) != 1:
        raise KeyError((area, item, year, element))
    return float(z.value.iloc[0]), str(z.flag.iloc[0])


def latest_actual(s: pd.DataFrame) -> dict:
    """Last year that carries new information (S2 rule): the last year whose value differs from the year before; a series that never changes
    returns its first year with grade D. Also returns the literal latest year."""
    s = s.dropna(subset=["value"]).reset_index(drop=True)
    yb = int(s.year.iloc[0]); i_b = 0
    for i in range(1, len(s)):
        if s.value.iloc[i] != s.value.iloc[i - 1]:
            yb = int(s.year.iloc[i]); i_b = i
    carry = [int(y) for y in s.year.iloc[i_b + 1:]]
    grade = FLAG_GRADE.get(str(s.flag.iloc[i_b]), "C") if (i_b > 0 or len(s) == 1) else "D"
    return dict(base_year=yb, value=float(s.value.iloc[i_b]), flag=str(s.flag.iloc[i_b]), grade=grade, carried_forward_years=carry,
                latest_year=int(s.year.iloc[-1]), latest_value=float(s.value.iloc[-1]), latest_flag=str(s.flag.iloc[-1]))


# ---------------------------------------------------------------- growth rule and ratios -----------------------------------------------------
def gdp_growth(country: str = CC) -> float:
    rule = pd.read_csv(REPO / "research_inputs/demand_v5/INDUSTRY_OUTPUT_2050_M08B.csv").set_index("country")
    return float(rule.at[country, "gdp_growth_2022_2050"])


def growth(y_b: int, country: str = CC) -> float:
    """S0 R2: q(2050) = q(y_b) x G^((2050 - y_b) / 28 x 0.5), G = AEO8 table D.2 real GDP 2050 / 2022 (v3 ammonia / non-ferrous rule)."""
    return gdp_growth(country) ** ((2050 - y_b) / 28.0 * ELASTICITY)


def ratios_2050() -> pd.DataFrame:
    return pd.read_csv(REPO / "research_inputs/registry_v5/INDUSTRY_SECTOR_RATIOS_PYPSA_EUR_2050.csv", index_col=0)


def ratios_today() -> pd.DataFrame:
    return pd.read_csv(REPO / "research_inputs/registry_v5/INDUSTRY_SECTOR_RATIOS_TODAY_EU27_2019.csv").set_index("sector")


RATIO_TO_OUT = {"elec": "electricity", "coal": "coal", "coke": "coal", "biomass": "biomass", "methane": "gas", "hydrogen": "hydrogen", "heat": "heat",
                "ammonia": "ammonia", "methanol": "methanol"}   # = s3_0_industry.RATIO_TO_OUT (naphtha excluded: feedstock)


def vec2050(sector: str, t: float, exclude: tuple = ()) -> dict:
    """PyPSA-Eur 2050 ratio column x tonnes -> {v3 carrier: MWh} (naphtha excluded as in s3_0_industry / v3_industry; `exclude` drops more rows)."""
    r = ratios_2050(); out = {k: 0.0 for k in OUTC}
    for k, oc in RATIO_TO_OUT.items():
        if k in exclude:
            continue
        out[oc] += float(r.at[k, sector]) * t
    return out


def today_vec(sector: str, t: float, exclude: tuple = ()) -> dict:
    """S1 / S2 convention: JRC-IDEES EU27 2019 today total of the sector, carrier structure of the PyPSA-Eur 2050 ratio column (rows elec, coal,
    coke, methane, biomass, hydrogen, heat); returns {ratio row: MWh}. `exclude` drops rows after scaling (closed-loop biomass)."""
    r50, tday = ratios_2050(), ratios_today()
    cars = ("elec", "coal", "coke", "methane", "biomass", "hydrogen", "heat")
    col = r50[sector]; tf = float(sum(col[c] for c in cars)); T = float(tday.at[sector, "today_total_mwh_per_t"])
    return {c: (0.0 if c in exclude else float(col[c]) / tf * T * t) for c in cars}


# ---------------------------------------------------------------- scratch data chain --------------------------------------------------------
CACHE_REL = "research_inputs/assembly_v1/sources/industry_cache.json"
D1_REL = "research_inputs/demand_v5/DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv"
S30_REL = "scripts_project/s3_0_industry.py"
PATCH_OLD = 'el19 = float(ratios.at["elec", "Cement"]) * cem_t19'
PATCH_NEW = 'el19 = float(ratios.at["elec", "Cement"]) * float(__import__("os").environ.get(f"V4S2_CEM_EL_T19_{c}", cem_t19))   # V4 scratch-only patch (cement correction ii)'


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
        src = self.orig["s30"].decode()
        if src.count(PATCH_OLD) != 1:
            raise ValueError("cement electricity line not found exactly once")
        (self.chain / S30_REL).write_text(src.replace(PATCH_OLD, PATCH_NEW)); self.patched = True

    def unpatch(self):
        (self.chain / S30_REL).write_bytes(self.orig["s30"]); self.patched = False

    def restore(self):
        (self.chain / CACHE_REL).write_bytes(self.orig["cache"]); (self.chain / D1_REL).write_bytes(self.orig["d1"])

    def run(self, moves: list | None = None, cem_el_t19: dict | None = None, country: str = CC):
        """moves: list of (subsector, carrier, d_mwh): d leaves sub19[subsector][carrier] of `country` (negative d adds energy). Returns the heat-band
        summary row, the other-bucket row and the s3_0 sub-sector rows of the country."""
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
                tot = sum(float(v) for k, v in r.items() if k not in ("country", "carrier"))
                m = (d.country == country) & (d.sector == "Industry") & (d.carrier == car)
                if m.sum() != 1:
                    raise ValueError(f"{country} Industry {car}: {m.sum()} rows")
                e19 = float(d.loc[m, "base_2019_mwh"].iloc[0])
                for sub, dv in subs.items():
                    x = dv * tot / e19
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
        pz = pd.read_csv(dd / "INDUSTRY_2050_PYPSA_EUR_aeo8_ats_anchor.csv"); pz = pz[pz.country == country]
        return row, ob, pz


def v3_layer(v3, row, fut, nf: dict, extra: dict | None = None) -> dict:
    """v3 conservation (D163-6 a) on one chain row: T = route total of the row + new explicit sub-sectors the chain does not contain;
    explicit = steel + cement + ammonia + dispersed + non-ferrous + new; Other = T - explicit, carriers scaled uniformly."""
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


# ---------------------------------------------------------------- UNSD export ---------------------------------------------------------------
def unsd_export(country: str = AREA) -> tuple[pd.DataFrame, dict]:
    """UNdata export 2025-05-02 (the model source), all years of one country; footnote codes resolved ('1' = Estimate)."""
    import glob, re
    rows, notes = [], {}
    for f in sorted(glob.glob(str(UNSD_DIR / "*.txt"))):
        txt = open(f, encoding="utf-8").read()
        _, _, foot = txt.partition('"fnSeqID";"Footnote"')
        for line in foot.strip().splitlines():
            m = re.match(r'^"(\d+)";"(.*)"$', line.strip())
            if m:
                notes[m.group(1)] = m.group(2)
        dd = pd.read_csv(f, sep=";", dtype=str, on_bad_lines="skip"); dd["file"] = Path(f).name
        rows.append(dd)
    d = pd.concat(rows, ignore_index=True)
    d = d[d["Country or Area"].eq(country)].copy()
    sp = d["Commodity - Transaction"].str.split(" - ", n=1, expand=True); d["commodity"], d["transaction"] = sp[0].str.strip(), sp[1].fillna("").str.strip()
    d["q"] = pd.to_numeric(d.Quantity, errors="coerce"); d["y"] = pd.to_numeric(d.Year, errors="coerce")
    d["footnote"] = d["Quantity Footnotes"].fillna("").map(lambda s: "; ".join(notes.get(x.strip(), x) for x in str(s).split(",") if x.strip()))
    return d.dropna(subset=["y"]).assign(y=lambda z: z.y.astype(int)), notes


def frozen_conv() -> dict:
    return json.loads((REPO / "research_inputs/assembly_v1/sources/FROZEN_UPSTREAM_CONVERSIONS.json").read_text())["constants"]["fuels_conv_toTWh"]


# ---------------------------------------------------------------- NEB 2019 text -------------------------------------------------------------
def neb_page(p: int) -> str:
    return (NEB_TXT / f"p{p:03d}_plain.txt").read_text(encoding="utf-8")


def neb_numbers(line: str) -> list[float]:
    import re
    toks = re.findall(r"-?[\d,]+(?:\.\d+)?|-(?=\s|$)", line)
    out = []
    for t in toks:
        out.append(0.0 if t == "-" else float(t.replace(",", "")))
    return out


# ---------------------------------------------------------------- evidence ------------------------------------------------------------------
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


def node_of(df: pd.DataFrame, regions) -> tuple[pd.Series, pd.Series]:
    """Point in the v3 onshore region (S1 rule); a point outside every region takes the nearest node of the same country (lat / lon columns)."""
    import geopandas as gpd
    g = gpd.GeoDataFrame(df[["lat", "lon"]].astype(float).copy(), geometry=gpd.points_from_xy(df.lon.astype(float), df.lat.astype(float)), crs=4326)
    r = regions[regions.country == CC]
    j = gpd.sjoin(g, r[["node", "geometry"]], how="left", predicate="within"); j = j[~j.index.duplicated()]
    out = j.node.copy(); how = pd.Series("point in region", index=j.index)
    rp, gp = r.to_crs(3857), g.to_crs(3857)   # metric distances for the nearest-region fallback
    for i in out[out.isna()].index:
        out.at[i] = rp.node.iloc[int(np.argmin(rp.geometry.distance(gp.geometry.at[i]).values))]; how.at[i] = "nearest node (point outside the onshore regions)"
    return out, how
