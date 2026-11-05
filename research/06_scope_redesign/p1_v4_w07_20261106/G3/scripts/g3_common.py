"""G3 (v4 W07, B-G3: Thailand, Philippines, Singapore) shared helpers. Nothing here writes into the repository worktree.

Paths (WSL view): G3 deliverable folder, the G3 worktree (read only), the scratch copy of the data chain OUTSIDE the repository
(/home/jin/v4w07_g3/chain), and read-only inputs of S0-S2 (FAOSTAT, SFI, GEM, route map) and W11 (EPPO page text, NCV tables).

Scratch chain (S2 v4s2_common.Chain extended to several countries and to the NCV of decision 207):
  1. NCV (mode I, 'multiplier unchanged', decision 204 item 1; W11 section 3.1): every IndustryFinalEnergy row of BASE_RECONSTRUCTION.json of the
     country is recomputed with the scheme factor (coal parents, or the child rows of the same flow when the scheme gives child values only); the
     ATS-anchor table base_2019_mwh of Industry x carrier changes by the delta, value_2050_mwh = base x multiplier_total; every cache cell
     (country x carrier x sub-sector) is multiplied by E_scheme / E_v3 of the export rows of that sub-sector flow (parents de-duplicated).
  2. Moves (physical deductions converted with the SAME NCV, W11 section 4.2 item 5): energy d leaves sub19[sub-sector][carrier]; the cache cell is
     lowered by d x sum(cache) / e19 and e19 by d (S2 rule), which lowers exactly that sub-sector and leaves the others unchanged.
  3. Cement correction (ii): one line of the scratch s3_0_industry.py reads the 2019 cement tonnes for the grinding electricity from an environment
     variable V4W07_CEM_EL_T19_<cc>; without the variable the line is identical in effect (checked in the reproduction).
v3 layer (D163-6 a): T = route total of the row + new explicit sub-sectors; Other = T - explicit (TH, PH, SG have no v3 non-ferrous).
"""
from __future__ import annotations

import ast
import glob
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

G3 = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w07_20261106/G3")
REPO = Path("/home/jin/wt_v4_g3")
CHAIN = Path("/home/jin/v4w07_g3/chain")
MAIN = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model")   # regions_onshore.geojson (read only, as S1 / S2)
S2W = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_data_20261105")       # S0-S2 deliverables and downloads (read only)
W11 = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_ncv_20261106")        # W11 deliverables (read only)
PYPSA_ASEAN = Path("/home/jin/research/SGP_ESE5004_Stage2/pypsa-asean")
UNSD_DIR = PYPSA_ASEAN / "data/demand/unsd/data"
SRC = REPO / "research_inputs/assembly_v1/sources"
CC3 = ("TH", "PH", "SG")
NAMES = {"TH": "Thailand", "PH": "Philippines", "SG": "Singapore"}
SUMMARY = "INDUSTRY_2050_SUMMARY_aeo8_ats_anchor_OTHER_USEFUL_HEAT_BANDS.csv"
S3_OUT = ["INDUSTRY_2050_SUMMARY_aeo8_ats_anchor.csv", SUMMARY, "INDUSTRY_2050_OTHER_BUCKET.csv", "INDUSTRY_2050_PYPSA_EUR_aeo8_ats_anchor.csv"]
CACHE_REL = "research_inputs/assembly_v1/sources/industry_cache.json"
ATS_REL = "research_inputs/demand_v5/DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv"
S30_REL = "scripts_project/s3_0_industry.py"
OUTC = ("electricity", "heat", "heat_medium_a", "heat_medium_b", "heat_high", "coal", "oil", "gas", "biomass", "hydrogen", "ammonia", "methanol")
CARS19 = ("coal", "oil", "gas", "biomass", "electricity")
FUELS = ("coal", "oil", "gas", "biomass")
ELASTICITY = 0.5
PATCH_OLD = 'el19 = float(ratios.at["elec", "Cement"]) * cem_t19'
PATCH_NEW = 'el19 = float(ratios.at["elec", "Cement"]) * float(__import__("os").environ.get(f"V4W07_CEM_EL_T19_{c}", cem_t19))   # V4 W07 G3 scratch-only patch (cement correction ii)'
FLAG_GRADE = {"A": "A", "X": "B", "E": "C", "I": "C", "M": "E"}
FAO_FILES = {"FO": ("FAOSTAT_data_en_11-6-2026 (2).csv", "de61d07f1801c3f013c0f506c5da57a3c21ceda5cb53a5d094b1fa3bd8f5e027"),
             "QCL": ("FAOSTAT_data_en_11-6-2026.csv", "f340a9468f09d8a2325efaf7918e8eb2ea06031c9a0620ac13e8bc793d8b32a8")}
