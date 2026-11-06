### D1：第一批数据替换与 HPC 打包前的代码准备（台账 W13、W14；第 212、214、215 项；2026-11-07；草稿，待并入共享台账）

- **指令：** `work/p1_v4_d1_20261107/V4_D1_INSTRUCTION.md` v1（SHA256 `189bcfa5…f8a5`，与 `V4_D1_SHA256.txt` 核对一致）。实施；求解器 2 次（第 7 节授权的 56 时段冒烟），没有下载数据文件（只读网页文献），没有连 HPC，没有打包。
- **分支：** `codex/v4-d1-20261107`（从 `7aa356e4` = W08 头；`bd890bf9` 为祖先，二者之间只改了 W08 交付目录），worktree `/home/jin/wt_v4_d1`；交付 `research/06_scope_redesign/p1_v4_d1_20261107/` = `work/p1_v4_d1_20261107/`。提交见 `PROGRESS.md`；已推送，没有开 PR。
- **打包前改动（VERIFIED）：** 表目录按开关集命名（`out_<模式>` 只给主集，其余带开关集 SHA256 前 12 位；构建核对网络 = 表目录 = 配置）；`research.demand.v4.hvc_basis`（两种口径 = I2）；EV 系数用注册表未取整值 0.302147020…；v4 包运行器 / 状态脚本副本（包 `COMMIT` 进 `RUN.json` 与回执；同时显示含常数项目标值与 LP 值）；`BATCH_DEF_2920x3h_v4hpc.json` 草案（PROPOSED：72 h、walltime 96 h、`runs/batch6`）。
- **数据替换（VERIFIED / EXACT）：** `research.biomass.missing_cost_rule`：五国油棕树干池按注册表代理价 6.267 EUR/MWh（v3.1 = 0）；11 行违反物理的登记区间截到物理界（甲醇 / t CO₂ 主值高于化学计量 0.18 %，未改）；T03：MPOB 103 期的 15 % / 22 % 是全国烧掉比例且算法缺锅炉效率，不可用；文献 + 能量平衡（纤维 1.00、PKS 0.485）判定保留纤维 1.00、PKS 0.50（泰国 PKS 矛盾，交审阅），潜力逐字节不变，检查点 0 差；逐国表 `PALM_MILL_SELF_USE.csv` 与低 / 高区间（东盟潜力 +47.8 / −11.0 TWh）。注册表 2,390 → 2,402 行。
- **抽蓄（PROPOSED，网络不改）：** 模型存量 5,406 MW = 2050 年存量（含在建 Cisokan、Bac Ai），IHA 2024 在运 2,260 MW，TH +779、PH +127 MW 待核；东盟研究成本约为模型现用值的 1/3；`PHS_PROPOSAL.md`。
- **网络与冒烟（VERIFIED）：** `d40352b2…`（一体化）、`c11f5b65…`（`no_new_xb`），与 W08 网络只差 5 个树干 Store 成本；静态检查与零松弛门通过；登记 0 ≤ ΔV ≤ 1.4493 bn（`365c8d62`，求解前）；2 次 optimal、`ACCEPTED_LAYER2`，ΔV = +1.449348 / +1.449345 bn，在界内；B6（回归）−2,248 EUR。
- **交付：** `REPORT.md`、`PHYSICS_BOUNDS_FIX.csv`、`PALM_MILL_SELF_USE.csv`、`PALM_MILL_ENERGY_BALANCE.csv`、`PHS_PROPOSAL.md`、`SMOKE56_D1.md`、`CHECKPOINTS.csv`、`DOWNLOAD_CANDIDATES.csv`、`EVIDENCE.json`、`PROGRESS.md`、审阅包（逐成员 SHA256 + CRC32）。
- **待决：** `REPORT.md` 第 0.1 节 7 问（泰国 PKS、棕榈残余物热值口径 / 空果串潜力、缺数成本规则写法、物理界修正与甲醇主值、抽蓄存量对账与候选、HPC 定义草案、W08 注册表片段的哈希更新）。
