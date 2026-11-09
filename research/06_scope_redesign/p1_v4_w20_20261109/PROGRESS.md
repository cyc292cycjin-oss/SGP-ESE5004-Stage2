# V4 W20 进度（断点续做用；每个子步一行，最后一行是续做点）

- 指令：`V4_W20_INSTRUCTION.md` v1，SHA256 `f4419a8347be3fa00cd7fec8e8fd508a2999dc91b56ee47304b5236f62a6f97b`（与 `V4_W20_SHA256.txt` 一致，开工前核对）。
- 会话：`claude-opus-5-5`，effort `xhigh`（会话元数据）；启动条件：W19a 会话已停止、本机无其他运行中的 Claude Code 会话、WSL 无 Gurobi 进程、可用内存 9 GiB。
- 分支 / worktree：`asean/v4-w20-20261109` / `/home/jin/wt_v4_w20`（自 `asean/v4-w14-20261109` 头 `ac75354c`，fetch 核过本地 = 远端；`26c2e47d` 是祖先，`26c2e47d..ac75354c` 只改 `research/06_scope_redesign/p1_v4_w14_20261109/`，交付目录之外 0 个文件）。
- 结果目录：`results_project/v4w20/{nets56,solves}`（主 checkout，git 忽略）；LP 核对草稿 `/home/jin/v4w20/lpcheck`。

| 子步 | 内容 | 状态 / 提交 |
|---|---|---|
| W20-0 | SHA256、模型、启动条件；读先读材料（D2c `SMOKE56_D2C.md`、W14 `REPORT.md` 第 0、2 节、M12b 指令与报告、M12 OWEN 输出与求解钩子） | 完成 |
| W20-1 | `scripts_project/v4_coalition.py` + `tests/research/test_v4_coalition.py`（25 passed）；(d) `test_v4_a2_fallback.py` + `test_m08a_a7.py` 10 passed；17 个 56 时段网络构建（`logs/build_nets56.txt`）；静态检查 17 / 17 通过（`evidence/STATIC_CHECKS_W20.json`）；LP 等价核对（`logs/lpcheck.txt`，不求解）；`COALITION_BUILD.md` | 完成，`a312974d`（回执中模块 SHA256 `db46d097…` = 提交内容；在该提交上重建 LTMS 逐字节相同，`logs/rebuild_check.txt`） |
| W20-2 | 求解前登记：`CORE_CHECK_V4_56.md` 第 1 节、`evidence/W20_XS_PRE.json`、`tables/W20_XS_PRE.csv`（恒等式差 −4,519 EUR，通过）、运行器 `scripts/w20_solve.sh` 与判定 `scripts/w20_eval.py` | 完成，`ad7b7f1a`（任何求解之前；已推送） |
| W20-3 | 17 次求解（GMS → … → minusVN），每次后判定：01:02:53–03:43:52 UTC，17 / 17 optimal，17 / 17 严格成立，0 违反（`logs/solve_status.txt`、`evidence/W20_RUN_VERDICTS.jsonl`）。第一次后台启动因 Git Bash 路径改写未运行（无状态文件、无求解），加 `MSYS_NO_PATHCONV=1` 重启 | 完成 |
| W20-4 | 比较与报告：`CORE_CHECK_V4_56.md` 第 2 节、`CORE_CHECK_V4_56.csv`、`REPORT.md`、`CHECKPOINTS.csv`、`EVIDENCE.json`、`evidence/W20_KVL_LOOPS.json`、`LEDGER_ENTRY_DRAFT.md`；审阅包（不入库，清单入 `evidence/`） | 完成，`2a83691a`；审阅包 `REVIEW_2a83691a.zip`（126,453 字节，SHA256 `903ff775361b6c26c23768f45e0647e5450634fd48c60579455dba484d4d80e2`，39 个成员，testzip 通过；不入库，清单 `evidence/REVIEW_ZIP_MANIFEST_2a83691a.txt`） |
| W20-4b | **过程事故（如实记录）：** 写本表上一行时，Git Bash 中用双引号包住的 `python -c` 字符串含反引号，bash 把反引号内的文件名当命令替换执行——审阅包清单被当作脚本逐行执行，清单列出的工作目录文件（含 `scripts/*.sh`、`*.py`、`*.md`）被 bash 逐个调用。核查：`w20_solve.sh` 在 `--confirmed` 守卫处拒绝（未求解、未调用求解器）；`w20_build.sh` / `w20_lpcheck.sh` 在 Git Bash 下找不到 `/home/jin`（Git Bash 的 `/home` 不存在），在 `cd` 处退出，未触及 WSL；工作目录无新增文件，除本表该行被替换成残缺文字外，所有文件与 `2a83691a` 逐字节相同（rsync 校验和比对）；WSL 结果目录、LP 核对回执完好；无求解进程。本行与上一行改用编辑工具重写 | 完成，`c477db3d` |
| W20-4c | **审阅包（以此为准）：** `REVIEW_c477db3d.zip`（129,866 字节，SHA256 `dea919125784a2c8e4ee8a97e3633c5f1101919f1b99bc1fd1d1577aaf42e78b`，40 个成员含 `repo/CODE_DIFF_ac75354c.patch`，testzip 通过；不入库，清单 `evidence/REVIEW_ZIP_MANIFEST_c477db3d.txt`）；`REVIEW_2a83691a.zip` 为前一版，内容只差事故记录 | 本提交 |

续做点：无（W20 完成，等待审阅）。审阅包与最终提交见 git log 与 `evidence/REVIEW_ZIP_MANIFEST_*.txt`。
