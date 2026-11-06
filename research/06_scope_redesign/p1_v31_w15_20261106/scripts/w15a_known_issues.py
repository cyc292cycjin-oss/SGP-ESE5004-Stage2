"""V31 W15 stage A, section 4 (decision 212): known-issue checks from the unsolved input networks, the registry and the interim exports
(read only; no solver, no solved network).

  python -I w15a_known_issues.py --pkg <hpc_package_v3_1> --exp <interim export> --s07 <supplement 07 export> --registry <DATA_REGISTRY.csv @a1ef782b>
         --out <work/p1_v31_w15_20261106>

Writes ZERO_COST_SCAN.csv, evidence/ZERO_COST_SUMMARY.json, evidence/OIL_PALM_TRUNK.json, evidence/BUNKER_CHECK.json.
"""
import argparse, csv, json, logging, warnings
from pathlib import Path

warnings.filterwarnings("ignore"); logging.disable(logging.WARNING)
import pandas as pd
import pypsa

PROXY = 6.26706128163   # registry value of the unsourced residues (cassava / coconut / other crop residues), instruction 4.1
NETS = {"F1": "integrated_2920_3h_unsolved.nc", "F2": "no_new_xb_2920_3h_unsolved.nc", "F4": "no_new_xb_ev05_2920_3h_unsolved.nc"}
ACCOUNTING = {   # carrier -> (class, reason, code reference) for design zeros
    "oil final-energy accounting": ("设计为 0：计量 / 记账链", "终端用能计量，燃料成本记在供应侧", "s3_layers / s2_layers 记账链"),
    "gas final-energy accounting": ("设计为 0：计量 / 记账链", "终端用能计量，燃料成本记在供应侧", "s3_layers / s2_layers 记账链"),
    "coal final-energy accounting": ("设计为 0：计量 / 记账链", "终端用能计量，燃料成本记在供应侧", "s3_layers / s2_layers 记账链"),
    "biomass final-energy accounting": ("设计为 0：计量 / 记账链", "终端用能计量，原料成本记在生物质池", "s2_layers 记账链"),
    "oil feedstock": ("设计为 0：计量 / 记账链", "原料用途计量", "s3_layers 记账链"), "gas feedstock": ("设计为 0：计量 / 记账链", "原料用途计量", "s3_layers 记账链"),
    "coal feedstock": ("设计为 0：计量 / 记账链", "原料用途计量", "s3_layers 记账链"),
    "oil pool": ("设计为 0：计量 / 记账链", "国家液体母线与节点之间的汇集链路；国内配送加价按决策为 0（liquid_domestic_distribution_markup）", "v3_layers"),
    "industry methanol": ("设计为 0：计量 / 记账链", "工业甲醇终端用量计量", "s2_layers"), "shipping methanol": ("设计为 0：计量 / 记账链", "船用甲醇终端用量计量", "s4c_layers / v3_layers"),
    "process emissions": ("设计为 0：排放记账", "工艺排放来源与去向的记账（外生排放量）", "s2_layers"),
    "waste incineration": ("设计为 0：排放记账", "'plastic waste burning'：塑料废弃物燃烧排放到大气的记账链（role WASTE_BURNING_RELEASE）", "s2_layers.py:1061"),
    "plastic waste": ("设计为 0：排放记账", "外生塑料废弃物来源（固定容量）", "s2_layers"),
    "gas production delivery": ("设计为 0：成本在别处", "气田交付链路；生产成本记在 'gas production' 发电机", "s3_layers"),
    "CO2 sequestration": ("设计为 0：成本在别处", "注入链路；封存成本记在 'co2 sequestered' Store", "s2_layers CO2 层"),
    "CO2 export extra-ASEAN": ("设计为 0：成本在别处", "区外封存出口链路；成本记在 'co2 sequestered extra-ASEAN' Store（统一 54.698 EUR/t）", "s4c_layers 区外封存"),
    "battery discharger": ("设计为 0：成本在别处", "PyPSA 约定：逆变器成本记在充电侧，放电侧为 0", "PyPSA-Eur 惯例"),
    "home battery discharger": ("设计为 0：成本在别处", "PyPSA 约定：逆变器成本记在充电侧，放电侧为 0", "PyPSA-Eur 惯例"),
    "cooking LPG": ("设计为 0：范围约定", "终端炉具设备成本不在模型范围内（固定需求的终端转换）", "s2_layers.py:960-962"),
    "cooking gas": ("设计为 0：范围约定", "终端炉具设备成本不在模型范围内（固定需求的终端转换）", "s2_layers.py:960-962"),
    "cooking electric": ("设计为 0：范围约定", "终端炉具设备成本不在模型范围内（固定需求的终端转换）", "s2_layers.py:960-962"),
    "co2 atmosphere": ("设计为 0：排放账户", "国家大气 CO2 账户 Store", "s2_layers / s4c_layers"),
    "co2 bunkers": ("设计为 0：排放账户", "国际燃料舱 CO2 账户 Store（第 195 项：计量流量逐时段为 0）", "s4c_layers"),
}
FIXED = {   # non-extendable carriers whose cost is outside the LP by design
    "ror existing": "存量资产：固定运维在常数项，边际成本为 0", "solar existing": "存量资产：固定运维在常数项，边际成本为 0",
    "hydro existing": "存量资产：固定运维在常数项，边际成本为 0", "PHS existing": "存量资产：固定运维在常数项，边际成本为 0",
    "BEV charger": "外生车队：充电桩容量固定（第 182、186 项），车辆成本不在范围内", "EV battery": "外生车队：电池容量固定，车辆成本不在范围内",
    "dedicated plant line": "老挝 IPP 专线（第 172、173 项）：合同容量固定，存量", "dedicated plant source": "老挝 IPP 专线的电源端：合同容量固定，存量",
    "B2B": "存量背靠背换流站，容量固定（非扩展，capital_cost 不进目标）", "DC": "存量直流，容量固定", "gas pipeline": "存量气管，容量固定",
}


