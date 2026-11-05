"""V4 W07 G2 (Viet Nam) shared helpers: paths, the scratch copy of the repository data chain (outside the repository), VN input edits in both
runs of the v3 VN rule, the v3 decomposition, and the evidence list.

Nothing here writes into the repository worktree. Scratch copy: /home/jin/v4w07_g2/chain (research_inputs + scripts_project of the worktree).

The v3 VN rule (scripts_project/v3_industry.py, run_vn_chain + main):
  * main run: s3_0_industry.py with the UNSD 2019 sub-sector shares of industry_cache.json -> T_v2(VN) = sum of the route carriers of the VN row;
  * APEC run: the VN cache records replaced by the APEC 2022 matrix (research_inputs/industry_v3/APEC2022_VN_INDUSTRY_PJ.csv), s3_0 re-run ->
    VN row used only for the decomposition (steel, cement, ammonia, dispersed, other);
  * D163-6 a: Other_v3 = T_v2(main) - explicit(APEC run); the other carriers are scaled uniformly.

Input edits (both runs share the D1/ATS base e19 of a carrier; the sub-sector matrices differ):
  s3_0 splits e19 by the matrix shares, sub19[s] = e19 * m[s] / sum(m). To move d MWh out of sub-sector s of a carrier, the matrix cell is lowered by
  x = d * sum(m) / e19 and e19 by d: sub19[s] falls by exactly d and every other sub-sector is unchanged. The same d is applied to the UNSD matrix
  (main run) and to the APEC matrix (APEC run), each in its own sub-sector where the row exists (see move_targets()).
"""
from __future__ import annotations

import filecmp
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

WORK = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w07_20261106/G2")
S2W = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_data_20261105")      # S0 / S1 / S2 deliverables (read only)
NCVW = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_ncv_20261106")      # W11 deliverables (read only)
INTAKE = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p2_data_intake/v3_20261102")
REPO = Path("/home/jin/wt_v4_g2")
CHAIN = Path("/home/jin/v4w07_g2/chain")
MAIN = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model")
UPSTREAM = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/model-source")
CC = "VN"
SUMMARY = "INDUSTRY_2050_SUMMARY_aeo8_ats_anchor_OTHER_USEFUL_HEAT_BANDS.csv"
CACHE_REL = "research_inputs/assembly_v1/sources/industry_cache.json"
ATS_REL = "research_inputs/demand_v5/DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv"
D1_REL = "research_inputs/demand_v5/DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER.csv"
APEC_REL = "research_inputs/industry_v3/APEC2022_VN_INDUSTRY_PJ.csv"
S30_REL = "scripts_project/s3_0_industry.py"
S3_OUT = ["INDUSTRY_2050_SUMMARY_aeo8_ats_anchor.csv", SUMMARY, "INDUSTRY_2050_OTHER_BUCKET.csv", "INDUSTRY_2050_PYPSA_EUR_aeo8_ats_anchor.csv",
          "INDUSTRY_2050_GAPS.csv"]
CARS19 = ("coal", "oil", "gas", "biomass", "electricity")
FUELS = ("coal", "oil", "gas", "biomass")
APEC_COL = dict(coal="coal_pj", oil="oil_pj", gas="gas_pj", biomass="biomass_pj", electricity="electricity_pj")
OUTC = ("electricity", "heat", "heat_medium_a", "heat_medium_b", "heat_high", "coal", "oil", "gas", "biomass", "hydrogen", "ammonia", "methanol")
ENV = {"PYTHONHASHSEED": "0", "PATH": "/usr/bin:/bin"}
ELASTICITY = 0.5
PATCH_OLD = 'el19 = float(ratios.at["elec", "Cement"]) * cem_t19'
PATCH_NEW = ('el19 = float(ratios.at["elec", "Cement"]) * float(__import__("os").environ.get(f"V4W07_CEM_EL_T19_{c}", cem_t19))'
             '   # V4 W07 G2 scratch-only patch (cement correction ii)')


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def jdump(obj, p: Path):
    p.write_text(json.dumps(obj, indent=1, ensure_ascii=False,
                            default=lambda x: float(x) if isinstance(x, (np.floating, np.integer)) else str(x)) + "\n", encoding="utf-8")


def import_v3(repo: Path = REPO):
    sp = str(repo / "scripts_project")
    if sp not in sys.path:
        sys.path.insert(0, sp)
    import v3_industry as v3   # noqa: E402  (ROOT = repository worktree; read only)
    return v3


