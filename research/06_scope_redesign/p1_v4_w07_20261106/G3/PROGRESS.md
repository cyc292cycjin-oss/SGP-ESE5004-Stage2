# G3 进度（v4 W07，B-G3：泰国 TH、菲律宾 PH、新加坡 SG）

- 指令：`../V4_W07_INSTRUCTION.md` v1，SHA256 `20d03b692f1d32733f34b04d85c01fb3df1345f95f366a6bf25de36ac7ec7baf`，与 `../V4_W07_SHA256.txt` 一致（2026-11-06 核对）。
- 分支：`codex/v4-w07-g3-20261106`，起点 `07e08f38`（`codex/v4-data-20261105` 头，本地与远端一致）；worktree `/home/jin/wt_v4_g3`；临时副本 `/home/jin/v4w07_g3/`（数据链副本 `chain/`，情形缓存 `scenario_cache/`）。
- 交付目录：`work/p1_v4_w07_20261106/G3/` = 仓库 `research/06_scope_redesign/p1_v4_w07_20261106/G3/`。

## 步骤

| 步 | 内容 | 状态 | 提交 |
|---|---|---|---|
| 0 | SHA 核对、读 A 部分与 A2 必读文件、建分支与 worktree | 完成 | — |
| 1 | 临时副本复现 TH / PH / SG 行（4 个 s3_0 输出逐字节相同；v3"其他"偏差 ≤ 4e-9 MWh） | 完成 | — |
| A | SDMX 查询与登记、热值（`g3_ncv.py`）、自备电厂（`g3_captive.py`） | 完成 | `88d36cf3` |
| B | 产品与节点（`g3_products.py`）、生物质（`g3_biomass.py`） | 完成 | `7dfaf728` |
| C | 链量化（`g3_chain.py`：两条热值线逐步累加、单步、可加性、敏感性） | 完成 | `0250f5b7` |
| D | 报告、决策、缺数、证据、台账草稿 | 完成 | 见最后一行 |
| E | 审阅包成员清单、本文件最后一行、推送 | 完成 | 见最后一行 |

## 运行环境说明

- 2026-11-06 02:16–02:45 SGT 之间 WSL 多次报 `Wsl/Service/E_UNEXPECTED`，Ubuntu 实例被重启（内核未重启，systemd 重新启动），tmux 中的后台进程随之消失。对策：`g3_chain.py` 每个情形算完即存盘（键含全部输入与脚本的 SHA256，不会复用过期结果），由 Windows 侧重试循环在 WSL 可用时续跑；每次续跑仍先做逐字节复现。
- 额度：求解器 0 次；本机计算约 10 分钟；新增磁盘约 0.11 GB。

## 恢复点

全部完成，等待审阅端审阅。若需重算：在 WSL 中依次运行 `scripts/g3_ncv.py`、`g3_captive.py`、`g3_products.py`、`g3_biomass.py`、`g3_chain.py`、`g3_summary.py`（`g3_sdmx.py` 不会覆盖已存的 SDMX 响应；`g3_usgs_text.py` 用 Windows 解释器）。
