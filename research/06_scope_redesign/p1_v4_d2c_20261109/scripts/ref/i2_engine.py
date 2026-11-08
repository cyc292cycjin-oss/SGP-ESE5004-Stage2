"""I2 unified recompute engine: one scratch copy of the repository data chain (/home/jin/v4i2/chain, outside the repository) that evaluates a
'case' for all eleven countries at once. Nothing is solved; the repository is never written.

Chain (repository code, run unchanged except the scratch-only patches below):
  D1 base table (2019 seed)  --m08b_demand.py-->  ATS anchor table + anchors  --(reading-I edits, sub-sector moves)-->  s3_0_industry.py
  --> INDUSTRY_2050_SUMMARY_aeo8_ats_anchor_OTHER_USEFUL_HEAT_BANDS.csv  --> v3 conservation layer (v3_industry.decompose + explicit products)
Scratch-only patches (each is a no-op without its environment variable; the gate checks the byte identity):
  m08b_demand.py  I1 anchor-variant block (I1_ANCHOR_MODE ras | frozen | fixedcol | independent; I1/scripts/i1_chain.py PATCH_BLOCK, copied) plus
                  the I2 anchor boundary alignment (decision 210 item 4 a): I2_ANCHOR_ADJ = {country: residue MWh removed from the seed that the
                  national balance contains}; in mode fixedcol (IId) the country's sector split is computed with the residue still in the industry
                  seed and the industry anchor is then lowered by residue x the industry multiplier (all other sector anchors and every multiplier
                  unchanged; the country TFEC anchor falls by the 2050 equivalent of the residue);
  s3_0_industry.py  cement correction (ii): grinding electricity on the USGS 2019 cement tonnes (env V4S2_CEM_EL_T19_<cc>; S2 / G0 line, copied);
                  W12 F7: solid-biomass cap share (env I2_BIO_CAP_SHARE, default 1.0) in the overflow rule.
Case keys (all optional): d1 (pd.Series base_2019_mwh by (country, sector, carrier, account) or None = repository), anchor_mode ('ras' default /
'frozen' / 'fixedcol' / 'I' = no m08b run), anchor_adj {cc: MWh}, ats_add [(cc, carrier, d_base_mwh)] (reading-I base change, multiplier kept),
cache (dict, default repository), vn_cache (dict for the VN decomposition run: 'apec' = v3 rule with the APEC matrix; dict = matrix of the
same run when vn_same_run), moves [(cc, sub, carrier, d_mwh)], products {cc: [item]}, cem {cc: t}, edgar_zero [cc], meoh_drop [cc],
bio_cap_share, biopot (bytes of a BIOMASS_POTENTIAL_2050.csv), nf {cc: {key: vector}}, extra {cc: {key: vector}} (2050 vectors without a 2019
deduction), bn_iii (bool), vn_same_run (bool).
"""
from __future__ import annotations

import copy
import hashlib
import io
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import i2_common as cm  # noqa: E402
from d1_common import fmt  # noqa: E402

CHAIN = cm.SCRATCH / "chain"
DV = "research_inputs/demand_v5"
D1_REL = f"{DV}/DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER.csv"
ATS_REL = f"{DV}/DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv"
ANCH_REL = f"{DV}/DEMAND_ANCHOR_AEO8_ATS.csv"
OUTRULE_REL = f"{DV}/INDUSTRY_OUTPUT_2050_M08B.csv"
BASEOUT_REL = f"{DV}/INDUSTRY_OUTPUT_BASE_M08B.csv"
CACHE_REL = "research_inputs/assembly_v1/sources/industry_cache.json"
EDGAR_REL = "research_inputs/registry_v5/sources/EDGAR2025_IPPU_FUGITIVE_WASTE_ASEAN11_2019.csv"
BIOPOT_REL = "research_inputs/biomass_v5/BIOMASS_POTENTIAL_2050.csv"
APEC_REL = "research_inputs/industry_v3/APEC2022_VN_INDUSTRY_PJ.csv"
SUMMARY = "INDUSTRY_2050_SUMMARY_aeo8_ats_anchor_OTHER_USEFUL_HEAT_BANDS.csv"
M08B_OUT = ["DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv", "DEMAND_ANCHOR_AEO8_ATS.csv", "INDUSTRY_OUTPUT_2050_M08B.csv", "INDUSTRY_OUTPUT_BASE_M08B.csv"]
S30_OUT = ["INDUSTRY_2050_SUMMARY_aeo8_ats_anchor.csv", SUMMARY, "INDUSTRY_2050_OTHER_BUCKET.csv", "INDUSTRY_2050_PYPSA_EUR_aeo8_ats_anchor.csv"]
KEY = ["country", "sector", "carrier", "account"]
EV_FACTOR = 0.30215   # oil_to_electricity x ev_share 1 (v3.1 networks; W12 section 3.2, I1 i1_chain.py)
CHEM = "chemical and petrochemical"
NMM = "non-metallic minerals"
APEC_COL = dict(coal="coal_pj", oil="oil_pj", gas="gas_pj", biomass="biomass_pj", electricity="electricity_pj")

