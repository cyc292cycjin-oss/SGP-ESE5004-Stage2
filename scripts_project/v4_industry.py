"""V4 W08 (decisions 203-211; W08_IMPLEMENTATION_SPEC.md sections 3-9, 11): v4 industry / demand chain and the W10 interface run_case(case).

    PYTHONHASHSEED=0 python scripts_project/v4_industry.py --anchor-mode ras            # v4 main tables -> research_inputs/industry_v4/out_ras/
    PYTHONHASHSEED=0 python scripts_project/v4_industry.py --anchor-mode iid            # IId sensitivity tables -> out_iid/
    PYTHONHASHSEED=0 python scripts_project/v4_industry.py --checkpoints <dir>          # cumulative checkpoints S0-S7 (snapshot JSON per step)

Chain (the I2 engine work/p1_v4_w07_20261106/I2/scripts/i2_engine.py moved into the repository; the scratch patches are the switch options of
m08b_demand.py and s3_0_industry.py, the session inputs are the tables of research_inputs/industry_v4/):
  D1 seed (v3.1 table, base column edited by the case)  --m08b_demand.py --anchor-mode / --residue-anchor-adj-->  ATS table + anchors
  --> reading-I edits (ats_add: items outside the anchor; moves: captive coal, product deductions) --> s3_0_industry.py --only-mode aeo8_ats_anchor
  --> conservation layer (v3_industry.decompose + explicit products + non-ferrous; Other = T_v2 - explicit, D163-6 a).
A case is a JSON-serialisable dict (I2 keys): d1 / d1_s0 (pd.Series base_2019_mwh by (country, sector, carrier, account)), anchor_mode ('ras',
'iid' (alias 'fixedcol'), 'iib' (alias 'frozen'), 'external', 'I' = reading I without m08b), anchor_adj {cc: MWh}, ats_add [(cc, carrier, MWh,
target multiplier)], cache, moves [(cc, sub, carrier, MWh)], products {cc: [item]}, cem {cc: t}, edgar_zero [cc], bn_iii, nf {cc: {key: vec}},
extra {cc: {key: vec}}, meoh_drop [cc], vn_same_run, bio_cap_share, biopot (path or bytes). run_case returns the snapshot (T_v2 = the 12 columns
of v3_industry.CARRIERS, biomass before overflow; 'other'; carriers; sub-sectors; anchors; sectors; overflow; deduction log). Nothing is solved.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import v3_industry as v3   # noqa: E402
import v4_industry_cache as VC   # noqa: E402
from d1_common import fmt   # noqa: E402
from v4_common import (ASEAN, BIOMASS_DIR, CARS19, DEMAND_DIR, FOSSIL, FUELS, IND_V3, OUTC, REG_DIR, ROOT, SECTORS, SRC, V4_DIR, V4_MAIN,   # noqa: E402
                       out_dir, sha256, switch_sha, switches)

D1_TABLE = DEMAND_DIR / "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER.csv"
ATS_V31 = DEMAND_DIR / "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv"
ANCH_V31 = DEMAND_DIR / "DEMAND_ANCHOR_AEO8_ATS.csv"
OUTRULE_V31 = DEMAND_DIR / "INDUSTRY_OUTPUT_2050_M08B.csv"
BASEOUT_V31 = DEMAND_DIR / "INDUSTRY_OUTPUT_BASE_M08B.csv"
CACHE_V31 = SRC / "industry_cache.json"
BIOPOT_V31 = BIOMASS_DIR / "BIOMASS_POTENTIAL_2050.csv"
BIOPOT_V4 = BIOMASS_DIR / "BIOMASS_POTENTIAL_2050_V4.csv"
APEC = IND_V3 / "APEC2022_VN_INDUSTRY_PJ.csv"
SUMMARY = "INDUSTRY_2050_SUMMARY_aeo8_ats_anchor_OTHER_USEFUL_HEAT_BANDS.csv"
MODE = "aeo8_ats_anchor"
KEY = ["country", "sector", "carrier", "account"]
EV_FACTOR_W08 = 0.30215   # W08: the rounded value of oil_to_electricity x ev_share (static-check difference 9.9e-6); kept for reference only
REGISTRY = REG_DIR / "DATA_REGISTRY.csv"


def ev_factor() -> float:
    """V4 D1 (decision 214 item 9): EV MWh_el per MWh of land-transport oil = share_transport_ice_efficiency / share_transport_electric_efficiency
    x share_land_transport_electric_share_2050 from the registry - the expression of s2_layers.add_demand_layer (oil_to_el x ev_share), unrounded
    (16.0712 / 53.19 x 1 = 0.302147020116563...)."""
    r = pd.read_csv(REGISTRY, dtype=str, keep_default_na=False).set_index("param_id").value
    return float(r["share_transport_ice_efficiency"]) / float(r["share_transport_electric_efficiency"]) * float(r["share_land_transport_electric_share_2050"])


EV_FACTOR = ev_factor()
CHEM = "chemical and petrochemical"
NMM = "non-metallic minerals"
PAPER = "paper pulp and print"
APEC_COL = dict(coal="coal_pj", oil="oil_pj", gas="gas_pj", biomass="biomass_pj", electricity="electricity_pj")
MODE_ALIAS = {"fixedcol": "iid", "frozen": "iib"}
IND_BIO = lambda cc: (cc, "Industry", "biomass", "IndustryFinalEnergy")   # noqa: E731


def fsum(d: dict) -> float:
    return float(sum(d.values()))


def template(tab: pd.DataFrame, c: str, sec: str, car: str) -> pd.Series:
    for cond in ((tab.country == c) & (tab.sector == sec) & ((tab.carrier == "electricity") == (car == "electricity")),
                 (tab.country == c) & (tab.sector == sec), (tab.sector == sec)):
        t = tab[cond]
        if len(t):
            return t.iloc[0].copy()
    raise KeyError((c, sec, car))


def write_d1(orig: bytes, case: pd.Series, s0: pd.Series) -> bytes:
    """Seed table: the v3.1 D1 table with the base column of every changed key replaced (d1_common.fmt, the D1 writer); value_2050 = base x
    multiplier_total; a new key is a clone of a row of the same country / sector (I2 write_d1)."""
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
                    t[col] = "V4_W08_NEW_ROW"
            if "in_existing_electricity_load" in t and k[2] != "electricity":
                t["in_existing_electricity_load"] = "False"
            if "existing_electricity_load_2050_mwh" in t and k[2] != "electricity":
                t["existing_electricity_load_2050_mwh"] = ""
            tab = pd.concat([tab, t.to_frame().T], ignore_index=True)
            idx[k] = tab.index[-1]
    buf = io.StringIO(); tab.to_csv(buf, index=False, lineterminator="\n")
    return buf.getvalue().encode()


def write_ats_I(orig: bytes, case: pd.Series, s0: pd.Series) -> bytes:
    """Reading I (sensitivity): base and value_2050 = base x the v3.1 multiplier_total, repr floats (I2 write_ats_I)."""
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


class Chain:
    """One work folder (outside research_inputs; default a temporary folder) in which m08b_demand.py and s3_0_industry.py write their v4 outputs."""

    def __init__(self, work: Path | None = None, python: str | None = None):
        self.work = Path(work) if work else Path(tempfile.mkdtemp(prefix="v4_chain_"))
        self.work.mkdir(parents=True, exist_ok=True)
        self.py = python or sys.executable
        self.orig = {p: p.read_bytes() for p in (D1_TABLE, ATS_V31, ANCH_V31, OUTRULE_V31, BASEOUT_V31)}
        self.cache_v31 = json.loads(CACHE_V31.read_text())
        self.fut = v3.future_vectors(); self.ne = v3.nickel_unit_energy()
        self.nf = {case: v3.nonferrous(self.fut, case, self.ne)[0] for case in ("main", "nf2023")}
        self.rule = pd.read_csv(OUTRULE_V31).set_index("country")
        self.m08b_cache, self.n_m08b, self.n_s30 = {}, 0, 0

    # ------------------------------------------------------------------------------------------------------------------------------ runs
    def _exec(self, args: list):
        env = dict(os.environ, PYTHONHASHSEED="0")
        r = subprocess.run([self.py, *[str(a) for a in args]], cwd=ROOT, capture_output=True, text=True, env=env)
        if r.returncode:
            raise RuntimeError(f"{args[0]}: {r.stderr[-3000:]}")

    def m08b(self, d1: bytes | None, mode: str, adj: dict | None) -> dict:
        mode = MODE_ALIAS.get(mode, mode)
        key = hashlib.sha256((d1 or b"REPO") + mode.encode() + json.dumps(adj or {}, sort_keys=True).encode()).hexdigest()
        if key in self.m08b_cache:
            return self.m08b_cache[key]
        names = ("ATS", "ANCH", "OUTRULE", "BASEOUT")
        if mode == "I" or (d1 is None and mode == "ras" and not adj):
            out = dict(zip(names, (self.orig[ATS_V31], self.orig[ANCH_V31], self.orig[OUTRULE_V31], self.orig[BASEOUT_V31])))
        else:
            wd = self.work / f"m08b_{key[:16]}"; wd.mkdir(parents=True, exist_ok=True)
            (wd / "d1_seed.csv").write_bytes(d1 if d1 is not None else self.orig[D1_TABLE])
            args = ["scripts_project/m08b_demand.py", "--table", wd / "d1_seed.csv", "--out-dir", wd, "--anchor-mode", mode]
            if adj:
                (wd / "residue_anchor_adj.json").write_text(json.dumps(adj)); args += ["--residue-anchor-adj", wd / "residue_anchor_adj.json"]
            self._exec(args); self.n_m08b += 1
            out = dict(zip(names, ((wd / ATS_V31.name).read_bytes(), (wd / ANCH_V31.name).read_bytes(), (wd / OUTRULE_V31.name).read_bytes(),
                                   (wd / BASEOUT_V31.name).read_bytes())))
            out["DIR"] = wd
        self.m08b_cache[key] = out
        return out

    def s30(self, ats: pd.DataFrame, cache: dict, cem: dict | None, edgar_zero: list | None, bio_cap: float | None, biopot, outrule: bytes):
        wd = self.work / "s30"
        if wd.exists():
            shutil.rmtree(wd)
        wd.mkdir(parents=True)
        (wd / "ats.csv").write_text(ats.to_csv(index=False, lineterminator="\n")); (wd / "cache.json").write_text(json.dumps(cache))
        (wd / "output_rule.csv").write_bytes(outrule)
        args = ["scripts_project/s3_0_industry.py", "--only-mode", MODE, "--ats-table", wd / "ats.csv", "--output-rule", wd / "output_rule.csv",
                "--cache", wd / "cache.json", "--out-dir", wd / "out"]
        if cem:
            pd.DataFrame([dict(country=c, cement_2019_t=repr(float(t))) for c, t in cem.items()]).to_csv(wd / "cem.csv", index=False)
            args += ["--cement-el-t19", wd / "cem.csv"]
        if edgar_zero:
            args += ["--edgar-2a1-zero", ",".join(edgar_zero)]
        if biopot is not None:
            if isinstance(biopot, (bytes, bytearray)):
                (wd / "biopot.csv").write_bytes(biopot); biopot = wd / "biopot.csv"
            args += ["--biomass-potential", biopot]
        if bio_cap is not None:
            args += ["--biomass-cap-share", repr(float(bio_cap))]
        self._exec(args); self.n_s30 += 1
        dd = wd / "out"
        S = pd.read_csv(dd / SUMMARY).set_index("country")
        ob = pd.read_csv(dd / "INDUSTRY_2050_OTHER_BUCKET.csv"); ob = ob[ob["mode"] == MODE].set_index("country")
        pz = pd.read_csv(dd / f"INDUSTRY_2050_PYPSA_EUR_{MODE}.csv")
        gp = pd.read_csv(dd / "INDUSTRY_2050_GAPS.csv"); gp = gp[gp["mode"] == MODE]
        main = pd.read_csv(dd / f"INDUSTRY_2050_SUMMARY_{MODE}.csv").set_index("country")
        return S, ob, pz, gp, main

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

    def apply_moves(self, ats: pd.DataFrame, cache: dict, moves: list, log: list | None = None):
        """d MWh leaves (sub, carrier): the cache cell falls by d x sum(cache) / e19 and the ATS industry base by d (value_2050 = base x the
        unchanged multiplier: reading I); negative d adds energy (I2 apply_moves)."""
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
                    out.setdefault(k, {c: 0.0 for c in CARS19})[car] = e * float(v) / tot if tot else 0.0
        return out

    # ------------------------------------------------------------------------------------------------------------------------------ products
    def deduct(self, cc, avail, other_avail, item, log):
        """S0 3.2 item 2 (uniform): fuel from the same-name UNSD row by the row's fuel mix, electricity from the row's electricity; the excess from
        the cache 'other' row; what cannot be found is recorded (D163-4) and not deducted (I2 deduct)."""
        mv = []; fuel, el = float(item["fuel19"]), float(item["el19"]); split = item.get("fuel_split")
        row = item.get("row"); el_row = item.get("el_from", "row") == "row"
        if split == "fossil":
            o = other_avail; ft_ = sum(o[f] for f in FOSSIL); split = {f: o[f] / ft_ for f in FOSSIL} if ft_ > 0 else None
        tf = te = 0.0
        if row and row in avail:
            r = avail[row]
            if split:
                for f, s in split.items():
                    d = min(fuel * s, r[f]); tf += d
                    if d > 0:
                        mv.append((cc, row, f, d)); r[f] -= d
            else:
                ft = sum(r[f] for f in FUELS); tf = min(fuel, ft)
                for f in FUELS:
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
                oft = sum(o[f] for f in FUELS); sf = min(ex_f, oft)
                for f in FUELS:
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
        non-ferrous + products; Other = T - explicit, carriers scaled uniformly (I2 layer)."""
        rT, rD = row_T.copy(), row_dec.copy()
        dropped = 0.0
        if meoh_drop:
            dropped = float(rT[v3.col("methanol")]); rT[v3.col("methanol")] = 0.0; rD[v3.col("methanol")] = 0.0
        T_chain = float(sum(rT[v3.col(x)] for x in v3.CARRIERS))
        if T_chain <= 0 and not extra:
            z = {k: 0.0 for k in OUTC}
            return dict(T=0.0, T_chain=0.0, other=z, other_total=0.0, explicit=0.0, scale=0.0, parts={}, by_sub={}, T_car=z, meoh_dropped=dropped)
        parts = v3.decompose(rD, self.fut)
        T = T_chain
        if bn_iii_t50 is not None:
            full = fsum(parts["cement"])
            parts["cement"] = {k: (self.fut["Cement"].get("electricity", 0.0) * bn_iii_t50 if k == "electricity" else 0.0) for k in parts["cement"]}
            T += fsum(parts["cement"]) - full
        parts.update({k: dict(v) for k, v in nf.items()})
        for k, v in extra.items():
            parts[k] = {oc: float(v.get(oc, 0.0)) for oc in OUTC}
            T += fsum(parts[k])
        expl = sum(fsum(v) for k, v in parts.items() if k != "other")
        so = fsum(parts["other"]); f = (T - expl) / so if so > 0 else 0.0
        if f < 0:
            raise ValueError(f"{cc}: explicit sub-sectors exceed T (D163-4 case)")
        parts["other"] = {k: v * f for k, v in parts["other"].items()}
        T_car = {k: sum(p.get(k, 0.0) for p in parts.values()) for k in OUTC}
        return dict(T=T, T_chain=T_chain, other=dict(parts["other"]), other_total=fsum(parts["other"]), explicit=expl, scale=f, parts=parts,
                    by_sub={k: fsum(v) for k, v in parts.items() if k != "other"}, T_car=T_car, meoh_dropped=dropped)

    def evaluate(self, ats, cache, moves, prods, extra, log, dlog, case, mo):
        cem, ez, bc, bp = case.get("cem"), case.get("edgar_zero"), case.get("bio_cap_share"), case.get("biopot")
        if any(prods.values()):
            a1 = ats.copy(); c1 = copy.deepcopy(cache); self.apply_moves(a1, c1, moves)
            S0, ob0, pz0, _, _ = self.s30(a1, c1, cem, ez, bc, bp, mo["OUTRULE"])
            for cc, items in prods.items():
                if not items:
                    continue
                avail = {k: dict(v) for k, v in self.sub19(a1, c1, cc).items()}
                pc = pz0[pz0.country == cc]
                cem19 = {c_: float(pc[(pc.subsector == "cement") & (pc.carrier == c_)].mwh_2019.sum()) for c_ in CARS19}
                if NMM in avail:
                    for c_ in CARS19:
                        avail[NMM][c_] = max(0.0, avail[NMM][c_] - cem19[c_])
                o = ob0.loc[cc]
                other_avail = {c_: max(0.0, float(o[f"other_2019_{c_}_mwh"]) - sum(avail.get(s_, {}).get(c_, 0.0) for s_ in ("construction", "mining and quarrying"))) for c_ in CARS19}
                for it in items:
                    moves += self.deduct(cc, avail, other_avail, it, dlog)
                    if it.get("v2050"):
                        extra.setdefault(cc, {})[it["name"]] = it["v2050"]
        self.apply_moves(ats, cache, moves, log)
        S, ob, pz, gp, main = self.s30(ats, cache, cem, ez, bc, bp, mo["OUTRULE"])
        return S, ob, pz, gp, main, moves

    # ------------------------------------------------------------------------------------------------------------------------------ case
    def run(self, case: dict) -> dict:
        self.vn_dlog = []
        d1 = None
        if case.get("d1") is not None:
            d1 = write_d1(self.orig[D1_TABLE], case["d1"], case["d1_s0"])
        mode = MODE_ALIAS.get(case.get("anchor_mode", "ras"), case.get("anchor_mode", "ras"))
        mo = dict(self.m08b(None if mode == "I" else d1, mode, case.get("anchor_adj")))
        if mode == "I" and case.get("d1") is not None:
            mo["ATS"] = write_ats_I(self.orig[ATS_V31], case["d1"], case["d1_s0"])
        ats = self.ats_frame(mo["ATS"])
        cache = copy.deepcopy(case.get("cache") or self.cache_v31)
        log, dlog, add_info = [], [], []
        for a in case.get("ats_add", []):   # reading-I base change of the industry row (multiplier kept)
            cc, car, dv = a[0], a[1], a[2]; m_t = a[3] if len(a) > 3 else None
            m_row = float(ats.loc[self.ind_row(ats, cc, car), "multiplier_total"].iloc[0])
            eff = dv * (m_t / m_row if (m_t and m_row) else 1.0)
            self.set_base(ats, cc, car, self.e19(ats, cc, car) + eff)
            add_info.append(dict(country=cc, carrier=car, d_mwh=dv, m_target=m_t, m_row=m_row, base_added_mwh=eff))
        extra = {c: dict(v) for c, v in case.get("extra", {}).items()}
        ats0 = ats.copy(); cache0 = copy.deepcopy(cache)
        S, ob, pz, gp, main, moves = self.evaluate(ats, cache, list(case.get("moves", [])), case.get("products", {}), extra, log, dlog, case, mo)
        vn_dec = None
        if not case.get("vn_same_run"):
            # v3 VN rule (v3_industry.run_vn_chain): T_v2(VN) from the run above, the decomposition from a run with the VN cache records replaced
            # by the APEC 2022 matrix; the VN moves and product deductions are evaluated again on that matrix
            vc = cache0
            a_ = pd.read_csv(APEC).set_index("cache_subsector")
            H = case.get("vn_dec_matrix")
            for r in vc["records"]:
                if r["country"] == "VN":
                    for s in r:
                        if s not in ("country", "carrier"):
                            r[s] = (float(H[r["carrier"]].get(s, 0.0)) if H is not None else (float(a_.at[s, APEC_COL[r["carrier"]]]) if s in a_.index else 0.0))
            vmoves = [m for m in case.get("moves", []) if m[0] == "VN"]
            vprods = {"VN": case.get("products", {}).get("VN", [])}
            S2, _, _, _, _, _ = self.evaluate(ats0, vc, vmoves, vprods, {}, [], self.vn_dlog, case, mo)
            vn_dec = S2.loc["VN"]
        an = pd.read_csv(io.BytesIO(mo["ANCH"])).set_index("country")
        res = dict(snap={}, log=log, dlog=dlog, vn_dlog=self.vn_dlog, gaps=gp, pz=pz, ats=ats, ats_sectors=self.sectors(ats), anchors=an, moves=moves,
                   ats_add_info=add_info, S=S, main=main, mo=mo, extra=extra)
        nf_mask = gp.item.str.contains("not found|exceeds the other bucket", regex=True) & (gp.carrier != "all") & (gp.carrier != "hydrogen")
        nf_case = case.get("nf", {})
        for cc in ASEAN:
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
                ind19_car={car: self.e19(ats, cc, car) for car in CARS19},
                prod50=prod50, other19=(float(o.other_2019_mwh) if o is not None else 0.0),
                other19_car={c_: (float(o[f"other_2019_{c_}_mwh"]) if o is not None else 0.0) for c_ in CARS19},
                ind_anchor=float(an.at[cc, "industry_anchor_mwh"]), ind_mult=float(an.at[cc, "industry_multiplier"]), tfec_anchor=float(an.at[cc, "ats_tfec_2050_mwh"]),
                overflow=float(row_T.get("biomass_overflow_industry_mwh", 0.0)), bio_before=float(row_T.get("pe_biomass_before_overflow_mwh", 0.0)),
                pot=float(row_T.get("solid_biomass_potential_main_mwh", 0.0)), gaps=float(gp[(gp.country == cc) & (gp.carrier != "hydrogen")].mwh.sum()),
                s30_not_found=float(gp[(gp.country == cc) & nf_mask].mwh.sum()),
                ind19_true=float(pd.to_numeric(ind.base_2019_mwh).sum()) - sum(a["base_added_mwh"] - a["d_mwh"] for a in add_info if a["country"] == cc))
        return res

    @staticmethod
    def sectors(ats: pd.DataFrame) -> dict:
        a = ats.copy(); a["v"] = pd.to_numeric(a.value_2050_mwh, errors="coerce").fillna(0.0)
        out = {}
        for cc in ASEAN:
            z = a[a.country == cc]
            land = float(z[(z.sector == "Transport") & z.account.isin(["RoadResidualFuel", "TransportNEC", "TransportEmbeddedFuelParent"]) & (z.carrier != "electricity")].v.sum())
            zz = z[z.account != "TransportEmbeddedFuelParent"]
            sec = {s: float(zz[zz.sector == s].v.sum()) for s in SECTORS + ["NonEnergyUse"]}
            out[cc] = dict(sec2050=sec, land=land, ev=land * EV_FACTOR, resf=float(z[(z.sector == "Residential") & (z.carrier != "electricity")].v.sum()),
                           rail_parent=float(z[z.account == "TransportEmbeddedFuelParent"].v.sum()), rail_child=float(z[z.account == "RailNonElectric"].v.sum()))
        return out


