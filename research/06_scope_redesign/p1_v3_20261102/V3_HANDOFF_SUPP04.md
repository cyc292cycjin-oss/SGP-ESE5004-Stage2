# 补充 04 交接说明（给新会话）

原会话上下文已到 78 %，按 `V3_REVIEW_DECISIONS_SUPP03.md` 新开会话。先读本目录全部 `V3_*` 文件，指令是该文件第 2 节（第 179 项：专线只输送存量电站出力）。这里只记文档里没有写、重新摸索会费时间的事。

## 环境

- worktree `/home/jin/wt_v3_20261102`，分支 `codex/v3-20261102`，当前 `25f98646`。主检出 `/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model`，结果 `results_project/v3/`。
- Python `/home/jin/miniforge3/envs/pypsa-earth/bin/python`，要 `PYTHONHASHSEED=0`。从 Git Bash 调用：`MSYS_NO_PATHCONV=1 wsl -d Ubuntu -- bash /home/jin/v3/x.sh`。
- 内联 `wsl bash -c` 里 `$VAR` 为空、`|` 和 `(` 会被解析，一律写脚本。Bash 工具 heredoc 里有单引号会中断，含单引号的文件用 Write 工具写到 `\\wsl.localhost\Ubuntu\home\jin\v3\`。
- 提交：先写消息文件，再 `bash /home/jin/v3/commit.sh <消息文件> <行数>`，它会镜像 `/home/jin/v3/*` 到 `scripts/wsl_v3/`，并强制加入被忽略的 csv。消息末尾带 Co-Authored-By。
- 推送走 Windows：`git -c safe.directory='*' -c credential.interactive=never -C "//wsl.localhost/Ubuntu/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model" push origin refs/heads/codex/v3-20261102:refs/heads/codex/v3-20261102`。
- 镜像 `bash /home/jin/v3/mirror_s1.sh`，把新报告加进它的 `F` 列表。
- 全量测试 `run_tests3.sh`，不能与任何 `s2_solve.py`（含 HiGHS、干跑）同时运行。基线是 3 项失败，与 v3 无关。

## 可复用脚本（`/home/jin/v3/`）

`mk_s3.py` 由补充 02 的脚本改写出 `build_s3.sh`、`pathcheck4.sh`、`smoke_s3.sh`、`dry_s3.sh`、`pkg_s3.sh`，改输出目录即可得到本轮版本（建议 `builds_bound`、`path_check5`、`smoke_s4`、`dry_screen4`、`pkg_check4`，包目录 `screen_package_v3_bound`）。`mk_def3.py` 生成批定义（从构建回执取提交）。`sm_s3.py`、`sm_s3b.py`、`chk_st3.py`、`chk_disc.py`、`g63.sh` 取报告数字，LA 电量表和 LA 风光表都在里面，加一列即可。构建脚本要求 tracked 工作区干净、输出目录不存在。

## 实施时要注意（从代码读到的）

1. **火电不是 Generator。** LA 的存量火电是 Link：`existing_survivor::LA2 5::Lignite::…`（`lignite existing`，`p_nom` 5,690.91 是燃料口径，出力 = 1,878 MW）、`existing_survivor::LA2 4::coal existing::S4A`（842.7，也是燃料口径）。审阅决定第 2.1 节只写了 Generator 与 StorageUnit，但 Hongsa 正是这种 Link。要移动 `bus1`，并按 `p_nom × efficiency` 计入源母线 Link 的 `p_nom`。这是对指令文字的补充，要在规则和报告里写明。
2. **"存量"含在建机组。** `existing_survivor` 里有 GEM 状态为 construction 的机组（Luang Prabang 1,460、Pak Beng 912、Pak Lay 770 等，投运年 2030 前后，见 `existing_unit_components` 的 `gem_status`）。审阅决定说以构建回执的存量标识为准，所以都移入，但第 2.3 节容量表要分列。
3. **移入判据：** `p_nom_extendable=False` 且不是候选的 Generator / StorageUnit / 上述 Link。注意 `external coal`、`external lignite`、`process emissions`、`plastic waste` 这些 Generator：`external *` 是燃料供应，挂在燃料母线；`process emissions`、`plastic waste` 不是发电机组，不要移动。
4. **层的位置：** `add_dedicated_plant_lines` 在 `s2_network.py` 里 `apply_ac_losses` 之后、`install_carbon_metadata` 之前。`tag_cross_border` 已在前面跑过，新 Link 要手工设 `border_class=domestic`、`transport_carrier`，新母线要有 `country`、`x`、`y`、`location`。
5. **列类型：** 加列或新行后要 `fillna` + `astype`，否则 netCDF 导出报 `unsupported dtype`（`n.links["reversed"]`、`stock` 已处理，新加的 `role` 列同样）。
6. **会受影响的检查：** `s2_network.static_validate_s2`、`v3_static.struct_diff`（`ALLOWED_NEW` / `ALLOWED_CHANGED`：新 Bus、新 Link 载体、机组 `bus` 变化）、`v3_static.dedicated_check`（`bus0` 以 LA 开头仍成立）、`gate_b11_supply_routes`（按母线名前缀找节点，新母线载体是 AC，要确认不被当成负荷节点）、节点数相关的列表（`n.buses.carrier == "AC"` 的用法）。`existing_unit_components` 的 `node` 不要改，它是 LA 节点；`add_dedicated_plant_lines` 用它校验。
7. **记账是停止条件。** `s4d_ledger.py`、`m12_allocation.py`、`m12_rhs_audit.py` 按母线国家归属。先用 HiGHS 8 时段路径检查（`pathcheck4.sh` 思路）确认 B16、Owen、GATES_V6，再问用户。闭不合就停下报告，不改记账规则。
8. **截短的 LP 检查** 用 `--label SMOKE_TEST_ONLY`，否则退出码 1。
9. **`RUN_PLAN_V3.md`** 下一节是第 19 节，第 17.1 节加标注"已被第 179 项取代"。`test_v3_runners.py::test_definitions_are_the_registered_plan` 要求 SHA、字节、构建提交都出现在该文件里。

## 上下文数字

第 3.3 节四列表的前三列在 `V3_REPORT_SUPPLEMENT03.md` 第 3.3 节。LA 水电资源逐月数字在 `V3_REPORT_SUPPLEMENT02.md` 第 3.3 节，判断 56 时段时先看来水（1 月 1,218 MW，9 月 17,619 MW）。
