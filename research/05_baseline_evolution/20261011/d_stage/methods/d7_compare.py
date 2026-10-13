"""D-7（只读，仅 DR1）：同一方案 A 下 2920×3h 与 C09 日模型（365×24h）结果对比。不求解、不改变任何结果。

成本口径：科学成本（网络中的原 capital_cost / marginal_cost，不含 V3 微扰）。
  资本 = Σ 扩建资产 capital_cost × 最优容量；运行 = Σ_t w_t × marginal_cost × 出力（Generator p、Link p0、Store p、StorageUnit p_dispatch）；
  固定 = 已知现有资产年度 FOM（一次）。三者之和与后处理 DUAL_COST_LEDGER 的 original_scientific_objective_known_scope 对账。
Usage: python d7_compare.py <daily solved nc> <daily postprocess dir> <2920 solved nc> <2920 postprocess dir> <out json>
"""
import sys, json, logging
from pathlib import Path
import numpy as np, pandas as pd, pypsa
logging.disable(logging.WARNING)
DN, DP, HN, HP, OUT = map(Path, sys.argv[1:6])
VRE = ['solar', 'solar rooftop', 'onwind', 'offwind-ac', 'offwind-dc', 'ror existing']


def summarize(nc, post):
    n = pypsa.Network(nc); w = n.snapshot_weightings.objective; country = n.buses.country
    out = {'snapshots': len(n.snapshots), 'hours_per_snapshot': float(w.iloc[0]), 'total_hours': float(w.sum())}
    cap = {}
    for c, nom in [('Generator', 'p_nom'), ('Link', 'p_nom'), ('Line', 's_nom'), ('StorageUnit', 'p_nom'), ('Store', 'e_nom')]:
        df = n.df(c); ext = df[df[nom + '_extendable']]; cap[c] = float((ext.capital_cost * ext[nom + '_opt']).sum())
    op = {'Generator': float((n.generators_t.p.mul(w, axis=0) * n.get_switchable_as_dense('Generator', 'marginal_cost')).sum().sum()),
          'Link': float((n.links_t.p0.mul(w, axis=0) * n.get_switchable_as_dense('Link', 'marginal_cost')).sum().sum()),
          'Store': float((n.stores_t.p.mul(w, axis=0) * n.get_switchable_as_dense('Store', 'marginal_cost')).sum().sum()),
          'StorageUnit': float((n.storage_units_t.p_dispatch.mul(w, axis=0) * n.get_switchable_as_dense('StorageUnit', 'marginal_cost')).sum().sum())}
    fom = float(n.meta.get('existing_annual_fixed_om_eur', 0.0)); led = json.loads((post / 'DUAL_COST_LEDGER.json').read_text())
    total = sum(cap.values()) + sum(op.values()) + fom
    out['cost_EUR'] = {'capital_by_component': cap, 'capital': sum(cap.values()), 'operating_by_component': op, 'operating': sum(op.values()), 'known_fixed_FOM_once': fom,
                       'total_recomputed': total, 'ledger_original_scientific_known_scope': led['original_scientific_objective_known_scope'],
                       'reconciliation_diff': total - led['original_scientific_objective_known_scope'], 'V3_adapted_objective': led['adapted_objective']}
    g = n.generators.assign(country=n.generators.bus.map(country))
    out['generator_capacity_MW'] = {f'{k[0]}|{k[1]}': float(v) for k, v in g.groupby(['carrier', 'country']).p_nom_opt.sum().items() if v > 0}
    out['generator_capacity_by_carrier_MW'] = {k: float(v) for k, v in g.groupby('carrier').p_nom_opt.sum().items()}
    s = n.stores.assign(country=n.stores.bus.map(country)); keep = s.carrier.isin(['battery', 'home battery', 'H2'])
    out['store_energy_MWh'] = {f'{k[0]}|{k[1]}': float(v) for k, v in s[keep].groupby(['carrier', 'country']).e_nom_opt.sum().items()}
    out['store_energy_by_carrier_MWh'] = {k: float(v) for k, v in s[keep].groupby('carrier').e_nom_opt.sum().items()}
    su = n.storage_units.assign(country=n.storage_units.bus.map(country))
    out['storage_unit_power_MW'] = {f'{k[0]}|{k[1]}': float(v) for k, v in su.groupby(['carrier', 'country']).p_nom_opt.sum().items()}
    L = n.links.assign(c0=n.links.bus0.map(country), c1=n.links.bus1.map(country))
    out['storage_link_power_MW'] = {k: float(v) for k, v in L[L.carrier.isin(['battery charger', 'battery discharger', 'home battery charger', 'home battery discharger', 'H2 Electrolysis', 'H2 Fuel Cell'])].groupby('carrier').p_nom_opt.sum().items()}
    li = n.lines.assign(c0=n.lines.bus0.map(country), c1=n.lines.bus1.map(country)); xb = li[li.c0 != li.c1]
    out['cross_border_AC_MW'] = {f'{a}-{b}' if a < b else f'{b}-{a}': 0.0 for a, b in zip(xb.c0, xb.c1)}
    for (a, b), v in zip(zip(xb.c0, xb.c1), xb.s_nom_opt): out['cross_border_AC_MW'][f'{a}-{b}' if a < b else f'{b}-{a}'] += float(v)
    xl = L[(L.c0 != L.c1) & L.carrier.isin(['DC', 'B2B'])]; out['cross_border_DC_B2B_MW'] = {}
    for (a, b), v in zip(zip(xl.c0, xl.c1), xl.p_nom_opt): k = f'{a}-{b}' if a < b else f'{b}-{a}'; out['cross_border_DC_B2B_MW'][k] = out['cross_border_DC_B2B_MW'].get(k, 0.0) + float(v)
    out['cross_border_total_MW'] = sum(out['cross_border_AC_MW'].values()) + sum(out['cross_border_DC_B2B_MW'].values())
    st = n.stores_t.p; thr = {}
    for car in ['battery', 'home battery', 'H2']:
        cols = n.stores.index[n.stores.carrier == car]; p = st[cols].mul(w, axis=0)
        thr[car] = {'discharge_MWh': float(p.clip(lower=0).sum().sum()), 'charge_MWh': float((-p.clip(upper=0)).sum().sum())}
    for car in su.carrier.unique():
        cols = su.index[su.carrier == car]
        thr['StorageUnit|' + car] = {'dispatch_MWh': float(n.storage_units_t.p_dispatch[cols].mul(w, axis=0).sum().sum()), 'store_MWh': float(n.storage_units_t.p_store[cols].mul(w, axis=0).sum().sum()),
                                     'spill_MWh': float(n.storage_units_t.spill[cols].mul(w, axis=0).sum().sum()) if 'spill' in n.storage_units_t and len(n.storage_units_t.spill.columns) else 0.0}
    out['storage_throughput'] = thr
    pmax = n.get_switchable_as_dense('Generator', 'p_max_pu'); curt = {}
    for car in VRE:
        cols = n.generators.index[n.generators.carrier == car]
        if not len(cols): continue
        avail = pmax[cols].mul(n.generators.p_nom_opt[cols], axis=1).mul(w, axis=0).sum().sum(); gen = n.generators_t.p[cols].mul(w, axis=0).sum().sum()
        curt[car] = {'available_MWh': float(avail), 'generated_MWh': float(gen), 'curtailed_MWh': float(avail - gen), 'curtailment_share': float((avail - gen) / avail) if avail else None}
    out['vre_curtailment'] = curt
    out['generation_by_carrier_MWh'] = {k: float(v) for k, v in n.generators_t.p.mul(w, axis=0).sum().groupby(n.generators.carrier).sum().items()}
    return out


