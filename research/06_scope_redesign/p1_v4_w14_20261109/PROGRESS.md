# W14 进度（V4_W14_INSTRUCTION.md v2，SHA256 6cb103dbe8822cd48d1fa699ec947be2a682d371e14337b13dceed38597d2243 已核对，与 V4_W14_SHA256.txt 一致；开工 2026-11-09 03:40 SGT）

- 执行：Claude Code，模型 Opus 5.5（`claude-opus-5-5`，开工时确认）；指令要求 effort Xhigh，会话的 effort 设定本会话看不到，不能自证（报告中注明）。
- 分支 `codex/v4-w14-20261109`，起点 `4e83d71ed20010b87867d7889693d879fe11a4ab` = `codex/v4-d2c-20261109` 头（fetch 核过，本地 = 远端）；D2c 审阅包 `REVIEW_612d8f6b.zip` 对应提交 `612d8f6b` 是其祖先，二者之间只改了 `research/06_scope_redesign/p1_v4_d2c_20261109/` 下 2 个文件（`PROGRESS.md`、`evidence/REVIEW_ZIP_MANIFEST_612d8f6b.txt`），交付目录之外 0 个。
- worktree `/home/jin/wt_v4_w14`；临时目录 `/home/jin/v4w14`；主检出 `results_project/v4w14/`（构建输出，不入库）。
- 交付目录 `work/p1_v4_w14_20261109/` = 仓库 `research/06_scope_redesign/p1_v4_w14_20261109/`（`hpc_package_v4/` 与 zip 不入库）。
- 额度：求解器至多 2 次（第 3 节演练），已用 0 / 2；本机计算上限 4 小时；磁盘新增上限 10 GB；不下载。

| 步 | 内容 | 状态 | 提交 |
|---|---|---|---|
| W14-1 | 第 1 节：分支、worktree、祖先核实；构建脚本 | 完成 | W14-1（本行所在提交 = 网络构建提交） |
| W14-2 | 第 2 节：2920×3h 与 56 时段网络、全部静态检查、与 D2c 冒烟网络比对 | 待做 | |
| W14-3 | 第 4 节：报警线、预测、`RUN_PLAN_HPC_V4.md` 与定义文件登记（打包前提交） | 待做 | |
| W14-4 | 第 5 节：`HPC_OPERATOR_GUIDE_V4.md`；打包脚本 | 待做 | |
| W14-5 | 第 3 节：打包 `hpc_package_v4` 与本机演练 | 待做 | |
| W14-6 | 第 6 节：报告、证据、审阅包、推送 | 待做 | |

续做点：W14-1 完成后在本行所在提交上构建网络（`scripts/build_w14.sh main`）。
