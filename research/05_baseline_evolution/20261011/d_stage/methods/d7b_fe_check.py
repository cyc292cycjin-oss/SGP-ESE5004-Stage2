"""D-7b 附录（只读，不求解）：final-energy accounting 类 Link（oil/coal/gas）的流量是否被外生固定。

逐条检查：Link 参数（p_min_pu/p_max_pu、p_nom/extendable、efficiency、时变覆盖）；终端母线 bus1 上的全部连接
（Load、Generator、Store、StorageUnit、Line、其他 Link 端口）；Load 是否为固定 p_set；解中 −p1 是否逐时段等于母线 Load；
网络元数据中是否有点名这些 Link 的额外约束钩子。
Usage: python d7b_fe_check.py <daily nc> <2920 nc> <out json>
"""
import sys, json, hashlib, logging, collections
from pathlib import Path
import numpy as np, pandas as pd, pypsa
logging.disable(logging.WARNING)
DN, HN, OUT = map(Path, sys.argv[1:4])


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 23), b''): h.update(b)
    return h.hexdigest()


def check(nc):
    n = pypsa.Network(nc); L = n.links; fe = L.index[L.carrier.str.endswith('final-energy accounting')]
    ports = sorted(int(c[3:]) for c in L.columns if c.startswith('bus') and c[3:].isdigit()); bc = n.buses.carrier
    out = {'snapshots': len(n.snapshots), 'links': int(len(fe)), 'by_carrier': L.loc[fe].carrier.value_counts().to_dict()}
    # 1. static parameters
    s = L.loc[fe]
    out['params'] = {'p_min_pu': s.p_min_pu.describe().to_dict(), 'p_max_pu': s.p_max_pu.describe().to_dict(),
                     'p_nom_extendable_count': int(s.p_nom_extendable.sum()), 'p_nom_min_max': [float(s.p_nom.min()), float(s.p_nom.max())],
                     'efficiency_unique': sorted(set(map(float, s.efficiency))), 'efficiency2_range': [float(s.efficiency2.min()), float(s.efficiency2.max())],
                     'p_min_pu_equals_p_max_pu_count': int((s.p_min_pu == s.p_max_pu).sum()), 'marginal_cost_range': [float(s.marginal_cost.min()), float(s.marginal_cost.max())],
                     'capital_cost_range': [float(s.capital_cost.min()), float(s.capital_cost.max())]}
    tv = {k: sorted(set(n.links_t[k].columns) & set(fe)) for k in ('p_min_pu', 'p_max_pu', 'p_set', 'efficiency', 'efficiency2') if k in n.links_t and len(n.links_t[k].columns)}
    out['time_varying_overrides'] = {k: len(v) for k, v in tv.items()}
    # 2. what is attached to each final-energy bus (bus1)
    b1 = s.bus1; att = collections.Counter(); per = []
    port_users = collections.defaultdict(list)
    for j in L.index:
        for k in ports:
            b = L.at[j, 'bus%d' % k]
            if b: port_users[b].append((j, k, L.at[j, 'carrier']))
    load_at = n.loads.groupby('bus').apply(lambda x: list(x.index)).to_dict()
    for j in fe:
        b = b1[j]; users = [u for u in port_users[b] if u[0] != j]
        sig = (bc[b], len(load_at.get(b, [])), int(n.generators.bus.eq(b).sum()), int(n.stores.bus.eq(b).sum()), int(n.storage_units.bus.eq(b).sum()),
               int(n.lines.bus0.eq(b).sum() + n.lines.bus1.eq(b).sum()), tuple(sorted({u[2] + '@port' + str(u[1]) for u in users})))
        att[sig] += 1
        per.append((j, b))
    out['final_bus_attachment_signatures'] = [{'bus_carrier': k[0], 'loads': k[1], 'generators': k[2], 'stores': k[3], 'storage_units': k[4], 'lines': k[5],
                                               'other_link_ports': list(k[6]), 'count': v} for k, v in att.items()]
    # 3. loads fixed? 4. flow equals load in solution
    ld_static = n.loads; pset_tv = set(n.loads_t.p_set.columns)
    w = n.snapshot_weightings.objective; p1 = n.links_t.p1; maxdev = 0.0; maxrel = 0.0; tot_load = 0.0; tot_flow = 0.0; nfixed = 0
    loads_kind = collections.Counter()
    for j, b in per:
        lds = load_at.get(b, [])
        for l in lds: loads_kind['time_varying_p_set' if l in pset_tv else 'static_p_set'] += 1
        dem = sum((n.loads_t.p_set[l] if l in pset_tv else pd.Series(float(ld_static.at[l, 'p_set']), index=n.snapshots)) for l in lds) if lds else pd.Series(0.0, index=n.snapshots)
        inj = -p1[j]; dev = (inj - dem).abs(); maxdev = max(maxdev, float(dev.max())); maxrel = max(maxrel, float((dev / np.maximum(1.0, dem.abs())).max()))
        tot_load += float((dem * w).sum()); tot_flow += float((inj * w).sum())
    out['loads_on_final_buses'] = dict(loads_kind)
    out['solution_flow_vs_load'] = {'max_abs_deviation_MW': maxdev, 'max_rel_deviation': maxrel, 'annual_load_TWh': tot_load / 1e6, 'annual_link_delivery_TWh': tot_flow / 1e6}
    # implied CO2 (efficiency2 per MWh input; input = delivery/efficiency)
    out['annual_input_TWh_th'] = float((n.links_t.p0[fe].mul(w, axis=0)).sum().sum() / 1e6)
    out['annual_co2_Mt'] = float((-n.links_t.p2[fe]).mul(w, axis=0).sum().sum() / 1e6)
    # 5. metadata hooks naming these links
    meta = json.dumps(n.meta, default=str); names = set(fe)
    out['meta_mentions'] = {'link_names_found_in_meta': int(sum(1 for x in list(names)[:2000] if x in meta)), 'keys_mentioning_final_energy': [k for k, v in n.meta.items() if 'final' in json.dumps(v, default=str).lower() and 'energy' in json.dumps(v, default=str).lower()][:20],
                           'required_constraint_hooks': n.meta.get('required_constraint_hooks'), 'store_power_rules_count': len(n.meta.get('store_power_rules', {})), 'external_annual_caps': n.meta.get('external_annual_caps')}
    return out


res = {'qualification': 'READ_ONLY_NO_SOLVE', 'inputs_sha256': {str(DN): sha(DN), str(HN): sha(HN)}, 'daily_365': check(DN), 'h3_2920': check(HN)}
OUT.write_text(json.dumps(res, indent=1, ensure_ascii=False, default=float) + '\n', encoding='utf-8'); print(json.dumps(res, indent=1, default=float)[:9000])
