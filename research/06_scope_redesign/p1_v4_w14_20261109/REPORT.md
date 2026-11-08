# v4 W14：打包 v4 主算一对（F1 一体化、F2 `no_new_xb`）并准备 HPC 提交（台账 W14；决策清单第 213、215、216、221、222、223 项）

- **指令：** `work/p1_v4_w14_20261109/V4_W14_INSTRUCTION.md` v2，SHA256 `6cb103dbe8822cd48d1fa699ec947be2a682d371e14337b13dceed38597d2243`，与 `V4_W14_SHA256.txt` 一致（开工前核对）。先读材料已读（v3.1 包的指南、计划、定义文件、`pack_results.sh`、`preflight.sh`；D1 的 `hpc_v4/` 与定义草案；`HPC_RUNTIME_FACTS.md`、`BASELINE_V31.md` 第 0 节；D2b `REPORT.md`；D2c `REPORT.md` 与 `SMOKE56_D2C.md`；本指令第 0 节）。
- **执行：** Claude Code，模型 **Opus 5.5**（`claude-opus-5-5`，开工时确认，满足指令要求）；指令要求 effort Xhigh，会话的 effort 设定本会话看不到，不能自证（如实注明）。用户启动本指令即视为"审阅端已通过 D2c"。
- **性质：** 构建、打包与本机演练。**不连 HPC**（上传、预检、提交都由用户操作）；**不改模型代码、输入、配置与注册表**（`research/` 之外 0 个文件改动，本分支各提交逐一核对）；只新增打包与运行计划文件及 v4 包专用的 HPC 脚本。本机求解见第 3 节。不跳过 git hooks（未用 `--no-verify` / `core.hooksPath`），不合并 main，不 force-push。许可只经 `GRB_LICENSE_FILE` 传给求解进程，未复制、未打印、未入包。
- **标记：** VERIFIED / EXACT / INFERENCE / PROPOSED。数值在 `EVIDENCE.json` 与各表中。

## 0. 结论摘要

1. **包已就绪，可以上传（VERIFIED）：** `work/p1_v4_w14_20261109/hpc_package_v4/`。
   - **包的 `COMMIT`：`26c2e47d025fdd4e46cb278718d93aeddabbe984`**（W14-4c，打包前本分支最后一次提交；`research/` 之外与网络构建提交 `59b128ea`、D2c 头 `4e83d71e` 逐文件相同）。
   - **`SHA256SUMS` 的 SHA256：`9f97e221c05b7196531776c21a1ef2f0478338d3f14b70ffe5d817c9f40b98fd`**。
   - **文件数 41**（`SHA256SUMS` 登记 39 个 + `SHA256SUMS` + `HPC_PACKAGE_MANIFEST.json`）；**大小 251,432,422 字节**（约 240 MiB；1 MB/s 约 4 分钟，0.1 MB/s 约 42 分钟）。
   - 一致性检查 **44 / 44 `ALL_CONSISTENT`**；零松弛门通过；**许可类字符串扫描（`pack_results.sh` 同一正则）对整个包 0 个文件**；包在自己的副本上预检 `PREFLIGHT OK`。