def pack(res: dict, label: str, extra: dict | None = None) -> dict:
    """Snapshot (JSON) in the I2 pack format (i2_chain.pack): per country T, other, share, carriers, sub-sectors, anchors, overflow, ..."""
    out = dict(label=label, countries={}, ats_sectors=res["ats_sectors"], dlog=res["dlog"], vn_dlog=res.get("vn_dlog", []), **(extra or {}))
    for cc, s in res["snap"].items():
        L = s["L"]
        out["countries"][cc] = dict(T=s["T"], other=s["other"], share=s["share"], T_car=L["T_car"], other_car=L["other"], scale=L["scale"],
                                    by_sub=L["by_sub"], parts={k: dict(v) for k, v in L["parts"].items()}, meoh_dropped=L["meoh_dropped"],
                                    **{k: s[k] for k in ("ind19", "ind19_true", "ind50_ats", "ind19_car", "prod50", "other19", "other19_car", "ind_anchor", "ind_mult", "tfec_anchor",
                                                         "overflow", "bio_before", "pot", "gaps", "s30_not_found")})
    out["ats_add_info"] = res.get("ats_add_info", [])
    return out


_CHAIN: Chain | None = None


def run_case(case: dict, chain: Chain | None = None) -> dict:
    """W10 interface (checklist section 11): one case -> snapshot (pack format). A module-level chain is reused between calls (m08b cache)."""
    global _CHAIN
    ch = chain or _CHAIN or Chain()
    if chain is None:
        _CHAIN = ch
    return pack(ch.run(case), str(case.get("label", "case")))


