# M12 进度（随进度更新）

- 指令：`M12_CLAUDE_CODE_INSTRUCTION.md` v1，SHA256 `4e0b05486e171b00922d9ac23c691802b4a375a40c4cb49b9165a3dac1183793`（与 `M12_INSTRUCTION_SHA256.txt` 一致，2026-10-21 核对）。
- 边界：不求解模型网络、不调用 Gurobi（含许可检查）、不连云；单元测试只用 scipy / HiGHS 解玩具 LP；不改模型、配置、网络与既有结果，只新增分析代码与文档。
- 工作树：`/home/jin/wt_m12_20261021`，分支 `codex/m12-allocation-20261021`（自 M08a 头 `820c2cae`，PR #45）。M08b 会话在另一 worktree（分支 `codex/m08b-demand-20261021`）并行。
- 被忽略输入：`research_inputs/finance_v5/{COUNTRY_WACC_PUBLIC_SOURCES,DISCOUNT_RATE_IN_USE}.csv` 已从 `/home/jin/wt_m080_20261020` 复制。

| 步 | 内容 | 状态 | 提交 |
|---|---|---|---|
| 0 | 核对 SHA256、开 worktree、探查账本 / 导出 / 约束结构 | 完成 | — |
| C1（通用部分）+ C4.1–2 | `m12_allocation.py` 通用函数（所有者编码与 α、对偶形式 y'b、市场结算形式、核心 / 去一国 / SCRB / 比例规则）；`tests/research/test_m12_allocation.py` 玩具 3 国 LP（scipy HiGHS，7 passed） | 完成 | 见 git log |
| C1（网络部分） | `run`（复用 `s4d_ledger` 所有者规则；逐走廊组件成本与两端对偶结算；α 0 / 0.5 / 1、按长度、区间；B16；与现行账本逐实体对账；S4P 规则 (ii)(iii) 同比例对照）、`benefit`（受益 + 5 种比例权重）、`loo`（c′(i)、C1 (b) 阈值、不可分成本、SCRB）；冒烟网络测试（8 passed） | 完成 | 见 git log |
| C4.3（部分） | S4N 试点一体化 + S4O-6 不互联：B16 7.2e-9 / 6.5e-7；α 0.5 与账本偏差 ≤ 1.5e-5 EUR；与 S4P ASPECT8 表最大偏差 1.5e-13 bn；B6 69.243 bn；Owen 受益为负仅燃料舱（−1.215 bn） | 完成 | 见 git log |
| C2 | `m12_rhs_audit.py`：只构建 LP（`l23_violation_analysis.build_model`），逐族按右端项所有者分类、耦合行检测、Owen 对偶形式 y'b（导出数组或行对偶 + 驻点重建溢流列 RC）、市场形式 − 对偶形式的精确分解、去一国右端项比对。365×24h 一体化 9,017,345 行、构建 33–42 s、峰值 8.05 GiB；非零右端项无主 0 / 无法归属 0；唯一耦合 = 齐次 KVL；对偶形式闭合 −6e-5 bn；**市场形式 − Owen = KVL 回路转移（VN +0.26、LA −0.26 bn）**；11 国去一国结构检查全部通过（24 时段截断；VN 另在 365×24h） | 完成 | 见 git log |
| C3 | `m08a_run_batch.sh`：每个运行 C1 之后、GATES_V6 验收之前执行 `m12_allocation.py run --register` 与（有导出数组且 `M12_DUAL=1` 时）`m12_rhs_audit.py audit --register-dir`；level2 在 `batch_reference`（重评）之后、formal 在两情景都通过之后执行 `benefit`；`OUT/<tag>_minus<CC>/` 存在时执行 `loo`；钩子测试 + M08a 原测试 12 passed | 完成 | 见 git log |
| C4.3 | S4N 一体化 + S4O-6 不互联：受益对照补 Owen 对偶形式（VN 51.852 / LA 2.482 bn，市场形式 51.595 / 2.738） | 完成 | 见 git log |
| 证据补充 | 对偶形式 α 区间、玩具证据、全量测试 544 / 64 / 0（头 dbb63113） | 完成 | dd7d2efe |
| 交付 | `M12_REPORT.md`、台账 M12 条目、draft PR、审阅 ZIP | 完成 | 见 git log / PR |

## 补充 01（第 136 项）— 接续计划（2026-10-21，原会话上下文 55 %，按补充 01 规定新开会话执行）

- 补充文件 `M12_SUPPLEMENT_01.md` SHA256 `d8f36a14df7285d27acda5aaf2399af14bc1f9bba260c21ad69a49c734a08ad4`，与 `M12_SUPPLEMENT_01_SHA256.txt` 一致（已核对）。规则同 M12：不求解、不调 Gurobi、不连云；玩具 LP 允许；继续用 worktree `/home/jin/wt_m12_20261021`（分支 `codex/m12-allocation-20261021`，头 82f59a17，PR #46）。
- **M08b 已完成**（PR #47，重建网络与冒烟均通过；网络见 `work/p1_m08b_20261021/evidence/M08B_NETWORK_FILES.csv`，365×24h integrated d9fab9aa…、disconnected 7234216e…），第 5 项可以直接做。

