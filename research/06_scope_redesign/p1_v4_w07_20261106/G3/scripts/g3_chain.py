"""G3 combined quantification in a scratch copy of the data chain (outside the repository) for TH, PH, SG.

    PYTHONHASHSEED=0 python scripts/g3_chain.py          (WSL pypsa-earth python)

0. Reproduction: the unmodified copy must give the four s3_0 outputs byte for byte and the v3 'other' bucket of TH / PH / SG within 1e-3 MWh;
   the patched copy (cement correction ii) without its environment variable must be byte identical too. Otherwise STOP.
1. Steps in the instruction / template order, cumulative, each under two NCV lines (A3 item 7): 'v3' (v3 factors) and '207' (decision 207 values):
   1 NCV -> 2 captive (b) central -> 3 cement (ii) -> 4 steel (spatial only) -> 5 pulp and paper -> 6 ethylene (HVC) -> 7 glass -> 8 closed loop (bagasse).
   Deduction rule for a new product (S0 3.2 item 2): 2019 energy leaves the same-name UNSD row (fuel by the row's fuel mix, electricity from the row's
   electricity; the non-metallic row after the cement that s3_0 takes from it); the excess leaves the cache 'other' row (after s3_0's own steel / cement
   takes); what cannot be found is recorded (D163-4) and not deducted. Pulp and paper: capped at the UNSD paper row (the row is the purchased energy of
   the national statistics; the excess is treated as self-supply, closed loop) - spill to 'other' as a sensitivity. 2050: explicit vectors added to
   T_v2, Other = T - explicit (D163-6 a). Captive: C in tonnes x the NCV of the line (W11 4.2 item 5).
2. Single steps (each alone on v3), additivity against the combined result, and sensitivities on the combined '207' line.
Outputs <CC>_OTHER_SHARE_STEPS.csv, <CC>_SUBSECTORS_V4.csv, <CC>_CAPTIVE.csv, tables/<CC>_COMBINED.csv, tables/<CC>_ADDITIVITY.csv,
tables/<CC>_DEDUCTION_LOG.csv, tables/_chain_evidence.json. Nothing is solved; the repository is not written.
"""
from __future__ import annotations

import filecmp
import json
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import g3_common as cm   # noqa: E402

STEP_LABEL = {0: "v3", 1: "+1 热值（第 207 项）", 2: "+2 自备电厂 (b) 中心值", 3: "+3 水泥修正 (ii)", 4: "+4 钢（只换空间）", 5: "+5 纸浆造纸（闭环规则）",
              6: "+6 乙烯 / HVC", 7: "+7 玻璃", 8: "+8 闭环：蔗渣移出 T_v2"}
SG_REFGAS_EXCESS_KT = None   # computed from the export in main()
CACHE_DIR = Path("/home/jin/v4w07_g3/scenario_cache")   # outside the repository and outside the deliverable folder