# ---- scratch-only patches ---------------------------------------------------------------------------------------------------------------------
M08B_PATCH_POINT = '    tfa["TL"] = {s: A_tfec["TL"] * w_tl[s] / w_tl_sum for s in SECTORS}\n'
M08B_PATCH_BLOCK = M08B_PATCH_POINT + '''    # ---- I1 scratch-only patch (anchor construction variants; default 'ras' leaves the repository code path unchanged) ----
    import os as _i1os
    _i1m = _i1os.environ.get("I1_ANCHOR_MODE", "ras")
    if _i1os.environ.get("I1_DUMP_ANCHORS"):
        json.dump(dict(tfa={c: {s: tfa[c][s] for s in SECTORS} for c in ASEAN}, t19={c: {s: t19[c][s] for s in SECTORS} for c in ASEAN}),
                  open(_i1os.environ["I1_DUMP_ANCHORS"], "w"))
    if _i1m == "frozen":
        _i1f = json.load(open(_i1os.environ["I1_FROZEN_ANCHORS"]))["tfa"]
        tfa = {c: {s: float(_i1f[c][s]) for s in SECTORS} for c in ASEAN}
    elif _i1m == "fixedcol":
        # RAS solution X = diag(r) seed diag(s): keep the v3 column factors s (taken from ID, all five seeds positive; the row factor cancels
        # in the normalisation), country totals from AEO8, sector split from the country's own (corrected) seed; no column constraint
        _i1d = json.load(open(_i1os.environ["I1_FROZEN_ANCHORS"]))
        _i1s = {s: _i1d["tfa"]["ID"][s] / _i1d["t19"]["ID"][s] for s in SECTORS}
        for c in ASEAN10:
            _i1w = {s: t19[c][s] * _i1s[s] for s in SECTORS}; _i1ws = sum(_i1w.values())
            tfa[c] = {s: A_tfec[c] * _i1w[s] / _i1ws for s in SECTORS}
        # ---- I2 scratch-only patch (decision 210 item 4 a): residues removed from the seed that the national balance contains ----
        if _i1os.environ.get("I2_ANCHOR_ADJ"):
            for c, _i2r in json.load(open(_i1os.environ["I2_ANCHOR_ADJ"])).items():
                if c not in ASEAN10 or not _i2r:
                    continue
                _i2seed = {s: t19[c][s] + (float(_i2r) if s == "Industry" else 0.0) for s in SECTORS}
                _i2w = {s: _i2seed[s] * _i1s[s] for s in SECTORS}; _i2ws = sum(_i2w.values())
                _i2t = {s: A_tfec[c] * _i2w[s] / _i2ws for s in SECTORS}
                _i2t["Industry"] = _i2t["Industry"] / _i2seed["Industry"] * t19[c]["Industry"]
                tfa[c] = _i2t
    elif _i1m == "independent":
        for c in ASEAN10:
            _i1w = {s: t19[c][s] * g_tfec[s] for s in SECTORS}; _i1ws = sum(_i1w.values())
            tfa[c] = {s: A_tfec[c] * _i1w[s] / _i1ws for s in SECTORS}
    if _i1os.environ.get("I2_ANCHOR_ADJ") and _i1m in ("ras", "frozen"):
        # ---- W08 scratch-only patch (decision 211 item 1): the residue anchor alignment applies in every anchor mode. 'ras' (IIa): RAS refit
        #      with the residue still in the industry seed of the countries whose national balance contains it (same row / column targets);
        #      then, as in IId, the industry anchor falls by residue x the industry multiplier (other sector anchors and every multiplier kept)
        _w8adj = {c: float(v) for c, v in json.load(open(_i1os.environ["I2_ANCHOR_ADJ"])).items() if c in ASEAN10 and v}
        if _i1m == "ras":
            _w8seed = np.array([[t19[c][s] + (_w8adj.get(c, 0.0) if s == "Industry" else 0.0) for s in SECTORS] for c in ASEAN10])
            _w8X, _w8it, _w8er, _w8ec = ras_split(_w8seed, row_t, col_t)
            for _w8i, c in enumerate(ASEAN10):
                tfa[c] = {s: float(_w8X[_w8i, j]) for j, s in enumerate(SECTORS)}
        for c, _w8r in _w8adj.items():
            tfa[c] = dict(tfa[c]); tfa[c]["Industry"] = tfa[c]["Industry"] / (t19[c]["Industry"] + _w8r) * t19[c]["Industry"]
'''
CEM_OLD = 'el19 = float(ratios.at["elec", "Cement"]) * cem_t19'
CEM_NEW = 'el19 = float(ratios.at["elec", "Cement"]) * float(__import__("os").environ.get(f"V4S2_CEM_EL_T19_{c}", cem_t19))   # V4 S2 / W07 / I2 scratch-only patch (cement correction ii)'
POT_OLD = 'pot = float(solid_pot.get(c, 0.0)); overflow = max(0.0, pe["biomass"] + ag_bio_50 - pot)'
POT_NEW = ('pot = float(solid_pot.get(c, 0.0)) * float(__import__("os").environ.get("I2_BIO_CAP_SHARE", "1.0")); overflow = max(0.0, pe["biomass"] + ag_bio_50 - pot)'
           '   # I2 scratch-only patch (W12 F7 cap margin)')