def gdp_growth(country: str = CC) -> float:
    rule = pd.read_csv(REPO / "research_inputs/demand_v5/INDUSTRY_OUTPUT_2050_M08B.csv").set_index("country")
    return float(rule.at[country, "gdp_growth_2022_2050"])


def growth(y_b: int, country: str = CC) -> float:
    """S0 R2: q(2050) = q(y_b) x G^((2050 - y_b) / 28 x 0.5)."""
    return gdp_growth(country) ** ((2050 - y_b) / 28.0 * ELASTICITY)


RATIO_TO_OUT = {"elec": "electricity", "coal": "coal", "coke": "coal", "biomass": "biomass", "methane": "gas", "hydrogen": "hydrogen", "heat": "heat",
                "ammonia": "ammonia", "methanol": "methanol"}


def ratios_2050() -> pd.DataFrame:
    return pd.read_csv(REPO / "research_inputs/registry_v5/INDUSTRY_SECTOR_RATIOS_PYPSA_EUR_2050.csv", index_col=0)


def ratios_today() -> pd.DataFrame:
    return pd.read_csv(REPO / "research_inputs/registry_v5/INDUSTRY_SECTOR_RATIOS_TODAY_EU27_2019.csv").set_index("sector")


def vec2050(sector: str, t: float) -> dict:
    r = ratios_2050(); out = {k: 0.0 for k in OUTC}
    for k, oc in RATIO_TO_OUT.items():
        out[oc] += float(r.at[k, sector]) * t
    return out