def diff(a, b):
    if isinstance(a, dict): return {k: diff(a.get(k), b.get(k)) for k in sorted(set(a) | set(b)) if isinstance(a.get(k, b.get(k)), (dict, int, float))}
    a = a or 0.0; b = b or 0.0; return {'daily': a, 'h3': b, 'abs': b - a, 'rel': (b - a) / abs(a) if a else None}


d = summarize(DN, DP); h = summarize(HN, HP)
res = {'qualification': 'READ_ONLY_POSTPROCESS_COMPARISON_NO_SOLVE', 'daily_365': d, 'h3_2920': h,
       'difference_h3_minus_daily': {k: diff(d[k], h[k]) for k in ('cost_EUR', 'generator_capacity_by_carrier_MW', 'store_energy_by_carrier_MWh', 'storage_link_power_MW',
                                                                  'storage_unit_power_MW', 'cross_border_AC_MW', 'cross_border_DC_B2B_MW', 'storage_throughput', 'vre_curtailment', 'generation_by_carrier_MWh', 'generator_capacity_MW', 'store_energy_MWh')},
       'cross_border_total_MW': diff(d['cross_border_total_MW'], h['cross_border_total_MW'])}
OUT.write_text(json.dumps(res, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
print(json.dumps({'cost': res['difference_h3_minus_daily']['cost_EUR'], 'gen': res['difference_h3_minus_daily']['generator_capacity_by_carrier_MW'],
                  'store': res['difference_h3_minus_daily']['store_energy_by_carrier_MWh'], 'xb': res['cross_border_total_MW'], 'curt': res['difference_h3_minus_daily']['vre_curtailment']}, indent=1)[:6000])
