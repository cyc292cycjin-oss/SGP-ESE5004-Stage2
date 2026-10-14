"""P0 问题 10：全部门耦合后的 2920 模型规模与内存外推（只做估算，不构建、不求解）。

基准（VERIFIED，P0_SCALE_BASELINE.json）：当前每时段 6,703 个时变变量；其中外生固定块 3,677 个
（final-energy accounting Link 1,256 + 生物质 obligation meter 807 + 固定资源 Store 的 e/p 1,614）。
新口径下该块被可替代技术链取代，因此先扣除，再按部门加入"每节点每时段新增时变变量"的三档假设（INFERENCE，
按上游 prepare_sector_network.py 的组件结构计数：每个 Link/Generator 1 个 p，每个 Store 2 个 e/p）。
比例系数（行/列、非零/列、内存/非零、时间）全部取自 D-1、D-5 和 Gate6 首次运行的实测回执。
"""
import json
from pathlib import Path
W = Path(__file__).resolve().parent
B = json.loads((W / 'P0_SCALE_BASELINE.json').read_text(encoding='utf-8'))
T = B['snapshots']; NOW = B['time_varying_variables_per_snapshot_total']; FIXED_BLOCK = 1256 + 807 + 1614
COLS, ROWS, NNZ = 19_568_505, 48_301_938, 90_782_037            # D-1 VERIFIED
R_PER_C, NZ_PER_C = ROWS / COLS, NNZ / COLS
MEM_BUILD = 25.2 / (NNZ / 1e6)                                   # D-1 build RSS 25.2 GiB @ 90.8M nnz
MEM_SOLVE = 24.9 / 62.504757                                     # D-5 RSS 24.9 GiB @ 62.5M nnz (main LP)
MEM_SOLVE_G6 = 33.2 / (NNZ / 1e6)                                # Gate6 first run 33.2 GiB @ 90.8M nnz (Barrier only)
T_D5 = {'barrier_s': 5479.0, 'crossover_s': 12753.0 - 5479.0, 'nnz_M': 62.504757}
# 每节点每时段新增时变变量（低 / 中 / 高）。依据：上游 add_heat（5 个热系统 × 热泵/电阻/锅炉/太阳能/储热）、
# add_land_transport（BEV 充电、V2G、EV 电池、ICE、FCEV）、add_industry（分子行业燃料替代与 CC）、add_shipping/aviation、
# H2（轮机、盐穴、压缩）、CO2（封存 Store、封存 Link、DAC、BECCS、vent）、生物质潜力（固体、沼气、升级、BtL）、
# 分子载体（NH3、甲醇、LNG 再气化与储罐、进口入口）、农业及其他。
SECTORS = {'heat_buildings': (25, 40, 54), 'cooling': (1, 3, 5), 'land_transport': (3, 7, 9), 'industry_subsectors': (8, 20, 35),
           'shipping_aviation': (4, 8, 12), 'hydrogen_extras': (2, 4, 5), 'co2_ccs_dac_beccs': (4, 8, 12), 'biomass_potential': (3, 6, 10),
           'molecule_carriers_imports': (6, 12, 18), 'agriculture_other': (1, 3, 5)}
CROSS_BORDER_EDGES, MOLECULE_CARRIERS = 24, 6        # 现有 24 条跨境电力边（ELECTRICITY_INTERCONNECT_CONTROL_SET）；H2、NH3、甲醇、合成燃料、LNG/gas、CO2


def case(i, nodes):
    add = sum(v[i] for v in SECTORS.values())
    per = NOW - FIXED_BLOCK + nodes * add + CROSS_BORDER_EDGES * MOLECULE_CARRIERS
    cols = per * T + 5_000 + nodes * add                 # 静态容量变量：现有约 4.5k，加上新增可扩展资产
    nnz = cols * NZ_PER_C
    return {'new_vars_per_node_per_snapshot': add, 'vars_per_snapshot': per, 'columns_M': cols / 1e6, 'rows_M': cols * R_PER_C / 1e6, 'nnz_M': nnz / 1e6,
            'build_RSS_GiB': nnz / 1e6 * MEM_BUILD, 'solve_RSS_GiB_D5_ratio': nnz / 1e6 * MEM_SOLVE, 'solve_RSS_GiB_Gate6_ratio': nnz / 1e6 * MEM_SOLVE_G6,
            'barrier_s_linear': T_D5['barrier_s'] * nnz / 1e6 / T_D5['nnz_M'], 'barrier_s_power1p5': T_D5['barrier_s'] * (nnz / 1e6 / T_D5['nnz_M']) ** 1.5}


res = {'qualification': 'ESTIMATE_ONLY_NO_BUILD_NO_SOLVE (INFERENCE)', 'baseline': {'vars_per_snapshot_now': NOW, 'fixed_block_removed': FIXED_BLOCK, 'columns': COLS, 'rows': ROWS, 'nnz': NNZ,
       'rows_per_column': R_PER_C, 'nnz_per_column': NZ_PER_C, 'build_GiB_per_M_nnz': MEM_BUILD, 'solve_GiB_per_M_nnz_D5': MEM_SOLVE, 'solve_GiB_per_M_nnz_Gate6': MEM_SOLVE_G6, 'D5_times': T_D5},
       'sector_assumptions_low_central_high': SECTORS,
       'limits_122': {'cgroup_GiB': 90, 'RSS_guard_GiB': 75, 'SoftMemLimit_GB_decimal': 65, 'native_TimeLimit_D5_s': 14400},
       'cases': {f'{lvl}_{nodes}nodes': case(i, nodes) for nodes in (100, 11) for i, lvl in enumerate(('low', 'central', 'high'))}}
(W / 'P0_SCALE_ESTIMATE.json').write_text(json.dumps(res, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
for k, v in res['cases'].items():
    print(k, {x: round(y, 1) if isinstance(y, float) else y for x, y in v.items()})
