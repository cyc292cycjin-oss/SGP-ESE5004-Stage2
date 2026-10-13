"""D-7b 只读补表：电力系统口径（只读后处理，未求解；不改任何模型、结果或回执）。

输入与 D-7 相同：C09 日模型与 D-5 2920 的已求解 NetCDF 及其后处理目录。
符号约定（PyPSA）：Link 端口 k 的 p_k 为从母线 k 取出的功率，注入母线 k 的功率为 −p_k；Line 同理（p0、p1）。
电力母线：buses.carrier ∈ {AC, DC, low voltage}（按实际数据判定，脚本打印全部母线 carrier 供核对）。
Usage: python d7b_power_tables.py <daily nc> <daily postprocess> <2920 nc> <2920 postprocess> <out json>
"""
import sys, json, hashlib, logging, collections
from pathlib import Path
import numpy as np, pandas as pd, pypsa
logging.disable(logging.WARNING)
DN, DP, HN, HP, OUT = map(Path, sys.argv[1:6])
ELEC = {'AC', 'DC', 'low voltage'}; FOSSIL = {'coal', 'gas', 'oil', 'lignite'}; TWH = 1e6


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 23), b''): h.update(b)
    return h.hexdigest()


def tables(nc, post):
    n = pypsa.Network(nc); w = n.snapshot_weightings.objective; bc = n.buses.carrier; cty = n.buses.country.fillna('').replace('', 'NONE')
    elec = bc.isin(ELEC); out = {'snapshots': len(n.snapshots), 'bus_carriers': bc.value_counts().to_dict(), 'electric_bus_carriers': sorted(ELEC)}
    # 1. Generator attachment
    g = n.generators.assign(bc=n.generators.bus.map(bc))
    gen_energy = n.generators_t.p.mul(w, axis=0).sum()
    out['1_generator_attachment'] = [{'carrier': c, 'bus_carrier': b, 'count': int(len(df)), 'p_nom_opt_MW': float(df.p_nom_opt.sum()),
                                      'annual_output_TWh': float(gen_energy[df.index].sum() / TWH)} for (c, b), df in g.groupby(['carrier', 'bc'])]
    # 2. power-producing links (any port k>=1 on an electric bus, bus0 not electric) and all links touching electric buses
    L = n.links; ports = sorted(int(c[3:]) for c in L.columns if c.startswith('bus') and c[3:].isdigit())
    P = {k: (n.links_t['p%d' % k] if ('p%d' % k) in n.links_t and len(n.links_t['p%d' % k].columns) else pd.DataFrame(0.0, index=n.snapshots, columns=L.index)).reindex(columns=L.index, fill_value=0.0) for k in ports}
    E = {k: (L['efficiency'] if k == 1 else L.get('efficiency%d' % k, pd.Series(0.0, index=L.index))) for k in ports if k >= 1}
    portc = {k: L['bus%d' % k].map(bc).fillna('') for k in ports}
    gen_links = L.index[(~portc[0].isin(ELEC)) & np.any([portc[k].isin(ELEC) for k in ports if k >= 1], axis=0)]
    rows = []
    for car, idx in L.loc[gen_links].groupby('carrier').groups.items():
        idx = list(idx); inj = 0.0
        for k in ports:
            if k == 0: continue
            mask = portc[k][idx].isin(ELEC); inj += float((-P[k][idx]).mul(w, axis=0).sum()[mask].sum())
        einp = float(P[0][idx].mul(w, axis=0).sum().sum()); capin = float(L.loc[idx, 'p_nom_opt'].sum())
        e_el = sum(float((L.loc[idx, 'p_nom_opt'] * E[k][idx]).where(portc[k][idx].isin(ELEC), 0.0).sum()) for k in ports if k >= 1)
        rows.append({'carrier': car, 'bus0_carrier': sorted(portc[0][idx].unique()), 'count': len(idx), 'p_nom_opt_input_MW': capin, 'electric_capacity_MWe': e_el,
                     'annual_input_TWh': einp / TWH, 'annual_electricity_TWh': float(inj) / TWH, 'capacity_factor': (float(inj) / (e_el * w.sum())) if e_el > 0 else None})
    out['2_power_generating_links'] = sorted(rows, key=lambda r: -r['annual_electricity_TWh'])
    # 3. country electricity balance over electric buses
    bal = collections.defaultdict(lambda: collections.defaultdict(float))
    def add(country, key, val): bal[country][key] += float(val)
    for j, gg in n.generators.iterrows():
        if bc[gg.bus] in ELEC: add(cty[gg.bus], 'gen|' + gg.carrier, gen_energy[j] / TWH)
    su = n.storage_units
    for j, s in su.iterrows():
        if bc[s.bus] in ELEC: add(cty[s.bus], 'storage_unit_net|' + s.carrier, float((n.storage_units_t.p[j] * w).sum()) / TWH)
    st = n.stores
    for j, s in st.iterrows():
        if bc[s.bus] in ELEC: add(cty[s.bus], 'store_net|' + s.carrier, float((n.stores_t.p[j] * w).sum()) / TWH)
    ld = n.loads_t.p if len(n.loads_t.p.columns) else n.get_switchable_as_dense('Load', 'p_set')
    for j, l in n.loads.iterrows():
        if bc[l.bus] in ELEC: add(cty[l.bus], 'load', -float((ld[j] * w).sum()) / TWH)
    for k in ports:
        en = (-P[k]).mul(w, axis=0).sum() / TWH
        for j in L.index:
            b = L.at[j, 'bus%d' % k]
            if not b or b not in bc.index or bc[b] not in ELEC: continue
            c0 = cty[L.at[j, 'bus0']] if L.at[j, 'bus0'] in cty.index else 'NONE'; car = L.at[j, 'carrier']
            elec_ports = [q for q in ports if L.at[j, 'bus%d' % q] in bc.index and bc[L.at[j, 'bus%d' % q]] in ELEC]
            other_elec_country = {cty[L.at[j, 'bus%d' % q]] for q in elec_ports}
            if len(other_elec_country) > 1: key = 'cross_border_link|' + car
            elif 0 in elec_ports and len(elec_ports) > 1: key = 'electric_to_electric_link|' + car
            elif k == 0: key = 'link_consumption|' + car
            else: key = 'link_output|' + car
            add(cty[b], key, en[j])
    lf = {0: n.lines_t.p0, 1: n.lines_t.p1}
    for j, ln in n.lines.iterrows():
        c0, c1 = cty[ln.bus0], cty[ln.bus1]; key = 'cross_border_line' if c0 != c1 else 'domestic_line'
        add(c0, key, -float((lf[0][j] * w).sum()) / TWH); add(c1, key, -float((lf[1][j] * w).sum()) / TWH)
    out['3_country_electricity_balance_TWh'] = {c: dict(sorted(v.items())) | {'RESIDUAL': sum(v.values())} for c, v in sorted(bal.items())}
    # 4. primary fossil supply
    fs = collections.defaultdict(float)
    for j, gg in n.generators.iterrows():
        if gg.carrier in FOSSIL: fs[(gg.carrier, cty[gg.bus])] += gen_energy[j] / TWH
    out['4_primary_fossil_supply_TWh_th'] = {f'{a}|{b}': v for (a, b), v in sorted(fs.items())}
    out['4_primary_fossil_supply_by_fuel_TWh_th'] = {f: sum(v for (a, b), v in fs.items() if a == f) for f in sorted(FOSSIL)}
    # 5. CO2 (reported, not a constraint)
    atm_bus = bc.index[bc == 'co2 atmosphere']; atm_store = st.index[st.bus.isin(atm_bus)]
    co2 = {'atmosphere_buses': list(atm_bus), 'atmosphere_stores': list(atm_store)}
    if len(atm_store):
        e = n.stores_t.e[atm_store]; e0 = st.loc[atm_store, 'e_initial']
        co2['store_cyclic'] = st.loc[atm_store, 'e_cyclic'].astype(bool).tolist()
        co2['store_delta_t'] = float((e.iloc[-1] - (e.iloc[-1] if st.loc[atm_store, 'e_cyclic'].any() else e0)).sum())
        co2['store_inflow_sum_t'] = float((n.stores_t.p[atm_store].mul(w, axis=0)).sum().sum() * -1)
    flow = 0.0; by = collections.defaultdict(float)
    for k in ports:
        en = (-P[k]).mul(w, axis=0).sum()
        for j in L.index[L['bus%d' % k].isin(atm_bus)]: flow += en[j]; by[L.at[j, 'carrier']] += en[j]
    co2['link_flows_into_atmosphere_t'] = flow; co2['link_flows_by_carrier_t'] = dict(sorted(by.items(), key=lambda x: -x[1]))
    gen_atm = n.generators.index[n.generators.bus.isin(atm_bus)]; co2['generators_on_atmosphere_t'] = float(gen_energy[gen_atm].sum()) if len(gen_atm) else 0.0
    co2['Mt_store_method'] = co2.get('store_inflow_sum_t', float('nan')) / 1e6; co2['Mt_link_method'] = flow / 1e6
    co2['difference_t'] = co2.get('store_inflow_sum_t', 0.0) - flow
    co2['reference_original_author_2050_cap_Mt'] = 100.0; co2['note'] = 'reported value only; no constraint added, no conclusion drawn'
    out['5_co2'] = co2
    # 6. cost by asset country (description only)
    cost = collections.defaultdict(lambda: {'capital': 0.0, 'operating': 0.0}); capsum = 0.0; opsum = 0.0
    def country_of(df, j, comp):
        if comp in ('Link', 'Line'):
            cs = {cty[df.at[j, 'bus%d' % q]] for q in (ports if comp == 'Link' else [0, 1]) if df.at[j, 'bus%d' % q] in cty.index and bc[df.at[j, 'bus%d' % q]] in ELEC}
            if len(cs) > 1: return 'CROSS_BORDER'
        return cty.get(df.at[j, 'bus0' if comp in ('Link', 'Line') else 'bus'], 'NONE')
    for comp, nom in [('Generator', 'p_nom'), ('Link', 'p_nom'), ('Line', 's_nom'), ('StorageUnit', 'p_nom'), ('Store', 'e_nom')]:
        df = n.df(comp); ext = df[df[nom + '_extendable']]
        for j in ext.index:
            v = float(ext.at[j, 'capital_cost'] * (ext.at[j, nom + '_opt'] - ext.at[j, nom])); cost[country_of(df, j, comp)]['capital'] += v; capsum += v
    mc = {'Generator': (n.generators_t.p, n.get_switchable_as_dense('Generator', 'marginal_cost')), 'Link': (P[0], n.get_switchable_as_dense('Link', 'marginal_cost')),
          'Store': (n.stores_t.p, n.get_switchable_as_dense('Store', 'marginal_cost')), 'StorageUnit': (n.storage_units_t.p_dispatch, n.get_switchable_as_dense('StorageUnit', 'marginal_cost'))}
    for comp, (p, m) in mc.items():
        df = n.df(comp); val = (p.reindex(columns=df.index, fill_value=0.0).mul(w, axis=0) * m.reindex(columns=df.index, fill_value=0.0)).sum()
        for j in df.index:
            if val[j]: cost[country_of(df, j, comp)]['operating'] += float(val[j]); opsum += float(val[j])
    recon = json.loads((post.parent / 'postprocess/PHYSICAL_CHECKS.json').read_text())['details']['objective_reconciliation']
    out['6_cost_by_asset_country_EUR'] = {'basis': 'asset location (bus0 / generator bus); CROSS_BORDER = assets whose electric ports lie in different countries; description only, NOT a cost allocation',
                                          'by_country': {c: v for c, v in sorted(cost.items())}, 'capital_total': capsum, 'operating_total': opsum,
                                          'known_fixed_FOM_once_not_allocated': float(n.meta.get('existing_annual_fixed_om_eur', 0.0)),
                                          'official_reconciliation': recon, 'capital_minus_official': capsum - recon['capital'], 'operating_minus_official': opsum - recon['variable']}
    return out


def diff(a, b):
    if isinstance(a, dict) or isinstance(b, dict):
        a = a or {}; b = b or {}; return {k: diff(a.get(k), b.get(k)) for k in sorted(set(a) | set(b))}
    if isinstance(a, (int, float)) or isinstance(b, (int, float)):
        if isinstance(a, bool) or isinstance(b, bool): return None
        a = a or 0.0; b = b or 0.0; return {'daily': a, 'h3': b, 'abs': b - a}
    return None


d = tables(DN, DP); h = tables(HN, HP)
res = {'qualification': 'READ_ONLY_POSTPROCESS_NO_SOLVE', 'inputs_sha256': {str(DN): sha(DN), str(HN): sha(HN)}, 'daily_365': d, 'h3_2920': h,
       'diff_country_balance': diff(d['3_country_electricity_balance_TWh'], h['3_country_electricity_balance_TWh']),
       'diff_primary_fossil_by_fuel': diff(d['4_primary_fossil_supply_by_fuel_TWh_th'], h['4_primary_fossil_supply_by_fuel_TWh_th'])}
OUT.write_text(json.dumps(res, indent=1, ensure_ascii=False, default=float) + '\n', encoding='utf-8')
print('ok')
