# S4F 进度记录（防中断用；每个子步骤提交后更新）

指令 `S4F_CLAUDE_CODE_INSTRUCTION.md`（v1，2026-10-17 14:50 SGT），开始前核对 SHA256 = `28d7458d47e282df6aaf5fa324e3772b886a67f9b178dd728696c5eac7216f03`，与 `S4F_INSTRUCTION_SHA256.txt` 一致（2026-10-17，VERIFIED）。模型 Opus 5.5。所有过程说明一律用中文。

- **分支：** `codex/s4f-extension-caps-20261017`，自 S4E 最终提交 bcda8001 开出（已核实 = PR #29 的 headRefOid `bcda8001456618a1cc9eb863ccbdb49ff41a59e1`）；draft PR 叠在 #29 上（基分支 `codex/s4e-corridors-storage-20261017`）。
- **仓库：** `cyc292cycjin-oss/SGP-ESE5004-Stage2`；WSL 路径 `/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model`；交付目录 `research/06_scope_redesign/p1_step4f_20261017/`，镜像 `D:\ResearchWorkspaces\ASEAN\work\p1_step4f_20261017\`。
- **求解：** Gurobi `formal_barrier`（档案 A）；止损：56×3h 单次 30 分钟，非最优即停、不重试。
- **资源（第 7 条）：** 本步不需要任何下载；若认为必须下载，先报告。适用工作原则第 3、6、7、8 条。
- **停止条件：**
  - PyPSA-Eur v2025.07.0 配置中找不到 `lines.max_extension` / `links.max_extension`；
  - TH–MY 存量依据无法按指令处理；
  - `tests/transport` 的失败涉及实际逻辑错误。

## 子步骤状态

| 节 | 内容 | 状态 | 提交 | 说明 |
|---|---|---|---|---|
| S4F-0 | 准备：§7 答复登记 | 完成 | 见提交记录 | 注册表片段 `s4f_0`（7 行）；`tests/research` 488 通过 / 0 失败 |
| S4F-1 | 单条输电扩建上限（第 96 项） | 完成 | 见提交记录 | 开关 `research.network.max_extension`：`pypsa_eur`（主算）/ `none` / `apg_plans`。`lines.max_extension` = 20,000 MW 同时作用于交流线与 DC 链路（新增量口径），`links.max_extension` 不使用（用户同意）；管道不设上限，与 PyPSA-Eur 相同。`none` 构建与 S4E 一体化网络逐组件一致；主算构建只有 `s_nom_max` / `p_nom_max` 不同。`apg_plans` 为 18 个 APG 分组上限，钩子 `research_apg_corridor_cap`，只构建核对。S4E 冒烟超限：一体化 22 个（405.6 GW）、不互联 16 个（555.3 GW）、NZE 20 个（367.8 GW） |
| S4F-2 | S4E 其余事项（第 97 项） | 完成 | 见提交记录 | (a) 停止 01 → 用户方案 1：线路 91 = 80 MW（C 级），Khlong Ngae–Gurun 300（AIMS），删除 4 条 OSM 250878579 重复记录，TH–MY 合计 380 MW；开关 `research.network.th_my_stock`（`apg_aims` / `frozen_base`）。作者 readjust 清单 19 条线（只记录）。(b) #4 印尼端为 ID_Sumatra3 3：432.2 km，海底份额 0.236，DC。(c) 老挝进越南封存 6 条 `CO2 transit rail`，陆运段 9.66–24.57 EUR/t，贸易类。(d) SG–VN、SG–KH 开关 `optional_sg_vn_kh`，构建核对。(g) `tests/transport` 改为在 pytest 下可运行。`tests/research` 499 通过，整个 `tests/` 516 通过 |
| S4F-3 | 冒烟 | 完成 | 见提交记录 | 代码 d9bc8012，档案 A，三项全部最优。目标值较 S4E 高 1.4–2.4 %。B5、B6（541.3 亿，7.8 %）、B16 通过，三项 `all_passed_solver_tolerances`。触及上限的组件：一体化 11 个、不互联 6 个；新走廊合计 263 GW（S4E 301），单条最大 20 GW。不互联中老挝进越南封存 7.5 Mt；越南封存用满（236 Mt） |
| S4F-4 | 云端部署包 | 完成 | 见提交记录 | 在 7e09744d 上重建四个网络，与冒烟网络逐组件一致；包 232,095,769 B、15 个文件；预检下限 36 / 72 / 104 GiB 不变；资源估算 §15（365×24h 单运行 34–67 min，悲观 98 min）；部署步骤 §10 第二批 7 项、§11 联盟规则；许可扫描无新增命中；`tests/research` 499、整个 `tests/` 516 通过 |
| S4F-5 | 上云前清单与交付 | 未开始 | — | |

## 提交记录（分支 `codex/s4f-extension-caps-20261017`）

| 提交 | 内容 |
|---|---|
| （S4F-0 提交） | S4F-0：§7 答复登记 |

## 续行点

- **停止 01（2026-10-17 09:44 UTC）：** 线路 91 不是 Sadao–Chuping，见 `S4F_STOP_01_LINE91.md`。用户已答复方案 1，停止解除。
- **S4F-0 至 S4F-3 已完成。** 下一步 S4F-4：
  - 外推（`/home/jin/s4f4_extrap.sh`）；
  - 预检下限，资源估算 §15；
  - 在最终代码提交上重建四个网络并打包（`/home/jin/s4f4_build.sh`）。
- **之后：** S4F-5 上云前清单与交付（报告、证据、审阅 ZIP）。

## S4F-1 前置核查（PyPSA-Eur v2025.07.0，本地已入库副本，VERIFIED）

- **配置：** `research_inputs/registry_v5/sources/pypsa_eur_v2025.07.0_config.default.yaml`（SHA256 bfbe9160…）。
  - 第 324 行 `lines.max_extension: 20000 #MW`；
  - 第 340 行 `links.max_extension: 30000 #MW`；
  - 同段另有 `lines.s_nom_max: .inf`、`links.p_nom_max: .inf`。
  - 两个键都在，不触发停止条件。
