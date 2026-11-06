"""V31 W15 stage A, section 3 (decision 213): resolution decomposition of the v3.1 2920x3h F1 / F2 against supplement 07 V1 / V2 (365 daily
time slices), from exported ledgers and capacities only (no solved network, no solver).

  python -I w15a_resolution.py --f <interim export> --s07 <supplement 07 export> --smoke <smoke56_v31 run dir> --pkg <hpc_package_v3_1>
         --s07pkg <screen_package_v3_dmax> --reg-s07 <registry @7aec953e> --reg-f <registry @a1ef782b> --out <work/p1_v31_w15_20261106> [--font <ttf/ttc>]

Writes RESOLUTION_DECOMP.csv (cost by category and technology group), RESOLUTION_CAPACITY.csv (capacity by technology x country),
RESOLUTION_DECOMP.png, evidence/NONRES_DIFFS.json, evidence/RESOLUTION_SUMMARY.json.
Cost numbers are the solved runs' own ledgers (VERIFIED); the split of new-build capital cost into annuity and FOM uses the cost table's
per-carrier ratio (INFERENCE); attributions to resolution / shipping basis are INFERENCE.
"""
import argparse, csv, hashlib, json, re
from collections import defaultdict
from pathlib import Path

import pandas as pd

GROUPS = [
    ("地面光伏", ["solar", "solar existing"]), ("屋顶光伏", ["solar rooftop"]), ("陆上风电", ["onwind", "onwind existing"]),
    ("海上风电", ["offwind-ac", "offwind-dc", "offwind-float", "offwind existing"]),
    ("固定电池储能", ["battery", "battery charger", "battery discharger"]), ("户用电池", ["home battery", "home battery charger", "home battery discharger"]),
    ("氢：电解", ["H2 Electrolysis"]), ("氢：储存", ["H2 Store Tank"]), ("氢：发电", ["H2 Fuel Cell", "H2 turbine"]), ("氢：管道", ["H2 pipeline"]),
    ("抽蓄", ["PHS", "PHS existing"]), ("水电", ["hydro", "hydro existing", "ror", "ror existing"]), ("地热", ["geothermal", "geothermal existing"]),
    ("核电", ["nuclear", "nuclear SMR"]), ("EV 电池与充电桩（固定）", ["EV battery", "BEV charger"]),
    ("气电", ["CCGT", "CCGT CC", "CCGT existing", "OCGT", "OCGT existing", "OCGT methanol"]),
    ("煤电与油电（存量）", ["coal existing", "lignite existing", "oil existing"]),
    ("生物质", ["BtL", "biogas upgrading", "biomass EOP", "biomass EOP CC", "industry biomass CC", "industry biomass boiler", "industry biomass boiler CC",
             "industry direct firing biomass", "industry direct firing biomass CC", "solid biomass", "biogas", "biomass-to-methanol", "electrobiofuels"]),
    ("CCS 与 CO2 链", ["co2 sequestered", "co2 sequestered extra-ASEAN", "co2 stored", "CO2 pipeline", "CO2 sequestration", "CO2 ship", "DAC",
                     "process emissions CC", "CO2 export extra-ASEAN", "CO2 transit export extra-ASEAN", "CO2 transit rail", "CO2 transit ship"]),
    ("化石制氢（SMR）", ["SMR", "SMR CC"]),
    ("化石燃料供应与进口", ["gas production", "gas production delivery", "LNG import", "coal", "lignite", "oil import", "H2 import", "FT fuel import",
                       "ammonia import", "methanol import"]),
    ("气管", ["gas pipeline"]), ("电力互联与专线", ["AC", "DC", "B2B", "dedicated plant line", "dedicated plant source"]),
    ("配电网", ["electricity distribution grid"]),
    ("合成燃料与储罐", ["methanolisation", "Haber-Bosch", "Fischer-Tropsch", "Sabatier", "methanol store", "ammonia store", "oil non-fossil store", "ammonia cracker"]),
    ("工业热", ["industry heat pump", "industry electric boiler", "industry gas boiler", "industry direct firing gas"]),
    ("液体船运与转运", ["methanol ship", "ammonia ship", "oil non-fossil ship", "liquid transit rail"]),
]
GROUP_OF = {c: g for g, cs in GROUPS for c in cs}
FREIGHT = ("liquid_ship_freight", "liquid_transit_freight", "co2_ship_freight", "co2_transit_freight", "co2_transit_ship_freight", "co2_transit_rail_freight")
CAT_ORDER = ["新建投资（年金）", "新建固定运维", "新建（未能拆分）", "存量固定运维", "燃料与边际成本", "运输运费", "跨境基础设施分摊", "贸易与结算（合计应约为 0）"]
SHIP_SA_MINUS_SB_56 = {"integrated": 0.5057e9, "no_new_xb": 0.5023e9}   # RUN_PLAN_V3.md section 25: 56x3h smoke S-A minus supplement-05 S-B (re-optimised)


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def jl(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def group(car: str) -> str:
    return GROUP_OF.get(car, "其他")


def inv_share(ccb: Path) -> dict:
    """Per carrier: share of the annuity in capital_cost = af / (af + FOM %/100) over cost-table rows (INFERENCE when the rows of a carrier differ)."""
    df = pd.read_csv(ccb)
    df = df[pd.to_numeric(df.annuity_factor, errors="coerce").notna() & pd.to_numeric(df.fom_pct, errors="coerce").notna()].copy()
    df["s"] = df.annuity_factor.astype(float) / (df.annuity_factor.astype(float) + df.fom_pct.astype(float) / 100.0)
    out = {}
    for car, g in df.groupby("carrier"):
        out[car] = dict(median=float(g.s.median()), min=float(g.s.min()), max=float(g.s.max()), rows=int(len(g)))
    return out


def ledger(d: Path, shares: dict) -> pd.DataFrame:
    L = pd.read_csv(d / "COUNTRY_COST_LEDGER_DETAIL.csv", keep_default_na=False)
    rows = []
    for r in L.itertuples(index=False):
        s, car, v = r.subject, r.carrier, float(r.eur)
        if s == "capex_new":
            sh = shares.get(car)
            if sh:
                rows.append(("新建投资（年金）", car, r.entity, v * sh["median"])); rows.append(("新建固定运维", car, r.entity, v * (1 - sh["median"])))
            else:
                rows.append(("新建（未能拆分）", car, r.entity, v))
        elif s == "fom_existing":
            rows.append(("存量固定运维", car, r.entity, v))
        elif s == "variable_cost":
            rows.append(("燃料与边际成本", car, r.entity, v))
        elif s in FREIGHT:
            rows.append(("运输运费", car or s, r.entity, v))
        elif s == "xb_share_infrastructure_cost":
            rows.append(("跨境基础设施分摊", car or s, r.entity, v))
        else:
            rows.append(("贸易与结算（合计应约为 0）", f"{s}|{car}", r.entity, v))
    df = pd.DataFrame(rows, columns=["category", "carrier", "entity", "eur"])
    df["group"] = [group(c) if cat not in ("贸易与结算（合计应约为 0）", "跨境基础设施分摊", "运输运费") else
                   {"运输运费": "运输运费", "跨境基础设施分摊": "跨境基础设施分摊"}.get(cat, "贸易与结算") for c, cat in zip(df.carrier, df.category)]
    return df


def capacity(d: Path) -> pd.DataFrame:
    C = jl(d / "CAPACITY_BY_TECH_COUNTRY.json"); rows = []
    for comp, recs in C.items():
        for r in recs:
            key = "e_nom_opt" if comp == "Store" else "p_nom_opt"
            car = r["carrier"]
            unit = ("t" if car.lower().startswith("co2") else "MWh") if comp == "Store" else "MW"
            rows.append((comp, car, r.get("country", ""), unit, float(r[key])))
    xb = pd.read_csv(d / "cross_border_flows.csv")
    for r in xb.itertuples(index=False):
        if r.country0 != r.country1:
            pair = "|".join(sorted([r.country0, r.country1]))
            rows.append(("CrossBorder", f"跨境 {r.carrier}", pair, "MW" if not str(r.carrier).startswith("CO2") else "t/h", float(r.capacity_opt_mw)))
    df = pd.DataFrame(rows, columns=["component", "carrier", "country", "unit", "value"])
    return df.groupby(["component", "carrier", "country", "unit"], as_index=False).value.sum()


def receipt_inputs(p: Path) -> dict:
    R = jl(p); out = {}
    for k, v in (R.get("inputs") or {}).items():
        if isinstance(v, dict):
            out[k] = v.get("sha256")
    for k in ("research_config_sha256", "research_config_subset_sha256"):
        out[k] = R.get(k)
    out["network_sha256"] = (R.get("network") or {}).get("sha256") or R.get("sha256") or (R.get("output") or {}).get("sha256")
    out["status"] = R.get("status")
    return out


def solve_meta(d: Path) -> dict:
    S = jl(d / "SOLVE_RECEIPT.json"); R = jl(d / "RUN.json")
    log = (d / "GUROBI_LOG_SCRUBBED.txt").read_text(encoding="utf-8", errors="replace")
    cpu = re.search(r"CPU model: (.*)", log); ver = re.search(r"Gurobi Optimizer version (\S+)", log)
    return dict(profile=S.get("solver_profile"), solver_parameters=S.get("solver_parameters"), cpu=cpu[1].strip() if cpu else None, gurobi=ver[1] if ver else None,
                snapshots=S["input_network"]["snapshots"], network_sha256=S["input_network"]["sha256"], objective=S["objective"], objective_lp=S["objective_lp"],
                constant=S["scaling"]["objective_constants"]["total_eur"], dust_cleanup=dict(mode=S["dust_cleanup"]["mode"], thresholds=S["dust_cleanup"]["thresholds"]),
                config_subset=S.get("config_subset", {}).get("network"), horizon=S["input_network"].get("horizon_scaling", {}).get("method"),
                ac_losses=S.get("transmission_losses", {}).get("ac_losses"), bunker_row_in_lp="research_bunker_co2_limit" in S["lp"].get("research_constraints", []),
                lp=dict(cols=S["lp"]["num_col"], rows=S["lp"]["num_row"], nnz=S["lp"]["nnz"]), label=R.get("label"))


def main():
    ap = argparse.ArgumentParser()
    for k in ("f", "s07", "smoke", "pkg", "s07pkg", "reg_s07", "reg_f", "out"):
        ap.add_argument("--" + k.replace("_", "-"), required=(k != "smoke"))
    ap.add_argument("--font")
    a = ap.parse_args()
    F, S07, PKG, SPKG, OUT = Path(a.f), Path(a.s07), Path(a.pkg), Path(a.s07pkg), Path(a.out)
    SM = Path(a.smoke) if a.smoke else None
    shares = inv_share(F / "F1" / "COMPONENT_COST_BREAKDOWN.csv")
    pairs = [("F1", "V1", "integrated"), ("F2", "V2", "no_new_xb")]
    dec_rows, cap_rows, summary = [], [], {}
    for fr, vr, sc in pairs:
        fd, vd = F / fr, S07 / vr
        Lf, Lv = ledger(fd, shares), ledger(vd, shares)
        Ls = ledger(SM / fr, shares) if SM and (SM / fr / "COUNTRY_COST_LEDGER_DETAIL.csv").exists() else None
        mf, mv = solve_meta(fd), solve_meta(vd)
        ms = solve_meta(SM / fr) if Ls is not None else None
        dZ = mf["objective"] - mv["objective"]
        tot_f, tot_v = Lf.eur.sum(), Lv.eur.sum()
        for level, keys in (("类别", ["category"]), ("技术组", ["group"]), ("类别×技术组", ["category", "group"])):
            gf = Lf.groupby(keys).eur.sum(); gv = Lv.groupby(keys).eur.sum(); gs = Ls.groupby(keys).eur.sum() if Ls is not None else None
            idx = gf.index.union(gv.index)
            for k in idx:
                f_, v_ = float(gf.get(k, 0.0)), float(gv.get(k, 0.0))
                if level == "类别×技术组" and abs(f_) < 1e5 and abs(v_) < 1e5:
                    continue
                kk = k if isinstance(k, tuple) else (k,)
                cat = kk[0] if "category" in keys else ""; grp = kk[-1] if "group" in keys else ""
                attr = "无（两边相同的常数项）" if cat == "存量固定运维" else ("船运口径（S-A / S-B）为主，另含分辨率下的流量变化" if (cat == "运输运费" or grp == "运输运费") else "分辨率（含日聚合规则）为主；船运口径重新优化的间接影响混在其中")
                dec_rows.append(dict(pair=f"{fr}−{vr}", scenario=sc, level=level, category=cat, group=grp,
                                     F_eur=round(f_, 2), s07_eur=round(v_, 2), delta_eur=round(f_ - v_, 2), share_of_dZ=round((f_ - v_) / dZ, 6),
                                     smoke56_F_eur=round(float(gs.get(k, 0.0)), 2) if gs is not None else "",
                                     attribution=attr, grade="VERIFIED（数值）/ INFERENCE（归因" + ("、投资与运维拆分）" if cat in ("新建投资（年金）", "新建固定运维") else "）")))
        resid = dZ - (tot_f - tot_v)
        fr_f = float(Lf[Lf.category == "运输运费"].eur.sum()); fr_v = float(Lv[Lv.category == "运输运费"].eur.sum())
        liq_f = float(Lf[(Lf.category == "运输运费") & Lf.carrier.isin(["methanol ship", "ammonia ship", "oil non-fossil ship", "liquid transit rail"])].eur.sum())
        liq_v = float(Lv[(Lv.category == "运输运费") & Lv.carrier.isin(["methanol ship", "ammonia ship", "oil non-fossil ship", "liquid transit rail"])].eur.sum())
        ship_lo, ship_hi = sorted([SHIP_SA_MINUS_SB_56[sc], liq_f - liq_v])
        other = float(Lf[Lf.group == "其他"].eur.sum() - Lv[Lv.group == "其他"].eur.sum())
        summary[f"{fr}-{vr}"] = dict(
            scenario=sc, objective_F_incl_constant=mf["objective"], objective_s07_incl_constant=mv["objective"], dZ_incl_constant=dZ,
            objective_F_lp=mf["objective_lp"], objective_s07_lp=mv["objective_lp"], dZ_lp=mf["objective_lp"] - mv["objective_lp"],
            constant_F=mf["constant"], constant_s07=mv["constant"], constant_equal=mf["constant"] == mv["constant"],
            instruction_quote_bn={"F1-V1": 36.4, "F2-V2": 33.6}[f"{fr}-{vr}"],
            instruction_quote_basis="F objective_lp (hpr_status, excl. constant) minus s07 objective incl. constant: mixed basis",
            mixed_basis_check=mf["objective_lp"] - mv["objective"],
            ledger_total_F=tot_f, ledger_total_s07=tot_v, ledger_vs_objective_residual=resid,
            category_delta={c: float(Lf[Lf.category == c].eur.sum() - Lv[Lv.category == c].eur.sum()) for c in CAT_ORDER},
            freight_delta_all=fr_f - fr_v, liquid_freight_delta=liq_f - liq_v,
            shipping_basis_band_eur=[ship_lo, ship_hi],
            shipping_basis_band_note="lower/upper of (56x3h smoke S-A minus S-B re-optimised, RUN_PLAN_V3 section 25) and (liquid ship freight delta here); INFERENCE",
            resolution_part_band_eur=[dZ - ship_hi, dZ - ship_lo],
            unclassified_group_delta=other, unclassified_share=other / dZ,
            smoke56=dict(objective=ms["objective"], snapshots=ms["snapshots"], note="56x3h, one dry-season week annualised (weight 156.43 h); reference only") if ms else None,
            solve_meta=dict(F=mf, s07=mv),
        )
        cf, cv = capacity(fd), capacity(vd)
        cs = capacity(SM / fr) if Ls is not None else None
        key = ["component", "carrier", "country", "unit"]
        m = cf.merge(cv, on=key, how="outer", suffixes=("_F", "_s07")).fillna({"value_F": 0.0, "value_s07": 0.0})
        if cs is not None:
            m = m.merge(cs.rename(columns={"value": "value_smoke56"}), on=key, how="left")
        for r in m.itertuples(index=False):
            car = r.carrier
            cap_rows.append(dict(pair=f"{fr}−{vr}", component=r.component, group=("电力互联与专线（跨境）" if r.component == "CrossBorder" else group(car)),
                                 carrier=car, country=r.country, unit=r.unit, F=round(r.value_F, 4), s07=round(r.value_s07, 4), delta=round(r.value_F - r.value_s07, 4),
                                 smoke56_F=(round(r.value_smoke56, 4) if cs is not None and pd.notna(r.value_smoke56) else "")))
    dec = pd.DataFrame(dec_rows)
    dec["cat_order"] = dec.category.map({c: i for i, c in enumerate(CAT_ORDER)}).fillna(99)
    dec = dec.sort_values(["pair", "level", "cat_order", "delta_eur"], key=lambda s: s if s.name != "delta_eur" else -s.abs()).drop(columns="cat_order")
    dec.to_csv(OUT / "RESOLUTION_DECOMP.csv", index=False, lineterminator="\n")
    cap = pd.DataFrame(cap_rows)
    cap = cap[(cap.F.abs() > 1e-3) | (cap.s07.abs() > 1e-3)]
    cap.sort_values(["pair", "group", "carrier", "country"]).to_csv(OUT / "RESOLUTION_CAPACITY.csv", index=False, lineterminator="\n")
    # ASEAN capacity totals by group (power in GW, energy in GWh, CO2 in Mt)
    tot = cap.groupby(["pair", "group", "carrier", "unit"], as_index=False)[["F", "s07"]].sum()
    summary["capacity_asean"] = {f"{r.pair}|{r.carrier}|{r.unit}": [r.F, r.s07] for r in tot.itertuples(index=False)}
    # ---------------------------------------------------------------- non-resolution differences (section 3.2)
    nr = dict(
        code_commit=dict(F=dict(package_commit=(PKG / "COMMIT").read_text().strip(), basis="package COMMIT; export records no commit (INTEGRITY_RUNS.json)"),
                         s07=dict(package_commit=(SPKG / "COMMIT").read_text().strip(), basis="screen_package_v3_dmax COMMIT")),
        build=dict(F1=receipt_inputs(PKG / "networks" / "integrated_BUILD_RECEIPT.json"), V1=receipt_inputs(SPKG / "networks" / "integrated_BUILD_RECEIPT.json"),
                   F2=receipt_inputs(PKG / "networks" / "no_new_xb_2920_3h_VARIANT_RECEIPT.json"), V2=receipt_inputs(SPKG / "networks" / "no_new_xb_365_24h_VARIANT_RECEIPT.json")),
        costs_table=dict(F=sha(PKG / "networks" / "integrated_costs_active_research.csv"), s07=sha(SPKG / "networks" / "integrated_costs_active_research.csv"),
                         F1_export=sha(F / "F1" / "costs_active_research.csv"), V1_export=sha(S07 / "V1" / "costs_active_research.csv")),
        registry=dict(s07_build_7aec953e=sha(Path(a.reg_s07)), F_build_a1ef782b=sha(Path(a.reg_f))),
        solve=dict(F1=solve_meta(F / "F1"), V1=solve_meta(S07 / "V1"), F2=solve_meta(F / "F2"), V2=solve_meta(S07 / "V2")),
        cost_share_split=dict(carriers_with_ratio=len(shares), carriers_ratio_spread_gt_0p02=sorted(c for c, s in shares.items() if s["max"] - s["min"] > 0.02)),
    )
    ra = pd.read_csv(a.reg_s07, keep_default_na=False, dtype=str).set_index("param_id"); rb = pd.read_csv(a.reg_f, keep_default_na=False, dtype=str).set_index("param_id")
    diff = []
    for i in ra.index.intersection(rb.index):
        cols = [c for c in ra.columns if c in rb.columns and ra.at[i, c] != rb.at[i, c]]
        if cols:
            diff.append(dict(param_id=i, columns=cols, value_equal=ra.at[i, "value"] == rb.at[i, "value"]))
    nr["registry"].update(rows_s07=len(ra), rows_F=len(rb), only_s07=sorted(set(ra.index) - set(rb.index)), only_F=sorted(set(rb.index) - set(ra.index)),
                          differing_rows=diff, any_value_differs=any(not d["value_equal"] for d in diff))
    (OUT / "evidence").mkdir(exist_ok=True)
    (OUT / "evidence" / "NONRES_DIFFS.json").write_text(json.dumps(nr, indent=1, ensure_ascii=False, default=str) + "\n", encoding="utf-8", newline="\n")
    (OUT / "evidence" / "RESOLUTION_SUMMARY.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False, default=str) + "\n", encoding="utf-8", newline="\n")
    (OUT / "evidence" / "CAPEX_FOM_SPLIT_RATIOS.json").write_text(json.dumps(shares, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    figure(dec, summary, OUT / "RESOLUTION_DECOMP.png", a.font)
    for k in ("F1-V1", "F2-V2"):
        s = summary[k]
        print(k, "dZ incl const %.4f bn" % (s["dZ_incl_constant"] / 1e9), "resid %.3f EUR" % s["ledger_vs_objective_residual"],
              "ship band", [round(x / 1e9, 3) for x in s["shipping_basis_band_eur"]], "other share %.4f" % s["unclassified_share"],
              {c: round(v / 1e9, 3) for c, v in s["category_delta"].items()})


def figure(dec: pd.DataFrame, summary: dict, path: Path, font: str | None):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    if font and Path(font).exists():
        font_manager.fontManager.addfont(font)
        matplotlib.rcParams["font.family"] = font_manager.FontProperties(fname=font).get_name()
    matplotlib.rcParams["axes.unicode_minus"] = False
    SURF, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
    C = {"F1−V1": "#2a78d6", "F2−V2": "#eb6834"}
    g = dec[dec.level == "技术组"].pivot_table(index="group", columns="pair", values="delta_eur", aggfunc="sum").fillna(0.0) / 1e9
    order = g.abs().max(axis=1).sort_values(ascending=False).index
    top = list(order[:14]); rest = [x for x in order if x not in top]
    if rest:
        g.loc["其余各组合计"] = g.loc[rest].sum(); top.append("其余各组合计")
    g = g.loc[top[::-1]]
    fig, axes = plt.subplots(1, 2, figsize=(14, 7.2), gridspec_kw=dict(width_ratios=[1.25, 1]), facecolor=SURF)
    ax = axes[0]; ax.set_facecolor(SURF)
    y = range(len(g)); h = 0.38
    for j, p in enumerate(["F1−V1", "F2−V2"]):
        ax.barh([i + (h / 2 if j == 0 else -h / 2) for i in y], g[p].values, height=h - 0.04, color=C[p], label={"F1−V1": "F1 − V1（一体化）", "F2−V2": "F2 − V2（no_new_xb）"}[p])
    ax.set_yticks(list(y)); ax.set_yticklabels(g.index, color=INK, fontsize=10)
    ax.axvline(0, color=INK2, lw=1)
    ax.grid(axis="x", color=GRID, lw=0.8); ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=INK2)
    ax.set_xlabel("年化成本差（bn EUR，2920×3h 减 365 个日均时段）", color=INK2)
    s1, s2 = summary["F1-V1"], summary["F2-V2"]
    ax.set_title("按技术组的成本差（账本，含常数项）\nF1 − V1 = %+.2f bn，F2 − V2 = %+.2f bn" % (s1["dZ_incl_constant"] / 1e9, s2["dZ_incl_constant"] / 1e9),
                 color=INK, fontsize=11, loc="left")
    ax.legend(frameon=False, loc="lower right", labelcolor=INK)
    # right: key power capacities, F1 vs V1 (GW)
    ax = axes[1]; ax.set_facecolor(SURF)
    cap = summary["capacity_asean"]
    items = [("地面光伏", "solar"), ("屋顶光伏", "solar rooftop"), ("陆上风电", "onwind"), ("固定电池放电", "battery discharger"), ("户用电池放电", "home battery discharger"),
             ("电解槽", "H2 Electrolysis"), ("SMR CC", "SMR CC"), ("新水电", "hydro"), ("地热（新建）", "geothermal"), ("DC 互联", "DC"), ("H2 管道", "H2 pipeline")]
    vals = [(lab, cap.get(f"F1−V1|{car}|MW", [0, 0])) for lab, car in items]
    labels = [v[0] for v in vals][::-1]; f_ = [v[1][0] / 1e3 for v in vals][::-1]; s_ = [v[1][1] / 1e3 for v in vals][::-1]
    yy = range(len(labels))
    ax.barh([i + h / 2 for i in yy], f_, height=h - 0.04, color="#2a78d6", label="F1（2920×3h）")
    ax.barh([i - h / 2 for i in yy], s_, height=h - 0.04, color="#8a8984", label="V1（365 个日均时段）")
    ax.set_xscale("symlog", linthresh=10)
    ax.set_yticks(list(yy)); ax.set_yticklabels(labels, color=INK, fontsize=10)
    ax.grid(axis="x", color=GRID, lw=0.8); ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(GRID); ax.tick_params(colors=INK2)
    ax.set_xlabel("东盟合计容量（GW，对称对数刻度；0–10 GW 段为线性）", color=INK2)
    ax.set_title("一体化的关键容量：F1 对 V1", color=INK, fontsize=11, loc="left")
    for i, (a_, b_) in enumerate(zip(f_, s_)):
        ax.text(max(a_, 0.01) * 1.08 + 0.3, i + h / 2, f"{a_:,.1f}", va="center", fontsize=8, color=INK2)
        ax.text(max(b_, 0.01) * 1.08 + 0.3, i - h / 2, f"{b_:,.1f}", va="center", fontsize=8, color=INK2)
    ax.legend(frameon=False, loc="lower right", labelcolor=INK)
    fig.text(0.01, 0.01, "来源：v3.1 HPC 中间导出（F1、F2）与补充 07 云端导出（V1、V2）的 COUNTRY_COST_LEDGER_DETAIL.csv、CAPACITY_BY_TECH_COUNTRY.json；"
             "成本差含分辨率与船运口径（S-A / S-B）两种来源，后者 F1 约 %.2f–%.2f、F2 约 %.2f–%.2f bn（INFERENCE）。" % tuple(
                 x / 1e9 for k in ("F1-V1", "F2-V2") for x in summary[k]["shipping_basis_band_eur"]), fontsize=8, color=INK2)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(path, dpi=150, facecolor=SURF)


if __name__ == "__main__":
    main()