# ====================================================================================================================== inputs and steps
def d1_series(p: Path) -> pd.Series:
    return pd.read_csv(p).groupby(KEY).base_2019_mwh.sum()   # default parser, as the reference engine (exact for the reference files)


class Inputs:
    """Every input of the v4 steps from the repository tables (research_inputs/industry_v4, demand_v5, registry_v5)."""

    def __init__(self):
        self.S0 = d1_series(V4_DIR / "D1_BASE2019_V31_REBUILD.csv"); self.B = d1_series(V4_DIR / "D1_BASE2019_SDMX.csv")
        self.cells = VC.load_cells(); self.res = VC.residues(self.cells)
        ra = self.res[self.res.cls == "a"]
        self.a_tot = ra.groupby("country").mwh.sum().to_dict()
        self.a_drop = {(x.country, x.code, x.tx) for x in ra.itertuples()}
        cov = pd.read_csv(V4_DIR / "NATIONAL_BALANCE_BIOMASS_COVERAGE.csv").set_index("country")
        self.balance_contains = {c: str(cov.at[c, "balance_contains_self_produced_residues"]) == "as_unsd" for c in cov.index}
        self.fw = VC.fuelwood_mean(self.cells)
        idb = self.cells[(self.cells.country == "ID") & (self.cells.tx != "121") & (self.cells.carrier == "biomass") & (self.cells.code == VC.FW_CODE)]
        self.idb_sdmx = float(idb.mwh.sum()); self.idb_main = self.idb_sdmx - self.fw["sdmx_mwh"] + self.fw["mean_mwh"]
        self.cache_full = VC.build_cache(self.cells)
        self.cache_a = VC.build_cache(self.cells, drop=self.a_drop, scale={("ID", VC.FW_CODE): self.fw["scale"]})
        self.cache_a_paper = VC.build_cache(self.cells, drop=set(self.a_drop) | {("ID", VC.FW_CODE, "1214G")}, scale={("ID", VC.FW_CODE): self.fw["scale"]})
        g = pd.read_csv(V4_DIR / "HOUSEHOLD_GASOLINE_2019.csv", float_precision="round_trip").set_index("country").base_2019_mwh
        self.gas = {cc: float(g.get(cc, 0.0)) for cc in ("ID", "MM")}
        an = pd.read_csv(ANCH_V31).set_index("country")
        self.m_v3 = {cc: float(an.at[cc, "industry_multiplier"]) for cc in ASEAN}
        self._items = {}

    def items_for(self, s: dict | None = None) -> dict:
        """Product items of the switch set s (V4 D1: research.demand.v4.hvc_basis b | a selects the HVC 2019 deduction and 2050 vector)."""
        basis = str((s or {}).get("hvc_basis", "b"))
        if basis not in self._items:
            import v4_products as P
            self._items[basis] = P.load_items(hvc_basis=basis)
        return self._items[basis]

    @property
    def items(self):   # the v4 main basis (b)
        return self.items_for(None)