- **代码：** `research_inputs/registry_v5/sources/pypsa_eur_v2025.07.0_prepare_sector_network.py`（SHA256 612c4a0c…）。
  - 第 6415–6417 行：`maxext = snakemake.params["lines"]["max_extension"]`，非 None 时调用 `limit_individual_line_extension(n, maxext)`。
  - 第 5573–5577 行：`n.lines["s_nom_max"] = n.lines["s_nom"] + maxext`；对 `carrier == "DC"` 的链路设 `p_nom_max = p_nom + maxext`。
  - 口径：是新增量（存量 + 上限），不是总量；作用于全部交流线和全部 `DC` 链路，不含 B2B 与管道。
  - 部门耦合流程中，直流链路用的也是 `lines.max_extension`（20,000 MW）；`links.max_extension` 在 `prepare_sector_network.py` 中没有被读取。
- **管道：** PyPSA-Eur 中新建氢管道（`H2 pipeline`）、CO₂ 管道（`CO2 pipeline`）、新建气管道（`gas pipeline new`）都没有单条上限。
  - 已有气管道：开 `H2_retrofit` 时 `p_nom_max = p_nom`，可退役不可扩建；否则不可扩建。
  - 氢改造管道：`p_nom_max = p_nom × H2_retrofit_capacity_per_CH4`，这是改造量上限，不是扩建上限。

## 对 S4E 报告 §7 的答复（用户已确认，指令原文摘要）

1. 新候选走廊容量：主算采用 PyPSA-Eur 单条扩建上限（第 96 项）；APG / AIMS 规划容量上限作保守敏感性。
2. TH–MY 存量：删去 4 条疑似重复的直流链路，总存量对齐 APG 380 MW（第 97 项 a）。
3. APG #4 印尼端点改为 ID_Sumatra3 3（北干巴鲁）（第 97 项 b）。
4. 联盟研究范围：交付后与第 14 项一并请师哥判断（第 97 项 f），本步不做。
5. 老挝经过境进入越南国内封存：允许（第 97 项 c）。
6. SG–VN、SG–KH：不进主算，列入第二批敏感性（第 97 项 d）。
7. PH 互联价值为负与走廊效果分离：不占用首批云端运行；正式结果后用分国账本明细分析，必要时列入第二批（第 97 项 e）。

## 用户中途指示

（暂无）
