# v4 W14：打包 v4 主算一对（F1 一体化、F2 `no_new_xb`）并准备 HPC 提交（台账 W14；决策清单第 213、215、216、221、222、223 项）

- **指令：** `work/p1_v4_w14_20261109/V4_W14_INSTRUCTION.md` v2，SHA256 `6cb103dbe8822cd48d1fa699ec947be2a682d371e14337b13dceed38597d2243`，与 `V4_W14_SHA256.txt` 一致（开工前核对）。先读材料已读（v3.1 包的指南、计划、定义文件、`pack_results.sh`、`preflight.sh`；D1 的 `hpc_v4/` 与定义草案；`HPC_RUNTIME_FACTS.md`、`BASELINE_V31.md` 第 0 节；D2b `REPORT.md`；D2c `REPORT.md` 与 `SMOKE56_D2C.md`；本指令第 0 节）。
- **执行：** Claude Code，模型 **Opus 5.5**（`claude-opus-5-5`，开工时确认，满足指令要求）；指令要求 effort Xhigh，会话的 effort 设定本会话看不到，不能自证（如实注明）。用户启动本指令即视为"审阅端已通过 D2c"。
- **性质：** 构建、打包与本机演练。**不连 HPC**（上传、预检、提交都由用户操作）；**不改模型代码、输入、配置与注册表**（`research/` 之外 0 个文件改动，本分支各提交逐一核对）；只新增打包与运行计划文件及 v4 包专用的 HPC 脚本。本机求解见第 3 节。不跳过 git hooks（未用 `--no-verify` / `core.hooksPath`），不合并 main，不 force-push。许可只经 `GRB_LICENSE_FILE` 传给求解进程，未复制、未打印、未入包。
- **标记：** VERIFIED / EXACT / INFERENCE / PROPOSED。数值在 `EVIDENCE.json` 与各表中。

## 0. 结论摘要

（打包与演练完成后填写。）

## 1. 分支（指令第 1 节）

| 项 | 值 |
|---|---|
| 分支 / worktree | `codex/v4-w14-20261109` / `/home/jin/wt_v4_w14` |
| 起点 | `4e83d71ed20010b87867d7889693d879fe11a4ab`（`codex/v4-d2c-20261109` 头；fetch 核过本地 = 远端） |
| D2c 审阅包对应提交 | `612d8f6b`（读自 D2c `PROGRESS.md` 与审阅包名 `REVIEW_612d8f6b.zip`）：**是头提交的祖先**；`612d8f6b..4e83d71e` 只改 `research/06_scope_redesign/p1_v4_d2c_20261109/` 下 2 个文件（`PROGRESS.md`、`evidence/REVIEW_ZIP_MANIFEST_612d8f6b.txt`），交付目录之外 0 个 |
| 提交 | 见 `PROGRESS.md`（W14-1 `59b128ea` = 网络构建提交；W14-2/3 `0c94a7fb` = 打包前的登记；W14-4 `6d45a37b`；W14-4b `12083cf5`；W14-4c = 包的代码提交） |

## 2. 网络（指令第 2 节；详见 `STATIC_CHECKS.md`）

## 3. 打包与本机演练（指令第 3 节；详见 `DRILL_REPORT.md`）

## 4. 运行计划与事前登记（指令第 4 节；`RUN_PLAN_HPC_V4.md`）

## 5. 操作指南（指令第 5 节；`HPC_OPERATOR_GUIDE_V4.md`）

## 6. 产出、额度与停止条件
