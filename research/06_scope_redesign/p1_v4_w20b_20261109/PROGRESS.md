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
| W20b-1a | `scripts_project/v4_coalition.py` 增加 `include_bunker="ports"`（`False`/`True` 路径不变）；`tests/research/test_v4_coalition_ports.py` 44 passed + W20 原测试 25 passed（`logs/tests_v4_coalition_w20b.txt`，2 分 8 秒，无求解调用）；第 2.3 条 x_{B,i}（`scripts/w20b_bunker_alloc.py`：重建 LP = 导出 LP，Σ_i x_{B,i} − x_B = 0.000 EUR，F1 与 F2 都通过；`BUNKER_PORT_ALLOCATION.csv`、`evidence/W20B_BUNKER_PORT_ALLOCATION.json`、`tables/W20B_BUNKER_LOADS.csv`） | 完成，`06c1ed1d` |
| W20b-1b | 在 `06c1ed1d`（干净工作树）上构建 18 个 56 时段网络（`scripts/w20b_build.sh`，`logs/build_nets56.txt`，1 分 19 秒，`results_project/v4w20b/nets56` 396 MB）；静态检查与零松弛门 18 / 18 通过（`scripts/w20b_static.py`，`evidence/STATIC_CHECKS_W20B.json`，`logs/static_w20b.txt`，3 分 14 秒）。**如实记录：** 静态检查第一次运行把 17 个按港口网络判为不通过——检查本身的错误：把燃料舱终端上游母线的"来源"只算发电机与流入链路，漏了节点–国家池双向链路（基网中 `oil pool KH2 0` 等，bus0 = 节点、`p_min_pu = −1`），且把被钩子固定为 0 的化石计量链路也算作供给；改为"不进账户的成员供给链路 + 来源含 Store 与双向链路"后重跑，18 / 18 通过；网络未改动 | 完成，`98bdff71` |
| W20b-2 | 求解前登记：`CORE_CHECK_V4_56_BUNKER.md` 第 1 节、`evidence/W20B_XS_PRE.json`、`tables/W20B_XS_PRE.csv`（11 国合并份额之和 − 目标值 = −4,519.48 EUR，通过）；运行器 `scripts/w20b_solve.sh`（守卫同 W20，另加数组无损压缩 `scripts/w20b_pack.sh`——假目录自测 5 / 5 OK、还原逐字节相同——与 4.0 GB 磁盘守卫）、判定 `scripts/w20b_eval.py`（干跑：网络 SHA 不符 → NO_RESULT；数值路径正确）、登记表生成 `scripts/w20b_regtable.py`、x^m(S) `scripts/w20b_xs.py` | 完成，`bbff7550`（任何 W20b 求解之前，已推送） |

| W20b-3 | 登记提交已推送（远端头 `bbff7550`）。2026-11-09 10:47:03–13:35:33 UTC `scripts/w20b_solve.sh --confirmed 2026-11-09T10:47Z`（后台，退出码 0，`DONE calls=18`）。**18 / 18 optimal**，C1 18 / 18 通过，`B1_BUNKERS` 17 / 17 通过，压缩 18 / 18 OK，间隔 330–334 s，无重试。R0：D = +3.7879 bn（STRICT）；17 个合并联盟 16 STRICT + 去 MM WITHIN（−0.0197 bn，阈值 3.606 bn），无违反，未触发停止 | 完成 |
| W20b-4 | 汇编 `scripts/w20b_compile.py`（第一次运行 `AttributeError`：回执 `gates` 的值是布尔量；改从 `BUNKER_ACCOUNT.json` 读账户门并加 `receipt_gates_false` 列后重跑，只读）→ `CORE_CHECK_V4_56_BUNKER.csv`、`CHECKPOINTS.csv`、`EVIDENCE.json`；`scripts/w20b_tables.py` → 第 2 节表格与 `tables/W20B_DS_DECOMPOSITION.csv`（恒等式残差 ≤ 1e-4 EUR）；`CORE_CHECK_V4_56_BUNKER.md` 第 2 节（第 1 节前 16,883 字节 SHA256 `306f31d2…` = 登记提交）；`REPORT.md`；`LEDGER_ENTRY_DRAFT.md`。**额度：** 求解 18 / 18；本机计算约 1.7 小时（求解进程 4,412 s、每次后处理合计 650 s、测试 128 s、构建 79 s、静态检查约 194 s × 2、x_{B,i} 39 s、其余脚本数分钟）≤ 2.5 小时；批次墙钟 2 h 48.5 min（含 17 个强制间隔 5,635 s，后处理计在间隔内）；磁盘新增约 3.23 GB（`results_project/v4w20b` 2.50 GB、worktree 0.72 GB、草稿与交付约 1 MB）≤ 5 GB | 本提交 |

续做点：W20b-4 之后只剩审阅包（`scripts/w20b_review_zip.py <本提交>`，zip 不入库，清单 `evidence/REVIEW_ZIP_MANIFEST_<提交8位>.txt` 在下一个提交入库）与推送核对（`git ls-remote`）。