class Runner:
    def __init__(self):
        self.v3 = cm.import_v3(); self.fut = self.v3.future_vectors()
        self.ch = cm.Chain(); self.ch.copy()
        T = cm.G3 / "tables"
        self.sch = json.loads((T / "_ncv_schemes.json").read_text())
        self.cap = json.loads((T / "_captive_inputs.json").read_text())
        self.prod = json.loads((T / "_products_inputs.json").read_text())
        self.E = cm.export_2019_flows()
        self.ncv_cache = {}
        self.log = []
        files = [T / n for n in ("_ncv_schemes.json", "_captive_inputs.json", "_products_inputs.json")] + sorted((cm.G3 / "scripts").glob("g3_*.py")) + \
                [cm.REPO / cm.S30_REL, cm.REPO / cm.CACHE_REL, cm.REPO / cm.ATS_REL]
        self.input_sha = {p.name: cm.sha256(p) for p in files}
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ NCV --------------------------------------------------------------
    def ncv(self, cc, name):
        if name in (None, "v3") or not self.sch[cc].get(name):
            return None, {}
        key = (cc, name)
        if key not in self.ncv_cache:
            fac = {tuple(k.split("|")): v for k, v in self.sch[cc][name].items()}
            sch = cm.NCV(f"{cc}:{name}", fac); dl, ra, _ = cm.ncv_deltas(sch, self.E, countries=(cc,))
            self.ncv_cache[key] = ((dl, ra), fac)
        return self.ncv_cache[key]

    def gj_t(self, cc, ncvname, com="Brown coal"):
        _, fac = self.ncv(cc, ncvname)
        return fac.get((cc, com), cm.upstream_conv()[com] * 1e6 * 3.6 / 1e3)

    # ------------------------------------------------------------------ captive moves ------------------------------------------------------
    def captive_moves(self, cc, level, ncvname, refinery_mode="b_prime"):
        mv = []
        if not level:
            return mv, 0.0, 0.0
        C_tot = E_tot = 0.0
        items = self.cap[cc]["levels"].get(level, [])
        cells = None
        if any("C_mwh_fixed" in it for it in items):   # energy-based C (TH): cap at the coal cell of the scratch inputs under this NCV line
            ncvd, _ = self.ncv(cc, ncvname); self.ch.prepare(ncvd, [], None); cells = self.ch.sub19(cc)
        for it in items:
            C = it["C_mwh_fixed"] if "C_mwh_fixed" in it else it["coal_kt"] * self.gj_t(cc, ncvname, it["commodity"]) * 1e3 / 3.6   # TH: energy-based (E / eta); PH: tonnes x NCV of the line
            E = it["E_gwh"] * 1e3
            if cells is not None and C > 0:
                f = min(1.0, 0.999999 * cells[it["row"]]["coal"] / C); C *= f; E *= f
                self.log.append(dict(scenario=getattr(self, "_name", ""), country=cc, product=f"captive {level}: {it['type']}", row=it["row"], fuel_wanted_mwh=C / f if f else C,
                                     el_wanted_mwh=0.0, fuel_from_row_mwh=C, el_from_row_mwh=0.0, fuel_from_other_mwh=0.0, el_from_other_mwh=0.0, not_found_mwh=0.0,
                                     capped_as_self_supply_mwh=0.0, rule=f"captive C capped at the scratch coal cell (factor {f:.3f})"))
            mv.append((cc, it["row"], "coal", C)); C_tot += C
            if it["electricity_added"] or refinery_mode == "b_literal":
                mv.append((cc, it["row"], "electricity", -E)); E_tot += E
        return mv, C_tot, E_tot

    # ------------------------------------------------------------------ product deductions -------------------------------------------------
    def deduct(self, cc, avail, other_avail, row, fuel, el, label, cap_row=False):
        """Take el from the row's electricity and fuel by the row's fuel mix; excess from the cache 'other' row (unless cap_row); log the rest."""
        mv = []; r = avail[row]
        ft = sum(r[f] for f in cm.FUELS)
        tf = min(fuel, ft)
        for f in cm.FUELS:
            d = tf * r[f] / ft if ft > 0 else 0.0
            if d > 0:
                mv.append((cc, row, f, d)); r[f] -= d
        te = min(el, r["electricity"])
        if te > 0:
            mv.append((cc, row, "electricity", te)); r["electricity"] -= te
        ex_f, ex_e = fuel - tf, el - te
        spill_f = spill_e = 0.0
        if not cap_row and (ex_f > 1e-6 or ex_e > 1e-6):
            o = other_avail; oft = sum(o[f] for f in cm.FUELS)
            spill_f = min(ex_f, oft)
            for f in cm.FUELS:
                d = spill_f * o[f] / oft if oft > 0 else 0.0
                if d > 0:
                    mv.append((cc, "other", f, d)); o[f] -= d
            spill_e = min(ex_e, o["electricity"])
            if spill_e > 0:
                mv.append((cc, "other", "electricity", spill_e)); o["electricity"] -= spill_e
        self.log.append(dict(scenario=getattr(self, "_name", ""), country=cc, product=label, row=row, fuel_wanted_mwh=fuel, el_wanted_mwh=el, fuel_from_row_mwh=tf, el_from_row_mwh=te,
                             fuel_from_other_mwh=spill_f, el_from_other_mwh=spill_e, not_found_mwh=(ex_f - spill_f) + (ex_e - spill_e) if not cap_row else 0.0,
                             capped_as_self_supply_mwh=(ex_f + ex_e) if cap_row else 0.0, rule="cap at the UNSD paper row (excess not deducted: self-supply or already moved by captive b)" if cap_row else "row, then other (S0 3.2 item 2)"))
        return mv

    # ------------------------------------------------------------------ scenario (with a resumable disk cache) ---------------------------
    def scenario(self, cc, name, **kw):
        """WSL may recycle the distribution during a run: every finished scenario is stored under CACHE_DIR, keyed by the scenario arguments and the
        SHA256 of every input (scripts, input JSONs, worktree s3_0 / cache / ATS), so a re-run resumes and never reuses a stale result."""
        import hashlib
        key = hashlib.sha256(json.dumps(dict(cc=cc, name=name, kw=kw, inputs=self.input_sha), sort_keys=True, default=str).encode()).hexdigest()[:24]
        f = CACHE_DIR / f"{cc}_{key}.json"
        if f.exists():
            d = json.loads(f.read_text()); self.log.extend(d["log"]); return d["rec"]
        n0 = len(self.log); self._n0 = n0; self._name = name
        rec = self._scenario(cc, name, **kw)
        f.write_text(json.dumps(dict(rec=rec, log=self.log[n0:]), default=float))
        return rec

    def _scenario(self, cc, name, ncv="v3", captive=None, refinery_mode="b_prime", cement=False, pp=None, eth=None, glass=False, copper=False,
                  closed_loop=None, sg_refgas=False, tag=""):
        ncvd, _ = self.ncv(cc, ncv)
        mv, C, E = self.captive_moves(cc, captive, ncv, refinery_mode)
        cem = {cc: self.prod[cc]["cement_usgs_2019_t"]} if cement and "cement_usgs_2019_t" in self.prod[cc] else None
        if sg_refgas:
            mv.append((cc, "chemical and petrochemical", "oil", SG_REFGAS_EXCESS_KT * cm.upstream_conv()["Refinery gas"] * 1e6))
        extra = {}
        P = self.prod[cc]
        if closed_loop and "sugar_closed_loop" in P:   # self-produced residues leave first: products deduct from purchased energy only
            mv.append((cc, P["sugar_closed_loop"]["row"], "biomass", P["sugar_closed_loop"]["bio19"]))
            if closed_loop == "bagasse+biogas" and "biogas_closed_loop" in P:
                for row, v in P["biogas_closed_loop"]["rows"].items():
                    mv.append((cc, row, "biomass", v))   # MWh
        if pp or eth or glass or copper:
            S0, ob0, pz0, _ = self.ch.run(ncvd, mv, cem)
            sub = self.ch.sub19(cc)
            avail = {k: dict(v) for k, v in sub.items()}
            pc = pz0[pz0.country == cc]
            cem19 = {c_: float(pc[(pc.subsector == "cement") & (pc.carrier == c_)].mwh_2019.sum()) for c_ in cm.CARS19}
            if "non-metallic minerals" in avail and sum(avail["non-metallic minerals"].values()) > 0:
                for c_ in cm.CARS19:
                    avail["non-metallic minerals"][c_] = max(0.0, avail["non-metallic minerals"][c_] - cem19[c_])
            o = ob0.loc[cc]
            other_avail = {c_: max(0.0, float(o[f"other_2019_{c_}_mwh"]) - sum(avail.get(s_, {}).get(c_, 0.0) for s_ in ("construction", "mining and quarrying"))) for c_ in cm.CARS19}
            if pp:
                p = P["pulp_paper"]; spill = pp == "spill"
                mv += self.deduct(cc, avail, other_avail, p["row"], p["fuel19"], p["el19"], f"pulp and paper ({pp})", cap_row=not spill)
                case = "literal_latest" if pp == "literal_latest" else "main"
                extra["pulp_paper"] = p["v2050_literal_rule"]["main"] if pp == "literal_rule" else p["v2050"][case]
            if eth:
                key = eth if "|" in eth else "main|central"
                e = P["ethylene"]["cases"][key]
                mv += self.deduct(cc, avail, other_avail, P["ethylene"]["row"], e["fuel19"], e["el19"], f"ethylene ({eth})")
                extra["ethylene"] = e["v2050_today_intensity"] if eth == "today_intensity" else e["v2050"]
            if glass and "glass" in P:
                g = P["glass"]; mv += self.deduct(cc, avail, other_avail, g["row"], g["fuel19"], g["el19"], "glass"); extra["glass"] = g["v2050"]
            if copper and "copper" in P:
                c_ = P["copper"]; mv += self.deduct(cc, avail, other_avail, c_["row"], c_["fuel19"], c_["el19"], "copper"); extra["copper"] = c_["v2050"]
        S, ob, pz, gaps = self.ch.run(ncvd, mv, cem)
        L = cm.v3_layer(self.v3, S.loc[cc], self.fut, {k: {kk: float(vv) for kk, vv in v.items()} for k, v in extra.items()})
        o = ob.loc[cc]
        g = gaps[(gaps.country == cc) & gaps.item.str.contains("not found|exceeds the other bucket", regex=True) & (gaps.carrier != "all")]
        mylog = [x for x in self.log[self._n0:] if x["country"] == cc]
        moved = sum(x["fuel_from_row_mwh"] + x["el_from_row_mwh"] + x["fuel_from_other_mwh"] + x["el_from_other_mwh"] for x in mylog if not x["product"].startswith("captive"))
        rec = dict(country=cc, scenario=name, tag=tag, ncv=ncv, captive=captive or "", refinery_mode=refinery_mode if captive else "", cement_ii=cement, pp=pp or "", eth=eth or "",
                   glass=glass, copper=copper, closed_loop=closed_loop or "", sg_refgas=sg_refgas, captive_C_mwh=C, captive_E_mwh=E,
                   industry_2019_in_chain_twh=float(o.industry_2019_mwh) / 1e6, industry_2019_incl_explicit_twh=(float(o.industry_2019_mwh) + moved) / 1e6,
                   explicit_products_2019_twh=moved / 1e6, other_2019_twh=float(o.other_2019_mwh) / 1e6,
                   T_2050_twh=L["T"] / 1e6, other_2050_twh=L["other_total"] / 1e6, other_share=L["other_total"] / L["T"], other_scale=L["scale"],
                   cement_2019_twh=float(pz[(pz.country == cc) & (pz.subsector == "cement")].mwh_2019.astype(float).sum()) / 1e6,
                   s3_unfound_mwh=float(g.mwh.sum()))
        for k in cm.OUTC:
            rec[f"other_2050_{k}_twh"] = L["other"].get(k, 0.0) / 1e6
        for k, v in L["by_sub"].items():
            rec[f"sub_2050_{k}_twh"] = v / 1e6
        for c_ in cm.CARS19:
            rec[f"other_2019_{c_}_twh"] = float(o[f"other_2019_{c_}_mwh"]) / 1e6
        rec["_parts"] = {k: {kk: vv / 1e6 for kk, vv in v.items()} for k, v in L["parts"].items()}
        rec["_log"] = mylog
        return rec


