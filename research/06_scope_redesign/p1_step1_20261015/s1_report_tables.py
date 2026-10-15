"""Print markdown tables for S1_REPORT.md from the receipts (read-only)."""
from pathlib import Path
import json
from collections import defaultdict
REPO=Path(r'\\wsl.localhost\Ubuntu\home\jin\research\SGP_ESE5004_Stage2\phase2\research_model');S1=REPO/'results_project'/'s1'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def fmt(x,d=1):return '—' if x is None else (f'{x:,.{d}f}' if isinstance(x,(int,float)) else str(x))

def inventory(scenario):
    r=read(S1/scenario/f'{scenario}_BUILD_RECEIPT.json');inv=r['inventory'];rows=defaultdict(lambda:dict(count=0,countries=set(),cap=0.,ext=0,xb=0,pending=0))
    for typ,recs in inv.items():
        if typ in ('Bus','Load'):continue
        for z in recs:
            k=(typ,z['carrier']);row=rows[k];row['count']+=z['count'];row['countries'].add(z['country']);row['xb']+=z.get('cross_border',0) or 0;row['pending']+=z.get('data_pending',0) or 0
            for nom in ['p_nom_mw_or_mwh','s_nom_mw_or_mwh','e_nom_mw_or_mwh']:
                if nom in z and z[nom] is not None:row['cap']+=z[nom]
            for nom in ['p_nom_extendable','s_nom_extendable','e_nom_extendable']:
                if nom in z and z[nom] is not None:row['ext']+=z[nom]
    print(f'\n#### {scenario}\n\n| 组件 | 载体 | 数量 | 覆盖国家数 | 现有/固定容量合计 (MW 或 MWh) | 可扩展数 | 跨境数 | DATA_PENDING |\n|---|---|---|---|---|---|---|---|')
    for (typ,car),row in sorted(rows.items()):print(f"| {typ} | {car} | {row['count']} | {len(row['countries'])} | {fmt(row['cap'])} | {row['ext']} | {row['xb']} | {row['pending']} |")
    print(f"\n负荷：{r['demand']['loads']} 个 Astar 电力 Load，{fmt(r['demand']['total_twh'],2)} TWh/a；母线 {r['network']['components']['Bus']}；时段 {r['network']['components'].get('snapshots','2920')}")

def smoke(scenario):
    d=S1/'smoke'/scenario
    if not (d/'SOLVE_RECEIPT.json').exists():print(scenario,'no smoke receipt');return
    r=read(d/'SOLVE_RECEIPT.json');print(f"\n#### {scenario}（SMOKE_TEST_ONLY）\n")
    print(f"- 状态：{r.get('status')} / {r.get('termination_condition')}；目标值 {fmt(r.get('objective'),0)}；求解 {fmt(r.get('solve_seconds'),1)} s；LP 建模 {fmt(r['lp']['build_seconds'],1)} s；峰值 RSS {fmt((r.get('peak_rss_bytes') or 0)/2**30,2)} GiB")
    print(f"- LP：{r['lp']['num_col']:,} 列 / {r['lp']['num_row']:,} 行 / {r['lp']['nnz']:,} 非零元；每国净零约束 {len(r['lp']['country_limits'])} 条")
    g=d/'V5_GATES.json'
    if g.exists():
        G=read(g);print('- V5 门槛：'+'；'.join(f"{k} {'PASS' if v['passed'] else 'FAIL'}" for k,v in G.items() if isinstance(v,dict) and 'passed' in v))
        a=G['A1_A2'];print(f"  - KKT：相对间隙 {a['relative_gap']:.2e}，行越界 {a['row_fail_count']}，列越界 {a['column_fail_count']}，驻点越界 {a['stationarity_fail_count']}，对偶符号 {a['dual_sign_fail_count']}")
        b1=G['B1'];print(f"  - B1：范围 {b1['scope']}；每吨只记一次 {b1['every_tonne_booked_once']}；ASEAN 合计 {fmt(b1['asean_total_tco2'],1)} tCO2（56 时段）")
        print('  - B1 各国最终大气储量 (tCO2)：'+', '.join(f"{c} {fmt(v['final_level_tco2'],1)}" for c,v in b1['countries'].items()))
        b11=G['B11'];print(f"  - B11：缺失 {b11['missing_count']}；DATA_PENDING {b11['data_pending_count']} {b11['data_pending_by_carrier']}")
    e=d/'INFEASIBILITY_DIAGNOSIS.json'
    if e.exists():
        E=read(e);print('- 不可行诊断：',E['status'],E['condition']);print('| 国家 | 需求 MWh | 零排放可再生潜力 MWh | 径流 MWh | 水库入流 MWh | 核电候选无上限 | 可覆盖 |\n|---|---|---|---|---|---|---|')
        for c,v in E['structural_supply'].items():print(f"| {c} | {fmt(v['demand_mwh'],0)} | {fmt(v['renewable_potential_mwh'],0)} | {fmt(v['ror_existing_mwh'],0)} | {fmt(v['reservoir_inflow_mwh'],0)} | {v['nuclear_candidate_unbounded']} | {v['zero_emission_supply_can_cover_demand']} |")
    cap=d/'CAPACITY_BY_TECH_COUNTRY.json'
    if cap.exists():
        C=read(cap);tot=defaultdict(float)
        for typ,recs in C.items():
            for z in recs:
                v=z.get('p_nom_opt',z.get('e_nom_opt',0.)) or 0.
                if v>1e-6:tot[(typ,z['carrier'])]+=v
        print('- 优化容量合计（>0）：'+'; '.join(f"{t}:{c} {fmt(v,0)}" for (t,c),v in sorted(tot.items())))

def main():
    print('## 组件清单');inventory('integrated');inventory('disconnected')
    print('\n## 冒烟测试');smoke('integrated');smoke('disconnected')
    for f in ['S1_COST_LAYER_HASH_CHECK.json','S1_DETERMINISM_CHECK.json']:
        p=S1/f
        if p.exists():print('\n'+f,json.dumps({k:v for k,v in read(p).items() if k not in ('with_layer','without_layer','rule')}))
    p=S1/'smoke'/'S1_SMOKE_B5_B6.json'
    if p.exists():
        x=read(p);print('\nB5',{k:v for k,v in x['B5'].items() if k!='config_differences'},'diff',x['B5']['config_differences']);print('B6',x['B6'])
if __name__=='__main__':main()