def fsum(d: dict) -> float:
    return float(sum(d.values()))


def template(tab: pd.DataFrame, c: str, sec: str, car: str) -> pd.Series:
    """I1 i1_chain.template (copied): a row of the same country / sector / electricity-or-not to clone for a new key."""
    for cond in ((tab.country == c) & (tab.sector == sec) & ((tab.carrier == "electricity") == (car == "electricity")),
                 (tab.country == c) & (tab.sector == sec), (tab.sector == sec)):
        t = tab[cond]
        if len(t):
            return t.iloc[0].copy()
    raise KeyError((c, sec, car))


def write_d1(orig: bytes, case: pd.Series, s0: pd.Series) -> bytes:
    """I1 i1_chain.write_table kind 'd1' (copied): base strings via d1_common.fmt (the D1 writer); value_2050 = base x multiplier_total."""
    tab = pd.read_csv(io.BytesIO(orig), keep_default_na=False, dtype=str)
    idx = {tuple(r): i for i, r in zip(tab.index, tab[KEY].values)}
    for k in sorted(set(case.index) | set(s0.index)):
        new = float(case.get(k, 0.0)); old = float(s0.get(k, 0.0))
        if new == old:
            continue
        if k in idx:
            i = idx[k]
            tab.at[i, "base_2019_mwh"] = fmt(new)
            mult = tab.at[i, "multiplier_total"]
            if tab.at[i, "value_2050_mwh"] != "":
                tab.at[i, "value_2050_mwh"] = fmt(new * float(mult)) if mult not in ("", None) else fmt(new)
        else:
            t = template(tab, k[0], k[1], k[2])
            t["country"], t["sector"], t["carrier"], t["account"] = k
            t["base_2019_mwh"] = fmt(new)
            mult = t["multiplier_total"]
            t["value_2050_mwh"] = fmt(new * float(mult)) if mult not in ("", None) else fmt(new)
            for col in ("base_status", "status"):
                if col in t:
                    t[col] = "I2_SCRATCH_NEW_ROW"
            if "in_existing_electricity_load" in t and k[2] != "electricity":
                t["in_existing_electricity_load"] = "False"
            if "existing_electricity_load_2050_mwh" in t and k[2] != "electricity":
                t["existing_electricity_load_2050_mwh"] = ""
            tab = pd.concat([tab, t.to_frame().T], ignore_index=True)
            idx[k] = tab.index[-1]
    buf = io.StringIO(); tab.to_csv(buf, index=False, lineterminator="\n")
    return buf.getvalue().encode()


def write_ats_I(orig: bytes, case: pd.Series, s0: pd.Series) -> bytes:
    """I1 i1_chain.write_table kind 'ats_I' (copied): reading I - base and value_2050 = base x the repository multiplier_total, repr floats."""
    tab = pd.read_csv(io.BytesIO(orig), keep_default_na=False, dtype=str)
    idx = {tuple(r): i for i, r in zip(tab.index, tab[KEY].values)}
    for k in sorted(set(case.index) | set(s0.index)):
        new = float(case.get(k, 0.0)); old = float(s0.get(k, 0.0))
        if new == old:
            continue
        if k in idx:
            i = idx[k]
            tab.at[i, "base_2019_mwh"] = repr(new)
            mult = tab.at[i, "multiplier_total"]
            if tab.at[i, "value_2050_mwh"] != "":
                tab.at[i, "value_2050_mwh"] = repr(new * float(mult)) if mult not in ("", None) else repr(new)
        else:
            t = template(tab, k[0], k[1], k[2])
            t["country"], t["sector"], t["carrier"], t["account"] = k
            t["base_2019_mwh"] = repr(new)
            mult = t["multiplier_total"]
            t["value_2050_mwh"] = repr(new * float(mult)) if mult not in ("", None) else repr(new)
            tab = pd.concat([tab, t.to_frame().T], ignore_index=True)
            idx[k] = tab.index[-1]
    buf = io.StringIO(); tab.to_csv(buf, index=False, lineterminator="\n")
    return buf.getvalue().encode()


def _ov_d2a(L: dict, row_T) -> tuple:
    """V4 D2a (Fable F-02): overflow of the conservation-layer biomass (T_v2 incl. the product vectors) against the s3_0 cap (cap share x potential),
    industry first, then agriculture - the rule of s3_0 / the build applied after the products."""
    bio = float(L["T_car"].get("biomass", 0.0)); ag = float(row_T.get("agriculture_biomass_2050_mwh", 0.0)); cap = float(row_T.get("solid_biomass_potential_main_mwh", 0.0))
    ov = max(0.0, bio + ag - cap); ov_ind = min(ov, bio)
    return ov_ind, min(ov - ov_ind, ag)