2. **网络 SHA256（VERIFIED）：** F1 一体化 `86f6d6a0fce2f0e04d12ee7993aee885256fcaadadaeeca308414017738c801d`（82,749,911 字节）；F2 `no_new_xb` `24e835f74365f63f6dc2c848f81bb43727e082be6c34f2c3aca0594641b25187`（82,112,443 字节）；元数据开关集 `d89ccbf4…`、表目录 `research_inputs/industry_v4/out_ras`。W08–D2c 全部静态检查、D1 元数据一致性与零松弛门在 2920×3h 与 56 时段网络上通过；在包的 `COMMIT` 上重建逐字节相同。
3. **冒烟期望值（VERIFIED）：** 56 时段网络与 D2c 冒烟网络逐组件相同（只差元数据里的构建路径）→ **F1 363,190,038,821.0828、F2 376,143,650,003.4369 EUR**（含常数项；本机迭代 89 / 80）。
4. **本机演练（VERIFIED；求解器 2 / 2 次）：** 在包的解压副本中原样执行 `pbs/hpr4_smoke56.pbs`：**`SMOKE_RESULT:PASS`**，F1、F2 optimal、`ACCEPTED_LAYER2`，**与期望值相对差 0.000e+00**，后处理 0 错、批级 exit 0、`DONE`；提交脚本 dry-run **以 `DRY_RUN_OK` 结束，顺序 F1 → F2（`after:F1`）→ 批级（`afterany:F1:F2`）**；冒烟后的 dry-run **0 条 NOTE**；bash 5.3 与 Atlas 的 bash 4.2 结果相同；四种拒绝路径都 exit 2、什么都没启动。演练副本不在 work/ 下，未上传。
5. **登记（打包前提交 `0c94a7fb`）：** `RUN_PLAN_HPC_V4.md`（第 222 项登记值 REGISTERED）；**报警线** F1 ΔV ≥ +10,121.37 M（目标值 ≥ 315,173,866,702 EUR）、F2 ΔV ≥ +14,468.58 M（≥ 331,497,457,505 EUR）；**预测** B6 为正、最可能 11.8–13.0 bn，目标值 F1 336–339、F2 348–351 bn，Owen 9 国为正、BUNKER 大概率为正、TH 与 PH 不确定。
6. **操作指南：** `HPC_OPERATOR_GUIDE_V4.md`（中文，步骤 A–G，开头列出与 v3.1 指南的 17 项差异；dry-run 期望输出已由演练逐行核对）。
7. **下一步（用户操作）：** 按指南 A → G：上传到 `/hpctmp/$USER/hpr4`，`sha256sum -c`、登录预检，冒烟作业必须 PASS，登录欢迎信息无维护通知后正式提交。本步未连 HPC。

### 0.1 待决问题（需要审阅端 / 用户决定或确认）

1. **构建提交不是包的 `COMMIT`：** 指令要求"在包的代码提交上构建"；因定义文件要登记构建提交而它本身属于包的提交，构建只能在 `59b128ea` 上做（v3 先例）。已证明等价：三个提交 `research/` 之外逐文件相同，且在包的 `COMMIT` 上重建四个网络逐字节相同（`STATIC_CHECKS.md` 第 4 节）。请确认接受这一读法。
2. **代码包内的日志清洗标记表：** 解开代码包后，`scripts_project/s2_solve.py` 第 181 行（`LICENSE_MARKERS`，求解日志中要删去的词）匹配 `pack_results.sh` 的正则；它不含许可内容，v3.1 包里是同一文件。包级扫描（代码包为二进制）为 0；打包脚本按该行 SHA256 列入白名单，其余命中一律拒绝。第一次打包（`6d45a37b`）因此被拒、第二次（`12083cf5`）的打包脚本自身含该行原文，均改名留存、不上传。请确认这一处理。
3. **VN 退化对偶：** v3.1 解中 VN 生物质池为零余量池，F1 的报警线因此更弱（仍有效）；一阶 ΔB6 中约 +4.26 bn 是这一假象，未用于预测（`RUN_PLAN_HPC_V4.md` 第 8 节）。
4. **验收并集：** 按指令为 {A1_A2, A1_A2_S4B, A3, A3_S4B, B1, B3, B8}；v3.1 的 F4 曾出现 B15、B3_S4B 并被审阅端接受，若 v4 出现同类闸门，按并集规则应报审阅端。
5. **Owen 符号：** PH、TH 的符号预测不确定（平移估计 −0.65 / −0.06 bn）；56 时段与 2920 的分国受益在 v3.1 中就可相差数 bn。
6. **effort：** 指令要求 Xhigh，会话的 effort 设定本会话看不到，不能自证。
7. **指南中的旧编号：** `hpr_submit.sh` 的固定提示文字里 "step D1 / step D first" 是 HPR 指南的旧编号（对应本指南的 C1 / C），指南 B4 已注明；未改脚本（与 v3.1 包相同的文件）。

## 1. 分支（指令第 1 节）

