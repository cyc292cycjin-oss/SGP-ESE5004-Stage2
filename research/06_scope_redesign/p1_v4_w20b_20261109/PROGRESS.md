# V4 W20b 进度（断点续做用；每个子步一行，最后一行是续做点）

- 指令：`V4_W20B_INSTRUCTION.md` v1，SHA256 `25f1db61db5e59914656ea24478311b3371f3b37e3b51dc35ff73f814b953e14`（与 `V4_W20B_SHA256.txt` 一致，开工前核对）。
- 会话：`claude-opus-5-5`，effort `xhigh`（会话元数据 `get_session self`）。
- 启动条件（2026-11-09 18:10 SGT 核查）：`list_sessions` 中无运行中的会话；Windows 上另有一个 Claude Code CLI 进程 4256，是桌面应用 17:59 启动时恢复的 W20 会话（`--resume=971cd140…`，`isRunning: false`，无子进程，空闲）——判为"已加载但空闲"，不是其他正在工作的会话；WSL 与 Windows 均无 Gurobi 进程；在线网卡只有 WLAN 与 WSL 虚拟网卡（无 AnyConnect），WSL 到令牌服务器 443 端口 TCP 连通；WSL 可用内存 9 GiB，`/` 剩余 711 GB。
- 分支 / worktree：`asean/v4-w20b-20261109` / `/home/jin/wt_v4_w20b`，自 `asean/v4-w20-20261109` 头 `b62ef3c0`（fetch 核过本地 = 远端）；W20 最后审阅包 `REVIEW_c477db3d.zip` 对应提交 `c477db3d` 是祖先，`c477db3d..b62ef3c0` 只改 `research/06_scope_redesign/p1_v4_w20_20261109/` 中 2 个文件（`PROGRESS.md`、`evidence/REVIEW_ZIP_MANIFEST_c477db3d.txt`），交付目录之外 0 个。
- 结果目录（计划）：`results_project/v4w20b/{nets56,solves}`（主 checkout，git 忽略）；草稿 `/home/jin/v4w20b`。
- 磁盘额度（5 GB）预估：W20 的 17 个求解目录合计 3.50 GB，本步 18 次约 3.9 GB + 网络约 0.38 GB + worktree 0.72 GB ≈ 5.0 GB，贴近上限。处理：每次求解的违例分析、C1 与判定完成后，对该次 `lp/`、`solution/`、`v5/kkt` 的 `.npy` 做 `gzip -1 -n`（先写原文件 SHA256 与大小清单，无损，可 `gunzip` 还原；W20 `minusBN` 实测 146 MB → 27 MB，< 1 s）。

| 子步 | 内容 | 状态 / 提交 |
|---|---|---|
| W20b-0 | SHA256、模型、启动条件；读先读材料（W20 `REPORT.md` 全文、`COALITION_BUILD.md`、`CORE_CHECK_V4_56.md`；W15 `BUNKER_ATTRIBUTION.md`；`m12_rhs_audit.py` 对偶形式与 `s4c_layers.py` 燃料舱结构）；分支与 worktree | 完成 |
| W20b-1a | `scripts_project/v4_coalition.py` 增加 `include_bunker="ports"`（`False`/`True` 路径不变）；`tests/research/test_v4_coalition_ports.py` 44 passed + W20 原测试 25 passed（`logs/tests_v4_coalition_w20b.txt`，2 分 8 秒，无求解调用）；第 2.3 条 x_{B,i}（`scripts/w20b_bunker_alloc.py`：重建 LP = 导出 LP，Σ_i x_{B,i} − x_B = 0.000 EUR，F1 与 F2 都通过；`BUNKER_PORT_ALLOCATION.csv`、`evidence/W20B_BUNKER_PORT_ALLOCATION.json`、`tables/W20B_BUNKER_LOADS.csv`） | 本提交 |

续做点：W20b-1b（在 W20b-1a 提交上构建 18 个网络、静态检查与零松弛门）。