def build_steps(I: Inputs, s: dict) -> list:
    """Cumulative steps S1-S7 (I2 i2_chain.build_steps with the decision-211 changes) for the switch set s; a step whose switch is off is a no-op."""
    items = lambda: I.items_for(s)   # noqa: E731  (V4 D1: product items of this switch set, hvc_basis)

    def d1_with(case, edits):
        if case.get("d1") is None:   # v3.1 seed: edits on the full-precision v3.1 rebuild
            case["d1"], case["d1_s0"] = I.S0.copy(), I.S0
        d = case["d1"].copy()
        for k, v in edits.items():
            d[k] = d.get(k, 0.0) + v
        return d

    def s1(c):
        c = dict(c)
        if s["base"] == "sdmx_2019":
            c.update(d1=I.B.copy(), d1_s0=I.S0, cache=I.cache_full)
        c["anchor_mode"] = s["anchor_mode"]
        return c

    def s2(c):
        c = dict(c)
        if not s["residue_boundary"]:
            return c
        ed = {IND_BIO(cc): -v for cc, v in I.a_tot.items()}
        ed[IND_BIO("ID")] = ed.get(IND_BIO("ID"), 0.0) - I.idb_sdmx
        c["d1"] = d1_with(c, ed)
        c["anchor_adj"] = {cc: v for cc, v in I.a_tot.items() if I.balance_contains.get(cc, True)}
        paper = s["id_paper_fuelwood"] == "residue"
        c["ats_add"] = list(c.get("ats_add", [])) + [("ID", "biomass", I.idb_main * I.fw["share_non_paper"] if paper else I.idb_main, I.m_v3["ID"])]
        c["cache"] = I.cache_a_paper if paper else I.cache_a
        return c

    def s3(c):
        c = dict(c)
        if s["household_gasoline"] == "none" and s["rail_parent"] == "in_d1" and not s.get("mm_gasoline"):
            return c
        ed = {}
        if s["household_gasoline"] == "id_to_road":
            ed.update({("ID", "Residential", "oil", "ResidentialFuel"): -I.gas["ID"], ("ID", "Transport", "oil", "RoadResidualFuel"): I.gas["ID"]})
        d = d1_with(c, ed)
        if s.get("mm_gasoline"):
            d[("MM", "Residential", "oil", "ResidentialFuel")] = d.get(("MM", "Residential", "oil", "ResidentialFuel"), 0.0) - I.gas["MM"]
            d[("MM", "Transport", "oil", "RoadResidualFuel")] = d.get(("MM", "Transport", "oil", "RoadResidualFuel"), 0.0) + I.gas["MM"]
        if s["rail_parent"] == "children_only":
            for k in [k for k in d.index if k[3] == "TransportEmbeddedFuelParent"]:
                d[k] = 0.0
        c["d1"] = d
        return c

    def s4(c):
        c = dict(c)
        if s["captive_coal"]:
            c["moves"] = list(c.get("moves", [])) + items()["captive"]
        return c

    def add_prod(c, cc, item):
        p = copy.deepcopy(c.get("products", {})); p.setdefault(cc, []).append(item); c["products"] = p

    def add_extra(c, cc, key, v):
        x = copy.deepcopy(c.get("extra", {})); x.setdefault(cc, {})[key] = v; c["extra"] = x

    def s5a(c):
        return dict(c)

    def s5b(c):
        c = dict(c)
        if s["products"]:
            c.update(cem=dict(items()["cement_usgs_2019_t"]), edgar_zero=list(items()["edgar_zero"]), bn_iii=True)
        return c

    def s5c(c):
        c = dict(c)
        if s["products"]:
            nf = copy.deepcopy(c.get("nf", {})); nf.setdefault("ID", {})["nonferrous_nickel"] = dict(items()["nickel_2023"]); c["nf"] = nf
        return c

    def s5d(c):
        c = dict(c)
        if s["products"]:
            for cc, it in items()["pp"].items():
                add_prod(c, cc, dict(it))
        return c

    def s5e(c):
        c = dict(c)
        if s["products"]:
            for cc, it in items()["hvc"].items():
                add_prod(c, cc, dict(it))
        return c

    def s5f(c):
        c = dict(c)
        if s["products"]:
            c["meoh_drop"] = list(items()["methanol_drop"])
            for cc, it in items()["methanol"].items():
                add_prod(c, cc, dict(it))
        return c

    def s5g(c):
        c = dict(c)
        if s["products"]:
            for cc, d in items()["new_plants"].items():
                for key, v in d.items():
                    add_extra(c, cc, key, v)
        return c

    def s6a(c):
        c = dict(c)
        if s["products"]:
            c["moves"] = list(c.get("moves", [])) + items()["my_ammonia_dup"]
        return c

    def s6b(c):
        c = dict(c)
        if s["products"]:
            for grp in ("glass", "alumina", "copper", "lime"):
                for cc, it in items()[grp].items():
                    add_prod(c, cc, dict(it))
        return c

    def s6c(c):
        c = dict(c)
        if s["vn_same_run"]:
            import v4_products as P
            H = P.vn_hybrid(c.get("cache") or I.cache_full, items()["vn_el_rows"])
            c["cache"] = P.set_vn_cache(c.get("cache") or I.cache_full, H); c["vn_same_run"] = True
        return c

    def s7(c):
        c = dict(c)
        if float(s["bio_cap_share"]) != 1.0:
            c["bio_cap_share"] = float(s["bio_cap_share"])
        if s["biomass_potential"] == "v4_adjusted":
            c["biopot"] = str(BIOPOT_V4)
        return c

    return [("S1", "基年替换（SDMX）与锚构造", s1), ("S2", "锚边界对齐（残渣移出、平衡表外燃料木材）", s2), ("S3", "(ii) 类：ID 家庭汽油移道路、铁路父行移出", s3),
            ("S4", "(i) 类：自备电厂 (b)（口径 I）", s4), ("S5a", "钢（只换空间）", s5a), ("S5b", "水泥 (ii) / BN (iii)", s5b), ("S5c", "镍 2023 基年（Case 3）", s5c),
            ("S5d", "纸浆造纸（统一规则）", s5d), ("S5e", "HVC（5.191 / 4.627）", s5e), ("S5f", "甲醇", s5f), ("S5g", "新装置", s5g),
            ("S6a", "MY 合成氨燃料重复（中档）", s6a), ("S6b", "玻璃、氧化铝、铜、石灰", s6b), ("S6c", "VN 混合拆分、同一次运行", s6c),
            ("S7", "网络层：生物质上限、潜力调整（只影响溢出）", s7)]