| 项 | 值 |
|---|---|
| 分支 / worktree | `codex/v4-w14-20261109` / `/home/jin/wt_v4_w14` |
| 起点 | `4e83d71ed20010b87867d7889693d879fe11a4ab`（`codex/v4-d2c-20261109` 头；fetch 核过本地 = 远端） |
| D2c 审阅包对应提交 | `612d8f6b`（读自 D2c `PROGRESS.md` 与审阅包名 `REVIEW_612d8f6b.zip`）：**是头提交的祖先**；`612d8f6b..4e83d71e` 只改 `research/06_scope_redesign/p1_v4_d2c_20261109/` 下 2 个文件（`PROGRESS.md`、`evidence/REVIEW_ZIP_MANIFEST_612d8f6b.txt`），交付目录之外 0 个 |
| 提交 | 见 `PROGRESS.md`（W14-1 `59b128ea` = 网络构建提交；W14-2/3 `0c94a7fb` = 打包前的登记；W14-4 `6d45a37b`；W14-4b `12083cf5`；W14-4c = 包的代码提交） |

## 2. 网络（指令第 2 节；详见 `STATIC_CHECKS.md`）

- **构建（第 2.1 条，VERIFIED）：** 构建提交 `59b128ea`（W14-1），v4 主开关集（`--override demand.v4.enabled=true`，`no_new_xb` 由一体化派生）；F1 `86f6d6a0fce2f0e04d12ee7993aee885256fcaadadaeeca308414017738c801d`（82,749,911 字节）、F2 `24e835f74365f63f6dc2c848f81bb43727e082be6c34f2c3aca0594641b25187`（82,112,443 字节）；网络元数据记录开关集 SHA256 `d89ccbf47b0002e65246ce75ba06158f76c340f5091127f6658eec06ed727a62` 与表目录 `research_inputs/industry_v4/out_ras`。2920×3h 只构建网络，本机未构建全尺寸 LP。
- **为何构建提交不是包的提交、如何保证等价（如实说明）：** 定义文件必须登记网络 SHA256 与构建提交（`base-check` 核对回执的 `code_sha`），而定义文件属于包的代码提交，所以构建只能早于包的提交（v3 先例）。保证：(1) `research/` 之外三个提交逐文件相同；(2) 在包的 `COMMIT` `26c2e47d` 上于同一 worktree 路径重建，四个网络与构建提交逐字节相同（`STATIC_CHECKS.md` 第 4 节）。
- **静态检查（第 2.2 条，VERIFIED）：** W08 / D1 / D2a / D2b / D2c 各步的 C1–C12、D1 的开关集与网络元数据一致性（含 B12 配置哈希恒等）、零松弛门（705 / 589 行，无强制零余量行）与"无新的零余量池"在 2920×3h 与 56 时段网络上**全部通过**。
- **与 D2c 冒烟网络（第 2.3 条，VERIFIED）：** 两网两分辨率**数据逐值相同**，只有元数据中构建 worktree 路径（地热母线映射来源）与变体的基网 SHA256 不同；按 `--truncate 56` 同一规则截出的 56 时段网络逐组件相同 → **HPC 冒烟期望值取 D2c 冒烟目标值**（F1 363,190,038,821.0828、F2 376,143,650,003.4369 EUR）。第 3 节仍按授权跑了 2 次求解，以原样验证冒烟作业体。

## 3. 打包与本机演练（指令第 3 节；详见 `DRILL_REPORT.md`）

- **打包（第 3.1 条）：** `hpc_v4/make_hpc_package_v4.sh`（以 v3.1 打包脚本为模板）生成代码包 `code_26c2e47d.tar.gz`、`COMMIT`、两张 2920×3h 网络与构建 / 变体回执、成本表、`BATCH_DEF.json`（由 D1 草案更新：只含 F1、F2、批级 `afterany:F1:F2`、`smoke56`、`install`、`build_only_f1`；登记值见第 0 节；`limits_status: REGISTERED`）、`pbs/`（`hpr4_*`）、`hpc/`（HPR 脚本 + D1 的 `hpr_status.sh`）、运行器（D1 的 `run_batch4.sh`）、`env/`（与 v3.1 同一锁文件）、`preflight.sh`（含 D1 的开关集与网络元数据一致性检查）、`pack_results.sh`、`SHA256SUMS`、`HPC_PACKAGE_MANIFEST.json`、计划、指南、参照值。与 v3.1 包相比，只有 `run_batch4.sh`、`preflight.sh`、`hpc/hpr_status.sh` 三个脚本不同，其余脚本与环境文件逐字节相同。
- **三次打包（如实）：** `6d45a37b` 被打包脚本自己的"解包代码"扫描拒绝（日志清洗标记表）；`12083cf5` 全部通过，但打包脚本自身含该行原文，改为按 SHA256 比对后重打；**`26c2e47d` 为交付包**。前两次的文件夹改名留存（`hpc_package_v4_refused_6d45a37b`、`hpc_package_v4_superseded_12083cf5`，不入库、不上传）。
- **演练（第 3.2 条）：** 全部在交付包的解压副本中进行（`/home/jin/v4w14/`）：预检与登录预检、BUILD_ONLY、作业体 BUILD_ONLY、四种拒绝路径、提交 dry-run（`DRY_RUN_OK`，依赖顺序正确）、冒烟作业体（`SMOKE_RESULT:PASS`，相对差 0）、冒烟后 dry-run（0 NOTE）；bash 4.2 与 5.3 相同。

