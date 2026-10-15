# S2 进度记录（防中断用；每个子步骤提交后更新）

分支 `codex/s2-co2-biomass-demand-20261015`（自 D1 分支 `codex/d1-data-registry-20261015` @ 8f977156 开出）；draft PR #23。
仓库 `cyc292cycjin-oss/SGP-ESE5004-Stage2`；WSL 路径 `/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model`。
求解环境：`/home/jin/miniforge3/envs/pypsa-earth/bin/python`，`PYTHONHASHSEED=0`，PyPSA 0.30.3 / linopy 0.5.5 / HiGHS 1.11（IPM）。

## 第一轮（S2 主指令 + 补充指令 01）— 已完成，报告 `S2_REPORT.md`

| 子步骤 | 状态 | 提交 |
|---|---|---|
| S2-0 数据层补齐 | 完成 | f0ad4070、f64e1fd0 |
| S2-1～S2-5 模型层 | 完成 | 7a0d9060 |
| S2-6 V5 门槛 | 完成 | 717ff6e0 |
| S2-7 构建与冒烟（两情景不可行，原因已定位） | 完成 | afbc4e8f |
| 报告与交付 | 完成 | df651acc |

## 修正轮（补充指令 02，第 55–60 项）— 执行顺序 R3 → R1 → R2 → R5 → R6 → R4 → R7 → 构建与冒烟

| 节 | 内容 | 状态 | 提交 | 说明 |
|---|---|---|---|---|
| R3 | 需求分国分配改用 AEO8 ATS 人均×人口相对因子（第 57 项） | 完成 | 见 git log "R3" | `d1_demand_2050.py`：`load_aeo8_country`，r_c = G_c/G_ASEAN（TL 用 GDP 相对因子）；主表 = AEO8 分配，`_GDP_SENSITIVITY` / `_POP_SENSITIVITY` 为敏感性；`DEMAND_2050_ALLOCATION_COMPARISON.csv` 为新旧对比；配置 `research.demand.country_allocation`（s2_network 按它选表）；核对 Σ人均×人口 = 431.96 / 746.07 Mtoe vs AEO8 432.2 / 746.2；过程排放表与登记表已重算（972 行）；测试 16 项通过 |
| R1 | 工业终端能源按 2050 工艺折算（第 55 项） | 完成 | 见 git log "R1" | `scripts_project/s2b_industry.py` → `research_inputs/demand_v5/INDUSTRY_2050_{PYPSA_EUR,SUMMARY}_{分配}.csv`、`INDUSTRY_2050_GAPS.csv`；钢铁（worldsteel + PyPSA-Eur 0.3/1.0 + technology-data EAF）、水泥（EDGAR 2.A.1/0.52 熟料 + technology-data 比率，窑炉燃料→甲烷）、其余子部门 2019 份额×乘数（PyPSA-Eur 比率待 JRC-IDEES，DATA_PENDING）；低温热行 = 0；生物质超潜力→甲烷（需求层内按实际绑定量计算）；`research.s2.industry.carrier_mode: pypsa_eur_2050`（bas_fixed 对照）；工业电力显式负荷并从 Astar 扣除；试构建通过（Load 1,985） |
| R2 | 化工原料碳属地口径（第 56 项） | 完成 | 见 git log "R2" | `scripts_project/s2b_feedstock.py` → `registry_v5/FEEDSTOCK_CARBON_TERRITORIAL_2050_{分配}.csv`：EDGAR 2.B+2.D × 工业乘数进过程排放母线（可被过程 CC 捕集）；本国废塑料焚烧 = What a Waste 3.0 2050 垃圾量 × 塑料份额 × （焚烧 + 未收集×露天焚烧）× IPCC 表 2.4（C 75%、化石 100%）→ 大气（新建 plastic waste 源 + 释放 Link，不建能量回收）；出口与填埋不计；`feedstock_carbon_mode: territorial`（full_release 为敏感性）；LA 塑料份额、KH/TH/VN 露天焚烧份额 DATA_PENDING；试构建通过 |
| R5 | 跨境 CO₂ 与氢管道候选走廊（第 59 项） | 待做 | — | |
| R6 | DAC 用热（第 60 项） | 待做 | — | |
| R4 | 短时域时段权重（第 58 项） | 待做 | — | |
| R7 | 验收细节（B11 只查有负荷节点；A3/A5 对账已知项） | 待做 | — | |
| 构建与冒烟 | 两情景构建、结构性缺口表、HiGHS 56×3h（R4 权重）、必要时 gap_diagnostic、全部测试 | 待做 | — | |
| 交付 | `S2B_REPORT.md`、更新 `S2_EVIDENCE.json`、`S2_PROGRESS.md`、`CLOUD_RESOURCE_ESTIMATE.md` | 待做 | — | |

## 如果再次中断，从哪里开始

- 按上表第一个"待做"的节继续；每节完成后提交并更新本表。
- R1 的前置事实：PyPSA-Eur v2025.07.0 的 `build_industry_sector_ratios.py` 依赖 JRC-IDEES-2021（本地没有，未授权下载），钢铁/水泥用 technology-data v0.15.0 的工艺行替代 IDEES 部分并逐行引用；其余子部门按 2019 载体份额 × 乘数并标 DATA_PENDING（见 S2B 报告）。
- 新来源文件已复制到 `research_inputs/registry_v5/sources/`：`AEO8_2050_BY_COUNTRY.csv`、`WORLDSTEEL_2019_ASEAN.csv/.md`、`SHA256SUMS_raw7.txt`、`pypsa_eur_v2025.07.0_{build_industry_sector_ratios,build_industry_sector_ratios_intermediate,prepare_sector_network}.py`、`IPCC2006_V3_Ch2_Mineral_Industry.pdf`。