| 步 | 内容（每步提交一次） | 状态 |
|---|---|---|
| S01-1 D1 | 对偶形式成为主值：`m12_rhs_audit.py audit` 输出 `OWEN.json/.csv/.md`（主值 = y′b，α 0 / 0.5 / 1、区间、按长度；市场形式并列；差额 = KVL 转移 + 残差：导出数组时分解为行互补 / 列互补 / 驻点，行对偶时 KVL 由潮流算、其余为残差）。C1 (c) 扩展：对偶恒等式 \|Σφ − c(N)\| / c(N) ≤ 1e-6 + 每个参与者的残差影响。`benefit` 主值改用对偶形式。报告写 2920×3h 估算（行数 72.1 M ≈ 365×24h 的 8 倍 → 本机比例 ≈ 5–6 min、≈ 64 GiB，INFERENCE；C1 本身已在云端为 2920×3h 各建一次模型，可考虑合并） | 完成（代码 + 测试；`loo` 也改用对偶形式主值；D1 玩具测试随本步提交；**新发现：** KVL 回路在去一国（物理）联盟中断开时，对偶形式可不在该博弈的核心内——玩具 {A, B} 超出 9.93，见报告补充 01；365×24h 证据在 S01-10 后统一重跑） |
| S01-2 D2 | 对偶形式的按长度分摊：审计中按组件记录跨境对行（`Line-ext-s_nom-*`、`Link-ext-p_nom-*`）的 y·b，用 `s4d_ledger.load_length_shares()` 逐组件拆分 | 完成（`length_split`：国家对行 y′b + 该组件目标常数，按组件长度份额拆分；"-reversed" 用孪生份额；缺份额 0.5；无法归到组件的对值 0.5；OWEN 输出"按长度"列；测试 2 项） |
| S01-3 D3 | 代码文档写入规则（区域外进口若加总量上限，须先定归属再运行）；审计 `owen_premise.passed = (shared == 0 且 unresolved == 0)`，不通过时 OWEN 输出标 `premise_failed` | 完成（规则写入两个模块文档与 PROPOSALS；`owen_premise.passed`；OWEN `premise`、`premise_failed`，前提不成立时 `usable_for_allocation = False`、MD 醒目提示；测试 1 项） |
| S01-4 D4 | `benefit` 两种口径：(A) 按比例分 B6，用去一国边际贡献检查 s_i·B6 ≤ φ_i^disc − c′_adj(i)（= 规则支付 ≥ c′_adj(i)；只对有去一国运行的国家），同样检查 Owen；(B) 按比例分一体化总成本（11 国分 c(N) − φ_BUNKER − SHARED），检查个体理性 支付 ≤ φ_i^disc。主讨论 (A)。批级顺序改为先 `loo` 再 `benefit --loo-check` | 完成（`benefit --loo-check`：(A) 每个权重下逐国 支付 ≥ c′（优先用 D8 加回值）、(B) 个体理性；Owen 主值同样两项检查；运行脚本 level2 / formal 都改为先 `m12_loo` 再 `m12_batch`；测试 1 项） |
| S01-5 D5 | 权重与模型同源：人口 AEO8 D.1 + TL UN WPP 2024（与 M08b `m08b_demand.py` 同一组数）；GDP = M08b 工业增长口径（AEO8 D.6 人均 GDP × D.1 人口；TL = KH / LA / MM 人均均值 × WPP）——实现前读 `git show codex/m08b-demand-20261021:scripts_project/m08b_demand.py` 取同一函数 / 数；电力两口径不变；SSP2 2050 改为对照 | 完成（读 M08b `m08b_demand.py`：GDP 实际用 AEO8 **表 D.2**（实际 GDP PPP 2017）而非 D.6，故 GDP 权重 = D.2 2050 水平；TL = KH / LA / MM 人均 GDP（D.2 / D.1）均值 × TL 人口；D.2 文件按原字节复制到本分支同一路径（SHA256 9189d862…，与 M08b 相同，合并无冲突）；人口 AEO8 D.1 + UN WPP 2024；主用 / 对照分列；测试 1 项） |
| S01-6 D6 | 不算 SCRB（只有 3 次去一国）；输出中写明"有 11 次时自动给出，单独成本以不互联分摊代理" | 完成（`loo`：少于 11 次时 `scrb.computed = False` 并写明理由；11 次齐全时自动计算并注明代理；不互联单独成本优先用其对偶形式；测试 1 项） |
| S01-7 D7 | `m08a_run_batch.sh` level2：A 档两情景之后，对 `LOO_COUNTRIES`（默认 "VN TH LA"）用 `VAR_CMD`（默认 `m08a_variants.py`，PYTHONHASHSEED=0，**不加** `--allow-stale-base`）由 `NETS/integrated_365_24h_unsolved.nc` 在云端生成变体到 `OUT/variants/`，STATUS 记录回执与 SHA256；`one_run` 增加可选参数（网络、成本表、回执），以标签 `integrated_A_minus<CC>`、档案 A 运行；`accept` 用变体回执——**先读 `scripts_project/v5/gates_v6.py` 的 accept / G2.1（约 143–200 行）确认能否接受 `*_VARIANT_RECEIPT.json`（字段 output.sha256），不能则加最小适配**；`batch_reference _A` 同时重评去一国运行；formal 不做去一国 | 未开始 |
| S01-8 D8 | `loo`：c(N − i)_adj = c(N − i) + Σ_{含 i 的走廊} 另一方份额(α) × fom_existing（`ALLOCATION_LINES.csv`）；同时报告原值与加回值，检查用加回值 | 未开始 |
| S01-9 D9 | formal：每次运行的 C1 用临时参照（同一 OUT 下第三批的 `BATCH_REFERENCE_A.json` 或 env `PROVISIONAL_REFERENCE`；都没有时记录"临时 = L23 默认"）；两次都完成后 `batch_reference ""`（重评两次运行，`grade_history` 保留）→ 先把 `V6_ACCEPTANCE.json`、`FORMAL_DECISION.json` 复制为 `*_PROVISIONAL.json`，再重新 accept / formal-check 得最终标签 → `m12_loo` / `m12_batch ""` | 未开始 |
| S01-10 D10 | 燃料舱严格单独成本：只用区域外进口满足燃料舱负荷（燃料舱净零 ⇒ 只能用非化石进口：FT 燃料进口 → 航空、绿色甲醇进口 → 航运；含计量链路效率与边际成本；纯算术、不求解），验证 φ_BUNKER（对偶形式）≤ 该值；写入 OWEN 输出与报告 | 未开始 |
| S01-11 测试 | D1：玩具中加一条跨所有者的齐次回路行（KVL 型），验证对偶形式在核心内、市场 − 对偶 = 回路转移；D10：玩具燃料舱型参与者（无资源、只有需求）份额 ≤ 严格单独成本、核心成立；D7 / D9：运行脚本假流水线（变体生成钩子 `VAR_CMD` 假实现、3 次去一国运行、`M12_LOO_*:runs=3`；formal 两次后 REFERENCE、临时副本、重新验收）；D8：加回算术；全量 `tests/research`（`/home/jin/m12_full_tests.sh`） | 未开始 |
| S01-12 M08b 网络 | 用 M08b 网络重跑 C2（365×24h 一体化 + 不互联）与去一国结构检查（VN / TH / LA 365×24h；其余 24 时段截断）；本分支没有 M08b 代码，`--repo /home/jin/wt_m08b_20261021`（模型钩子用 M08b 代码），变体用 M08b worktree 的 `m08a_variants.py`、不加 stale 开关；输出到 `evidence/s01_m08b/` | 未开始 |
| S01-13 交付 | `M12_REPORT.md` 末尾追加"补充 01"一节；台账 M12 条目注明补充 01；PR #46 正文更新（`gh pr edit` 会因 Projects classic 报错，用 `gh api -X PATCH repos/cyc292cycjin-oss/SGP-ESE5004-Stage2/pulls/46 -F body=@file`）；审阅 ZIP 重做（`scripts/m12_review_zip.py`）；完成后停止 | 未开始 |