## 4. 运行计划与事前登记（指令第 4 节；`RUN_PLAN_HPC_V4.md`）

- **提交时点：** `RUN_PLAN_HPC_V4.md`、定义文件（REGISTERED）、报警线与预测在提交 `0c94a7fb`（W14-2/3）入库，早于任何打包与任何 HPC 提交；之后各提交未改其第 0–15 节的任何数值。
- **内容：** 目的与范围（第 0 节）；登记值（第 2、3、5、12 节）；验收（C1 (a)(b)(c) + GATES_V6 `ACCEPTED_LAYER2`，失败门在 v3.1 并集 {A1_A2, A1_A2_S4B, A3, A3_S4B, B1, B3, B8} 内，第 7 节）；**报警线**（第 8 节）；**预测**（第 9 节）；批级后处理（B6、Owen、与 v3.1 基线的对照，`REFERENCE_VALUES.json`）；结果回收（G1 中间导出、G2 结果包、60 天清除，第 10 节）。
- **报警线（第 214 项第⑤条；规则 EXACT，数值取 v3.1 2920×3h HPC 对偶；`scripts/w14_bounds_pre.py`）：** 脚本逐组件枚举 v3.1 与 v4 网络的全部差异，**未能归类的条数 0**。右端类（负荷、生物质池、固定容量、来水、燃气年度上限）用 v3.1 带符号对偶给下界；新增的终端核算母线用对偶延拓（新链路降低成本非负），新水库按 D2a 规则；成本类（树干代理价、LNG 加价）下界 0、一阶上界 F1 +1,681.03 M / F2 +2,106.55 M；系数类（逸散系数、甲醇化效率）只给一阶估计 +52.91 M / +44.76 M 并注明无界；常数项精确差 −3.92 M（v3.1 常数项在 2920 与 56 时段回执中相同）。**报警线：F1 ΔV ≥ +10,121.37 M（含常数项目标值 ≥ 315,173,866,702.07 EUR）；F2 ΔV ≥ +14,468.58 M（≥ 331,497,457,504.98 EUR）**；LP 值的报警线同时给出。须知：v3.1 解中 VN 生物质池为零余量池、对偶退化，F1 的下界因此更弱（仍有效）。
- **预测（INFERENCE，第 9 节）：** 目标值（含常数项）F1 最可能 336–339 bn（区间 325–350）、F2 348–351 bn（337–362）；**B6 为正，最可能 11.8–13.0 bn，区间 10.5–14.5 bn**；Owen 受益为正：BN、ID、KH、LA、MM、MY、SG、TL、VN，大概率为正：BUNKER，不确定：TH、PH；迭代 F1 210–260、F2 140–200；进程 2 峰值 RSS F1 105–130、F2 95–120 GiB；进程 2 用时 F1 8–20 h、F2 4–12 h。方法：v3.1 2920 实测 + 56 时段 v4−v3.1 实际差的平移与比例两种外推；一阶 ΔB6 中 VN 退化对偶的假象（约 +4.26 bn）已剔除。

## 5. 操作指南（指令第 5 节；`HPC_OPERATOR_GUIDE_V4.md`）