class Chain:
    """Scratch copy of the data chain. run() applies VN edits, runs s3_0 twice (UNSD matrix, then APEC matrix) and returns both VN rows."""

    M08B_OTHER = ("research_inputs/demand_v5/DEMAND_ANCHOR_AEO8_ATS.csv", "research_inputs/demand_v5/INDUSTRY_OUTPUT_2050_M08B.csv",
                  "research_inputs/demand_v5/INDUSTRY_OUTPUT_BASE_M08B.csv")

    def __init__(self, repo: Path = REPO, chain: Path = CHAIN):
        self.repo, self.chain = repo, chain
        self.orig = {rel: (repo / rel).read_bytes() for rel in (CACHE_REL, ATS_REL, D1_REL, APEC_REL, S30_REL) + self.M08B_OTHER}
        self.patched = False

    def m08b(self):
        r = subprocess.run([sys.executable, "m08b_demand.py"], cwd=self.chain / "scripts_project", capture_output=True, text=True, env=dict(ENV))
        if r.returncode:
            raise RuntimeError(r.stderr[-3000:])

    def copy(self):
        if self.chain.exists():
            shutil.rmtree(self.chain)
        self.chain.mkdir(parents=True)
        shutil.copytree(self.repo / "research_inputs", self.chain / "research_inputs")
        shutil.copytree(self.repo / "scripts_project", self.chain / "scripts_project", ignore=shutil.ignore_patterns("__pycache__", "retired"))
        (self.chain / "scripts_project/retired").mkdir(exist_ok=True)

    def restore(self):
        for rel, b in self.orig.items():
            if rel == S30_REL and self.patched:
                continue
            (self.chain / rel).write_bytes(b)

    def patch(self):
        src = self.orig[S30_REL].decode()
        if src.count(PATCH_OLD) != 1:
            raise ValueError("cement electricity line not found exactly once")
        (self.chain / S30_REL).write_text(src.replace(PATCH_OLD, PATCH_NEW)); self.patched = True

    def unpatch(self):
        (self.chain / S30_REL).write_bytes(self.orig[S30_REL]); self.patched = False

    def _s30(self, extra_env: dict | None = None):
        env = dict(ENV); env.update(extra_env or {})
        r = subprocess.run([sys.executable, "s3_0_industry.py"], cwd=self.chain / "scripts_project", capture_output=True, text=True, env=env)
        if r.returncode:
            raise RuntimeError(r.stderr[-3000:])

    def apec_matrix(self) -> pd.DataFrame:
        return pd.read_csv(self.chain / APEC_REL).set_index("cache_subsector")

    def run(self, moves_unsd=(), moves_apec=(), base_delta: dict | None = None, apec_override: pd.DataFrame | None = None,
            cache_ratio: dict | None = None, cem_el_t19: float | None = None, keep_outputs: bool = False, cache_add: dict | None = None,
            d1_delta: dict | None = None) -> dict:
        """moves_*: (subsector, carrier, d_mwh) leaving sub19 of VN in that run (negative d adds); every move must have the same per-carrier
        total in both runs (it changes the shared e19). base_delta: {carrier: d_mwh} added to e19 of the ATS table (growth mode I: multiplier
        unchanged) WITHOUT a matching matrix edit (the shares then spread it over all sub-sectors, e.g. an NCV change of a whole carrier).
        cache_ratio: {(carrier, subsector): factor} on the UNSD matrix (NCV); cache_add: {(carrier, subsector): MWh} added to UNSD matrix cells
        (pair it with base_delta or d1_delta of the same total). d1_delta: {carrier: d_mwh} added to the D1 table, then m08b_demand.py is run
        (growth mode II: AEO8 anchors absolute). apec_override: a replacement APEC-run matrix (any unit, shares only).
        Returns {'main': VN row, 'apec': VN row, 'gaps': VN gap rows, 'pz': VN s3_0 rows, ...}."""
        self.restore()
        if d1_delta:
            d1 = pd.read_csv(self.chain / D1_REL, keep_default_na=False, dtype=str)
            for c, dv in d1_delta.items():
                m = (d1.country == CC) & (d1.sector == "Industry") & (d1.carrier == c)
                if m.sum() != 1:
                    raise ValueError(f"D1 {CC} Industry {c}: {m.sum()} rows")
                d1.loc[m, "base_2019_mwh"] = repr(float(d1.loc[m, "base_2019_mwh"].iloc[0]) + dv)
            (self.chain / D1_REL).write_text(d1.to_csv(index=False))
            self.m08b()
        moves_unsd = [m for m in moves_unsd if abs(m[2]) > 0]; moves_apec = [m for m in moves_apec if abs(m[2]) > 0]
        tot_u = {c: sum(m[2] for m in moves_unsd if m[1] == c) for c in CARS19}
        tot_a = {c: sum(m[2] for m in moves_apec if m[1] == c) for c in CARS19}
        for c in CARS19:
            if abs(tot_u[c] - tot_a[c]) > 1e-6:
                raise ValueError(f"moves differ between the runs for {c}: {tot_u[c]} vs {tot_a[c]}")
        ats = pd.read_csv(self.chain / ATS_REL, keep_default_na=False, dtype=str)
        e19 = {}
        for c in CARS19:
            m = (ats.country == CC) & (ats.sector == "Industry") & (ats.carrier == c)
            if m.sum() != 1:
                raise ValueError(f"{CC} Industry {c}: {m.sum()} rows")
            e19[c] = float(ats.loc[m, "base_2019_mwh"].iloc[0])
        # UNSD matrix (main run): NCV cell ratios first (shares within a carrier), then moves relative to the edited matrix and the edited e19
        cache = json.loads(self.orig[CACHE_REL]); recs = {r["carrier"]: r for r in cache["records"] if r["country"] == CC}
        if cache_ratio:
            for (car, sub), f in cache_ratio.items():
                recs[car][sub] = repr(float(recs[car][sub]) * float(f))
        if cache_add:
            for (car, sub), x in cache_add.items():
                recs[car][sub] = repr(float(recs[car][sub]) + float(x))
        bd = {c: float((base_delta or {}).get(c, 0.0)) for c in CARS19}
        e19_1 = {c: e19[c] + bd[c] for c in CARS19}

        def edit(matrix_get, matrix_set, moves, e_ref):
            by = {}
            for sub, car, dv in moves:
                by.setdefault(car, {}); by[car][sub] = by[car].get(sub, 0.0) + dv
            for car, subs in by.items():
                tot = matrix_get(car, None)
                for sub, dv in subs.items():
                    x = dv * tot / e_ref[car]
                    v = matrix_get(car, sub)
                    if v - x < -1e-6 * max(1.0, abs(v)):
                        raise ValueError(f"{sub} {car}: move {dv} MWh exceeds the matrix cell")
                    matrix_set(car, sub, v - x)

        def u_get(car, sub):
            r = recs[car]
            return sum(float(v) for k, v in r.items() if k not in ("country", "carrier")) if sub is None else float(r[sub])

        def u_set(car, sub, v):
            recs[car][sub] = repr(v)
        edit(u_get, u_set, moves_unsd, e19_1)
        e19_2 = {c: e19_1[c] - tot_u[c] for c in CARS19}
        for c in CARS19:
            if bd[c] or tot_u[c]:
                m = (ats.country == CC) & (ats.sector == "Industry") & (ats.carrier == c)
                ats.loc[m, "base_2019_mwh"] = repr(e19_2[c])
                ats.loc[m, "value_2050_mwh"] = repr(e19_2[c] * float(ats.loc[m, "multiplier_total"].iloc[0]))
        (self.chain / ATS_REL).write_text(ats.to_csv(index=False))
        (self.chain / CACHE_REL).write_text(json.dumps(cache))
        env = {"V4W07_CEM_EL_T19_VN": repr(float(cem_el_t19))} if cem_el_t19 is not None else {}
        if env and not self.patched:
            raise ValueError("cement correction needs the scratch patch")
        self._s30(env)
        dd = self.chain / "research_inputs/demand_v5"
        main = pd.read_csv(dd / SUMMARY).set_index("country").loc[CC].copy()
        gaps = pd.read_csv(dd / "INDUSTRY_2050_GAPS.csv"); gaps = gaps[(gaps["mode"] == "aeo8_ats_anchor") & (gaps.country == CC)].copy()
        pz = pd.read_csv(dd / "INDUSTRY_2050_PYPSA_EUR_aeo8_ats_anchor.csv"); pz = pz[pz.country == CC].copy()
        ob = pd.read_csv(dd / "INDUSTRY_2050_OTHER_BUCKET.csv"); ob = ob[(ob["mode"] == "aeo8_ats_anchor") & (ob.country == CC)].iloc[0].copy()
        outs = {f: (dd / f).read_bytes() for f in S3_OUT} if keep_outputs else None
        # APEC run: VN cache records replaced by the APEC matrix (v3 rule), then the APEC moves relative to e19_2 + tot (the same e19 edit)
        a = (apec_override if apec_override is not None else self.apec_matrix()).copy()
        cache2 = json.loads(self.orig[CACHE_REL])
        for r in cache2["records"]:
            if r["country"] == CC:
                k = APEC_COL[r["carrier"]]
                for s in r:
                    if s not in ("country", "carrier"):
                        r[s] = float(a.at[s, k]) if s in a.index else 0.0
        recs2 = {r["carrier"]: r for r in cache2["records"] if r["country"] == CC}

        def a_get(car, sub):
            r = recs2[car]
            return sum(float(v) for k, v in r.items() if k not in ("country", "carrier")) if sub is None else float(r[sub])

        def a_set(car, sub, v):
            recs2[car][sub] = v
        edit(a_get, a_set, moves_apec, e19_1)
        (self.chain / CACHE_REL).write_text(json.dumps(cache2))
        self._s30(env)
        apec_row = pd.read_csv(dd / SUMMARY).set_index("country").loc[CC].copy()
        gaps_a = pd.read_csv(dd / "INDUSTRY_2050_GAPS.csv"); gaps_a = gaps_a[(gaps_a["mode"] == "aeo8_ats_anchor") & (gaps_a.country == CC)].copy()
        pz_a = pd.read_csv(dd / "INDUSTRY_2050_PYPSA_EUR_aeo8_ats_anchor.csv"); pz_a = pz_a[pz_a.country == CC].copy()
        ob_a = pd.read_csv(dd / "INDUSTRY_2050_OTHER_BUCKET.csv"); ob_a = ob_a[(ob_a["mode"] == "aeo8_ats_anchor") & (ob_a.country == CC)].iloc[0].copy()
        self.restore()
        return dict(main=main, apec=apec_row, gaps=gaps, gaps_apec=gaps_a, pz=pz, pz_apec=pz_a, ob=ob, ob_apec=ob_a, e19=e19_2, outs=outs)