已知代码位置：分摊 `scripts_project/m12_allocation.py`（`run` 约在 `def run(`；`benefit`、`loo`、`thresholds_bn`、`socio_weights`）；审计 `scripts_project/m12_rhs_audit.py`（`audit`、`decompose`、`objective_constants`、`loo_compare`）；运行脚本 `scripts_project/m08a_run_batch.sh`（`one_run`、`m12_run`、`m12_batch`、`m12_loo`、level2 / formal 分支）；测试 `tests/research/test_m12_allocation.py`；工具脚本 `/home/jin/m12_c2.sh`、`/home/jin/m12_c43.sh`、`/home/jin/m12_commit.sh`（消息 `/home/jin/m12_msg.txt`）。注意：Bash 工具的 heredoc 不能含撇号；`wsl bash -c` 中 `$变量` 会丢失，检查放脚本文件。

## 接续点（M12 主体）

全部子步已完成，按指令停止，等待审阅。工具脚本（WSL）：`/home/jin/m12_commit.sh`（镜像 + 提交，消息 `/home/jin/m12_msg.txt`）、`/home/jin/m12_c43.sh`（C4.3）、`/home/jin/m12_c2.sh`（C2：STEP=smoke | smoke_nc | full365 | dis365 | variants | loo365 | loo24）、`/home/jin/m12_loo_recompare.sh`、`/home/jin/m12_full_tests.sh`；去一国变体网络在 `/home/jin/m12_local/variants/`（未提交）。待决定事项见 `M12_REPORT.md` 第 6 节。
