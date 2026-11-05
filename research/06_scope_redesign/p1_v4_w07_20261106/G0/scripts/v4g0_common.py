"""V4 W07 G0 (Indonesia final, decisions 203-207): shared helpers - paths, input pinning, the scratch copy of the repository data chain with
the coal-NCV edit at UNSD-row level, physical moves between UNSD sub-sectors, the cement-(ii) scratch patch, and the v3 conservation layer.

Nothing here writes into the repository worktree. The scratch copy is /home/jin/v4w07_g0/chain (research_inputs + scripts_project of the G0
worktree /home/jin/wt_v4_g0, branched from codex/v4-data-20261105 at 07e08f38).

Chain edits (scratch copy only; method of S2 v4s2_common.Chain and W11 v4ncv_chain, combined):
  * coal NCV (decision 207; W11 section 4.2 item 5: first the UNSD rows, then the physical deductions at the same NCV): every ID industry
    coal cell of industry_cache.json is multiplied by (energy at the new NCV) / (energy at the v3 NCV) of its own UNSD hard-coal tonnes
    (coke-oven coke unchanged), and the ATS-anchor Industry coal base_2019_mwh moves by the same total; value_2050_mwh = base x the
    unchanged multiplier_total (growth reading I, decision 204 item 1). The cache coal sum equals the D1 base before and after.
  * moves (sub-sector, carrier, d MWh): d leaves sub19[sub][carrier]; the cache cell is lowered by d x sum(cache) / e19 and e19 by d, which
    lowers exactly that sub-sector (s3_0 splits e19 by cache shares; ID gas / oil cache sums differ from e19). Negative d adds energy.
  * cement correction (ii): one scratch-only line of s3_0_industry.py reads the 2019 cement tonnes of the grinding electricity from the
    environment (V4S2_CEM_EL_T19_ID = USGS 71.9 Mt); without the variable the outputs are byte-identical (checked).
  * growth reading II (comparison only, NCV step): the NCV delta goes to the D1 ratio table instead and m08b_demand.py re-solves the RAS.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

WORK = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w07_20261106/G0")
INSTR = WORK.parent / "V4_W07_INSTRUCTION.md"
REPO = Path("/home/jin/wt_v4_g0")
CHAIN = Path("/home/jin/v4w07_g0/chain")
MAIN = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model")   # regions_onshore.geojson (as S1 / S2)
S2D = REPO / "research/06_scope_redesign/p1_v4_data_20261105"              # S0 / S1 / S2 deliverables as committed at 07e08f38 (read only)
W11D = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_ncv_20261106")     # W11 deliverable (branch codex/v4-ncv-20261106 a3ad32b5; read only)
S2WORK = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_data_20261105")   # downloads/ (FAOSTAT, SFI, GEM, Wei 2020) - not in git, read only
SUMMARY = "INDUSTRY_2050_SUMMARY_aeo8_ats_anchor_OTHER_USEFUL_HEAT_BANDS.csv"
CACHE_REL = "research_inputs/assembly_v1/sources/industry_cache.json"
ATS_REL = "research_inputs/demand_v5/DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv"
D1_REL = "research_inputs/demand_v5/DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER.csv"
S30_REL = "scripts_project/s3_0_industry.py"
S3_OUT = ["INDUSTRY_2050_SUMMARY_aeo8_ats_anchor.csv", SUMMARY, "INDUSTRY_2050_OTHER_BUCKET.csv", "INDUSTRY_2050_PYPSA_EUR_aeo8_ats_anchor.csv"]
M08B_OUT = ["DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv", "DEMAND_ANCHOR_AEO8_ATS.csv", "INDUSTRY_OUTPUT_2050_M08B.csv", "INDUSTRY_OUTPUT_BASE_M08B.csv"]
OUTC = ("electricity", "heat", "heat_medium_a", "heat_medium_b", "heat_high", "coal", "oil", "gas", "biomass", "hydrogen", "ammonia", "methanol")
CARS19 = ("coal", "oil", "gas", "biomass", "electricity")
FUELS = ("coal", "oil", "gas", "biomass")
FOSSIL = ("coal", "oil", "gas")
CHEM = "chemical and petrochemical"
ENV = {"PYTHONHASHSEED": "0", "PATH": "/usr/bin:/bin"}
PATCH_OLD = 'el19 = float(ratios.at["elec", "Cement"]) * cem_t19'
PATCH_NEW = 'el19 = float(ratios.at["elec", "Cement"]) * float(__import__("os").environ.get(f"V4S2_CEM_EL_T19_{c}", cem_t19))   # V4 S2 / W07 G0 scratch-only patch (cement correction ii)'
USGS_CEMENT_2019_T = 71.9e6   # USGS MYB 2023 Indonesia table 1 (S1 / S2)

# ---- coal NCV (GJ/t) ---------------------------------------------------------------------------------------------------------------------
F_HARD_V3_TWH_PER_KT = 0.007167   # FROZEN_UPSTREAM_CONVERSIONS.json fuels_conv_toTWh 'Hard coal' (pypsa-asean get_conv_factors)
F_COKE_V3_TWH_PER_KT = 0.0078334  # 'Coke-oven coke' (unchanged by every scheme)
NCV_V3 = F_HARD_V3_TWH_PER_KT * 3600.0   # 25.8012 GJ/t
NCV = {"v3": NCV_V3,
       "207": 20.29,                       # decision 207 item 2: HEESI 'average coal' 3.4554 BOE/t (used from 2023), main
       "unsd": 24.4800154511,              # W11 (b): UN Energy Balances 2019 TJ / UNdata kt, VERIFIED (sensitivity)
       "ipcc": 18.9}                       # W11 (d): IPCC 2006 sub-bituminous default (sensitivity)
NCV_LABEL = {"v3": "v3 25.80", "207": "207: 20.29", "unsd": "UNSD 24.48", "ipcc": "IPCC 18.9"}
HEESI_AVG_COAL_EXACT = 3.4554 * 3.6 / 0.6130   # 20.2928 GJ/t (BOE = 3.6 / 0.6130 GJ, W11 section 2.2); the instruction's 20.29 is used
# UNSD 2019 ID industry coal tonnes by cache sub-sector (W11 ncv/NCV_CACHE_RATIOS_2019.csv 'commodities', VERIFIED against the cache cells)
COKE_KT = {"iron and steel": 520.3, CHEM: 0.0, "other": 57.8}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def jdump(obj, p: Path):
    p.write_text(json.dumps(obj, indent=1, ensure_ascii=False, default=lambda x: float(x) if isinstance(x, (np.floating, np.integer)) else str(x)) + "\n", encoding="utf-8")


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


def growth(y_b: int, country: str = "ID") -> float:
    """S0 R2: G^((2050 - y_b)/28 x 0.5), G = AEO8 table D.2 real GDP 2050 / 2022 (v3 ammonia / non-ferrous rule)."""
    rule = pd.read_csv(REPO / "research_inputs/demand_v5/INDUSTRY_OUTPUT_2050_M08B.csv").set_index("country")
    return float(rule.at[country, "gdp_growth_2022_2050"]) ** ((2050 - y_b) / 28.0 * 0.5)


def import_v3():
    sys.path.insert(0, str(REPO / "scripts_project"))
    import v3_industry as v3   # noqa: E402  (ROOT = G0 worktree; read only)
    return v3


def spread(fuel_mwh: float, el_mwh: float, mix: dict, fuels=FUELS) -> dict:
    """s3_0_industry spread(): fuel over the given fuel mix, electricity separately."""
    ft = sum(mix[f] for f in fuels)
    out = {f: (fuel_mwh * mix[f] / ft if ft else 0.0) for f in fuels}
    out["electricity"] = el_mwh
    return out


def v3_layer(v3, row, fut, nf: dict, extra: dict | None = None) -> dict:
    """v3 conservation (D163-6 a): T = route total of the chain row + new explicit sub-sectors not in the chain; explicit = steel + cement +
    ammonia + dispersed + non-ferrous + new; Other = T - explicit, carriers scaled uniformly (same as S2 v4s2_common.v3_layer)."""
    extra = extra or {}
    T_chain = float(sum(row[v3.col(x)] for x in v3.CARRIERS))
    parts = v3.decompose(row, fut); parts.update(nf); parts.update(extra)
    T = T_chain + sum(sum(v.values()) for v in extra.values())
    expl = sum(sum(v.values()) for k, v in parts.items() if k != "other")
    so = sum(parts["other"].values()); f = (T - expl) / so
    other = {k: v * f for k, v in parts["other"].items()}
    by_sub = {k: sum(v.values()) for k, v in parts.items() if k != "other"}
    return dict(T=T, T_chain=T_chain, other=other, other_total=sum(other.values()), scale=f, explicit=expl, by_sub=by_sub,
                explicit_carriers={k: dict(v) for k, v in parts.items() if k != "other"}, other_unscaled=dict(parts["other"]))


class Chain:
    def __init__(self, repo: Path = REPO, chain: Path = CHAIN):
        self.repo, self.chain = repo, chain
        self.orig = {k: (repo / rel).read_bytes() for k, rel in (("cache", CACHE_REL), ("ats", ATS_REL), ("d1", D1_REL), ("s30", S30_REL))}
        self.m08b_out = {f: (repo / "research_inputs/demand_v5" / f).read_bytes() for f in M08B_OUT if f != Path(ATS_REL).name}   # regenerated by mode II
        self.patched = False
        self.last = {}

    # ---------------------------------------------------------------- copy / patch / restore
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
        for k, rel in (("cache", CACHE_REL), ("ats", ATS_REL), ("d1", D1_REL)):
            (self.chain / rel).write_bytes(self.orig[k])
        for f, b in self.m08b_out.items():
            (self.chain / "research_inputs/demand_v5" / f).write_bytes(b)

    # ---------------------------------------------------------------- edits (in memory)
    @staticmethod
    def ncv_cells(cache: dict, F: float, country: str = "ID") -> dict:
        """Coal cells of `country` at hard-coal NCV F (GJ/t): {sub: (v3_mwh, new_mwh, hard_coal_kt)}; coke-oven coke unchanged."""
        rec = [r for r in cache["records"] if r["country"] == country and r["carrier"] == "coal"]
        if len(rec) != 1:
            raise ValueError("coal record")
        out = {}
        for k, v in rec[0].items():
            if k in ("country", "carrier"):
                continue
            v = float(v)
            if v == 0.0:
                continue
            if k not in COKE_KT:
                raise ValueError(f"unexpected ID coal cache cell {k}")
            hc_kt = (v - COKE_KT[k] * F_COKE_V3_TWH_PER_KT * 1e6) / (F_HARD_V3_TWH_PER_KT * 1e6)
            out[k] = (v, v + hc_kt * 1e3 * (F - NCV_V3) / 3.6, hc_kt)
        return out

    def edited(self, ncv: float | None = None, moves=(), country: str = "ID", table: str = "ats"):
        """Apply the NCV edit, then the moves, to the original cache and the ATS (or D1) table; returns (cache, table, log)."""
        cache = json.loads(self.orig["cache"])
        d = pd.read_csv(io.BytesIO(self.orig[table]), keep_default_na=False, dtype=str)
        log = dict(ncv={}, moves=[])
        msel = (d.country == country) & ((d.sector == "Industry") if table == "ats" else (d.account == "IndustryFinalEnergy") | (d.account == "UNSD_electricity_Industry"))

        def row(car):
            m = msel & (d.carrier == car)
            if table == "d1" and car == "electricity":
                m = (d.country == country) & (d.account == "UNSD_electricity_Industry") & (d.carrier == car)
            elif table == "d1":
                m = (d.country == country) & (d.account == "IndustryFinalEnergy") & (d.carrier == car)
            if m.sum() != 1:
                raise ValueError(f"{table}: {country} Industry {car}: {m.sum()} rows")
            return m

        def set_base(m, b):
            d.loc[m, "base_2019_mwh"] = repr(b)
            if table == "ats":
                d.loc[m, "value_2050_mwh"] = repr(b * float(d.loc[m, "multiplier_total"].iloc[0]))

        recs = {r["carrier"]: r for r in cache["records"] if r["country"] == country}
        if ncv is not None and abs(ncv - NCV_V3) > 1e-12:
            cells = self.ncv_cells(cache, ncv, country)
            r = recs["coal"]; tot0 = sum(float(v) for k, v in r.items() if k not in ("country", "carrier"))
            m = row("coal"); e19 = float(d.loc[m, "base_2019_mwh"].iloc[0])
            if abs(tot0 - e19) > 1e-3:
                raise ValueError(f"coal cache sum {tot0} != D1 base {e19}")
            dlt = 0.0
            for k, (v0, v1, kt) in cells.items():
                r[k] = repr(float(r[k]) * (v1 / v0)); dlt += v1 - v0
                log["ncv"][k] = dict(v3_mwh=v0, new_mwh=v1, hard_coal_kt=kt)
            set_base(m, e19 + dlt)
            log["ncv"]["_delta_mwh"] = dlt; log["ncv"]["_F"] = ncv
        by_car = {}
        for sub, car, dv in moves:
            if abs(dv) > 0:
                by_car.setdefault(car, {}); by_car[car][sub] = by_car[car].get(sub, 0.0) + dv
        for car, subs in by_car.items():
            r = recs[car]
            tot = sum(float(v) for k, v in r.items() if k not in ("country", "carrier"))
            m = row(car); e19 = float(d.loc[m, "base_2019_mwh"].iloc[0])
            for sub, dv in subs.items():
                x = dv * tot / e19
                if float(r[sub]) - x < -1e-6:
                    raise ValueError(f"{country} {sub} {car}: move {dv} MWh exceeds the cache cell {r[sub]}")
                r[sub] = repr(float(r[sub]) - x)
                log["moves"].append(dict(sub=sub, carrier=car, d_mwh=dv))
            set_base(m, e19 - sum(subs.values()))
        return cache, d, log

    def sub19(self, ncv=None, moves=(), country: str = "ID") -> dict:
        """2019 energy per (UNSD sub-sector, carrier) as s3_0 splits it (e19 x cache / sum cache), after the edits; no run needed."""
        cache, d, _ = self.edited(ncv, moves, country)
        out = {}
        for r in cache["records"]:
            if r["country"] != country:
                continue
            car = r["carrier"]; tot = sum(float(v) for k, v in r.items() if k not in ("country", "carrier"))
            e19 = float(d[(d.country == country) & (d.sector == "Industry") & (d.carrier == car)].base_2019_mwh.astype(float).iloc[0])
            for k, v in r.items():
                if k not in ("country", "carrier"):
                    out.setdefault(k, {})[car] = e19 * float(v) / tot if tot else 0.0
        return out

    def ats_industry(self, ncv=None, moves=(), country: str = "ID") -> dict:
        _, d, _ = self.edited(ncv, moves, country)
        z = d[(d.country == country) & (d.sector == "Industry")]
        return dict(base_2019_mwh=float(z.base_2019_mwh.astype(float).sum()), value_2050_mwh=float(z.value_2050_mwh.astype(float).sum()),
                    by_carrier={c: float(v) for c, v in zip(z.carrier, z.value_2050_mwh.astype(float))})

    # ---------------------------------------------------------------- run
    def _exec(self, script: str, env: dict):
        r = subprocess.run([sys.executable, script], cwd=self.chain / "scripts_project", capture_output=True, text=True, env=env)
        if r.returncode:
            raise RuntimeError(f"{script}: {r.stderr[-3000:]}")

    def run(self, ncv=None, moves=(), cem: bool = False, country: str = "ID", mode: str = "I"):
        """Edit (scratch copy), run s3_0_industry.py (mode II: m08b_demand.py first), return (summary row, other-bucket row, s3_0 sub-sector rows)."""
        self.restore()
        if mode == "I":
            if ncv is not None or moves:
                cache, d, log = self.edited(ncv, moves, country, "ats")
                (self.chain / CACHE_REL).write_text(json.dumps(cache)); d.to_csv(self.chain / ATS_REL, index=False)
            else:
                log = {}
        else:   # growth reading II: NCV delta on the D1 ratio table, RAS re-solved by m08b
            if moves:
                raise ValueError("mode II is used for the NCV step only")
            cache, d, log = self.edited(ncv, (), country, "d1")
            (self.chain / CACHE_REL).write_text(json.dumps(cache)); d.to_csv(self.chain / D1_REL, index=False)
            self._exec("m08b_demand.py", dict(ENV))
        env = dict(ENV)
        if cem:
            if not self.patched:
                raise ValueError("cement correction needs the scratch patch")
            env[f"V4S2_CEM_EL_T19_{country}"] = repr(float(USGS_CEMENT_2019_T))
        self._exec("s3_0_industry.py", env)
        dd = self.chain / "research_inputs/demand_v5"
        row = pd.read_csv(dd / SUMMARY).set_index("country").loc[country]
        ob = pd.read_csv(dd / "INDUSTRY_2050_OTHER_BUCKET.csv")
        ob = ob[(ob["mode"] == "aeo8_ats_anchor") & (ob.country == country)].iloc[0]
        pz = pd.read_csv(dd / "INDUSTRY_2050_PYPSA_EUR_aeo8_ats_anchor.csv")
        pz = pz[pz.country == country]
        ats = pd.read_csv(self.chain / ATS_REL, keep_default_na=False)
        ats = ats[(ats.country == country) & (ats.sector == "Industry")]
        self.last = dict(log=log, ats_2050_mwh=float(pd.to_numeric(ats.value_2050_mwh).sum()), ats_2019_mwh=float(pd.to_numeric(ats.base_2019_mwh).sum()))
        return row, ob, pz