def main():
    t0 = time.time()
    global SG_REFGAS_EXCESS_KT
    R = Runner(); ev = cm.Ev("chain")
    # ---------------------------------------------------------------- reproduction --------------------------------------------------------
    S, ob, pz, gaps = R.ch.run()
    dd, rd = R.ch.chain / "research_inputs/demand_v5", cm.REPO / "research_inputs/demand_v5"
    same = {f: filecmp.cmp(dd / f, rd / f, shallow=False) for f in cm.S3_OUT}
    sub = pd.read_csv(rd.parent / "industry_v3/INDUSTRY_2050_SUBSECTOR_CARRIER_V3.csv"); sub = sub[(sub.case == "main") & (sub.subsector == "other")]
    devs = {}
    for cc in cm.CC3:
        L = cm.v3_layer(R.v3, S.loc[cc], R.fut); gg = sub[sub.country == cc].set_index("carrier").mwh_2050
        devs[cc] = max(abs(L["other"].get(k, 0.0) - float(gg.get(k, 0.0))) for k in set(L["other"]) | set(gg.index))
    R.ch.prepare(cem_t19={"ZZ": 1.0})   # patched s3_0, no variable for TH / PH / SG
    import subprocess
    r = subprocess.run([sys.executable, "s3_0_industry.py"], cwd=R.ch.chain / "scripts_project", capture_output=True, text=True, env={"PYTHONHASHSEED": "0", "PATH": "/usr/bin:/bin"})
    same_p = {f: filecmp.cmp(dd / f, rd / f, shallow=False) for f in cm.S3_OUT}
    repro = dict(byte_identical=same, byte_identical_patched_no_env=same_p, max_abs_dev_v3_other_mwh=devs)
    ev.put("reproduction.byte_identical_all", float(all(same.values()) and all(same_p.values())), "bool", "filecmp of the four s3_0 outputs (unmodified and patched copy)", "EXACT", "-")
    for cc, d in devs.items():
        ev.put(f"reproduction.{cc}.max_abs_dev_v3_other_mwh", d, "MWh", "v3 layer of the copy vs INDUSTRY_2050_SUBSECTOR_CARRIER_V3.csv", "EXACT", "-")
    if not (all(same.values()) and all(same_p.values())) or max(devs.values()) > 1e-3:
        raise SystemExit(f"STOP: the unmodified scratch copy does not reproduce the repository: {repro}")
    # SG refinery gas: chemical consumption above what production leaves after refinery own use and autoproducers
    X = cm.unsd_export(("SG",)); X = X[X.year == 2019]
    rg = X[X.commodity.str.lower() == "refinery gas"]
    val = lambda tr: float(rg[rg.transaction.str.lower() == tr].q.max())
    prod_, own_, auto_, chem_ = val("production"), val("own use by oil refineries"), val("transformation in electricity plants - autoproducers"), val("consumption by chemical and petrochemical")
    SG_REFGAS_EXCESS_KT = chem_ - (prod_ - own_ - auto_)
    for k, v in (("production", prod_), ("refinery_own_use", own_), ("autoproducer", auto_), ("chemical", chem_), ("excess_over_supply", SG_REFGAS_EXCESS_KT)):
        ev.put(f"SG.refinery_gas_2019_kt.{k}", v, "kt", "UNSD 2019 SG refinery gas (export)", "VERIFIED" if k != "excess_over_supply" else "EXACT", "B")
    naph = float(X[(X.commodity == "Naphtha") & (X.transaction.str.lower() == "non-energy uses")].q.max())
    ev.put("SG.naphtha_neu_2019_kt", naph, "kt", "UNSD 2019 SG naphtha non-energy uses", "VERIFIED", "B")

    # ---------------------------------------------------------------- steps ---------------------------------------------------------------
    P = R.prod
    plan = {cc: dict(captive="central", cement="cement_usgs_2019_t" in P[cc], pp="main" if "pulp_paper" in P[cc] else None, eth="main|central",
                     glass="glass" in P[cc], closed_loop="bagasse" if "sugar_closed_loop" in P[cc] else None) for cc in cm.CC3}
    rows = {cc: [] for cc in cm.CC3}
    for cc in cm.CC3:
        pl = plan[cc]
        for line in ("v3", "207"):
            for k in range(0, 9):
                kw = dict(ncv=line if k >= 1 else "v3", captive=pl["captive"] if k >= 2 else None, cement=pl["cement"] and k >= 3, pp=pl["pp"] if k >= 5 else None,
                          eth=pl["eth"] if k >= 6 else None, glass=pl["glass"] and k >= 7, closed_loop=pl["closed_loop"] if k >= 8 else None)
                if line == "v3" and k == 0 and rows[cc]:
                    continue
                rec = R.scenario(cc, f"{line}:{k}", tag=f"step{k}", **kw)
                rec["step"] = k; rec["ncv_line"] = line
                rows[cc].append(rec)
        # single steps on v3
        singles = [("single:1 NCV", dict(ncv="207")), ("single:2 captive", dict(captive=pl["captive"])), ("single:3 cement ii", dict(cement=pl["cement"])),
                   ("single:5 pulp paper", dict(pp=pl["pp"])), ("single:6 ethylene", dict(eth=pl["eth"])), ("single:7 glass", dict(glass=pl["glass"])),
                   ("single:8 closed loop", dict(closed_loop=pl["closed_loop"]))]
        for nm, kw in singles:
            rec = R.scenario(cc, nm, tag="single", **kw); rec["step"] = -1; rec["ncv_line"] = "single"; rows[cc].append(rec)
        # sensitivities on the combined 207 line
        base = dict(ncv="207", captive=pl["captive"], cement=pl["cement"], pp=pl["pp"], eth=pl["eth"], glass=pl["glass"], closed_loop=pl["closed_loop"])
        sens = []
        if cc == "TH":
            sens = [("sens: 热值 SDMX 子项 / IPCC 煤种（= W11 d）", dict(ncv="sens_children_ipcc")), ("sens: 热值 EPPO 进口煤 26.37", dict(ncv="sens_eppo")),
                    ("sens: 热值维持 v3（其余全部）", dict(ncv="v3")),
                    ("sens: 自备 GIPT 非炼油机组在工业行 (b)", dict(captive="sens_nonrefinery")), ("sens: 自备 GIPT 全部机组在工业行 (b)", dict(captive="sens_all_gipt")),
                    ("sens: 乙烯利用率 0.75", dict(eth="main|low")), ("sens: 乙烯利用率 0.95", dict(eth="main|high")),
                    ("sens: 乙烯 2020 基年（含 Cracker No 5）", dict(eth="base_2020_incl_new|central")), ("sens: 乙烯 2050 用 2019 能源用途强度", dict(eth="today_intensity")),
                    ("sens: 纸浆造纸 字面闭环（生物质全部单列）", dict(pp="literal_rule")), ("sens: 纸浆造纸 超出造纸行部分从其他扣", dict(pp="spill")),
                    ("sens: 纸浆造纸 字面最近年份基年", dict(pp="literal_latest")), ("sens: 闭环不移出蔗渣（维持 v3）", dict(closed_loop=None)),
                    ("sens: 闭环 蔗渣 + 沼气", dict(closed_loop="bagasse+biogas"))]
        elif cc == "PH":
            sens = [("sens: 热值 IPCC 次烟煤 18.9", dict(ncv="sens_ipcc_subbit")), ("sens: 热值 APEC 22.098", dict(ncv="sens_apec")), ("sens: 热值维持 v3（其余全部）", dict(ncv="v3")),
                    ("sens: 自备低档", dict(captive="low")), ("sens: 自备高档", dict(captive="high")), ("sens: 自备 (b) 字面（炼厂电力记为工业用电）", dict(refinery_mode="b_literal")),
                    ("sens: 乙烯利用率 0.75", dict(eth="main|low")), ("sens: 乙烯利用率 0.95", dict(eth="main|high")), ("sens: 不计乙烯（2019 年在运存疑）", dict(eth=None)),
                    ("sens: 乙烯 2050 用 2019 能源用途强度", dict(eth="today_intensity")),
                    ("sens: 纸浆造纸 字面闭环（生物质全部单列）", dict(pp="literal_rule")), ("sens: 纸浆造纸 超出造纸行部分从其他扣", dict(pp="spill")),
                    ("sens: 加铜冶炼（PASAR，ETSAP 2018）", dict(copper=True)), ("sens: 闭环不移出蔗渣（维持 v3）", dict(closed_loop=None))]
        else:
            sens = [("sens: 乙烯含 GEPDSGP0004（SFI 全部 5,261 kt）", dict(eth="with_duplicate|central")), ("sens: 乙烯利用率 0.75", dict(eth="main|low")),
                    ("sens: 乙烯利用率 0.95", dict(eth="main|high")), ("sens: 乙烯 2050 用 2019 能源用途强度", dict(eth="today_intensity")),
                    ("sens: 化工行炼厂气超出供应部分移出（783 kt）", dict(sg_refgas=True)), ("sens: 不计乙烯", dict(eth=None))]
        for nm, kw in sens:
            k2 = dict(base); k2.update(kw)
            rec = R.scenario(cc, nm, tag="sens", **k2); rec["step"] = 99; rec["ncv_line"] = "sens"; rows[cc].append(rec)
        # single sensitivity on v3 for SG refinery gas
        if cc == "SG":
            rec = R.scenario(cc, "single: 化工行炼厂气超出供应部分移出（v3 上）", tag="single", sg_refgas=True); rec["step"] = -1; rec["ncv_line"] = "single"; rows[cc].append(rec)
    R.ch.restore()
    # ---------------------------------------------------------------- outputs --------------------------------------------------------------
    pd.DataFrame(R.log).to_csv(cm.G3 / "tables/DEDUCTION_LOG.csv", index=False, float_format="%.3f")
    carmap = [("elec", "electricity"), ("heat_lt150", "heat"), ("heat_150_200", "heat_medium_a"), ("heat_200_400", "heat_medium_b"), ("heat_gt400", "heat_high"),
              ("oil", "oil"), ("gas", "gas"), ("coal", "coal"), ("biomass", "biomass"), ("H2", "hydrogen")]
    for cc in cm.CC3:
        D = pd.DataFrame([{k: v for k, v in r.items() if k not in ("_parts", "_log")} for r in rows[cc]])
        v3row = D[(D.ncv_line == "v3") & (D.step == 0)].iloc[0]
        for c_ in [c_ for c_ in D.columns if c_.endswith("_twh")]:
            D[f"d_{c_}"] = D[c_] - float(v3row[c_])
        D.to_csv(cm.G3 / f"tables/{cc}_COMBINED.csv", index=False, float_format="%.6f")
        # A6 steps table
        out = []
        for line in ("v3", "207"):
            Z = D[D.step.between(0, 8) & (((D.ncv_line == line) & ((D.step > 0) | (line == "v3"))) | ((D.ncv_line == "v3") & (D.step == 0)))].sort_values("step")
            prev = None
            for r in Z.itertuples():
                rec = dict(step=STEP_LABEL[int(r.step)], ncv_scheme=line, T_v2_2050_TWh=r.T_2050_twh, other_2050_TWh=r.other_2050_twh, other_share=r.other_share,
                           delta_TWh=(r.other_2050_twh - prev.other_2050_twh) if prev is not None else 0.0)
                for a, b in carmap:
                    rec[a] = getattr(r, f"other_2050_{b}_twh")
                rec["grade"] = "EXACT (v3)" if int(r.step) == 0 else "PROPOSED (quantified, C)"
                rec["delta_T_TWh"] = (r.T_2050_twh - prev.T_2050_twh) if prev is not None else 0.0
                rec["scenario"] = r.scenario
                out.append(rec); prev = r
        for r in D[D.ncv_line == "sens"].itertuples():
            base = D[(D.ncv_line == "207") & (D.step == 8)].iloc[0]
            rec = dict(step=r.scenario, ncv_scheme=r.ncv, T_v2_2050_TWh=r.T_2050_twh, other_2050_TWh=r.other_2050_twh, other_share=r.other_share,
                       delta_TWh=r.other_2050_twh - float(base.other_2050_twh))
            for a, b in carmap:
                rec[a] = getattr(r, f"other_2050_{b}_twh")
            rec["grade"] = "PROPOSED (sensitivity, C)"; rec["delta_T_TWh"] = r.T_2050_twh - float(base.T_2050_twh); rec["scenario"] = "sensitivity vs combined 207 line"
            out.append(rec)
        pd.DataFrame(out).to_csv(cm.G3 / f"{cc}_OTHER_SHARE_STEPS.csv", index=False, float_format="%.6f")
        # additivity (single steps on v3 vs combined 207 line)
        comb = D[(D.ncv_line == "207") & (D.step == 8)].iloc[0]; singles = D[(D.ncv_line == "single") & D.scenario.str.match(r"^single:\d")]
        A = []
        for c_ in ["T_2050_twh", "other_2050_twh"] + [f"other_2050_{k}_twh" for k in cm.OUTC]:
            s = float(singles[f"d_{c_}"].sum()); x = float(comb[f"d_{c_}"])
            A.append(dict(quantity=c_, sum_of_single_steps_twh=s, combined_twh=x, non_additive_twh=x - s))
        pd.DataFrame(A).to_csv(cm.G3 / f"tables/{cc}_ADDITIVITY.csv", index=False, float_format="%.6f")
        for r in D.itertuples():
            for k in ("T_2050_twh", "other_2050_twh", "other_share", "d_T_2050_twh", "d_other_2050_twh", "other_2019_twh"):
                ev.put(f"{cc}.{r.scenario}.{k}", getattr(r, k), "-" if k == "other_share" else "TWh", f"tables/{cc}_COMBINED.csv (scratch chain)",
                       "EXACT" if r.scenario == "v3:0" else "PROPOSED (quantified)", "C")
        for a in A:
            ev.put(f"{cc}.additivity.{a['quantity']}", a["non_additive_twh"], "TWh", f"tables/{cc}_ADDITIVITY.csv", "EXACT", "C")
        # A6 subsectors (combined 207 line)
        comb_rec = [r for r in rows[cc] if r["ncv_line"] == "207" and r["step"] == 8][0]; parts = comb_rec["_parts"]
        det = pd.read_csv(cm.G3 / f"tables/{cc}_PRODUCTS_DETAIL.csv")
        lg = pd.DataFrame(comb_rec["_log"]) if comb_rec["_log"] else pd.DataFrame(columns=["product", "row", "rule", "fuel_from_row_mwh", "el_from_row_mwh", "fuel_from_other_mwh", "el_from_other_mwh"])
        srows = []
        name_map = {"steel": "steel", "cement": "cement", "pulp_paper": "pulp and paper", "ethylene": "ethylene (HVC)", "glass": "glass", "copper": "copper (sensitivity)"}
        for part, v in parts.items():
            d_ = det[det.subsector == name_map.get(part, part)]
            dd_ = d_.iloc[0].to_dict() if len(d_) else {}
            prod_lbl = {"pulp_paper": "pulp and paper", "ethylene": "ethylene", "glass": "glass"}.get(part)
            l_ = lg[lg["product"].str.startswith(prod_lbl)] if prod_lbl else lg.iloc[0:0]
            pass   # the combined scenario holds one deduction per product
            rec = dict(subsector=part, route=dd_.get("route", {"dispersed": "UNSD sub-sector rows x PyPSA-Eur fallback (v3)", "other": "useful-heat bands (v3)", "ammonia": "-"}.get(part, "")),
                       activity_source=dd_.get("activity_source", ""), base_year=dd_.get("base_year", ""), activity_base=dd_.get("activity_base", ""), activity_2050=dd_.get("activity_2050", ""),
                       sec_source=dd_.get("sec_source", ""), energy_2019_deducted_TWh=(float(l_.fuel_from_row_mwh.sum() + l_.el_from_row_mwh.sum() + l_.fuel_from_other_mwh.sum() + l_.el_from_other_mwh.sum()) / 1e6 if len(l_) else ""),
                       deducted_from_row=(f"{l_.row.iloc[0]} ({l_.rule.iloc[0]}); from other {float(l_.fuel_from_other_mwh.sum() + l_.el_from_other_mwh.sum()) / 1e6:.3f} TWh" if len(l_) else ""),
                       energy_2050_TWh=sum(v.values()))
            for k in cm.OUTC:
                rec[k] = v.get(k, 0.0)
            rec["closed_loop_biomass_TWh"] = ""
            rec["grade"] = dd_.get("grade", "C")
            srows.append(rec)
        if "pulp_paper" in P[cc]:
            for r_ in srows:
                if r_["subsector"] == "pulp_paper":
                    r_["closed_loop_biomass_TWh"] = f"2019 {P[cc]['pulp_paper']['closed_loop_bl19'] / 1e6:.3f}; 2050 {P[cc]['pulp_paper']['closed_loop_bl2050']['main'] / 1e6:.3f}"
        if "sugar_closed_loop" in P[cc]:
            srows.append(dict(subsector="sugar (bagasse, closed loop)", route="outside T_v2", activity_source="UNSD 2019 bagasse in the food row", base_year=2019,
                              activity_base=P[cc]["sugar_closed_loop"]["bagasse_kt"] * 1e3, activity_2050=0.0, energy_2019_deducted_TWh=P[cc]["sugar_closed_loop"]["bio19"] / 1e6,
                              deducted_from_row="food and tobacco (biomass)", energy_2050_TWh=0.0, closed_loop_biomass_TWh=f"2019 {P[cc]['sugar_closed_loop']['bio19'] / 1e6:.3f}", grade="B"))
        pd.DataFrame(srows).to_csv(cm.G3 / f"{cc}_SUBSECTORS_V4.csv", index=False, float_format="%.6f")
        # A6 captive
        cap = R.cap[cc]; Dv = D.set_index("scenario")
        b207 = Dv.loc["207:1"]; c207 = Dv.loc["207:2"]
        def lvl(l):
            items = cap["levels"].get(l, [])
            return sum(i["coal_kt"] for i in items), sum((i["C_mwh_fixed"] / 1e3 if "C_mwh_fixed" in i else i["coal_kt"] * R.gj_t(cc, "207", i["commodity"]) / 3.6) for i in items) / 1e3, sum(i["E_gwh"] for i in items) / 1e3
        lv_names = {"TH": ("low", "central", "sens_all_gipt"), "PH": ("low", "central", "high"), "SG": ("low", "central", "high")}[cc]
        (kl, tl, el), (kc, tc, ec), (kh, th, eh) = (lvl(x) for x in lv_names)
        ineq = cap.get("inequality")
        crow = dict(country=cc, inequality_result=(ineq["verdict"] if isinstance(ineq, dict) else ineq),
                    gipt_captive_MW_2019=float(pd.read_csv(cm.G3 / "tables/CAPTIVE_UNITS_GIPT_2019.csv").query("iso == @cc and Type == 'coal'")["Capacity (MW)"].sum()),
                    C_low_TWh=tl, C_low_kt=kl, C_central_TWh=tc, C_central_kt=kc, C_high_TWh=th, C_high_kt=kh, E_low_TWh=el, E_central_TWh=ec, E_high_TWh=eh,
                    central_rule=cap["central_rule"], option_b_effect_2050=f"T_v2 {c207.T_2050_twh - b207.T_2050_twh:+.3f} TWh, other {c207.other_2050_twh - b207.other_2050_twh:+.3f} TWh (207 line, step 2)",
                    high_level_name=lv_names[2], NCV_used=(f"Brown coal {R.gj_t(cc, '207'):.3f} GJ/t (207 line)" if cc != "SG" else "-"))
        sens_rows = [r for r in rows[cc] if r["ncv_line"] == "sens" and ("自备" in r["scenario"])]
        crow["sensitivity_effects_2050"] = "; ".join(f"{r['scenario'].replace('sens: ', '')}: C used {sum(x['fuel_from_row_mwh'] for x in r['_log'] if x['product'].startswith('captive')) / 1e6 or r['captive_C_mwh'] / 1e6:.3f} TWh, "
                                                     f"T_v2 {r['T_2050_twh'] - float(Dv.loc['207:8'].T_2050_twh):+.3f}, other {r['other_2050_twh'] - float(Dv.loc['207:8'].other_2050_twh):+.3f} TWh vs combined"
                                                     for r in sens_rows)
        pd.DataFrame([crow]).to_csv(cm.G3 / f"{cc}_CAPTIVE.csv", index=False, float_format="%.6f")
    ev.extra["reproduction"] = repro; ev.extra["plan"] = plan; ev.extra["timing_s"] = time.time() - t0
    ev.write(cm.G3 / "tables/_chain_evidence.json")
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30); pd.set_option("display.max_colwidth", 60)
    print(json.dumps(repro, default=str)[:600]); print("timing s", round(time.time() - t0, 1))
    for cc in cm.CC3:
        D = pd.read_csv(cm.G3 / f"tables/{cc}_COMBINED.csv")
        print("=====", cc); print(D[["scenario", "other_2019_twh", "T_2050_twh", "d_T_2050_twh", "other_2050_twh", "d_other_2050_twh", "other_share", "explicit_products_2019_twh", "s3_unfound_mwh"]].round(3).to_string())


if __name__ == "__main__":
    main()