def zero_cost(n: pypsa.Network) -> pd.DataFrame:
    rows = []
    for comp, df, dft, ext, nom in (("Generator", n.generators, n.generators_t, "p_nom_extendable", "p_nom"), ("Link", n.links, n.links_t, "p_nom_extendable", "p_nom"),
                                    ("Store", n.stores, n.stores_t, "e_nom_extendable", "e_nom"), ("StorageUnit", n.storage_units, n.storage_units_t, "p_nom_extendable", "p_nom")):
        mct = dft.marginal_cost if "marginal_cost" in dft else pd.DataFrame()
        tv = set(mct.columns[(mct != 0).any()]) if len(mct.columns) else set()
        mcs = df["marginal_cost_storage"] if "marginal_cost_storage" in df else pd.Series(0.0, index=df.index)
        z = df[(df.marginal_cost == 0) & ~df.index.isin(tv) & ((df.capital_cost == 0) | ~df[ext]) & (mcs == 0)]
        for name, r in z.iterrows():
            rows.append(dict(component=comp, name=name, carrier=r.carrier, country=str(r.get("country", "") or ""), extendable=bool(r[ext]), nom=float(r[nom]),
                             capital_cost=float(r.capital_cost), reversed=str(r.get("reversed", "")) == "True", kind=str(r.get("gas_pipeline_kind", "") or ""),
                             length=float(r.get("length", 0.0) or 0.0) if comp == "Link" else None))
    return pd.DataFrame(rows)


def classify(r, reg: pd.DataFrame) -> dict:
    out = dict(registry_param="", registry_status="", registry_value="", registry_source_present="", classification="待核", reason="", code_ref="")
    if r.component == "Store" and " biomass " in r["name"]:
        cc, cat = r["name"].split(" biomass ", 1); pid = f"biomass_cost_{cc}_{cat}"
        out.update(registry_param=pid, code_ref="scripts_project/s2_layers.py:467（成本列为空即 marginal_cost = 0）")
        if pid in reg.index:
            x = reg.loc[pid]; out.update(registry_status=x.status, registry_value=x.value, registry_source_present=bool(x.source.strip()))
            if x.status == "DATA_PENDING":
                out.update(classification="缺数被当作 0", reason="注册表成本为 DATA_PENDING、来源为空；生物质成本表该列为空，代码按 0 建 Store")
            elif x.value.strip() in ("0", "0.0"):
                out.update(classification="登记为 0（有来源）", reason=f"注册表 {x.status}、值 0；来源：{x.source.strip()[:80]}")
        else:
            out.update(classification="待核", reason="注册表无对应成本行")
        return pd.Series(out)
    if r.reversed:
        out.update(classification="设计为 0：双向链路的反向孪生", reason="reversed=True；成本在正向链路上，两向容量由 research_lossy_bidirectional_sync 绑定", code_ref="s2_layers / s3_layers 双向链路")
        return pd.Series(out)
    if r.carrier in ACCOUNTING:
        c, why, ref = ACCOUNTING[r.carrier]; out.update(classification=c, reason=why, code_ref=ref)
        return pd.Series(out)
    if not r.extendable and r.carrier in FIXED:
        out.update(classification="设计为 0：存量或外生固定容量", reason=FIXED[r.carrier], code_ref="")
        return pd.Series(out)
    out.update(reason="未匹配到设计规则")
    return pd.Series(out)


