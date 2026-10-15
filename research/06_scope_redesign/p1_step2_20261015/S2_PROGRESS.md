# S2 进度记录（防中断用；每个子步骤提交后更新）

分支 `codex/s2-co2-biomass-demand-20261015`（自 D1 分支 `codex/d1-data-registry-20261015` @ 8f977156 开出）。
仓库 `cyc292cycjin-oss/SGP-ESE5004-Stage2`；WSL 路径 `/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model`。
求解环境：`/home/jin/miniforge3/envs/pypsa-earth/bin/python`，`PYTHONHASHSEED=0`，PyPSA 0.30.3 / linopy 0.5.5 / HiGHS 1.11（IPM）。

| 子步骤 | 状态 | 提交 | 说明 |
|---|---|---|---|
| S2-0 数据层补齐（补充指令 0.1–0.5） | 完成 | f0ad4070、f64e1fd0 | 报告 `S2_0_DATA_TOPUP.md`；registry 937 行；DATA_PENDING 98 → 22；13 项 D1 测试通过（f0ad4070 提交时有 1 项测试期望写错，f64e1fd0 修正） |
| S2-1 成本层切换 / SMR / 存量地热 / lvopt / gap_diagnostic | 完成 | 7a0d9060 | `scripts_project/s2_costs.py`（燃料价按第 33 项取 D1 登记的 WEO 2025 NZE 值覆盖 v0.15.0 燃料行；SMR 与地热取 AEO8 C 级；FT 投资按 EUR/kW_FT 处理）；`s2_layers.py` 中 `add_existing_geothermal`（186 MW，逐台在役判断）、`set_transmission_s2`（lvopt，2.79 倍为敏感性）、`add_gap_slack` |
| S2-2 CO₂ 捕集、运输、封存 | 完成 | 7a0d9060 | `s2_layers.add_co2_layer`：每节点 `co2 stored` 缓冲 + 每国 `co2 sequestered {ISO2}`（上限 = 潜力/50，8 国；LA/MM/SG 为 0 不建）；109 条 CO₂ 管道（19 条跨境受 `cross_border.co2` 控制）；CCGT CC、SMR CC、BECCS、工业生物质 CC、过程排放 CC、DAC（电供热）；钩子 `research_co2_storage_cap` |
| S2-3 生物质供给 | 完成 | 7a0d9060 | `add_biomass_layer`：每国 `solid biomass {c}` / `biogas {c}` 母线，107 个品类 Store（主算潜力，伐木残余 ZERO_BY_DECISION 不建）；用途：发电(+CC)、工业(+CC)、沼气提纯、BtL；删除 360 TWh 全区池配置 |
| S2-4 需求层 | 完成 | 7a0d9060 | `add_demand_layer`：D1 需求表 → 1,906 个 Load（归属表 `S2_DEMAND_OWNERSHIP.csv`）；EV/充电桩、Astar 交通用电扣除、铁路燃油计量（U2）、航空国内/国际（开关）、工业聚合载体（U1）、原料碳（PyPSA-Eur 口径，方法问题）、建筑炊事（第 23 项）、农业；航运推迟到 S3 |
| S2-5 工业低温热 | 完成 | 7a0d9060 | `add_industrial_heat`：97 个节点热母线，电锅炉/高温热泵/燃气锅炉/生物质锅炉(+CC) |
| S2-6 V5 门槛 | 完成 | 717ff6e0 | `v5/v5_gates.py`：新增 B2、B3、B8、B11；B12 接受 `S2_SECTOR_COUPLED_SMOKE` |
| S2-7 构建与冒烟 | 完成 | afbc4e8f | 两情景构建 + 静态校验；56×3h HiGHS 冒烟两情景不可行（原因定位，未放宽）；gap_diagnostic 两轮（第 2 轮最优）；结构性缺口表；测试 364 通过 / 4 基线失败 |
| 报告与交付 | 完成 | 本提交之后的最后一个提交 | `S2_REPORT.md`、`S2_EVIDENCE.json`、`S2_TEST_RUN.json`、`CLOUD_RESOURCE_ESTIMATE.md` §6、台账条目；draft PR 叠在 PR #22 上 |

## S2-7 结论（2026-10-15）

- 冒烟求解（`results_project/s2/smoke/*_run1_infeasible_postprocess_crash/`）：integrated、disconnected 均为 HiGHS IPM `Infeasible`；原后处理在静态负荷上崩溃（KeyError），已改为 `structural_diagnosis_s2`，事后诊断写入 `POSTHOC_STRUCTURAL_DIAGNOSIS.json`（不重跑）。
- 结构原因（不放宽约束，`results_project/s2/S2_STRUCTURAL_GAP_ANNUAL.json`）：
  1. 固定生物质终端需求 > 本国固体生物质潜力：SG 0.184 vs 0.030 TWh/a，VN 208 vs 125.8 TWh/a（两情景都不可行；第 36 项不建跨境生物质）。
  2. 无 CO₂ 去向：MM 既无封存潜力也无跨境管道（两情景）；LA、SG 在不互联情景下无封存潜力且跨境管道关闭。
  3. 封存上限不足（不互联）：KH 需 34.0 Mt/a vs 上限 1.7；VN 需 598 vs 236 Mt/a。
- gap_diagnostic 第 1 轮（`results_project/s2/gap_diagnostic_run1_infeasible_no_biomass_slack/`，仅电力 + CO₂ 松弛）不可行；第 2 轮网络 `results_project/s2/{integrated,disconnected}_gap2/` 加入每国 `gap slack biomass`，结果在 `results_project/s2/gap_diagnostic/`（两情景最优）。截断时域未缩放目标函数权重是诊断的已知局限（报告第 7.3 节，修正方案 PROPOSED）。

## 如果再次中断，从哪里开始

1. 全部子步骤已完成；若最后一个提交（报告与交付）不在 `git log` 中，重新 `git add` 报告文件并提交（文件清单见上表最后一行），然后 `git push` 并开 draft PR（`gh pr create --repo cyc292cycjin-oss/SGP-ESE5004-Stage2 --base codex/d1-data-registry-20261015 --draft`）。
2. 镜像交付文件到 `work/p1_step2_20261015/`（WSL 与 `D:\ResearchWorkspaces\ASEAN\work\p1_step2_20261015`）。
3. 之后停止，等待审阅；待用户决定的事项见 `S2_REPORT.md` 第 10 节。

## 提交说明

S2-1～S2-5 的代码在"逐子步提交"的补充说明到达之前已经一次写完（同一模块 `s2_layers.py`），因此作为一个提交登记；S2-6、S2-7 与报告分别提交。
