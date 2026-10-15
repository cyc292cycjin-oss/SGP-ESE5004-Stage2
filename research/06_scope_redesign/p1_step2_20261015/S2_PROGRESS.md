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

## 修正轮（补充指令 02，第 55–60 项）— 执行顺序 R3 → R1 → R2 → R5 → R6 → R4 → R7 → 构建与冒烟 — 已完成，报告 `S2B_REPORT.md`

| 节 | 内容 | 状态 | 提交 | 说明 |
|---|---|---|---|---|
| R3 | 需求分国分配改用 AEO8 ATS 人均×人口相对因子（第 57 项） | 完成 | bd6debcd | `d1_demand_2050.py`：`load_aeo8_country`，r_c = G_c/G_ASEAN（TL 用 GDP 相对因子）；主表 = AEO8 分配，`_GDP_SENSITIVITY` / `_POP_SENSITIVITY` 为敏感性；`DEMAND_2050_ALLOCATION_COMPARISON.csv` 为新旧对比；配置 `research.demand.country_allocation`；核对 Σ人均×人口 = 431.96 / 746.07 Mtoe vs AEO8 432.2 / 746.2 |
| R1 | 工业终端能源按 2050 工艺折算（第 55 项） | 完成 | cff39662 | `scripts_project/s2b_industry.py` → `demand_v5/INDUSTRY_2050_{PYPSA_EUR,SUMMARY}_{分配}.csv`、`INDUSTRY_2050_GAPS.csv`；钢铁（worldsteel + PyPSA-Eur 0.3/1.0 + technology-data EAF）、水泥（EDGAR 2.A.1/0.52 熟料 + technology-data 比率，窑炉燃料→甲烷）、其余子部门 2019 份额×乘数（PyPSA-Eur 比率待 JRC-IDEES，DATA_PENDING）；低温热行 = 0；生物质超潜力→甲烷；`carrier_mode: pypsa_eur_2050`（bas_fixed 对照）；工业电力显式负荷并从 Astar 扣除 |
| R2 | 化工原料碳属地口径（第 56 项） | 完成 | ab85b7ce | `scripts_project/s2b_feedstock.py` → `registry_v5/FEEDSTOCK_CARBON_TERRITORIAL_2050_{分配}.csv`：EDGAR 2.B+2.D × 乘数进过程母线；废塑料焚烧（What a Waste 3.0 × IPCC 表 2.4）→ 大气；出口与填埋不计；`feedstock_carbon_mode: territorial`（full_release 敏感性）；LA 塑料份额、KH/TH/VN 露天焚烧份额 DATA_PENDING |
| R5 | 跨境 CO₂ 与氢管道候选走廊（第 59 项） | 完成 | 09a517c7 | `s2_layers.pipeline_candidates`（PyPSA-Eur create_network_topology；大圆 × 1.25；走廊表海底份额）；上游氢管道 110 → 109 条候选，CO₂ 同拓扑；跨境 19 对；MM 无跨境电力走廊 → 数据缺口，国内 21 条 |
| R6 | DAC 用热（第 60 项） | 完成 | 182bce70 | DAC 第 4 端口 = 节点工业低温热母线（热 1.4、电 0.55 MWh/t；technology-data 第 938–942 行；PyPSA-Eur add_dac）；`dac_heat_mode: industry_heat_bus`（electric_cop1 敏感性） |
| R4 | 短时域时段权重（第 58 项） | 完成 | d337d986 | `s2_solve.set_representative_weights`：权重 8760/N，年度上限不缩放；B12 登记权重和/唯一值/SHA256 |
| R7 | 验收细节 | 完成 | 47ce2e15（+ 构建提交中的细化） | B11 只判有负荷母线（母线或一跳下游有 Load），辅助母线单列；A3/A5 把松弛×罚款计入已知项 |
| 构建与冒烟 | 两情景构建、结构性缺口表、HiGHS 56×3h（R4 权重）、gap_diagnostic、全部测试 | 完成 | 见 git log "构建与冒烟" | `results_project/s2b/`：构建通过（RSS 0.58 GiB）；冒烟两情景不可行（MM 等无 CO₂ 去向）；gap_diagnostic 两情景最优：一体化只剩 MM 5.13 Mt/a（过程 + 废塑料），不互联 VN 234.5 / KH 16.5 / SG 12.8 / LA 8.6 / MM 5.1 Mt/a；电力、生物质缺口 0；B11 细化后通过（重算文件）；测试 371 通过 / 4 基线失败 |
| 交付 | `S2B_REPORT.md`、`S2_EVIDENCE.json`（v2）、`S2B_TEST_RUN.json`、`CLOUD_RESOURCE_ESTIMATE.md` §7、台账 | 完成 | 最后一个提交 | 镜像到 `work/p1_step2_20261015/` |

## 如果再次中断，从哪里开始

- 修正轮全部完成。若最后两个提交（构建与冒烟、报告）不在 `git log` 中：重新 `git add` 对应文件并提交、`git push`，更新 PR #23 说明（`gh pr edit`），镜像交付文件；之后停止等待审阅。
- 待用户决定的事项见 `S2B_REPORT.md` 第 15 节（JRC-IDEES-2021 下载授权、MM 跨境走廊、R2 数据缺口、钢铁/水泥替代比率、KH 交通链等）。