def v3_layer(v3, res: dict, fut: dict, extra: dict | None = None) -> dict:
    """v3 conservation (D163-6 a) for VN: T = route total of the main run + new explicit sub-sectors not in the chain; the decomposition of the
    APEC run; explicit = steel + cement + ammonia + dispersed (+ new); Other = T - explicit, carriers scaled uniformly."""
    extra = extra or {}
    T_chain = float(sum(res["main"][v3.col(x)] for x in v3.CARRIERS))
    parts = v3.decompose(res["apec"], fut); parts.update(extra)
    T = T_chain + sum(sum(v.values()) for v in extra.values())
    expl = sum(sum(v.values()) for k, v in parts.items() if k != "other")
    so = sum(parts["other"].values()); f = (T - expl) / so
    other = {k: v * f for k, v in parts["other"].items()}
    by_sub = {k: sum(v.values()) for k, v in parts.items() if k != "other"}
    T_apec = float(sum(res["apec"][v3.col(x)] for x in v3.CARRIERS))
    return dict(T=T, T_chain=T_chain, T_apec_run=T_apec, other=other, other_total=sum(other.values()), scale=f, explicit=expl, by_sub=by_sub,
                explicit_carriers={k: dict(v) for k, v in parts.items() if k != "other"}, other_unscaled=dict(parts["other"]))