class Engine:
    def __init__(self, fresh: bool = True):
        self.t0 = time.time(); self.n_m08b = self.n_s30 = 0; self.m08b_cache = {}
        self.orig = {rel: (cm.REPO / rel).read_bytes() for rel in (D1_REL, ATS_REL, ANCH_REL, OUTRULE_REL, BASEOUT_REL, CACHE_REL, EDGAR_REL, BIOPOT_REL, APEC_REL)}
        self.repo_s30 = {f: (cm.DEMAND / f).read_bytes() for f in S30_OUT}
        if fresh or not CHAIN.exists():
            if CHAIN.exists():
                shutil.rmtree(CHAIN)
            CHAIN.mkdir(parents=True)
            shutil.copytree(cm.REPO / "research_inputs", CHAIN / "research_inputs")
            shutil.copytree(cm.REPO / "scripts_project", CHAIN / "scripts_project", ignore=shutil.ignore_patterns("__pycache__", "retired"))
            (CHAIN / "scripts_project/retired").mkdir(exist_ok=True)
        self.patch_src = {}
        for f, pairs in (("m08b_demand.py", [(M08B_PATCH_POINT, M08B_PATCH_BLOCK)]), ("s3_0_industry.py", [(CEM_OLD, CEM_NEW), (POT_OLD, POT_NEW)])):
            src = (cm.SP / f).read_text()
            for old, new in pairs:
                if src.count(old) != 1:
                    raise SystemExit(f"STOP: patch point not unique in {f}")
                src = src.replace(old, new)
            (CHAIN / "scripts_project" / f).write_text(src); self.patch_src[f] = cm.sha256_bytes(src.encode())
        self.frozen = cm.SCRATCH / "anchors_v3_ras.json"
        import v3_industry as v3   # noqa: E402  (repository module, read only)
        self.v3 = v3; self.fut = v3.future_vectors(); self.ne = v3.nickel_unit_energy()
        self.nf = {case: v3.nonferrous(self.fut, case, self.ne)[0] for case in ("main", "nf2023")}
        self.rule = pd.read_csv(cm.DEMAND / "INDUSTRY_OUTPUT_2050_M08B.csv").set_index("country")
        self.gate = None

    # ------------------------------------------------------------------------------------------------------------------------------ runs
    def _exec(self, script: str, env: dict):
        r = subprocess.run([cm.PY, script], cwd=CHAIN / "scripts_project", capture_output=True, text=True, env={**cm.ENV, **env})
        if r.returncode:
            raise RuntimeError(f"{script}: {r.stderr[-3000:]}")

    def restore(self):
        for rel, b in self.orig.items():
            (CHAIN / rel).write_bytes(b)

    def reproduce(self) -> dict:
        """Gate (instruction section 7 stop condition): the patched, unmodified copy reproduces the repository byte for byte - m08b (default
        mode) + s3_0 = 8 files, s3_0 alone = 4 files - and writes the v3 anchors used by the IId / IIb variants."""
        self.restore()
        self._exec("m08b_demand.py", {"I1_DUMP_ANCHORS": str(self.frozen)}); self._exec("s3_0_industry.py", {})
        same8 = {f: (CHAIN / DV / f).read_bytes() == (cm.DEMAND / f).read_bytes() for f in M08B_OUT + S30_OUT}
        self.restore(); self._exec("s3_0_industry.py", {})
        same4 = {f: (CHAIN / DV / f).read_bytes() == (cm.DEMAND / f).read_bytes() for f in S30_OUT}
        self.restore()
        self.gate = dict(m08b_s30_byte_identical=same8, s30_byte_identical=same4, patch_sha256=self.patch_src)
        if not (all(same8.values()) and all(same4.values())):
            raise SystemExit(f"STOP: the unmodified scratch copy does not reproduce the repository outputs: {self.gate}")
        return self.gate

    def m08b(self, d1: bytes | None, mode: str, adj: dict | None) -> dict:
        key = hashlib.sha256((d1 or b"REPO") + mode.encode() + json.dumps(adj or {}, sort_keys=True).encode()).hexdigest()
        if key in self.m08b_cache:
            return self.m08b_cache[key]
        if mode == "I" or (d1 is None and mode == "ras" and not adj):
            out = {rel: self.orig[rel] for rel in (ATS_REL, ANCH_REL, OUTRULE_REL, BASEOUT_REL)}
        else:
            (CHAIN / D1_REL).write_bytes(d1 if d1 is not None else self.orig[D1_REL])
            env = {"I1_ANCHOR_MODE": mode, "I1_FROZEN_ANCHORS": str(self.frozen)}
            if adj:
                p = cm.SCRATCH / f"anchor_adj_{key[:12]}.json"; p.write_text(json.dumps(adj)); env["I2_ANCHOR_ADJ"] = str(p)
            self._exec("m08b_demand.py", env); self.n_m08b += 1
            out = {rel: (CHAIN / rel).read_bytes() for rel in (ATS_REL, ANCH_REL, OUTRULE_REL, BASEOUT_REL)}
            (CHAIN / D1_REL).write_bytes(self.orig[D1_REL])
        self.m08b_cache[key] = out
        return out

    # ------------------------------------------------------------------------------------------------------------------------------ edits
    @staticmethod
    def ats_frame(b: bytes) -> pd.DataFrame:
        return pd.read_csv(io.BytesIO(b), keep_default_na=False, dtype=str)

    @staticmethod
    def ind_row(d: pd.DataFrame, cc: str, car: str):
        m = (d.country == cc) & (d.sector == "Industry") & (d.carrier == car)
        if m.sum() != 1:
            raise ValueError(f"ATS: {cc} Industry {car}: {m.sum()} rows")
        return m

    @classmethod
    def set_base(cls, d: pd.DataFrame, cc: str, car: str, new_base: float):
        m = cls.ind_row(d, cc, car)
        d.loc[m, "base_2019_mwh"] = repr(float(new_base))
        mult = d.loc[m, "multiplier_total"].iloc[0]
        d.loc[m, "value_2050_mwh"] = repr(float(new_base) * float(mult)) if mult not in ("", None) else repr(float(new_base))

    @classmethod
    def e19(cls, d: pd.DataFrame, cc: str, car: str) -> float:
        m = (d.country == cc) & (d.sector == "Industry") & (d.carrier == car)
        return float(pd.to_numeric(d.loc[m, "base_2019_mwh"]).sum()) if m.any() else 0.0

    @staticmethod
    def recs(cache: dict, cc: str) -> dict:
        return {r["carrier"]: r for r in cache["records"] if r["country"] == cc}

    @staticmethod
    def subs_of(cache: dict) -> list:
        return [k for k in cache["records"][0] if k not in ("country", "carrier")]

    def apply_moves(self, ats: pd.DataFrame, cache: dict, moves: list, log: list | None = None):
        """G0 v4g0_common.Chain.edited (generalised to every country): d MWh leaves (sub, carrier) - the cache cell is lowered by d x sum(cache) /
        e19 and the ATS industry base by d (value_2050 = base x the unchanged multiplier: reading I); negative d adds energy."""
        by = {}
        for cc, sub, car, dv in moves:
            if abs(dv) > 0:
                by.setdefault((cc, car), {}); by[(cc, car)][sub] = by[(cc, car)].get(sub, 0.0) + dv
        for (cc, car), subs in by.items():
            r = self.recs(cache, cc)[car]
            tot = sum(float(v) for k, v in r.items() if k not in ("country", "carrier"))
            e = self.e19(ats, cc, car)
            for sub, dv in subs.items():
                x = dv * tot / e if e else 0.0
                if float(r[sub]) - x < -1e-6 * max(1.0, tot):
                    raise ValueError(f"{cc} {sub} {car}: move {dv} MWh exceeds the cache cell ({float(r[sub]) * e / tot if tot else 0} MWh)")
                r[sub] = repr(max(0.0, float(r[sub]) - x))
                if log is not None:
                    log.append(dict(country=cc, sub=sub, carrier=car, d_mwh=dv))
            self.set_base(ats, cc, car, e - sum(subs.values()))

    def sub19(self, ats: pd.DataFrame, cache: dict, cc: str) -> dict:
        out = {}
        for car, r in self.recs(cache, cc).items():
            tot = sum(float(v) for k, v in r.items() if k not in ("country", "carrier")); e = self.e19(ats, cc, car)
            for k, v in r.items():
                if k not in ("country", "carrier"):
                    out.setdefault(k, {c: 0.0 for c in cm.CARS19})[car] = e * float(v) / tot if tot else 0.0
        return out

    def s30(self, ats: pd.DataFrame, cache: dict, cem: dict | None, edgar_zero: list | None, bio_cap: float | None, biopot: bytes | None, outrule: bytes, baseout: bytes, anch: bytes):
        self.restore()
        (CHAIN / ATS_REL).write_text(ats.to_csv(index=False, lineterminator="\n")); (CHAIN / CACHE_REL).write_text(json.dumps(cache))
        (CHAIN / OUTRULE_REL).write_bytes(outrule); (CHAIN / BASEOUT_REL).write_bytes(baseout); (CHAIN / ANCH_REL).write_bytes(anch)
        if edgar_zero:
            ed = pd.read_csv(CHAIN / EDGAR_REL, dtype=str, keep_default_na=False)
            m = ed.iso.isin(edgar_zero) & (ed.ipcc_code_2006_for_standard_report == "2.A.1")
            ed.loc[m, "kt_CO2_2019"] = "0"; ed.to_csv(CHAIN / EDGAR_REL, index=False)
        if biopot is not None:
            (CHAIN / BIOPOT_REL).write_bytes(biopot)
        env = {f"V4S2_CEM_EL_T19_{c}": repr(float(t)) for c, t in (cem or {}).items()}
        if bio_cap is not None:
            env["I2_BIO_CAP_SHARE"] = repr(float(bio_cap))
        self._exec("s3_0_industry.py", env); self.n_s30 += 1
        dd = CHAIN / DV
        S = pd.read_csv(dd / SUMMARY).set_index("country")
        ob = pd.read_csv(dd / "INDUSTRY_2050_OTHER_BUCKET.csv"); ob = ob[ob["mode"] == "aeo8_ats_anchor"].set_index("country")
        pz = pd.read_csv(dd / "INDUSTRY_2050_PYPSA_EUR_aeo8_ats_anchor.csv")
        gp = pd.read_csv(dd / "INDUSTRY_2050_GAPS.csv"); gp = gp[gp["mode"] == "aeo8_ats_anchor"]
        self.restore()
        return S, ob, pz, gp

    # ------------------------------------------------------------------------------------------------------------------------------ products
    def deduct(self, cc, avail, other_avail, item, log):
        """S0 3.2 item 2 (uniform, I2): fuel from the same-name UNSD row by the row's fuel mix, electricity from the row's electricity; the
        excess from the cache 'other' row (fuel by its fuel mix, or by the item's fixed carrier split); what cannot be found is recorded
        (D163-4) and not deducted. item: dict(name, row, fuel19, el19, fuel_split=None|{carrier: share}, spill=True)."""
        mv = []; fuel, el = float(item["fuel19"]), float(item["el19"]); split = item.get("fuel_split")
        row = item.get("row"); el_row = item.get("el_from", "row") == "row"
        if split == "fossil":   # G0 pulp rule: non-biomass fuel over the fossil mix of the source (computed on the 'other' bucket)
            o = other_avail; ft_ = sum(o[f] for f in cm.FOSSIL); split = {f: o[f] / ft_ for f in cm.FOSSIL} if ft_ > 0 else None
        tf = te = 0.0
        if row and row in avail:
            r = avail[row]
            if split:
                for f, s in split.items():
                    d = min(fuel * s, r[f]); tf += d
                    if d > 0:
                        mv.append((cc, row, f, d)); r[f] -= d
            else:
                ft = sum(r[f] for f in cm.FUELS); tf = min(fuel, ft)
                for f in cm.FUELS:
                    d = tf * r[f] / ft if ft > 0 else 0.0
                    if d > 0:
                        mv.append((cc, row, f, d)); r[f] -= d
            te = min(el, r["electricity"]) if el_row else 0.0
            if te > 0:
                mv.append((cc, row, "electricity", te)); r["electricity"] -= te
        ex_f, ex_e = fuel - tf, el - te; sf = se = 0.0
        if item.get("spill", True) and (ex_f > 1e-6 or ex_e > 1e-6):
            o = other_avail
            if split:
                for f, s in split.items():
                    d = min(ex_f * s, o[f]); sf += d
                    if d > 0:
                        mv.append((cc, "other", f, d)); o[f] -= d
            else:
                oft = sum(o[f] for f in cm.FUELS); sf = min(ex_f, oft)
                for f in cm.FUELS:
                    d = sf * o[f] / oft if oft > 0 else 0.0
                    if d > 0:
                        mv.append((cc, "other", f, d)); o[f] -= d
            se = min(ex_e, o["electricity"])
            if se > 0:
                mv.append((cc, "other", "electricity", se)); o["electricity"] -= se
        log.append(dict(country=cc, product=item["name"], row=row or "other", fuel_wanted_mwh=fuel, el_wanted_mwh=el, fuel_from_row_mwh=tf, el_from_row_mwh=te,
                        fuel_from_other_mwh=sf, el_from_other_mwh=se, not_found_mwh=(ex_f - sf) + (ex_e - se) if item.get("spill", True) else 0.0,
                        capped_mwh=(ex_f + ex_e) if not item.get("spill", True) else 0.0))
        return mv

    # ------------------------------------------------------------------------------------------------------------------------------ layer
    def layer(self, row_T: pd.Series, row_dec: pd.Series, cc: str, nf: dict, extra: dict, bn_iii_t50: float | None, meoh_drop: bool):
        """v3 conservation (D163-6 a) with explicit products: T = route total of the T row (+ products); parts = decompose(decomposition row) +
        non-ferrous + products; Other = T - explicit, carriers scaled uniformly. BN (iii): cement part = electricity of the PyPSA-Eur cement
        ratio x 2050 cement (G4). meoh_drop: the EU27-weight methanol load of the chemicals row is dropped (decision 210 item 7; DFX F2 precedent)."""
        v3 = self.v3
        rT, rD = row_T.copy(), row_dec.copy()
        dropped = 0.0
        if meoh_drop:
            dropped = float(rT[v3.col("methanol")]); rT[v3.col("methanol")] = 0.0; rD[v3.col("methanol")] = 0.0
        T_chain = float(sum(rT[v3.col(x)] for x in v3.CARRIERS))
        if T_chain <= 0 and not extra:
            z = {k: 0.0 for k in cm.OUTC}
            return dict(T=0.0, T_chain=0.0, other=z, other_total=0.0, explicit=0.0, scale=0.0, parts={}, by_sub={}, T_car=z, meoh_dropped=dropped)
        parts = v3.decompose(rD, self.fut)
        T = T_chain
        if bn_iii_t50 is not None:
            full = fsum(parts["cement"])
            parts["cement"] = {k: (self.fut["Cement"].get("electricity", 0.0) * bn_iii_t50 if k == "electricity" else 0.0) for k in parts["cement"]}
            T += fsum(parts["cement"]) - full
        parts.update({k: dict(v) for k, v in nf.items()})
        for k, v in extra.items():
            parts[k] = {oc: float(v.get(oc, 0.0)) for oc in cm.OUTC}
            T += fsum(parts[k])
        expl = sum(fsum(v) for k, v in parts.items() if k != "other")
        so = fsum(parts["other"]); f = (T - expl) / so if so > 0 else 0.0
        if f < 0:
            raise ValueError(f"{cc}: explicit sub-sectors exceed T (D163-4 case)")
        parts["other"] = {k: v * f for k, v in parts["other"].items()}
        T_car = {k: sum(p.get(k, 0.0) for p in parts.values()) for k in cm.OUTC}
        return dict(T=T, T_chain=T_chain, other=dict(parts["other"]), other_total=fsum(parts["other"]), explicit=expl, scale=f, parts=parts,
                    by_sub={k: fsum(v) for k, v in parts.items() if k != "other"}, T_car=T_car, meoh_dropped=dropped)

    def evaluate(self, ats, cache, moves, prods, extra, log, dlog, case, mo):
        """Apply the base moves, deduct the product items (pre-run of s3_0 for the row availabilities, G3 g3_chain.Runner._scenario), apply all
        moves to (ats, cache) in place and run s3_0. extra is filled with the products' 2050 vectors."""
        cem, ez, bc, bp = case.get("cem"), case.get("edgar_zero"), case.get("bio_cap_share"), case.get("biopot")
        if any(prods.values()):
            a1 = ats.copy(); c1 = copy.deepcopy(cache); self.apply_moves(a1, c1, moves)
            S0, ob0, pz0, _ = self.s30(a1, c1, cem, ez, bc, bp, mo[OUTRULE_REL], mo[BASEOUT_REL], mo[ANCH_REL])
            for cc, items in prods.items():
                if not items:
                    continue
                avail = {k: dict(v) for k, v in self.sub19(a1, c1, cc).items()}
                pc = pz0[pz0.country == cc]
                cem19 = {c_: float(pc[(pc.subsector == "cement") & (pc.carrier == c_)].mwh_2019.sum()) for c_ in cm.CARS19}
                if NMM in avail:
                    for c_ in cm.CARS19:
                        avail[NMM][c_] = max(0.0, avail[NMM][c_] - cem19[c_])
                o = ob0.loc[cc]
                other_avail = {c_: max(0.0, float(o[f"other_2019_{c_}_mwh"]) - sum(avail.get(s_, {}).get(c_, 0.0) for s_ in ("construction", "mining and quarrying"))) for c_ in cm.CARS19}
                for it in items:
                    moves += self.deduct(cc, avail, other_avail, it, dlog)
                    if it.get("v2050"):
                        extra.setdefault(cc, {})[it["name"]] = it["v2050"]
        self.apply_moves(ats, cache, moves, log)
        S, ob, pz, gp = self.s30(ats, cache, cem, ez, bc, bp, mo[OUTRULE_REL], mo[BASEOUT_REL], mo[ANCH_REL])
        return S, ob, pz, gp, moves

    # ------------------------------------------------------------------------------------------------------------------------------ case
    def run(self, case: dict) -> dict:
        self.vn_dlog = []
        d1 = None
        if case.get("d1") is not None:
            d1 = write_d1(self.orig[D1_REL], case["d1"], case["d1_s0"])
        mode = case.get("anchor_mode", "ras")
        mo = dict(self.m08b(None if mode == "I" else d1, mode, case.get("anchor_adj")))
        if mode == "I" and case.get("d1") is not None:   # reading I: ATS rows = new base x the repository multipliers (I1 'ats_I')
            mo[ATS_REL] = write_ats_I(self.orig[ATS_REL], case["d1"], case["d1_s0"])
        ats = self.ats_frame(mo[ATS_REL])
        cache = copy.deepcopy(case.get("cache") or json.loads(self.orig[CACHE_REL]))
        log, dlog = [], []
        add_info = []
        for a in case.get("ats_add", []):   # reading-I base change of the industry row (multiplier kept)
            cc, car, dv = a[0], a[1], a[2]; m_t = a[3] if len(a) > 3 else None
            m_row = float(ats.loc[self.ind_row(ats, cc, car), "multiplier_total"].iloc[0])
            eff = dv * (m_t / m_row if (m_t and m_row) else 1.0)   # grow at the target multiplier m_t: s3_0 multiplies e19 by the row multiplier
            self.set_base(ats, cc, car, self.e19(ats, cc, car) + eff)
            add_info.append(dict(country=cc, carrier=car, d_mwh=dv, m_target=m_t, m_row=m_row, base_added_mwh=eff))
        cem, ez, bc, bp = case.get("cem"), case.get("edgar_zero"), case.get("bio_cap_share"), case.get("biopot")
        extra = {c: dict(v) for c, v in case.get("extra", {}).items()}
        ats0 = ats.copy(); cache0 = copy.deepcopy(cache)
        S, ob, pz, gp, moves = self.evaluate(ats, cache, list(case.get("moves", [])), case.get("products", {}), extra, log, dlog, case, mo)
        vn_dec = None
        if not case.get("vn_same_run"):
            # v3 VN rule (v3_industry.run_vn_chain): T_v2(VN) from the run above, the decomposition from a run with the VN cache records replaced by
            # the APEC 2022 matrix; the VN moves and product deductions are evaluated again on that matrix (as G2 v4w07g2_common.Chain.run did)
            vc = cache0
            a = pd.read_csv(io.BytesIO(self.orig[APEC_REL])).set_index("cache_subsector")
            H = case.get("vn_dec_matrix")   # optional {carrier: {sub: MWh}} for the decomposition run (G2 hybrid under the v3 rule)
            for r in vc["records"]:
                if r["country"] == "VN":
                    for s in r:
                        if s not in ("country", "carrier"):
                            r[s] = (float(H[r["carrier"]].get(s, 0.0)) if H is not None else (float(a.at[s, APEC_COL[r["carrier"]]]) if s in a.index else 0.0))
            vmoves = [m for m in case.get("moves", []) if m[0] == "VN"]
            vprods = {"VN": case.get("products", {}).get("VN", [])}
            S2, _, _, _, _ = self.evaluate(ats0, vc, vmoves, vprods, {}, [], self.vn_dlog, case, mo)
            vn_dec = S2.loc["VN"]
        an = pd.read_csv(io.BytesIO(mo[ANCH_REL])).set_index("country")
        res = dict(snap={}, log=log, dlog=dlog, vn_dlog=self.vn_dlog, gaps=gp, pz=pz, ats_sectors=self.sectors(ats), anchors=an, moves=moves, ats_add_info=add_info)
        nf_mask = gp.item.str.contains("not found|exceeds the other bucket", regex=True) & (gp.carrier != "all") & (gp.carrier != "hydrogen")
        nf_case = case.get("nf", {})
        for cc in cm.ASEAN:
            if cc not in S.index:
                continue
            nf = dict(self.nf["main"].get(cc, {}))
            nf.update(nf_case.get(cc, {}))
            row_T = S.loc[cc]; row_D = vn_dec if (cc == "VN" and vn_dec is not None) else row_T
            iii = float(self.rule.at[cc, "cement_2050_mt"]) * 1e6 if (case.get("bn_iii") and cc == "BN") else None
            L = self.layer(row_T, row_D, cc, nf, extra.get(cc, {}), iii, cc in case.get("meoh_drop", []))
            o = ob.loc[cc] if cc in ob.index else None
            prod50 = sum(fsum(v) for v in extra.get(cc, {}).values())
            ind = ats[(ats.country == cc) & (ats.sector == "Industry")]
            res["snap"][cc] = dict(
                L=L, T=L["T"], other=L["other_total"], share=(L["other_total"] / L["T"] if L["T"] > 0 else 0.0),
                ind19=float(pd.to_numeric(ind.base_2019_mwh).sum()), ind50_ats=float(pd.to_numeric(ind.value_2050_mwh, errors="coerce").fillna(0).sum()),
                ind19_car={car: self.e19(ats, cc, car) for car in cm.CARS19},
                prod50=prod50, other19=(float(o.other_2019_mwh) if o is not None else 0.0),
                other19_car={c_: (float(o[f"other_2019_{c_}_mwh"]) if o is not None else 0.0) for c_ in cm.CARS19},
                ind_anchor=float(an.at[cc, "industry_anchor_mwh"]), ind_mult=float(an.at[cc, "industry_multiplier"]), tfec_anchor=float(an.at[cc, "ats_tfec_2050_mwh"]),
                overflow=_ov_d2a(L, row_T)[0], overflow_agriculture=_ov_d2a(L, row_T)[1], bio_before=float(L["T_car"].get("biomass", 0.0)),
                agriculture_biomass=float(row_T.get("agriculture_biomass_2050_mwh", 0.0)),
                overflow_s30=float(row_T.get("biomass_overflow_industry_mwh", 0.0)), bio_before_s30=float(row_T.get("pe_biomass_before_overflow_mwh", 0.0)),
                pot=float(row_T.get("solid_biomass_potential_main_mwh", 0.0)), gaps=float(gp[(gp.country == cc) & (gp.carrier != "hydrogen")].mwh.sum()),
                s30_not_found=float(gp[(gp.country == cc) & nf_mask].mwh.sum()),
                ind19_true=float(pd.to_numeric(ind.base_2019_mwh).sum()) - sum(a["base_added_mwh"] - a["d_mwh"] for a in add_info if a["country"] == cc))
        return res

    @staticmethod
    def sectors(ats: pd.DataFrame) -> dict:
        a = ats.copy(); a["v"] = pd.to_numeric(a.value_2050_mwh, errors="coerce").fillna(0.0); a["b"] = pd.to_numeric(a.base_2019_mwh, errors="coerce").fillna(0.0)
        out = {}
        for cc in cm.ASEAN:
            z = a[a.country == cc]
            land = float(z[(z.sector == "Transport") & z.account.isin(["RoadResidualFuel", "TransportNEC", "TransportEmbeddedFuelParent"]) & (z.carrier != "electricity")].v.sum())
            zz = z[z.account != "TransportEmbeddedFuelParent"]
            sec = {s: float(zz[zz.sector == s].v.sum()) for s in cm.SECTORS + ["NonEnergyUse"]}
            out[cc] = dict(sec2050=sec, land=land, ev=land * EV_FACTOR, resf=float(z[(z.sector == "Residential") & (z.carrier != "electricity")].v.sum()),
                           rail_parent=float(z[z.account == "TransportEmbeddedFuelParent"].v.sum()), rail_child=float(z[z.account == "RailNonElectric"].v.sum()))
        return out
