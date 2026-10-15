# S3 进度记录（防中断用；每个子步骤提交后更新）

分支 `codex/s3-gas-imports-shipping-20261015`（自 S2 分支 `codex/s2-co2-biomass-demand-20261015` @ 8d61bd37 开出）；draft PR 叠在 PR #23 上（S3-1 后开）。
仓库 `cyc292cycjin-oss/SGP-ESE5004-Stage2`；WSL 路径 `/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model`。
求解环境：`/home/jin/miniforge3/envs/pypsa-earth/bin/python`，`PYTHONHASHSEED=0`，PyPSA 0.30.3 / linopy 0.5.5 / HiGHS 1.11（IPM）；截断运行权重按第 58 项（8760/N）。
构建/冒烟输出：`results_project/s3/`（忽略于 git；回执复制到本目录 `evidence/`）。

| 子步骤 | 内容 | 状态 | 提交 | 说明 |
|---|---|---|---|---|
| S3-0 | 收尾修正：第 61 项 IDEES 工业比率；第 59/62 项走廊（TH–MM、LA–MM）与 APG 核对；第 63 项废塑料代理值；柬埔寨交通链核对；重算结构表 + 冒烟 | 完成（见下） | 9a6f9e20 | 详见下表；报告 §1 |
| S3-1 | 天然气网络与国内生产、LNG | 完成 | ca4657b6（draft PR #24） | `s3_1_gas_data.py` → `gas_v5/`（存量跨境管道 7 条：6 条登记容量、MY–SG DATA_PENDING；产量上限表）；`s3_layers.add_gas_network`：移除 100 个节点外部气源，84 个井口发电机（年上限 = UNSD 2019 产量 × 负荷份额，C 级；价格 = 进口价；逸散因子 S2-0），111 条候选 + 14 条连通性补全（PyPSA-Eur 1968–2010 行）+ 6 条存量管道，16 个 LNG 接收站节点（2.5× 规则，再气化加价 DATA_PENDING = 0）；两情景构建通过（`results_project/s3_1/`），结构表同 S3-0；测试 374 通过 / 4 基线失败；报告 §2、§9 |
| S3-2 | 东盟外进口（化石 + 绿色载体，Neumann 等 2025 价格 +20%） | 完成 | b0c6b068 | 价格基准取 Zenodo 10.5281/zenodo.14872184 `results.parquet`（2040，default，按出口地最小值，与 PyPSA-Eur 进口分支 5a87cedd 同法）：液氢 88.13 / 氨 97.32 / 甲醇 120.97 / FT 125.09 → ×1.20；`s3_layers.add_imports`：全区油池（节点外部油源移除，100 条双向分配链路）、`ASEAN ammonia/methanol/oil non-fossil` 母线 + 进口发电机、16 个 LNG 站址液氢进口（LNG 容量上限、终端成本 8,421.6 EUR/MW/a）；煤分节点不变；第 64 项引用进口分支 4553–4557 / 4659–4665 行；两情景构建通过（`results_project/s3_2/`）；测试 376 通过 / 4 基线；报告 §3。大文件（arXiv/SI PDF、parquet）不入 git，只登记 URL/时间/SHA |
| S3-3 | 氨与甲醇（全区母线、哈伯-博施、甲醇合成、氨裂解） | 完成 | e18ccd46 + 077028c8（测试修正） | `s3_layers.add_ammonia_methanol`：97 节点 × {哈伯-博施、氨裂解、甲醇合成（节点捕集 CO₂）、生物质制甲醇、甲醇 OCGT}（PyPSA-Eur 默认开关与代码行已登记）+ 两个全区储存；需求层切到 `regional_buses`（氨负荷 55.03 TWh 直接挂全区母线，工业甲醇 5.62 TWh 经节点使用链路记排放 0.2482 t/MWh）；`country_carbon.component_country` 忽略 ASEAN 池端口；两情景构建通过（`results_project/s3_3/`）；报告 §4 |
| S3-4 | 航运（D1 表 651.19 TWh 油当量，甲醇份额 1） | 完成 | cfa53849 | 需求层 S3-4 段：国内 92.76 + 国际燃料舱 558.42 TWh（开关与航空共用）× 0.40/0.46 = 566.25 TWh 甲醇，节点链路从 `ASEAN methanol` 取用并按 0.2482 t/MWh 记消费国排放；指令的 670.2 TWh 未从当前 D1 表复现（已登记，待用户确认）；两情景构建通过（`results_project/s3_4/`）；测试 379 通过 / 4 基线；报告 §5 |
| S3-5 | 合成/生物燃料碳归属（origin_neutral 主算，producer_credit 敏感性） | 完成 | ededdc9e | `s3_layers.add_fuel_carbon_mode`：油分化石/非化石池（100 节点非化石母线 + 723 条零排放孪生消费链路），甲醇母线即非化石母线（消费端口移除），FT/甲醇合成在生产国记 +碳，BtL/生物质制甲醇信用移除，进口零；`co2 stored` 不拆分的等价性已论证；`s2_network.py --override` 构建 producer_credit（`results_project/s3_5_pc/`）；SG 算例 115.5 Mt；测试 382 通过 / 4 基线；报告 §6 |
| S3-6 | V5 门槛新增 B 组检查 | 完成 | b8ac3ed9 | `v5_gates.py`：B13 只进不出、B14 接收站 ≤ 2.5×、B15 国内生产上限、B16 两情景进口价格一致；B1 扩展（进口载体零碳、S3 燃料端口）、B11 扩展（油池合并、全区母线）、B12 扩展（`--override` 哈希、S3 开关登记）；`s2_solve.py` 求解后运行 B13–B15；`s3_6_gates_check.py` 静态检查三个 S3-5 网络全部通过（`evidence/s3_6/`）；报告 §7 |
| S3-7 | 构建与冒烟（两种碳归属模式 × 两情景） | 完成（本步提交） | 本步提交 | 四网络构建（`results_project/s3_7/`，LP 559k/1.27M/2.83M）；HiGHS IPM 一体化冒烟"不可行"、单纯形 2 h 20 min 未收敛（第 65 项停止）；Gurobi（Method 2 / NumericFocus 3 / BarHomogeneous 1 / Crossover 1 / Threads 8）：一体化 barrier 最优 6.988e11 → crossover INF_OR_UNBD，诊断 LP 最优同目标（松弛 0）→ 可行，HiGHS"不可行"定性为数值问题；pc 一体化同样 barrier 最优 / INF_OR_UNBD；不互联诊断 INF_OR_UNBD；止损规则（30 min、非最优即停、不重试）已执行，一次重复运行事故已登记；用户补充 1（进口价格 2040→2050 降幅 9–12%，下限保持 −20%）与 2（LP 系数范围、缩放建议 PROPOSED）完成；报告 §8，云资源 §8 |
| 交付 | `S3_REPORT.md`、`S3_EVIDENCE.json`、`S3_TEST_RUN.json`、`DOWNLOAD_LIST.csv`（+ `DOWNLOAD_LIST_CLOSED_S3.csv`、`DATA_PENDING_LIST.csv`、`DATA_REGISTRY.csv` 副本）、`CLOUD_RESOURCE_ESTIMATE.md` §8（在 p1_step2 目录） | 完成 | 本步提交 | `s3_collect_evidence.py` 汇总；证据目录 `evidence/s3_0 … s3_7`（Gurobi 日志只保留剔除许可行的副本）；镜像到 `D:\ResearchWorkspaces\ASEAN\work\p1_step3_20261015\` |

## S3-0 明细

| 项 | 做法 | 输出 |
|---|---|---|
| 0.1 第 61 项 | `scripts_project/s3_0_industry_ratios.py`：原样导入 PyPSA-Eur v2025.07.0 `build_industry_sector_ratios.py` 的 11 个部门函数（iron_and_steel 102、chemicals_industry 296、nonmetalic_mineral_products 635、pulp_paper_printing 832、food_beverages_tobacco 991、non_ferrous_metals 1057、transport_equipment 1259、machinery_equipment 1309、textiles_and_leather 1361、wood_and_wood_products 1410、other_industrial_sectors 1455 行），参数取 config.default.yaml 815–910 行，`reference_year` 2019；EU27 氨产量按 PyPSA-Eur 规则从 USGS 氮表 T12 复现（只读获取，15,712.9 kt NH3，18 国）；`scripts_project/s3_0_industry.py`：全部子部门改用这些比率（钢铁 0.3 DRI+EAF / 0.7 EAF；水泥 = 熟料/0.656 × Cement 比率；其余子部门 = UNSD 2019 能耗 × 乘数 × 效率因子（2050/2019 EU27 单耗）× 2050 载体份额；UNSD→PyPSA-Eur 映射表 C 级）；低温热行 → 节点工业低温热母线；S2B technology-data 钢铁/水泥 → `*_TD_SENSITIVITY.csv`（开关 `research.s2.industry.ratio_source`） | `registry_v5/INDUSTRY_SECTOR_RATIOS_PYPSA_EUR_2050.csv`（27 列）、`..._TODAY_EU27_2019.csv`、`demand_v5/INDUSTRY_2050_SUMMARY_*.csv`（覆盖 S2B）、`INDUSTRY_SUBSECTOR_MAPPING_UNSD_PYPSA_EUR.csv`、`INDUSTRY_2050_COMPARISON_BAS_S2B_S3.csv`（S2B 列取自冻结文件 `..._S2B_FROZEN.csv` = 提交 8d61bd37）、`INDUSTRY_2050_GAPS.csv` |
| 0.2 第 59/62 项 | `scripts_project/s3_0_corridors.py`：走廊表新增 `APG11_TH_MM`（MM2 4–TH2 4，大圆 233 km × 1.25 = 291.8 km，2025 容量 0，候选）与 `APG17_LA_MM`（LA2 5–MM2 13，284 km × 1.25 = 354.7 km，2025 容量 30 MW 存量）；线路在构建时由 `s2_layers.add_apg_corridor_lines` 生成（成本 42.01 EUR/MW/km/a、线型/电气参数按基础网最小并联数的跨境线）；24 走廊 vs 18 个 APG 项目核对表 | `corridors/cross_border_corridors.csv`（26 行）、`CORRIDOR_APG_CROSSCHECK_2024.csv`、`CORRIDOR_APG_EVIDENCE.json`；H2/CO₂ 候选自动再生成（跨境候选 19 → 21，MM 接入） |
| 0.3 第 63 项 | `s2b_feedstock.py`：LA 塑料份额 = 10 国 MSW-2050 加权均值 0.165（敏感性 0–0.29）；KH/TH/VN 未收集垃圾露天焚烧份额 = ID+MM+PH 加权均值 0.739（敏感性 0–0.739） | `FEEDSTOCK_CARBON_TERRITORIAL_2050_*.csv`、登记表 C 级行 |
| 0.4 KH 核对 | `scripts_project/s3_0_kh_check.py`（只报告） | `KH_TRANSPORT_CHAIN_CHECK.json` |
| 0.5 构建与冒烟 | `results_project/s3/`：两情景构建通过（Line 107 = 105 + 2），年度结构性缺口表（一体化 11 国全部有 CO₂ 去向；不互联 KH/LA/MM/SG/VN 缺口），56×3h 冒烟：一体化 HiGHS IPM "imprecise" → 报不可行，gap_diagnostic 最优且全部松弛为 0（求解精度问题，非物理缺口，报告 §1.5）；不互联真实不可行，gap_diagnostic CO₂ 缺口 KH 16.5 / LA 8.5 / MM 4.3 / SG 11.9 / VN 96.4 Mt；测试 371 通过 / 4 基线失败 | `evidence/s3_0/`（回执、结构表、测试日志）、`S3_0_SMOKE_CHECK.json`（`s3_0_smoke_check.py`） |

## 用户补充（2026-10-16，在 S3-7 与 S3_REPORT.md 中处理）

1. 进口价格年份：Zenodo 14872184 的到岸价是 2040 年假设，模型其余技术取 technology-data 2050。用 technology-data 2040 与 2050 两套数据比较进口供应链主要成本项（光伏、陆上风电、电解槽、氨合成、甲醇合成、FT、液氢储运）的降幅，估算 2040→2050 进口价格的可能降幅并说明偏差方向；若估算降幅超过 20%，把进口价格敏感性下限从 −20% 放宽到估算值并登记依据；主算仍用论文数据，不自行改价。
2. 一体化情景可行性确认：S3-7 冒烟中用独立方法确认一体化情景可行（HiGHS 开启 crossover / 单纯形法求同一 LP），并报告 LP 系数范围（矩阵、目标、右端项的最大/最小值之比）；若范围过大，指出造成的组件并提出缩放建议（PROPOSED，不自行修改）。

## 如果再次中断，从哪里开始

- 按上表第一个"进行中/待做"的子步骤继续；每步完成后提交并更新本表。
- S3-0 的构建/冒烟脚本：`/home/jin/run_s3_build.sh`（输出 `results_project/s3/STATUS.txt`，`DONE` 为结束标志）；测试：`/home/jin/run_s3_tests.sh`。