def final_case(I: Inputs, s: dict) -> dict:
    case = {}
    for _, _, f in build_steps(I, s):
        case = f(case)
    return case


def checkpoints(outdir: Path, s: dict, steps: set | None = None, chain: Chain | None = None) -> dict:
    """Cumulative steps S0-S7 for the switch set s; one snapshot JSON per step (pack format)."""
    outdir.mkdir(parents=True, exist_ok=True)
    ch = chain or Chain()
    I = Inputs()
    case = {}
    done = {}
    jobs = [("S0", "v3.1", lambda c: {})] + build_steps(I, s)
    if steps:
        last = max(i for i, j in enumerate(jobs) if j[0] in steps)
        jobs = jobs[:last + 1]
    for code, label, f in jobs:
        case = f(case) if code != "S0" else {}
        if steps and code not in steps:
            continue
        obj = pack(ch.run(case), f"{code} {label}")
        (outdir / f"step_{code}.json").write_text(json.dumps(obj, default=float))
        done[code] = sum(v["T"] for v in obj["countries"].values()) / 1e6
        print(code, label, round(done[code], 6), flush=True)
    (outdir / "SWITCHES.json").write_text(json.dumps(dict(switches=s, switch_sha256=switch_sha(s), m08b_runs=ch.n_m08b, s30_runs=ch.n_s30, asean_T_v2_TWh=done), indent=1))
    return done