def b3_used(exp_dir: Path) -> dict:
    p = exp_dir / "V5_GATES.json"
    if not p.exists():
        return {}
    G = json.loads(p.read_text(encoding="utf-8"))
    return {r["store"]: dict(potential_mwh=r["potential_mwh"], used_mwh=r["used_mwh"], share_used=r["share_used"]) for r in G["B3"]["rows"]}


def main():
    ap = argparse.ArgumentParser()
    for k in ("pkg", "exp", "s07", "registry", "out"):
        ap.add_argument("--" + k, required=True)
    a = ap.parse_args()
    PKG, EXP, S07, OUT = Path(a.pkg), Path(a.exp), Path(a.s07), Path(a.out)
    reg = pd.read_csv(a.registry, keep_default_na=False, dtype=str).set_index("param_id")
    frames, nets = [], {}
    for rid, f in NETS.items():
        n = pypsa.Network(PKG / "networks" / f); nets[rid] = n
        z = zero_cost(n); z["run"] = rid; frames.append(z)
    Z = pd.concat(frames)
    key = ["component", "name"]
    U = Z.drop_duplicates(key).drop(columns="run").set_index(key)
    for rid in NETS:
        U[f"in_{rid}"] = U.index.isin(Z[Z.run == rid].set_index(key).index)
    U = U.reset_index()
    U = pd.concat([U, U.apply(lambda r: classify(r, reg), axis=1)], axis=1)
    used = {rid: b3_used(EXP / rid) for rid in NETS}
    used_s07 = {rid: b3_used(S07 / rid) for rid in ("V1", "V2")}
    for rid in NETS:
        U[f"used_mwh_{rid}"] = [used[rid].get(nm, {}).get("used_mwh", "") if c == "Store" else "" for c, nm in zip(U.component, U.name)]
    U["output_note"] = ["阶段 A 可读：B3 生物质池放出量" if (c == "Store" and " biomass " in nm) else "阶段 B 用已解网络补放出 / 出力"
                        for c, nm in zip(U.component, U.name)]
    cols = ["classification", "component", "carrier", "name", "country", "extendable", "nom", "capital_cost", "reversed", "registry_param", "registry_status",
            "registry_value", "registry_source_present", "reason", "code_ref", "in_F1", "in_F2", "in_F4", "used_mwh_F1", "used_mwh_F2", "used_mwh_F4", "output_note"]
    order = {"缺数被当作 0": 0, "待核": 1, "登记为 0（有来源）": 2}
    U["_o"] = U.classification.map(lambda c: order.get(c, 3))
    U.sort_values(["_o", "classification", "component", "carrier", "name"])[cols].to_csv(OUT / "ZERO_COST_SCAN.csv", index=False, lineterminator="\n")
    summ = U.groupby(["classification", "component", "carrier"]).size().rename("count").reset_index()
    # existing gas pipelines read with an empty length (s3_layers.py:161) -> zero capital cost: check
    gp = []
    for rid, n in nets.items():
        L = n.links
        if "gas_pipeline_kind" in L:
            x = L[(L.gas_pipeline_kind == "existing_2025")]
            gp.append(dict(run=rid, existing=len(x), length_zero=int((x.length == 0).sum()), extendable=int(x.p_nom_extendable.sum()),
                           names_length_zero=list(x.index[x.length == 0])))
    (OUT / "evidence").mkdir(exist_ok=True)
    (OUT / "evidence" / "ZERO_COST_SUMMARY.json").write_text(json.dumps(dict(
        definition="zero-cost component: marginal_cost 0 (static, no non-zero time series), marginal_cost_storage 0, and capital_cost 0 or not extendable; unsolved input networks of the v3.1 package",
        by_classification=U.classification.value_counts().to_dict(), by_class_component_carrier=summ.to_dict("records"),
        code_empty_to_zero_sites=[dict(site="scripts_project/s2_layers.py:467", what="biomass cost empty -> marginal_cost 0", affected="5 oil_palm_trunk Stores (ID, KH, MY, PH, TH)"),
                                  dict(site="scripts_project/s2_layers.py:463", what="biomass potential empty -> 0 -> no Store (skipped)", affected="no Store built; DATA_PENDING / ZERO_BY_DECISION rows skipped before"),
                                  dict(site="scripts_project/s3_layers.py:161", what="existing gas pipeline length empty -> 0 (capital cost of a fixed existing link)", affected=gp),
                                  dict(site="scripts_project/s2b_feedstock.py:144", what="MSW incineration share not reported -> 0, registered as SOURCE_ZERO (a quantity, not a cost)", affected="registry rows waste_incineration_share_*")],
        grep="git grep -nE '!= \"\" else 0(\\.0)?' d3b9a3bc -- scripts_project (cost / price / length / share fields)"),
        indent=1, ensure_ascii=False, default=str) + "\n", encoding="utf-8", newline="\n")
    # ---------------------------------------------------------------- oil palm trunk (4.1)
    opt = {}
    for cc in ("ID", "KH", "MY", "PH", "TH"):
        st = f"{cc} biomass oil_palm_trunk"; n = nets["F1"]
        row = dict(store=st, marginal_cost_in_network=float(n.stores.at[st, "marginal_cost"]), e_nom=float(n.stores.at[st, "e_nom"]), e_initial=float(n.stores.at[st, "e_initial"]),
                   registry_cost=dict(status=reg.at[f"biomass_cost_{cc}_oil_palm_trunk", "status"], value=reg.at[f"biomass_cost_{cc}_oil_palm_trunk", "value"]),
                   registry_potential=dict(status=reg.at[f"biomass_potential_{cc}_oil_palm_trunk", "status"], value=float(reg.at[f"biomass_potential_{cc}_oil_palm_trunk", "value"])),
                   proxy_eur_per_mwh=PROXY)
        for rid in NETS:
            u = used[rid].get(st)
            if u:
                row[rid] = dict(used_mwh=u["used_mwh"], share_used=u["share_used"], first_order_dZ_eur=u["used_mwh"] * PROXY)
        for rid in ("V1", "V2"):
            u = used_s07[rid].get(st)
            if u:
                row["s07_" + rid] = dict(used_mwh=u["used_mwh"], share_used=u["share_used"], first_order_dZ_eur=u["used_mwh"] * PROXY)
        opt[cc] = row
    (OUT / "evidence" / "OIL_PALM_TRUNK.json").write_text(json.dumps(dict(
        note=("first-order dZ = used energy x proxy (envelope; for a cost-type parameter it is an upper bound of the true dZ, decision 212 (b)); "
              "allocated to the country of the Store (INFERENCE); proxy = registry value of the unsourced residues"),
        stores=opt), indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    # ---------------------------------------------------------------- bunker (4.3)
    bk = {}
    for rid in NETS:
        d = EXP / rid; B = json.loads((d / "BUNKER_ACCOUNT.json").read_text(encoding="utf-8"))
        S = json.loads((d / "SOLVE_RECEIPT.json").read_text(encoding="utf-8"))
        with (d / "NODAL_PRICES.csv").open(encoding="utf-8") as fh:
            rd = csv.reader(fh); head = next(rd); prow = next((x for x in rd if x and x[0] == "co2 bunkers ASEAN"), None)
        n = nets[rid]; w = n.snapshot_weightings.stores
        bk[rid] = dict(passed=B["passed"], final_level_tco2=B["final_level_tco2"], gross_co2_flow_t=B["gross_co2_flow_t"], tolerance_t=B["tolerance_t"],
                       ports=len(B["port_tonnes"]), ports_nonzero=sum(1 for v in B["port_tonnes"].values() if v != 0.0),
                       max_abs_port_tonnes=max(abs(v) for v in B["port_tonnes"].values()), supply_rows=len(B["supply_mwh"]),
                       supply_total_mwh=sum(B["supply_mwh"].values()), min_weight_h=float(w.min()), snapshots=len(w),
                       lp_bunker_rows=S["lp"]["num_row"], constraint_in_lp="research_bunker_co2_limit" in S["lp"].get("research_constraints", []),
                       gates_B1_BUNKERS=S["gates"].get("B1_BUNKERS"),
                       nodal_price_row=dict(present=prow is not None, note_present=bool(prow and "note" in head and prow[head.index("note")]),
                                            values_nan=bool(prow) and all(v in ("", "nan", "NaN") for k, v in zip(head, prow) if k not in ("bus", "node", "carrier", "country", "note")),
                                            value_columns=sum(1 for k in head if k not in ("bus", "node", "carrier", "country", "note"))))
    (OUT / "evidence" / "BUNKER_CHECK.json").write_text(json.dumps(dict(
        logic=("gross_co2_flow_t = sum over the 82 ports of sum_t w_t |flow_t| (s4c_layers.bunker_gross_co2_flow); with every w_t >= 3 h > 0, "
               "gross = 0.0 exactly implies every metering flow is 0 in every snapshot (EXACT)"), runs=bk), indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(U.classification.value_counts().to_string())
    print("待核:", U[U.classification == "待核"][["component", "carrier", "name"]].head(20).to_string())
    for cc, r in opt.items():
        print(cc, {k: (round(v["used_mwh"] / 1e6, 3), round(v["first_order_dZ_eur"] / 1e9, 4)) for k, v in r.items() if isinstance(v, dict) and "used_mwh" in v})
    print({k: (v["gross_co2_flow_t"], v["ports_nonzero"], v["final_level_tco2"], v["nodal_price_row"]) for k, v in bk.items()})
    print("gas pipelines existing:", gp)


if __name__ == "__main__":
    main()
