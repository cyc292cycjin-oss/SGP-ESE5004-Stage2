# DFX v3 第 0 节：暂停会话（v1 指令）遗留的检查与隔离

检查时间：2026-10-26 21:35–21:50 SGT（WSL `date`）。本指令（v3，SHA256 `b60da4c6…5a6df`）的执行者只检查、记录，不沿用、不删除、不改名暂停会话留下的任何东西。

## 1. 分支与 worktree

| 项 | 结果 |
|---|---|
| `git branch -a \| grep dfx` | 只有 `codex/dfx-20261026`（本地分支，未推送：远端无同名分支；`+` 表示已被 worktree 检出） |
| `git worktree list` | `/home/jin/wt_dfx_20261026  b0dbd52c [codex/dfx-20261026]` |
| 该分支的提交 | 1 个：`b0dbd52c` "DFX-0 rules registered before any v2 build (no cloud, no solve): DFX_RULES.md, progress file, instruction copy"（2026-10-26 21:24:32 +0800），父提交 = `55ab07c0`（B4P 头）；改动 7 个文件 / +392 行，全部在 `research/06_scope_redesign/p1_dfx_20261026/`（v1 指令副本与 SHA、DFX_PROGRESS.md、DFX_RULES.md、scripts/commit.sh、scripts/probe_sources.py、scripts/ras_prototype.py）；**未改 `scripts_project/`、`research_inputs/`、`configs/`、`tests/`** |
| 该 worktree 工作树 | `git status --short` 为空（干净，无未跟踪文件） |

## 2. 目录与文件

| 位置 | 结果 |
|---|---|
| 主检出 `results_project/` | 没有 `dfx` 相关目录或文件（`ls results_project \| grep -i dfx` 为空） |
| `/home/jin/` | `/home/jin/dfx/`（21:22 最后修改）：`commit.sh`（提交辅助）、`msg_0.txt`（b0dbd52c 的提交信息）、`probe_sources.py`（只读探查：IDEES / USGS / 配置 SHA）、`ras_prototype.py`（只读 RAS 原型）；`/home/jin/wt_dfx_20261026/`（worktree） |
| 其它 | 无 `/home/jin/*dfx*` 之外的遗留 |

## 3. 进程

`ps -eo pid,ppid,etime,cmd | grep -E "dfx|s2_network|gurobi|s2_solve|pytest|python"`：只有系统进程（networkd-dispatcher、unattended-upgrades）和 conda shell hook，etime 均为 1 s——WSL 实例在本次检查前已被重启，暂停会话的进程（若曾有）已不存在。**没有需要终止的进程，也没有归属不明的进程。**

## 4. Gurobi 调用

- `/home/jin/dfx/`、`/home/jin/wt_dfx_20261026/` 下没有 `gurobi*.log`；主检出 `results_project/` 下 2026-10-26 20:50 之后没有新文件；
- 暂停会话的提交信息写明 "no cloud, no solve"，其脚本均为只读探查；
- 结论：**暂停会话没有调用过 Gurobi（本机 0 次）**；本指令第一次调用前无需等待间隔（最近一次本机 Gurobi 会话是 B4P 2026-10-26 05:xx SGT 的截短探针，间隔远超 5 分钟）。

## 5. 处理

- 不沿用 `b0dbd52c` 的任何内容（规则、原型脚本、进度文件），本指令的规则与数值全部重新核实、重新写入；
- 分支 `codex/dfx-20261026`、worktree `/home/jin/wt_dfx_20261026`、目录 `/home/jin/dfx/` 原样保留；
- 本指令使用新分支 `codex/dfx-v3-20261026`、新 worktree `/home/jin/wt_dfx_v3_20261026`（从 `codex/b4-prep-20261026` 本地头 `55ab07c0` 建立），中间结果写到主检出 `results_project/dfx_v3/`，辅助脚本在 `/home/jin/dfx3/`（镜像到本目录 `scripts/wsl_dfx3/`）。

## 6. 基分支核对（第 2 节"分支"）

- `codex/b4-prep-20261026` 本地头 `55ab07c0`（= `f806e3e7` + 只含报告 / 证据 / 进度的交付提交）；`git ls-remote origin` 在检查时无法连接 GitHub（443 端口超时），远端头待推送时再核对；
- `git diff --name-only ec80668f 55ab07c0 -- scripts_project research_inputs configs`：11 个文件，全部与需求构建无关：`b4_batch4.py`、`b4_split_solve.py`、`m08a_run_batch.sh`、`m08a_variants.py`（成本表路径记法）、`m10_batch3_summary.py`、`m10r_synthetic_solution.py`、`m12_allocation.py`、`m12_rhs_audit.py`、`s2_solve.py`（分进程求解）、`s4d_ledger.py`、`s4d_ledger_redo.py`（账本修正）；`research_inputs/`、`configs/` 无差异；`ec80668f` 是 `55ab07c0` 的祖先（merge-base = ec80668f）。核对通过。