def band_row(lay: dict) -> dict:
    """A6 carrier columns (TWh) of the 'other' bucket."""
    o = lay["other"]
    return dict(elec=o.get("electricity", 0.0) / 1e6, heat_lt150=o.get("heat", 0.0) / 1e6, heat_150_200=o.get("heat_medium_a", 0.0) / 1e6,
                heat_200_400=o.get("heat_medium_b", 0.0) / 1e6, heat_gt400=o.get("heat_high", 0.0) / 1e6, oil=o.get("oil", 0.0) / 1e6,
                gas=o.get("gas", 0.0) / 1e6, coal=o.get("coal", 0.0) / 1e6, biomass=o.get("biomass", 0.0) / 1e6, H2=o.get("hydrogen", 0.0) / 1e6)


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


def same_bytes(a: Path, b: Path) -> bool:
    return filecmp.cmp(a, b, shallow=False)


# ---------------------------------------------------------------- UNSD SDMX (sdmx/*.xml, A5 exception) --------------------------------------
SDMX_FILES = ("VN_coal", "VN_biomass", "VN_gas_elec", "VN_oil_ind")
_G = "{http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic}"


def codelists() -> dict:
    return json.loads((REPO / "research_inputs/assembly_v1/sources/unsd_targeted/codelists.json").read_text())


def sdmx_long() -> pd.DataFrame:
    import xml.etree.ElementTree as ET
    cl = codelists(); rows = []
    for f in SDMX_FILES:
        root = ET.parse(WORK / "sdmx" / f"{f}.xml").getroot()
        for s in root.iter(_G + "Series"):
            key = {v.get("id"): v.get("value") for v in s.find(_G + "SeriesKey")}
            att = {v.get("id"): v.get("value") for v in s.find(_G + "Attributes")} if s.find(_G + "Attributes") is not None else {}
            for o in s.findall(_G + "Obs"):
                oa = {a.get("id"): a.get("value") for a in o.find(_G + "Attributes")} if o.find(_G + "Attributes") is not None else {}
                rows.append(dict(file=f, commodity=key["COMMODITY"], transaction=key["TRANSACTION"], unit=att.get("UNIT_MEASURE"),
                                 year=int(o.find(_G + "ObsDimension").get("value")), value=float(o.find(_G + "ObsValue").get("value")),
                                 unit_mult=oa.get("UNIT_MULT"), obs_status=oa.get("OBS_STATUS"),
                                 conversion_factor=float(oa["CONVERSION_FACTOR"]) if oa.get("CONVERSION_FACTOR") else np.nan))
    d = pd.DataFrame(rows)
    d["commodity_name"] = d.commodity.map(cl["CL_COMMODITY_NRG"]); d["transaction_name"] = d.transaction.map(cl["CL_TRANSACTION_NRG"])
    # energy (TJ): mass or volume units x the SDMX conversion factor (GJ per unit of the thousand-unit quantity = TJ per thousand units);
    # TJ commodities (gas GCV, other vegetal) as reported; GWh x 3.6
    d["tj"] = np.where(d.unit.isin(["TN", "M3"]), d.value * d.conversion_factor, np.where(d.unit == "GWHR", d.value * 3.6, np.where(d.unit == "TJ", d.value, np.nan)))
    return d


def frozen_factors() -> dict:
    return json.loads((REPO / "research_inputs/assembly_v1/sources/FROZEN_UPSTREAM_CONVERSIONS.json").read_text())["constants"]["fuels_conv_toTWh"]


def capsule_vn_2019() -> pd.DataFrame:
    c = json.loads((REPO / "research_inputs/assembly_v1/sources/UNSD_2019_SOURCE_CAPSULE.json").read_text())
    r = pd.DataFrame(c["records"])
    return r[r.Country == CC].copy()
