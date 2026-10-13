"""由 evidence/D7B_POWER_SYSTEM_TABLES.json 生成 D7B_POWER_SYSTEM_TABLES.md 的表格部分（数字全部来自 JSON，不手抄）。"""
import json, collections, sys
from pathlib import Path
W = Path(__file__).resolve().parents[1]; R = json.loads((W / 'evidence/D7B_POWER_SYSTEM_TABLES.json').read_text(encoding='utf-8'))
d, h = R['daily_365'], R['h3_2920']; out = []
f0 = lambda x: f'{x:,.0f}'; f1 = lambda x: f'{x:,.1f}'; f2 = lambda x: f'{x:,.2f}'


def t1():
    key = lambda t: {(x['carrier'], x['bus_carrier']): x for x in t['1_generator_attachment']}
    a, b = key(d), key(h); out.append('| Generator carrier | 所在母线 carrier | 个数 | p_nom_opt 日模型（MW） | p_nom_opt 2920（MW） | 年出力 日模型（TWh） | 年出力 2920（TWh） |\n|---|---|---|---|---|---|---|')
    for k in sorted(set(a) | set(b)):
        x, y = a.get(k, {}), b.get(k, {})
        out.append(f"| {k[0]} | {k[1]} | {x.get('count', y.get('count'))} | {f0(x.get('p_nom_opt_MW', 0))} | {f0(y.get('p_nom_opt_MW', 0))} | {f1(x.get('annual_output_TWh', 0))} | {f1(y.get('annual_output_TWh', 0))} |")


def t2():
    a = {x['carrier']: x for x in d['2_power_generating_links']}; b = {x['carrier']: x for x in h['2_power_generating_links']}
    out.append('| 发电 Link | 输入母线 | 输入侧容量 日 / 2920（MW） | 电输出容量 日 / 2920（MW_e） | 年输入 日 / 2920（TWh） | 年发电 日 / 2920（TWh） | 容量因子 日 / 2920 |\n|---|---|---|---|---|---|---|')
    cf = lambda v: '—' if v is None else f'{v:.3f}'
    for k in sorted(set(a) | set(b), key=lambda k: -(b.get(k, a.get(k))['annual_electricity_TWh'])):
        x, y = a.get(k, {}), b.get(k, {}); bus = '、'.join((x or y)['bus0_carrier'])
        out.append(f"| {k} | {bus} | {f0(x.get('p_nom_opt_input_MW', 0))} / {f0(y.get('p_nom_opt_input_MW', 0))} | {f0(x.get('electric_capacity_MWe', 0))} / {f0(y.get('electric_capacity_MWe', 0))} | "
                   f"{f1(x.get('annual_input_TWh', 0))} / {f1(y.get('annual_input_TWh', 0))} | {f1(x.get('annual_electricity_TWh', 0))} / {f1(y.get('annual_electricity_TWh', 0))} | {cf(x.get('capacity_factor'))} / {cf(y.get('capacity_factor'))} |")


def grp(k):
    if k.startswith('gen|solar'): return '光伏（直接挂电力母线）'
    if k.startswith('gen|'): return '其他直接发电（风电、径流水电）'
    if k.startswith('link_output|'):
        c = k.split('|')[1]
        if 'battery' in c or 'Fuel Cell' in c: return '储能/燃料电池放电'
        return '火电 Link 输出'
    if k.startswith('storage_unit'): return '水电/抽蓄（净）'
    if k == 'load': return '电力负荷'
    if k.startswith('link_consumption'): return '耗电 Link 输入（充电、电解）'
    if k.startswith('cross_border'): return '净进口（跨境线路与 DC/B2B）'
    return '国内传输与配电（净）'


COLS = ['光伏（直接挂电力母线）', '其他直接发电（风电、径流水电）', '火电 Link 输出', '水电/抽蓄（净）', '储能/燃料电池放电', '耗电 Link 输入（充电、电解）', '电力负荷', '净进口（跨境线路与 DC/B2B）', '国内传输与配电（净）']


def t3(t, title):
    out.append(f'**{title}**（TWh/年；注入为正，负荷与耗电为负）\n')
    out.append('| 国家 | ' + ' | '.join(COLS) + ' | 残差 |\n|' + '---|' * (len(COLS) + 2))
    for c, v in t['3_country_electricity_balance_TWh'].items():
        a = collections.defaultdict(float)
        for k, x in v.items():
            if k != 'RESIDUAL': a[grp(k)] += x
        out.append(f'| {c} | ' + ' | '.join(f1(a[k]) for k in COLS) + f" | {v['RESIDUAL']:.1e} |")
    out.append('')