def write_anchor_tables(chain: Chain | None = None) -> dict:
    """Frozen v3 anchor tables for the IId / IIb modes (checklist section 3): m08b_demand.py on the v3.1 table (RAS, outputs in the work folder)
    with --dump-anchors; DEMAND_ANCHOR_V3_SECTOR_FACTORS.csv = sigma_s = tfa_ID,s / t19_ID,s (I1: the RAS solution is rank one, every country gives
    the same factors up to the row factor), DEMAND_ANCHOR_V3_FROZEN.csv = tfa per country x sector (exact floats, repr)."""
    ch = chain or Chain()
    wd = ch.work / "v31_anchor_dump"; wd.mkdir(parents=True, exist_ok=True)
    ch._exec(["scripts_project/m08b_demand.py", "--out-dir", wd, "--dump-anchors", wd / "anchors_v3_ras.json"])
    d = json.loads((wd / "anchors_v3_ras.json").read_text())
    same = {p.name: (wd / p.name).read_bytes() == p.read_bytes() for p in (ATS_V31, ANCH_V31, OUTRULE_V31, BASEOUT_V31)}
    if not all(same.values()):
        raise SystemExit(f"STOP: the v3.1 m08b run in the work folder does not reproduce the repository tables: {same}")
    sig = [dict(sector=s, factor=repr(d["tfa"]["ID"][s] / d["t19"]["ID"][s]), basis="v3.1 RAS solution (DFX F1.3) on the v3.1 seed: tfa_ID,s / t19_ID,s (rank one: r_c x sigma_s)")
           for s in SECTORS]
    pd.DataFrame(sig).to_csv(DEMAND_DIR / "DEMAND_ANCHOR_V3_SECTOR_FACTORS.csv", index=False, lineterminator="\n")
    fr = [dict(country=c, sector=s, anchor_mwh=repr(d["tfa"][c][s]), t19_mwh=repr(d["t19"][c][s])) for c in ASEAN for s in SECTORS]
    pd.DataFrame(fr).to_csv(DEMAND_DIR / "DEMAND_ANCHOR_V3_FROZEN.csv", index=False, lineterminator="\n")
    (wd / "anchors_v3_ras.json").replace(V4_DIR / "ANCHORS_V31_RAS_DUMP.json")
    return dict(same=same, sigma={r["sector"]: float(r["factor"]) for r in sig})


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--write-anchor-tables", action="store_true", help="write DEMAND_ANCHOR_V3_SECTOR_FACTORS.csv / DEMAND_ANCHOR_V3_FROZEN.csv (v3.1 RAS dump)")
    p.add_argument("--anchor-mode", default=None, choices=("ras", "iid", "iib", "external"))
    p.add_argument("--set", action="append", default=[], help="switch override key=value (research.demand.v4 keys)")
    p.add_argument("--checkpoints", type=Path, default=None, help="write the cumulative checkpoints S0-S7 into this folder (no table output)")
    p.add_argument("--steps", default="", help="comma-separated steps for --checkpoints")
    p.add_argument("--config-switches", action="store_true", help="take the switch set from the configuration (default: the v4 main set V4_MAIN)")
    p.add_argument("--work", type=Path, default=None)
    a = p.parse_args()
    if a.write_anchor_tables:
        print(json.dumps(write_anchor_tables(Chain(a.work)), indent=1)); return
    import yaml
    ov = {k: yaml.safe_load(v) for k, v in (x.split("=", 1) for x in a.set)}
    if a.anchor_mode:
        ov["anchor_mode"] = a.anchor_mode
    if a.config_switches:
        from v4_common import load_config
        s = switches(load_config(), ov)
    else:
        s = switches(None, {**V4_MAIN, **ov})
    if a.checkpoints is not None:
        checkpoints(a.checkpoints, s, set(x for x in a.steps.split(",") if x) or None, Chain(a.work))
        return
    import v4_outputs as O
    O.write_tables(s, Chain(a.work))


if __name__ == "__main__":
    main()
