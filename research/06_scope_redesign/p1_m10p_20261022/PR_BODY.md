## M10P：第三批上云准备（本机；不连云、不上传、不调用 Gurobi）——第 133、138–141 项

指令 `M10P_CLAUDE_CODE_INSTRUCTION.md` v1（SHA256 `bd2461e7…bbd1`，核对一致）。叠在 #48（M12b）上。报告：`research/06_scope_redesign/p1_m10p_20261022/M10P_REPORT.md`；运行计划：`RUN_PLAN.md`。

### 整合
- #45、#47、#46、#48 与 S4Q #41（`FIXED_RUNS`）的全部提交已在 M12b 头 `1f46517d` 中，**无需 merge**（`evidence/M10P_PR_COMMIT_CHECK.json`）。
- `tests/research` 全量：整合分支 582 passed / 67 skipped / 0 failed；最终代码 `eac6c3e0` **595 passed / 67 skipped / 0 failed**（玩具 LP 按指令允许，照常运行）。

### 网络（第 1.4 节停止条件）
- 在干净提交 `b46fc23d` 上重建，四个 SHA256 都与 `ec80668f` 构建不同；原因：数据逐项相同，只有元数据 `s2_layers.geothermal.bus_mapping_source.path`（构建 worktree 的绝对路径，`s2_network.py:344`）不同。
- 用户决定 A：部署包用 `ec80668f` 原构建（365×24h 一体化 `75704334…`、不互联 `888a009b…`，P1 用 2920×3h 一体化 `bca20fc0…`）。

### 新增 / 修改
- `scripts_project/s2_solve.py`：`--stop-before-solve`（干跑：构建并导出 LP、固定参数后在求解前退出）。
- `scripts_project/m10_batch3_summary.py`：运行表、核对、`LEVEL2.json`、B6、敏感性差额、批级汇总、P1 解析。
- `scripts_project/m08a_variants.py`：分国 WACC 变体的元数据只记成本表文件名与 SHA256（干跑发现：绝对路径使变体 SHA256 随目录变化）。
- `research/06_scope_redesign/p1_m10p_20261022/cloud_package/`：`run_batch3.sh`（两会话、线程预算、许可间隔、临时→本批参照重评、D12 停批、安全停止、续跑、`BUILD_ONLY` / `POST_ONLY`）、`preflight.sh`、`pack_results.sh`、`make_package.sh`、`env/`（锁定清单、安装与核对）。
- 测试：`tests/research/test_m10p_batch3.py`（12 项，替身流水线，无求解器）、`test_m08a_a7.py::test_wacc_variant_bytes_independent_of_the_folder`。

### 部署包与干跑
- 部署包 `work/p1_m10p_20261022/cloud_package_dist/`（不入库）：提交 `eac6c3e0`，23 个文件 283.7 MB，`PACKAGE_MANIFEST.json`（逐文件 SHA256）`f36a4b6c…`；非克隆部署环境下载约 743 MB。
- 干跑：预检 OK；7 个变体三遍逐字节相同；R1–R11 全部"LP 构建完成、求解前退出"且核对通过（参数、输入 SHA256、G2.2、路径）；P1 参数核对通过；后处理演练（M12b 冒烟结果）全过，与 M12b 证据差 0.0 EUR。第一版包 `be1ce466` 因上述 WACC 变体问题作废（保留）。

### 仍需用户决定
25 核上 R3 / R4 先后跑；无返回解的运行是否对敏感性运行也停批；P1 内存风险（2920×3h 构建粗估约 80 GiB）；第 3 阶段两条固定通道；实例规格（≥ 72 GiB、≥ 16 核、≥ 50 GiB 盘）；代码归档是否瘦身；两处路径依赖的处理。详见报告第 8 节。

未连云、未上传、未调用 Gurobi。完成后停止，等待审阅。

🤖 Generated with [Claude Code](https://claude.com/claude-code)