def t4():
    a, b = d['4_primary_fossil_supply_TWh_th'], h['4_primary_fossil_supply_TWh_th']
    out.append('| 燃料 | 日模型（TWh_th） | 2920（TWh_th） | 差 |\n|---|---|---|---|')
    for k in sorted(d['4_primary_fossil_supply_by_fuel_TWh_th']):
        x, y = d['4_primary_fossil_supply_by_fuel_TWh_th'][k], h['4_primary_fossil_supply_by_fuel_TWh_th'][k]; out.append(f'| {k} | {f1(x)} | {f1(y)} | {y - x:+,.1f} |')
    out.append('\n分国家（TWh_th，日模型 / 2920）：\n\n| 燃料 \\| 国家 | ' + ' | '.join(sorted({k.split('|')[1] for k in a})) + ' |\n|' + '---|' * (1 + len({k.split('|')[1] for k in a})))
    cs = sorted({k.split('|')[1] for k in a})
    for fu in sorted({k.split('|')[0] for k in a}):
        out.append(f'| {fu} | ' + ' | '.join(f"{a.get(fu + '|' + c, 0):,.0f} / {b.get(fu + '|' + c, 0):,.0f}" for c in cs) + ' |')


def t5():
    out.append('| 口径 | 日模型（MtCO₂/年） | 2920（MtCO₂/年） |\n|---|---|---|')
    out.append(f"| 大气 Store 库存变化（流入合计） | {f1(d['5_co2']['Mt_store_method'])} | {f1(h['5_co2']['Mt_store_method'])} |")
    out.append(f"| 进入大气母线的 Link 流量求和 | {f1(d['5_co2']['Mt_link_method'])} | {f1(h['5_co2']['Mt_link_method'])} |")
    out.append(f"| 两种算法之差（t） | {d['5_co2']['difference_t']:.1e} | {h['5_co2']['difference_t']:.1e} |")
    out.append('| 原作者 2050 cap（仅并列，不作结论、不加约束） | 100 | 100 |\n')
    out.append('按 Link carrier 拆分（MtCO₂/年，日模型 / 2920）：\n\n| carrier | 日模型 | 2920 |\n|---|---|---|')
    a, b = d['5_co2']['link_flows_by_carrier_t'], h['5_co2']['link_flows_by_carrier_t']
    for k in sorted(set(a) | set(b), key=lambda k: -b.get(k, 0)):
        if abs(a.get(k, 0)) + abs(b.get(k, 0)) > 0: out.append(f'| {k} | {a.get(k, 0) / 1e6:,.2f} | {b.get(k, 0) / 1e6:,.2f} |')


def t6():
    a, b = d['6_cost_by_asset_country_EUR'], h['6_cost_by_asset_country_EUR']
    out.append('| 资产所在地 | 资本 日模型 | 资本 2920 | 运行 日模型 | 运行 2920 |\n|---|---|---|---|---|')
    for c in sorted(set(a['by_country']) | set(b['by_country'])):
        x, y = a['by_country'].get(c, {'capital': 0, 'operating': 0}), b['by_country'].get(c, {'capital': 0, 'operating': 0})
        out.append(f"| {c} | {x['capital'] / 1e9:,.3f} | {y['capital'] / 1e9:,.3f} | {x['operating'] / 1e9:,.3f} | {y['operating'] / 1e9:,.3f} |")
    out.append(f"| **合计** | **{a['capital_total'] / 1e9:,.3f}** | **{b['capital_total'] / 1e9:,.3f}** | **{a['operating_total'] / 1e9:,.3f}** | **{b['operating_total'] / 1e9:,.3f}** |")
    out.append(f"| 已知现有资产 FOM（一次，不分摊） | {a['known_fixed_FOM_once_not_allocated'] / 1e9:,.3f} | {b['known_fixed_FOM_once_not_allocated'] / 1e9:,.3f} | — | — |\n")
    out.append(f"单位：十亿 EUR/年。与官方对账（PHYSICAL_CHECKS 的 objective_reconciliation）的差：资本 {a['capital_minus_official']:.1e} / {b['capital_minus_official']:.1e} EUR，运行 {a['operating_minus_official']:.1e} / {b['operating_minus_official']:.1e} EUR。")


sections = {'T1': t1, 'T2': t2, 'T3D': lambda: t3(d, '日模型（C09）'), 'T3H': lambda: t3(h, '2920（D-5）'), 'T4': t4, 'T5': t5, 'T6': t6}
tmpl = (W / 'methods/D7B_POWER_SYSTEM_TABLES.template.md').read_text(encoding='utf-8')
for k, fn in sections.items():
    out.clear(); fn(); tmpl = tmpl.replace('{{' + k + '}}', '\n'.join(out))
tmpl = tmpl.replace('{{SHA_D}}', list(R['inputs_sha256'].values())[0]).replace('{{SHA_H}}', list(R['inputs_sha256'].values())[1])
(W / 'D7B_POWER_SYSTEM_TABLES.md').write_text(tmpl, encoding='utf-8'); print('ok')