# cache sub-sector -> UNSD flow (W11 v4ncv_deltas.CACHE_FLOW)
CACHE_FLOW = {"iron and steel": "Ironandsteel", "chemical and petrochemical": "Chemicalandpetrochemical", "non-ferrous metals": "Non-ferrousmetals",
              "non-metallic minerals": "Non-metallicminerals", "transport equipment": "Transportequipment", "machinery": "Machinery",
              "mining and quarrying": "Miningandquarrying", "food and tobacco": "Foodandtobacco", "paper pulp and print": "Paper,pulpandprinting",
              "wood and wood products": "Woodandwoodproducts", "textile and leather": "Textileandleather", "construction": "Construction",
              "other": "Industriesn.e.s"}
CHILDREN = {"Hard coal": ["Anthracite", "Other bituminous coal", "Coking coal"], "Brown coal": ["Lignite", "Sub-bituminous coal"]}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


# ------------------------------------------------------------------ evidence ---------------------------------------------------------------
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


# ------------------------------------------------------------------ UNSD export ------------------------------------------------------------
_FLOW_RULES = [   # W11 v4ncv_common._FLOW_RULES (subset used here)
    (r"^consumption by manufacturing, construction and non-fuel( mining)?( industry)?$", "Manufacturing,const.,mining"),
    (r"^consumption by iron and steel( industry)?$", "Ironandsteel"),
    (r"^consumption by chemical( and petrochemical)?( ?industry)?$", "Chemicalandpetrochemical"),
    (r"^consumption by non-ferrous metals( industry)?$", "Non-ferrousmetals"),
    (r"^consumption by non-metallic minerals( industry)?$", "Non-metallicminerals"),
    (r"^consumption by transport equipment( industry)?$", "Transportequipment"),
    (r"^consumption by machinery( industry)?$", "Machinery"),
    (r"^consumption by mining and quarrying( industry)?$", "Miningandquarrying"),
    (r"^consumption by food(, beverage)? and tobacco( industry)?$", "Foodandtobacco"),
    (r"^consumption by paper, pulp and print(ing)?( industry)?$", "Paper,pulpandprinting"),
    (r"^consumption by wood and wood products( industry)?$", "Woodandwoodproducts"),
    (r"^consumption by textile and leather( industry)?$", "Textileandleather"),
    (r"^consumption by construction( industry)?$", "Construction"),
    (r"^consumption not elsewhere specified \(industry\)$|^consumption by industries not elsewhere specified$", "Industriesn.e.s"),
    (r"^consumption by households$", "Households"),
    (r"^transformation in electricity plants - main activity producers$|^transformation in main activity( producer)? electricity plants$", "Electricityplants_main"),
    (r"^transformation in electricity plants - autoproducers$|^transformation in autoproducer electricity plants$", "Electricityplants_auto"),
    (r"^production$", "Primaryproduction"), (r"^imports$", "Imports"), (r"^exports$", "Exports"),
    (r"^consumption for non-energy uses?$|^non-energy uses?$", "Non-energyuse"),
    (r"^final energy consumption$", "Finalenergyconsumption"),
]


def flow_of(transaction: str) -> str | None:
    t = re.sub(r"\s+", " ", transaction.strip().lower())
    for pat, flow in _FLOW_RULES:
        if re.match(pat, t):
            return flow
    return None


def unsd_export(countries=CC3) -> pd.DataFrame:
    names = {v: k for k, v in NAMES.items() if k in countries}
    fs = sorted(glob.glob(str(UNSD_DIR / "*.txt")))
    df = pd.concat((pd.read_csv(f, sep=";", dtype=str, keep_default_na=False).assign(SourceFile=Path(f).name) for f in fs), ignore_index=True)
    df = df[df["Country or Area"].isin(names)].copy()
    sp = df["Commodity - Transaction"].str.split(" - ", n=1, expand=True)
    df["commodity"] = sp[0].str.strip(); df["transaction"] = sp[1].fillna("").str.strip()
    df["country"] = df["Country or Area"].map(names); df["q"] = pd.to_numeric(df["Quantity"], errors="coerce"); df["year"] = df.Year.astype(int)
    df["flow"] = df.transaction.map(flow_of)
    return df


