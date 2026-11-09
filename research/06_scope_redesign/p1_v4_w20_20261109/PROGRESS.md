# V4 W20 进度（断点续做用；每个子步一行，最后一行是续做点）

- 指令：`V4_W20_INSTRUCTION.md` v1，SHA256 `f4419a8347be3fa00cd7fec8e8fd508a2999dc91b56ee47304b5236f62a6f97b`（与 `V4_W20_SHA256.txt` 一致，开工前核对）。
- 会话：`claude-opus-5-5`，effort `xhigh`（会话元数据）；启动条件：W19a 会话已停止、本机无其他运行中的 Claude Code 会话、WSL 无 Gurobi 进程、可用内存 9 GiB。
- 分支 / worktree：`asean/v4-w20-20261109` / `/home/jin/wt_v4_w20`（自 `asean/v4-w14-20261109` 头 `ac75354c`，fetch 核过本地 = 远端；`26c2e47d` 是祖先，`26c2e47d..ac75354c` 只改 `research/06_scope_redesign/p1_v4_w14_20261109/`，交付目录之外 0 个文件）。
- 结果目录：`results_project/v4w20/{nets56,solves}`（主 checkout，git 忽略）；LP 核对草稿 `/home/jin/v4w20/lpcheck`。

| 子步 | 内容 | 状态 / 提交 |
|---|---|---|
| W20-0 | SHA256、模型、启动条件；读先读材料（D2c `SMOKE56_D2C.md`、W14 `REPORT.md` 第 0、2 节、M12b 指令与报告、M12 OWEN 输出与求解钩子） | 完成 |
| W20-1 | `scripts_project/v4_coalition.py` + `tests/research/test_v4_coalition.py`（25 passed）；(d) `test_v4_a2_fallback.py` + `test_m08a_a7.py` 10 passed；17 个 56 时段网络构建（`logs/build_nets56.txt`）；静态检查 17 / 17 通过（`evidence/STATIC_CHECKS_W20.json`）；LP 等价核对（`logs/lpcheck.txt`，不求解）；`COALITION_BUILD.md` | 完成，`a312974d`（回执中模块 SHA256 `db46d097…` = 提交内容；在该提交上重建 LTMS 逐字节相同，`logs/rebuild_check.txt`） |
| W20-2 | 求解前登记：`CORE_CHECK_V4_56.md` 第 1 节、`evidence/W20_XS_PRE.json`、`tables/W20_XS_PRE.csv`（恒等式差 −4,519 EUR，通过）、运行器 `scripts/w20_solve.sh` 与判定 `scripts/w20_eval.py` | 本提交（W20-2，任何求解之前） |
| W20-3 | 17 次求解（GMS → … → minusVN），每次后判定 | 未开始 |
| W20-4 | 比较与报告：`CORE_CHECK_V4_56.csv`、`REPORT.md`、`CHECKPOINTS.csv`、`EVIDENCE.json`、审阅包 | 未开始 |

续做点：W20-2 提交后启动 `bash scripts/w20_solve.sh --confirmed <时间>`（已有 `SOLVE_RECEIPT.json` 的联盟跳过，不重解）。