中文，按 v3.1 指南的步骤与格式；开头一张表列出与 v3.1 指南的全部差异（17 项）。步骤：**A** 本机核对（文件数、`COMMIT`、`limits_status`、`SHA256SUMS` 的哈希、无演练标记）与单路上传到 `/hpctmp/$USER/hpr4`（PowerShell，账号只在当前窗口用 `$HPC_USER` 变量）；**B** atlas8 上 `sha256sum -c`、工具与 `RUNDIRS` 核对、许可属性、登录预检（含 v4 元数据检查的期望行）、不提交演练（期望 3 行 qsub 与 2 条 NOTE）；**C** 冒烟提交与判读（期望值、相对差 ≤ 1e-6、`SMOKE_RESULT:PASS` 的全部判据）；**D** 正式提交（只在冒烟 PASS、登录欢迎信息无与约 4 天重叠的维护通知、再次演练 0 条 NOTE 之后）；**E** 监控（`hpr_status.sh` 同时显示含常数项目标值与 `objective_lp`、常数项、包 `COMMIT`；报警线）；**F** 回收（G1 中间导出、G2 结果包，`Get-FileHash` 核对）；**G** STOP / STOP_SAFE 的处理表（无 F3 / F4，`PREDECESSOR_NOT_ENDED` 不适用）。指南中没有任何账号、密码、主机连接串或许可内容；dry-run 期望输出按代码写出，并由第 3 节的演练逐行核对（`DRILL_REPORT.md`）。

## 6. 产出、额度与停止条件

- **产出（`work/p1_v4_w14_20261109/`）：** `hpc_package_v4/`（上传用，不入库）、`RUN_PLAN_HPC_V4.md`、`HPC_OPERATOR_GUIDE_V4.md`、`STATIC_CHECKS.md`（+ `STATIC_CHECKS.json`）、`DRILL_REPORT.md`、`REPORT.md`、`EVIDENCE.json`、`PROGRESS.md`、`LEDGER_ENTRY_DRAFT.md`（台账条目草稿；指令未指定台账分支）、`batch_def/`、`hpc_v4/`（打包脚本、v4 预检、参照值）、`evidence/`（报警线、网络差异、56 时段截取、零松弛、冒烟演练记录）、`tables/W14_BOUNDS_PRE.csv`、`logs/`、方法脚本 `scripts/`；审阅包 `REVIEW_<提交>.zip`（不入库，清单入 `evidence/`；含包的全部文本文件，两张网络与代码包只列 SHA256）。
- **额度：** 求解器 **2 / 2 次**（第 3 节冒烟演练；无重试、无参数改动、同一时刻至多 1 个 Gurobi 进程，求解前令牌服务器 TCP 预检通过）。本机计算约 1.6 小时（构建 3 次各约 1.7 分钟、静态与零松弛 1.3 分钟、报警线 0.6 分钟（第一次因经 /mnt/d 反复读块而中止、未产出结果）、打包 3 次各约 1.5 分钟、干跑 4 次各约 2.5 分钟、冒烟后 dry-run 2 次各数秒、冒烟演练 26 分钟），在 4 小时内。磁盘新增约 7.1 GB（`/home/jin/v4w14` 4.9 GB，主要是 5 个演练副本；worktree 0.72；`results_project/v4w14` 0.79；交付目录 0.72，含两份留存的旧包），在 10 GB 内。未下载任何文件。
- **未做的事：** 未连 HPC、未上传、未提交作业；未改模型代码、输入、配置与注册表；未跑全量测试（本步没有代码改动，`research/` 之外 0 个文件变化）；未合并 main、未 force-push、未跳过 git hooks。
- **停止条件逐项：** 指令 SHA256 一致；会话模型为 Opus 5.5；D2c 审阅提交 `612d8f6b` 是头提交的祖先且差异只在 D2c 交付目录；全部静态检查通过；演练 PASS、dry-run `DRY_RUN_OK`；包中许可类字符串 0（代码包内的日志清洗标记表见 0.1 第 2 条）；无需改模型代码、输入、配置或注册表；未连 HPC；未读、未打印、未复制许可内容（求解只经 `GRB_LICENSE_FILE`；演练的预检只核对许可文件的存在与权限，dry-run 用权限 600 的占位文件）。**均未触发。**
