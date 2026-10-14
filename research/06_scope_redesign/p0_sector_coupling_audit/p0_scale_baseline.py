"""P0 问题 10 的基准统计（只读，不构建、不求解）：当前 2920 模型按组件、按用途分解的时变变量与约束规模。
输入：D-5 的已求解 2920 NetCDF（与 D-1 构建同一结构）与 D-1 约束覆盖表。
Usage: python p0_scale_baseline.py <2920 solved nc> <D1_CONSTRAINT_COVERAGE.json> <out json>
"""
import sys, json, hashlib, logging, collections
from pathlib import Path
import pypsa
logging.disable(logging.WARNING)
NC, COV, OUT = map(Path, sys.argv[1:4])
n = pypsa.Network(NC); T = len(n.snapshots); bc = n.buses.carrier
role = lambda c: ('fixed_final_energy_accounting' if 'final-energy accounting' in c else 'biomass_obligation_meter' if 'obligation metering' in c else c)
per_snap = collections.Counter(); detail = collections.Counter()
for c in n.generators.carrier: per_snap['Generator-p'] += 1; detail['Generator|' + c] += 1
for c in n.links.carrier: per_snap['Link-p'] += 1; detail['Link|' + role(c)] += 1
per_snap['Line-s'] += len(n.lines)
for c in n.stores.carrier:
    k = 'fixed_resource_store' if n.stores.e_nom_extendable.eq(False).any() and c in ('Fuelwood', 'Charcoal', 'Biodiesel', 'Bagasse', 'Biogases', 'Biogasoline', 'Animal waste') else c
    per_snap['Store-e'] += 1; per_snap['Store-p'] += 1; detail['Store|' + k] += 2
per_snap['StorageUnit(p_dispatch,p_store,soc,spill)'] += 4 * len(n.storage_units)
static = {'Generator-p_nom(ext)': int(n.generators.p_nom_extendable.sum()), 'Link-p_nom(ext)': int(n.links.p_nom_extendable.sum()),
          'Line-s_nom(ext)': int(n.lines.s_nom_extendable.sum()), 'Store-e_nom(ext)': int(n.stores.e_nom_extendable.sum()), 'StorageUnit-p_nom(ext)': int(n.storage_units.p_nom_extendable.sum())}
cov = json.loads(COV.read_text(encoding='utf-8'))
res = {'qualification': 'READ_ONLY_COUNT_NO_BUILD_NO_SOLVE', 'nc_sha256': hashlib.sha256(NC.read_bytes()).hexdigest(), 'snapshots': T,
       'nodes_AC': int((bc == 'AC').sum()), 'buses_by_carrier': bc.value_counts().to_dict(),
       'time_varying_variables_per_snapshot': dict(per_snap), 'time_varying_variables_per_snapshot_total': sum(per_snap.values()),
       'columns_estimate': sum(per_snap.values()) * T + sum(static.values()), 'static_extendable_variables': static,
       'per_snapshot_by_role': dict(sorted(detail.items(), key=lambda x: -x[1])),
       'constraint_rows_by_family': {f['family']: f['rows'] for f in cov['families']}, 'constraint_rows_total': sum(f['rows'] for f in cov['families'])}
OUT.write_text(json.dumps(res, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
print(json.dumps({k: res[k] for k in ('snapshots', 'nodes_AC', 'time_varying_variables_per_snapshot', 'time_varying_variables_per_snapshot_total', 'columns_estimate', 'static_extendable_variables', 'constraint_rows_total')}, indent=1))
print(json.dumps(dict(list(res['per_snapshot_by_role'].items())[:40]), indent=0))