def export_2019_flows() -> pd.DataFrame:
    """2019 rows by (country, commodity, flow), one value each (W11 convention: duplicated spellings with the same quantity kept once)."""
    d = unsd_export()
    d = d[(d.year == 2019) & d.flow.notna()].copy()
    d["commodity"] = d.commodity.replace({"Hrad coal": "Hard coal"})
    d = d.drop_duplicates(["country", "commodity", "flow", "q"])
    return d.groupby(["country", "commodity", "flow"], as_index=False).q.max()


def upstream_conv() -> dict:
    """pypsa-asean get_conv_factors dictionary (TWh per thousand unit), parsed with ast (no import; = W11 upstream_dicts)."""
    tree = ast.parse((PYPSA_ASEAN / "scripts/_helpers.py").read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "get_conv_factors":
            for sub in ast.walk(node):
                if isinstance(sub, ast.Assign) and isinstance(sub.value, ast.Dict) and len(sub.value.keys) > 10:
                    return ast.literal_eval(sub.value)
    raise ValueError("get_conv_factors not found")


# ------------------------------------------------------------------ NCV schemes ------------------------------------------------------------
class NCV:
    """A scheme = {(cc, commodity): GJ per unit}; commodities not given keep the v3 factor. Child values (Lignite, Sub-bituminous coal, ...)
    are applied through the child rows of the same flow when the scheme has no value for the parent (W11 v4ncv_deltas.energy)."""

    def __init__(self, name: str, factors: dict):
        self.name, self.f = name, dict(factors)
        self.conv = upstream_conv()

    def v3(self, com: str) -> float:   # MWh per unit
        return self.conv[com] * 1e6

    def mwh_per_unit(self, cc: str, com: str) -> float:
        key = "Hard coal" if com == "Hrad coal" else com
        if (cc, key) in self.f:
            return self.f[(cc, key)] * 1000.0 / 3.6
        return self.v3(com)

    def energy(self, cc: str, com: str, qty: float, flow: str | None, E: pd.DataFrame) -> float:
        parent = "Hard coal" if com in ("Hard coal", "Hrad coal") else ("Brown coal" if com == "Brown coal" else None)
        if parent and (cc, parent) not in self.f and any((cc, ch) in self.f for ch in CHILDREN[parent]):
            ch = E[(E.country == cc) & (E.flow == flow) & E.commodity.isin(CHILDREN[parent])]
            if len(ch) and abs(ch.q.sum() - qty) <= 1e-6 * max(1.0, abs(qty)):
                return float(sum(r.q * self.mwh_per_unit(cc, r.commodity) for r in ch.itertuples()))
            raise ValueError(f"{cc} {com} {flow}: children do not add up to the parent ({ch.q.sum()} vs {qty})")
        return qty * self.mwh_per_unit(cc, com)


def base_rows(cc: str) -> list[dict]:
    """IndustryFinalEnergy rows of BASE_RECONSTRUCTION.json of a country (the D1 industry base) with physical units."""
    b = json.loads((SRC / "BASE_RECONSTRUCTION.json").read_text())
    return [r for r in b["selected_rows"] if r["Country"] == cc and r["Account"] == "IndustryFinalEnergy"]


def ncv_deltas(scheme: NCV, E: pd.DataFrame, countries=CC3) -> tuple[dict, dict, list]:
    """(delta MWh per (cc, carrier) of the Industry base, cache ratio per (cc, carrier, sub-sector), row log)."""
    dl, log = {}, []
    for cc in countries:
        for r in base_rows(cc):
            if r["RawUnit"] not in ("Metric tons,  thousand", "Cubic metres, thousand") or r["Commodity"] not in scheme.conv:
                continue
            q = float(r["RawValue"]); v3 = float(r["MWh"])
            if abs(q * scheme.v3(r["Commodity"]) - v3) > 1e-3:   # biofuel blend rows: effective quantity = file MWh / v3 factor (W11)
                q = v3 / scheme.v3(r["Commodity"])
            e = scheme.energy(cc, r["Commodity"], q, "Manufacturing,const.,mining", E)
            if abs(e - v3) > 1e-9:
                dl[(cc, r["Carrier"])] = dl.get((cc, r["Carrier"]), 0.0) + (e - v3)
                log.append(dict(country=cc, carrier=r["Carrier"], commodity=r["Commodity"], qty=q, v3_mwh=v3, scheme_mwh=e))
    conv = scheme.conv
    car_of = {}
    for c_ in conv:
        lc = c_.lower()
        car_of[c_] = "coal" if any(k in lc for k in ("coal", "lignite", "anthracite", "coke", "bitumin", "patent", "peat")) and "petroleum" not in lc else None
    ratios = {}
    for cc in countries:
        for sub, flow in CACHE_FLOW.items():
            e = E[(E.country == cc) & (E.flow == flow)]
            qs = e.set_index("commodity").q
            keep = [c_ for c_ in qs.index if not ((c_ in CHILDREN["Hard coal"] and "Hard coal" in qs.index) or (c_ in CHILDREN["Brown coal"] and "Brown coal" in qs.index))]
            items = [(c_, float(qs[c_])) for c_ in keep if car_of.get(c_) == "coal"]
            if not items:
                continue
            v3 = sum(q * scheme.v3(c_) for c_, q in items)
            sc = sum(scheme.energy(cc, c_, q, flow, E) for c_, q in items)
            if v3 > 0 and abs(sc / v3 - 1) > 1e-12:
                ratios[(cc, "coal", sub)] = sc / v3
    return dl, ratios, log


# ------------------------------------------------------------------ scratch data chain -----------------------------------------------------
class Chain:
    def __init__(self, repo: Path = REPO, chain: Path = CHAIN):
        self.repo, self.chain = repo, chain
        self.orig = {"cache": (repo / CACHE_REL).read_bytes(), "ats": (repo / ATS_REL).read_bytes(), "s30": (repo / S30_REL).read_bytes()}

    def copy(self):
        if self.chain.exists():
            shutil.rmtree(self.chain)
        self.chain.mkdir(parents=True)
        shutil.copytree(self.repo / "research_inputs", self.chain / "research_inputs")
        shutil.copytree(self.repo / "scripts_project", self.chain / "scripts_project", ignore=shutil.ignore_patterns("__pycache__", "retired"))
        (self.chain / "scripts_project/retired").mkdir(exist_ok=True)
        src = self.orig["s30"].decode()
        if src.count(PATCH_OLD) != 1:
            raise ValueError("cement electricity line not found exactly once")
        self.patched_src = src.replace(PATCH_OLD, PATCH_NEW)

    def restore(self, patched: bool = False):
        (self.chain / CACHE_REL).write_bytes(self.orig["cache"]); (self.chain / ATS_REL).write_bytes(self.orig["ats"])
        if patched:
            (self.chain / S30_REL).write_text(self.patched_src)
        else:
            (self.chain / S30_REL).write_bytes(self.orig["s30"])

    def prepare(self, ncv: tuple | None = None, moves: list | None = None, cem_t19: dict | None = None):
        """ncv = (delta {(cc, carrier): MWh}, ratio {(cc, carrier, sub): x}); moves = [(cc, sub, carrier, d_mwh)] on top of the NCV state."""
        self.restore(patched=bool(cem_t19))
        cache = json.loads(self.orig["cache"]); d = pd.read_csv(self.chain / ATS_REL, keep_default_na=False, dtype=str)
        recs = {(r["country"], r["carrier"]): r for r in cache["records"]}

        def ats_mask(cc, car):
            m = (d.country == cc) & (d.sector == "Industry") & (d.carrier == car)
            if m.sum() != 1:
                raise ValueError(f"{cc} Industry {car}: {m.sum()} rows")
            return m

        def set_base(m, b):
            d.loc[m, "base_2019_mwh"] = repr(b); d.loc[m, "value_2050_mwh"] = repr(b * float(d.loc[m, "multiplier_total"].iloc[0]))

        if ncv:
            dl, ratios = ncv
            for (cc, car), dv in dl.items():
                m = ats_mask(cc, car); set_base(m, float(d.loc[m, "base_2019_mwh"].iloc[0]) + dv)
            for (cc, car, sub), x in ratios.items():
                r = recs[(cc, car)]; r[sub] = repr(float(r[sub]) * x)
        moves = [m_ for m_ in (moves or []) if abs(m_[3]) > 0]
        by = {}
        for cc, sub, car, dv in moves:
            by.setdefault((cc, car), {}); by[(cc, car)][sub] = by[(cc, car)].get(sub, 0.0) + dv
        for (cc, car), subs in by.items():
            r = recs[(cc, car)]
            tot = sum(float(v) for k, v in r.items() if k not in ("country", "carrier"))   # cache sum of the carrier (after NCV)
            m = ats_mask(cc, car); e19 = float(d.loc[m, "base_2019_mwh"].iloc[0])        # D1 base of the carrier (after NCV)
            for sub, dv in subs.items():
                x = dv * tot / e19   # lowers sub19[sub][car] by exactly dv, other sub-sectors unchanged
                if float(r[sub]) - x < -1e-6:
                    raise ValueError(f"{cc} {sub} {car}: move {dv:.6g} MWh exceeds the cache cell ({float(r[sub]) * e19 / tot:.6g} MWh)")
                r[sub] = repr(float(r[sub]) - x)
            set_base(m, e19 - sum(subs.values()))
        (self.chain / CACHE_REL).write_text(json.dumps(cache)); d.to_csv(self.chain / ATS_REL, index=False)

    def run(self, ncv=None, moves=None, cem_t19=None):
        self.prepare(ncv, moves, cem_t19)
        env = {"PYTHONHASHSEED": "0", "PATH": "/usr/bin:/bin"}
        for k, v in (cem_t19 or {}).items():
            env[f"V4W07_CEM_EL_T19_{k}"] = repr(float(v))
        r = subprocess.run([sys.executable, "s3_0_industry.py"], cwd=self.chain / "scripts_project", capture_output=True, text=True, env=env)
        if r.returncode:
            raise RuntimeError(r.stderr[-3000:])
        dd = self.chain / "research_inputs/demand_v5"
        S = pd.read_csv(dd / SUMMARY).set_index("country")
        ob = pd.read_csv(dd / "INDUSTRY_2050_OTHER_BUCKET.csv"); ob = ob[ob["mode"] == "aeo8_ats_anchor"].set_index("country")
        pz = pd.read_csv(dd / "INDUSTRY_2050_PYPSA_EUR_aeo8_ats_anchor.csv")
        gaps = pd.read_csv(dd / "INDUSTRY_2050_GAPS.csv"); gaps = gaps[gaps["mode"] == "aeo8_ats_anchor"]
        return S, ob, pz, gaps

    def sub19(self, cc: str) -> dict:
        """{sub-sector: {carrier: MWh}} of the current scratch inputs (cache shares x D1 base), as s3_0_industry line 161."""
        cache = json.loads((self.chain / CACHE_REL).read_text()); d = pd.read_csv(self.chain / ATS_REL, keep_default_na=False)
        d = d[(d.country == cc) & (d.sector == "Industry")].set_index("carrier").base_2019_mwh.astype(float)
        out = {}
        for r in cache["records"]:
            if r["country"] != cc:
                continue
            tot = sum(float(v) for k, v in r.items() if k not in ("country", "carrier"))
            for k, v in r.items():
                if k in ("country", "carrier"):
                    continue
                out.setdefault(k, {c: 0.0 for c in CARS19})[r["carrier"]] = float(d.get(r["carrier"], 0.0)) * float(v) / tot if tot > 0 else 0.0
        return out


def import_v3(repo: Path = REPO):
    sys.path.insert(0, str(repo / "scripts_project"))
    import v3_industry as v3   # noqa: E402  (read only)
    return v3


def v3_layer(v3, row, fut, extra: dict | None = None) -> dict:
    """D163-6 a on one chain row (no v3 non-ferrous for TH / PH / SG): T = route total + new explicit sub-sectors; Other = T - explicit."""
    extra = extra or {}
    T_chain = float(sum(row[v3.col(x)] for x in v3.CARRIERS))
    parts = v3.decompose(row, fut); parts.update(extra)
    T = T_chain + sum(sum(v.values()) for v in extra.values())
    expl = sum(sum(v.values()) for k, v in parts.items() if k != "other")
    so = sum(parts["other"].values()); f = (T - expl) / so if so else 0.0
    other = {k: v * f for k, v in parts["other"].items()}
    return dict(T=T, T_chain=T_chain, other=other, other_total=sum(other.values()), scale=f, explicit=expl,
                by_sub={k: sum(v.values()) for k, v in parts.items() if k != "other"}, parts=parts)


# ------------------------------------------------------------------ FAOSTAT, growth, ratios -------------------------------------------------
def fao(domain: str) -> pd.DataFrame:
    name, sha = FAO_FILES[domain]
    p = S2W / "downloads/15_faostat" / name
    if sha256(p) != sha:
        raise ValueError(f"{name}: SHA256 differs from the S2 record")
    d = pd.read_csv(p, dtype=str, encoding="utf-8-sig")
    d["year"] = d.Year.astype(int); d["value"] = pd.to_numeric(d.Value, errors="coerce"); d["flag"] = d.Flag.fillna("")
    return d


def series(d, area, item, element="Production") -> pd.DataFrame:
    s = d[(d.Area == area) & (d.Item == item) & (d.Element == element)].sort_values("year")
    if s.year.duplicated().any():
        raise ValueError(f"{area} {item}: duplicated years")
    return s[["year", "value", "flag", "Unit"]].reset_index(drop=True)


def latest_actual(s: pd.DataFrame) -> dict:
    """S2 rule: last year that carries new information (later equal E / I values are carry-forwards); literal latest year as sensitivity."""
    s = s.dropna(subset=["value"]).reset_index(drop=True)
    yb = int(s.year.iloc[0]); i_b = 0
    for i in range(1, len(s)):
        if s.value.iloc[i] != s.value.iloc[i - 1]:
            yb = int(s.year.iloc[i]); i_b = i
    grade = FLAG_GRADE.get(str(s.flag.iloc[i_b]), "C") if (i_b > 0 or len(s) == 1) else "D"
    return dict(base_year=yb, value=float(s.value.iloc[i_b]), flag=str(s.flag.iloc[i_b]), grade=grade, carried_forward_years=[int(y) for y in s.year.iloc[i_b + 1:]],
                latest_year=int(s.year.iloc[-1]), latest_value=float(s.value.iloc[-1]), latest_flag=str(s.flag.iloc[-1]))


def gdp_growth(cc: str) -> float:
    return float(pd.read_csv(REPO / "research_inputs/demand_v5/INDUSTRY_OUTPUT_2050_M08B.csv").set_index("country").at[cc, "gdp_growth_2022_2050"])


def growth(y_b: int, cc: str) -> float:
    """S0 R2: q(2050) = q(y_b) x G^((2050 - y_b) / 28 x 0.5)."""
    return gdp_growth(cc) ** ((2050 - y_b) / 28.0 * ELASTICITY)


def ratios_2050() -> pd.DataFrame:
    return pd.read_csv(REPO / "research_inputs/registry_v5/INDUSTRY_SECTOR_RATIOS_PYPSA_EUR_2050.csv", index_col=0)


def ratios_today() -> pd.DataFrame:
    return pd.read_csv(REPO / "research_inputs/registry_v5/INDUSTRY_SECTOR_RATIOS_TODAY_EU27_2019.csv").set_index("sector")


RATIO_TO_OUT = {"elec": "electricity", "coal": "coal", "coke": "coal", "biomass": "biomass", "methane": "gas", "hydrogen": "hydrogen", "heat": "heat",
                "ammonia": "ammonia", "methanol": "methanol"}   # = s3_0_industry.RATIO_TO_OUT (naphtha excluded)


def vec2050(sector: str, t: float) -> dict:
    r = ratios_2050(); out = {k: 0.0 for k in OUTC}
    for k, oc in RATIO_TO_OUT.items():
        out[oc] += float(r.at[k, sector]) * t
    return out


def today_vec(sector: str, t: float) -> dict:
    """S1 / S2 convention: JRC-IDEES EU27 2019 today total (MWh/t) with the carrier structure of the PyPSA-Eur 2050 ratio column."""
    r50 = ratios_2050(); tday = ratios_today()
    cars = ("elec", "coal", "coke", "methane", "biomass", "hydrogen", "heat")
    col = r50[sector]; tf = float(sum(col[c] for c in cars)); T = float(tday.at[sector, "today_total_mwh_per_t"])
    return {c: float(col[c]) / tf * T * t for c in cars}


def node_of(df: pd.DataFrame, regions, cc: str):
    """S1 v4s1_facilities.node_of for any country: point in the v3 onshore region, else nearest node of the same country."""
    import geopandas as gpd
    g = gpd.GeoDataFrame(df[["lat", "lon"]].copy(), geometry=gpd.points_from_xy(df.lon, df.lat), crs=4326)
    r = regions[regions.country == cc]
    j = gpd.sjoin(g, r[["node", "geometry"]], how="left", predicate="within"); j = j[~j.index.duplicated()]
    out = j.node.copy(); how = pd.Series("point in region", index=j.index)
    for i in j[j.node.isna()].index:
        out.at[i] = r.node.iloc[int(np.argmin(r.geometry.distance(g.geometry.at[i]).values))]; how.at[i] = "nearest node (point outside the onshore regions)"
    return out, how
