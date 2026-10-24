# M10R 报告：第三批收尾修复——分国账本缺陷、R9 后处理重做与 R11 补跑的准备（本机；不连云）

1. **缺陷机制（VERIFIED）：** 一体化构建把走廊表的全部 67 条走廊写入 `existing_cross_border_fom_ledger` meta，其中 50 条是零容量候选线路（`capacity_2025_mw = 0`、`annual_fom_eur = 0`，如 LA–VN 的线路 59）；保留存量变体删除这 46 条候选线路（及 283 条非存量链路）但不过滤 meta；`s4d_ledger.country_cost_ledger` 第 130 行与 `m12_rhs_audit.objective_constants` 第 199 行在检查金额之前就按 meta 行查归属表 → `KeyError: '59'` → B16 不可计算 → C1 (c)、M12、Owen 不可计算、G2.3 不过。归属表本身按网络实际设备建立（正确），错在 meta 行的无保护查找。
2. **56×3h 复现（VERIFIED，授权求解 1/3）：** 从一体化 2920×3h 基础网络生成保留存量变体、取前 56 个时段以档案 A 求解（341 s，optimal，4.19 GiB），用 v5 代码后处理得到与云端 R9 **完全相同的失败链**（B16 `'59'`、C1 abc = 110、M12 退出码 1 同一 KeyError、Owen 跳过、GATES_V6 仅 `b16_computable` 不过 → NOT_ACCEPTED，分级 g2 停批）。
3. **修复（提交 `40ecdf57`）：** meta 行的设备在网络中 → 按该设备的归属（两端国家的走廊实体，与一体化运行同一套半线 / 长度份额规则）入账；设备不在网络且金额为 0 → 跳过并计数；不在网络且金额非 0 → 明确报错（常数无主）。修复后 56×3h 保留存量：B16 相对误差 3.7e-12（差 1.19 EUR），C1 abc = 111，M12 恒等式通过，Owen 可用，**ACCEPTED_LAYER2**。
4. **回归（VERIFIED）：** 56×3h 五个无缺陷数据集（M08b 冒烟 s01 一体化 / 不互联、M12b 去 VN / TH / LA）修复前后账本、B16、C1、M12、Owen、GATES_V6 的每个文件逐字节或逐数相同；365×24h：在 v5 包的两个基础网络与 7 个变体（与 `EXPECTED_VARIANTS.json` 逐字节相同）上核对，只有 R9 的 meta 有指向已删设备的行（50 行，全为 0 EUR），R1–R8、R10、R11 都不走修复的代码路径；并且（用户补充授权后）在核对通过的完整包上用修复后代码对 R1–R8、R10 从求解后网络**实际重算**了账本、B16 与 M12 分摊：账本三表、`LEDGER_IDENTITY`、`V5_GATES`、`ALLOCATION` 三件与云端原结果逐字节 / 逐数相同，`NODAL_PRICES.csv` 按母线对齐后全部数值相同（只有行顺序不同）；365×24h 的 Owen 审计回归留到云端补做（需要实例上的数组）。
5. **燃料舱 WACC（VERIFIED 数值 + INFERENCE 机制）：** R10 − R1 的 ASEAN 项 −4.753 bn 全部在燃料舱（甲醇燃料 −3.107、非化石油 −1.646 bn）；燃料舱没有任何资产，购买量在两次运行中完全相同（485.6 TWh 甲醇、239.6 TWh 非化石油），差额是池对偶价格下降（甲醇 −6.40、非化石油 −6.87 EUR/MWh）；区域池层面的设备（甲醇 / 氨储罐）无成本层行、不被重新年化，仍按统一 7 %。
6. **云端补做的办法已登记（`RUN_PLAN.md` 第 11 节，在任何补做结果出现之前）：** `run_batch3.sh --only R11`（只求解从未启动的运行，承认但不受 R9 的 STOP 阻止，分级规则照旧）、`--repost R9 --into <新目录>`（不求解、不读许可、原目录不改）、`--summary-s1`；替身测试覆盖 R11 正常 / 无解 / G2 不过、拒绝已结束运行、重做不启动求解；全量测试 **631 passed / 67 skipped / 0 failed**（基线 615 / 68 + 16 个新增）。
7. **演练（VERIFIED）：** 2 个基础网络 + 7 个变体的 9 种网络类型在 56×3h 上各跑一遍完整后处理链（账本 / B16、违反分析、C1、M12、Owen、GATES_V6、分类）：8 种用真实求解结果（含授权的第 2、3 次求解：分国 WACC 不互联 = R11 的类型、b1 不互联 = R8 的类型，均 optimal、ACCEPTED_LAYER2），分国 WACC 一体化用维数正确的合成解（只验证"跑通、不报错、恒等式可算"）；`DRILL_POSTPROC.json` 全部通过，打包脚本现在要求它对应包提交。
8. **v6 包与干跑：** 包提交 `2a77f1b8`，24 文件 / 148,650,102 B，清单 `4113db64…`，`SHA256SUMS` `c2d77c49…`；两个基础网络、构建回执、成本表、`EXPECTED_VARIANTS.json` 与 v5 逐字节相同；全量测试 631 passed / 67 skipped / 0 failed；干跑：预检 OK、`--only R11` 构建到求解前退出（与 v5 的 R11 相同）、`--repost R9` 在 56×3h 保留存量上跑通（原目录不变，违反分析与 C1 (a)(b) 相同，标签 → ACCEPTED_LAYER2）、全类型演练通过；**批次模式 BUILD_ONLY（R1–R11）未做**（本机计算约 71 min，再做会触及 1.5 h 上限，第 7 节决定 4）。
9. **本机 Gurobi：** 3 次（授权 3 次），全部 56×3h 档案 A、30 分钟止损、optimal（341 / 356 / 306 s，≤ 4.4 GiB），间隔 2,472 s 与 303 s；未求解任何 365×24h / 2920×3h 网络；不连云、不上传。
10. **需要用户决定（第 7 节）：** 云端补做的执行与机器（原实例优先）；R9 新标签按 `RUN_PLAN.md` 11.3 登记；构建层清理（零容量候选走廊写入 meta）的时机；是否授权约 20 分钟本机计算补做批次模式 BUILD_ONLY 干跑。

---

**指令：** `M10R_CLAUDE_CODE_INSTRUCTION.md` v1（SHA256 `4a6ce9360643d47d32110d34fef402f5577b8b7d4fa05e430746bec255ec2e9e`，与 `M10R_INSTRUCTION_SHA256.txt` 一致）。**位置：** worktree `/home/jin/wt_m10p_20261022`，分支 `codex/m10-batch3-20261022`，起点 `efef93bf`（干净；v5 包提交 `e0a89f8e`）。**边界：** 不连云、不上传；本机 Gurobi 求解 3 次（授权 3 次），全部 56×3h；未求解任何 365×24h / 2920×3h 网络；tmux `m10dl`（完整包续传）未触碰。过程记录 `M10R_PROGRESS.md`，证据 `M10R_EVIDENCE.json`，辅助脚本 `scripts/`（本机 `/home/jin/m10r/` 的副本）。

## 1. 诊断（B1）

### 1.1 机制

- **归属表（`s4d_ledger.owners`）按网络实际设备建立：** 对网络中每条 Line / Link 取两端母线的国家；`border_class == cross_border` 且两端是两个国家 → 走廊实体 `XB:<A>|<B>@<类型>:<名>`；域内 → 该国；只接区域母线 → 燃料舱 / 池。一体化运行中跨境线路 59（LA2 3 – VN2 2，515.1 km，AC）归属 `XB:LA|VN`，其新建容量的年化投资、存量 FOM 与阻塞租金记在走廊实体上，再按半线（主值，0.5 / 0.5）或在境长度份额（敏感性，`XB_LENGTH_SHARES_S4H2.csv`：LA 0.6384 / VN 0.3616）分到两国。
- **meta 账本按走廊表建立：** `scenario_network.existing_cross_border_fom`（构建时）对走廊表 `cross_border_corridors.csv` 的每一行计算 FOM% × 投资 × 长度 × 2025 容量，写入 `existing_cross_border_fom_ledger`。表中 67 条走廊里 50 条的 2025 容量为 0（S4E1 / S4H2 候选与"零容量候选"线路 59、60、63、64、APG11 等，决定 100），FOM 为 0。一体化 365×24h 基础网络：62 条跨境交流线路中 46 条 `s_nom_min = 0`，292 条跨境链路。
- **保留存量变体不过滤 meta：** `m08a_layers.apply_stock_mode(keep_stock_no_new)` 只保留 `s_nom_min > 0` 的 16 条存量线路、7 条存量链路（2 条 DC + 5 条既有气管道）及 2 条反向孪生，删除 46 条线路、283 条链路，并**有意保留** `existing_cross_border_fom_eur`（8,993,064.82 EUR，与一体化相同——被删行的 FOM 全为 0，常数无需改变），但 67 行 meta 原样留下。去一国变体（`apply_remove_countries`）会按 `gone` 过滤 meta，所以 R5–R7 无此问题。
- **无保护的查找：** `country_cost_ledger` 第 129–130 行 `add(own[r.component_type][r.component], …)`——`own["Line"]` 是按网络中线路重建索引的 Series，不含已删除的 '59'，而 `add()` 对零金额的跳过发生在查找之后 → `KeyError: '59'`（meta 顺序中第一条已删行）。`objective_constants`（Owen 审计常数）第 198–201 行同一写法。

**结论：** 这不是"归属表按情景建"，而是"meta 账本按走廊表建、变体删设备不删 meta、后处理对 meta 行无保护地查归属表"。R9 的求解正常（C1 (a)(b) 通过），缺陷只在后处理。

### 1.2 同类路径清单

| 路径 | 行 | 对 meta 行的处理 | R9 上的表现 | 处置 |
|---|---|---|---|---|
| `s4d_ledger.country_cost_ledger` | 129–130 | `own[t][c]` 无保护 | **KeyError '59'**（B16） | 修复 |
| `m12_rhs_audit.objective_constants` | 198–201 | `O.maps[t][c]` 无保护 | 未走到（M12 先失败）；修复前 56×3h 复现中同样会在 Owen 审计失败 | 修复 |
| `m12_allocation.corridor_components` | 221–226 | `extra.reindex(sel)` | 安全 | 不改 |
| `m12_allocation.allocation_from_network` | 341 | 调用账本 | 经路径 1 失败（M12 退出 1） | 经路径 1 修复 |
| `s4o_c1_precision` (c) | 311–314 | 读 `V5_GATES.B16_LEDGER` | `relative_error = null` → (c) 不过 | 经路径 1 修复 |
| `gates_v6.g2_3` | 159–160 | `b16_computable` | 不过 | 经路径 1 修复 |
| `s4i_static_audit` | 317 | 只用 `owners()` | 安全 | 不改 |
| `s4m_s1_check` | 88 | 调用账本 | 同路径 1（不在批次流水线中） | 经路径 1 修复 |
| `m08a_layers.apply_remove_countries` | 227–229 | 按 `gone` 过滤 meta | 安全 | 不改 |

**7 个变体逐一判断**（`variants365/XB_LEDGER_CHECK_365.json`，在 v5 包的 365×24h 基础网络上实际生成并核对；7 个变体 SHA256 与 `EXPECTED_VARIANTS.json` 逐一相同）：

| 网络 | meta 行 | 跨境线路 / 链路 | 指向已删设备的 meta 行 | 其中金额非 0 | 走修复路径 |
|---|---|---|---|---|---|
| 一体化基础（R1、R3） | 67 | 62 / 292 | 0 | 0 | 否 |
| 不互联基础（R2、R4） | 0 | 0 / 0 | 0 | 0 | 否 |
| R5 去 VN | 52 | 47 / 217 | 0 | 0 | 否 |
| R6 去 TH | 36 | 32 / 175 | 0 | 0 | 否 |
| R7 去 LA | 38 | 33 / 192 | 0 | 0 | 否 |
| R8 b1 | 0 | 0 / 0 | 0 | 0 | 否 |
| **R9 保留存量** | 67 | 16 / 9 | **50** | 0 | **是** |
| R10 分国 WACC 一体化 | 67 | 62 / 292 | 0 | 0 | 否 |
| R11 分国 WACC 不互联 | 0 | 0 / 0 | 0 | 0 | 否 |

### 1.3 56×3h 复现（授权求解 1/3；VERIFIED）

- 变体：`m08a_variants.py` 从 M08b 补充 01 一体化 2920×3h 基础网络（`bca20fc0…`）生成 `disconnected_keepstock_2920_3h_unsolved.nc`（SHA256 `ffd7a691…`；与 M08b 当时生成的 `f9c9a873…` 只差 meta 中记录的脚本哈希——`research_config_sha256`、组件数、字节数、存量账目全同）。
- 求解：`s2_solve.py --truncate 56`，档案 A `formal_barrier`，TimeLimit 1,750 s、墙钟 1,800 s；2026-10-23 18:32:58–18:38:39 UTC（02:32–02:38 SGT 10-24），341 s，**optimal**，目标 318,479,975,461.52 EUR，峰值 4.19 GiB。
- v5 代码（worktree 头 `efef93bf`）后处理：`V5_GATES.B16_LEDGER` = `{"passed": false, "error": "'59'"}`（回溯到 `s4d_ledger.py:130`）；违反分析正常；C1 abc = **110**（(c) 的 `b16.relative_error = null`）；M12 退出码 1，`m12.err` 末行 `KeyError: '59'`；Owen 跳过（无 ALLOCATION.json）；GATES_V6 **NOT_ACCEPTED**，G2.3 四项检查中只有 `b16_computable` 为 false；`stop-class` → g2 / stop。与云端 R9（`M10_RUNS.json`）逐项相同。

## 2. 修复（B2）

### 2.1 会计口径与依据

保留下来的跨境存量线路 / 链路的固定运维费与容量的归属，与一体化运行中同一设备的处理一致：归属由网络实际包含的设备及其两端母线所属国家决定（`owners()` 的既有规则：走廊实体 `XB:<A>|<B>`，半线主值、长度份额敏感性），不依赖情景名；`existing_cross_border_fom_eur` 常数在变体中保持不变（M08a A7 的登记：被删行的 FOM 为 0，常数不变）。代码里对这类线路没有另外的会计规则（登记册 `disconnected_definition_sensitivity`："existing cross-border FOM constant kept"）。因此修复只是让 meta 行的入账尊重"设备是否在网络中"：

- 设备在网络中 → `add(own[t][c], "fom_existing", carrier, eur)`（与修复前相同）；
- 设备不在网络中且金额为 0 → 跳过并计数（诊断 `existing_cross_border_fom_ledger = {rows, booked, booked_eur, absent_zero, absent_zero_components}`）；
- 设备不在网络中且金额非 0 → `ValueError`（目标函数常数无主，恒等式不可能成立；比静默跳过更安全）。

`m12_rhs_audit.objective_constants` 同样处理（新增诊断 `fom_ledger = {rows, booked, absent_zero}`）。只改这两处；阈值、档案、时限、网络、成本表、停批分级、变体生成（`m08a_layers` / `m08a_variants`，否则变体 SHA256 会变、`EXPECTED_VARIANTS.json` 须重登记）都不改。

### 2.2 改动与测试

| 文件 | 改动 | 对结果 / 云端时间的作用 |
|---|---|---|
| `scripts_project/s4d_ledger.py` | meta 行入账加保护与诊断（+15 行） | 保留存量网络上 B16 可计算；其他网络逐数不变；无时间影响 |
| `scripts_project/m12_rhs_audit.py` | `objective_constants` 同一保护（+9 行） | 保留存量网络上 Owen 审计可计算；其他网络逐数不变 |
| `scripts_project/s4d_ledger_redo.py`（新） | 从求解后网络重做 `s2_solve.py` 的 S4D-3 导出块（账本三表、NODAL_PRICES、LEDGER_IDENTITY、`V5_GATES.B16_LEDGER` 与 `all_passed_*`）到新目录，写 `LEDGER_REDO.json` | `--repost` 的账本步骤；365×24h 约 1–2 分钟（INFERENCE） |
| `tests/research/test_m10r_keepstock_ledger.py`（新） | 玩具保留存量网络（入账 / 跳过 / 报错 / Owen 常数 / 重做工具）+ 56×3h 端到端（本机结果存在时） | 9 passed（含原 `test_s4d_3.py` 4 个） |

提交 `40ecdf57`（B1–B2）。

### 2.3 回归（关键）

**56×3h（全部输入在本机；修复前 = 头 `efef93bf`，修复后 = `40ecdf57` 的代码）：** 对每个数据集在新目录重跑账本重做 → C1 run（smoke_s01 本批参照）→ M12 run → Owen 审计 → GATES_V6 → 分类，比较器 `compare_dirs.py`（CSV 逐字节；JSON 逐数、忽略路径 / 时间 / 峰值内存 / 代码哈希与修复**新增的两个诊断键**）。

| 数据集 | 账本 CSV ×3 | NODAL_PRICES | LEDGER_IDENTITY | V5_GATES | PRECISION | ALLOCATION ×3–4 | V6_ACCEPTANCE | OWEN.json / .csv | RHS_* ×4 | STOP_CLASS | 结论 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| M08b s01 一体化 | 相同 | 相同 | 相同 | 相同 | 相同 | 相同 | 相同 | 相同 | 相同 | 相同 | all_equal |
| M08b s01 不互联 | 相同 | 相同 | 相同 | 相同 | 相同 | 相同 | 相同 | 相同 | 相同 | 相同 | all_equal |
| M12b 去 VN | 相同 | 相同 | 相同 | 相同 | 相同 | 相同 | 相同 | 相同 | 相同 | 相同 | all_equal |
| M12b 去 TH | 相同 | 相同 | 相同 | 相同 | 相同 | 相同 | 相同 | 相同 | 相同 | 相同 | all_equal |
| M12b 去 LA | 相同 | 相同 | 相同 | 相同 | 相同 | 相同 | 相同 | 相同 | 相同 | 相同 | all_equal |
| 保留存量（本次求解） | 修复前不可计算 → 修复后可计算 | — | — | B16 false→true | abc 110→111 | 不可计算→可计算 | NOT_ACCEPTED→ACCEPTED_LAYER2 | 不可计算→可计算 | 同左 | g2→accepted | 按预期 |

- 逐数比较中 OWEN.json / RHS_AUDIT.json 唯一的数值差异是构建耗时与峰值内存（`build_seconds`、`peak_rss_gib`）和记录目录路径的字符串，无任何结果数不同（`regress_compare/*.json`）。
- 保留存量修复后：B16 相对误差 3.7348e-12、差 +1.19 EUR；C1 (a) −1.09e-8 bn、(b)(c) 通过；M12 恒等式差 1.19 EUR、与账本表最大偏差 7.6e-6 EUR；Owen 对偶形式 `usable_for_allocation = true`；GATES_V6 G1 abc 全 true、G2.1–G2.3 全 true → ACCEPTED_LAYER2。分国账本总额（bn EUR）：ID 82.77、VN 62.27、TH 36.19、MY 21.34、PH 18.12、SG 9.23、KH 4.73、MM 3.17、LA 1.94、BN 0.48、TL 0.38、燃料舱 77.86、池 −0.000。
- 修复前后对保留存量数据集：C1 (a)(b) 的每个数（返回解差额、分国一阶影响）相同（`REGRESS` 的 PRECISION 差异只在 (c) / b16 字段与验收标志）。

**365×24h（第三批 9 个已接受运行；VERIFIED）。** 两层证据：

(i) **结构性证明：** 修复只改变"meta 行的设备不在网络中"这一分支；在实际的两个 365×24h 基础网络与 7 个变体上核对（表 1.2），除 R9 外没有任何网络走到这一分支，所以 R1–R8、R10 的后处理按构造不变。

(ii) **实际重算（用户 2026-10-24 补充授权约 40 min 本机计算后完成；不调用 Gurobi）：** 完整包下载完成并核对通过（1,744,049,251 B，SHA256 `46f1afbc…` 一致，`FULL_VERIFY.json`：461 个文件、导出问题 0），对 R1–R8、R10 用修复后代码（`f0dc96dc` = `2a77f1b8` 的代码）从求解后 365×24h 网络重算账本、B16（`s4d_ledger_redo.py`）与 M12 分摊（`m12_allocation.py run`），输出到新目录（`/home/jin/m10r_365/<编号>/`；原包只读），再与轻量包的云端原结果（v5 代码）逐项比较（`compare_dirs.py`；证据 `evidence/regression_365x24h/`）。每运行账本 5–8 s、M12 4–5 s，峰值 0.8 GiB（日网络 365 个时段）。

| 运行 | 账本三表（字节） | `LEDGER_IDENTITY`（逐数） | `V5_GATES` 含 B16（逐数） | B16 相对误差（修复前 = 修复后） | `ALLOCATION.json / .csv / _LINES.csv`（逐数 / 字节） | M12 恒等式差 EUR（= 池净额，与原值相同） | `NODAL_PRICES.csv` |
|---|---|---|---|---|---|---|---|
| R1 | 相同 | 相同 | 相同 | 1.265e-8 | 相同 | −3,160.62 | 对齐后相同 |
| R2 | 相同 | 相同 | 相同 | 1.862e-7 | 相同 | −48,624.08 | 对齐后相同 |
| R3 | 相同 | 相同 | 相同 | 1.491e-8 | 相同 | −3,725.30 | 对齐后相同 |
| R4 | 相同 | 相同 | 相同 | 1.006e-7 | 相同 | +26,262.49 | 对齐后相同 |
| R5 | 相同 | 相同 | 相同 | 8.527e-8 | 相同 | −17,265.73 | 对齐后相同 |
| R6 | 相同 | 相同 | 相同 | 2.613e-9 | 相同 | −588.55 | 对齐后相同 |
| R7 | 相同 | 相同 | 相同 | 1.765e-8 | 相同 | +4,436.35 | 对齐后相同 |
| R8 | 相同 | 相同 | 相同 | 4.678e-8 | 相同 | −12,291.02 | 对齐后相同 |
| R10 | 相同 | 相同 | 相同 | 8.205e-9 | 相同 | +1,952.86 | 对齐后相同 |

- `NODAL_PRICES.csv` 的字节比较报告"不同"，原因只是**行顺序**：云端文件由求解进程内存中的网络写出（母线按求解时的列序），本机重做从 NetCDF 读回（导入后的列序）；按母线名对齐后 9 个运行的全部数值（每运行 1.04–1.14 百万个数）与文本列逐一相同、行集合相同（`NODAL_PRICES_ALIGNED_CHECK.json`）。
- 求解后网络的 `objective` 与回执一致（`objective_equal = true`，9 / 9）；meta 账本：一体化类 67 行全部入账、`absent_zero = 0`；去一国类 52 / 36 / 38 行全部入账；不互联类 0 行。
- `V6_ACCEPTANCE.json` 与 `m12_owen/` 不在本次授权范围（Owen 审计需要实例上的 LP / 解数组），比较中按预期缺失；**365×24h 的 Owen 对偶形式回归留到云端补做**（第 5 节第 5 步）。

### 2.4 燃料舱 WACC 的解释（只读核对，不判定）

R10 − R1 的"ASEAN"项 −4.753 bn = 燃料舱 −4.753 bn + 池 −0.000（池净额 +3,160 → −1,953 EUR，量级 1e3）。

| 实体 | 科目 | 载体 | R1 bn | R10 bn | 差 bn |
|---|---|---|---|---|---|
| ASEAN_BUNKER | liquid_pool_methanol | shipping methanol | 46.999 | 43.892 | −3.107 |
| ASEAN_BUNKER | liquid_pool_oil non-fossil | oil final-energy accounting | 18.522 | 16.876 | −1.646 |
| ASEAN_POOL | 合计（买入甲醇 / 非化石油 / 氨，卖给燃料舱与各国） | | 0.000 | −0.000 | −0.000 |

- **燃料舱用哪个 WACC：** 燃料舱（`ASEAN_BUNKER`）没有任何资产——账本只有向池购买航运甲醇与航空非化石油的结算项（`capex_new = 0`），因此不涉及任何 WACC。
- **区域层面的设备用哪个 WACC：** 区域池上的设备只有甲醇储罐与氨储罐（`Store:methanol store` / `ammonia store`）；它们的载体没有成本层行（`COMPONENT_COST_BREAKDOWN_SUMMARY.no_cost_row_by_carrier`），`apply_wacc_mode` 对没有成本行的设备跳过（且其母线国家为 ASEAN，不在分国 WACC 表中，`skipped_no_country = 0` 说明没有设备因无国家被跳过——它们在更早的"无成本行"分支已跳过），所以仍按统一 7 % 的年化投资；R10 变体回执：6,494 个设备重新年化，98 个分布式设备按 `technology_data_fixed` 保留 4 %。
- **变化的来源（VERIFIED 数值）：** 燃料舱的购买量在两次运行中完全相同——甲醇 46.999 / 96.788 = 43.892 / 90.390 = 485.6 TWh，非化石油 18.522 / 77.322 = 16.876 / 70.450 = 239.6 TWh（燃料舱负荷为固定需求）；差额全部是池对偶价格的下降：`ASEAN methanol` 均价 96.788 → 90.390 EUR/MWh（−6.40），`ASEAN oil non-fossil` 77.322 → 70.450（−6.87），`ASEAN ammonia` 73.685 → 67.661（−6.02）。
- **机制（INFERENCE）：** 分国 WACC 下，生产燃料的国家（SG 2.89 %、MY 4.41 %、PH 4.54 %、VN 4.55 %、BN 4.68 %、TH 5.25 % 均低于 7 %）的电解、甲醇合成、费托与配套可再生资产的年化投资下降，池的边际供给成本随之下降，燃料舱以更低的池价买入同样的量；ID（7.07 %）、LA、KH、MM、TL 高于 7 % 的国家成本上升（R10 − R1：ID +1.833、MM +1.021 bn），与账本差额的符号一致。只解释，不判定。

## 3. 云端补做的事先登记办法（B3）

### 3.1 新模式的语义（`run_batch3.sh`；批次模式行为未变）

默认关闭；不带新参数时脚本的每一步与 v5 相同（`START` 行多一个 `mode=batch` 字段；B4 的 BUILD_ONLY 干跑逐运行与 v5 比较）。提交 `ae7e3f6e`。

| 模式 | 命令 | 语义 | 对 G2 停批的处理 | 不做的事 |
|---|---|---|---|---|
| `--only R11[,…]` | `GRB_LICENSE_FILE=… PY=… bash run_batch3.sh --auth "<授权原文>" --only R11` | 只求解所列的、从未启动过的运行：第 0 阶段只生成 / 核对所选运行的变体（与 `EXPECTED_VARIANTS.json` 比较），启动前距所有求解的最晚结束与脚本启动 ≥ 330 s，档案 / TimeLimit 28,800 / 墙钟 30,000 / 成本表 / 标签与登记值相同；求解后按 3.5 节做违反分析、C1（必须有本批 `BATCH_REFERENCE.json`，否则拒绝启动）、M12、Owen、GATES_V6、分级分类、导出；结果包只含所选运行（`results_*_only_R11_*`，`export/R11/ARRAYS_MANIFEST.json` 只列该运行的数组） | 启动时记录已有的 `STOP`（`ONLY_MODE:…:existing_stop=R9`），它**不阻止**所选运行；所选运行自身 G2 不过 → 追加 `STOP`、后续所选运行不启动、`HALTED_ONLY`、退出码 3；无返回解 / C1 (a) 不过 → `UNUSABLE`，继续下一个；只有 (b)/(c) 不过 → 不停；启动时存在 `STOP_SAFE` → 拒绝 | 不重评（本批参照已是最终）、不做第二级比较、不改 `BATCH3_SUMMARY`、不触碰其他运行目录 |
| `--only` 的干跑 | `BUILD_ONLY=1 PY=… bash run_batch3.sh --only R11`（无 `--auth`） | 所选运行的变体 + `--stop-before-solve` 构建 + `BUILD_CHECK.json`，许可绊线 `/nonexistent/…` | 同上 | 不求解 |
| `--repost R9 --into <新目录>` | `PY=… bash run_batch3.sh --repost R9 --into runs/batch3_s1`（无 `--auth`；原实例以外加 `--arrays <含 lp/ 与 solution/ 的目录>`） | 无求解模式：不读许可、不留间隔、`--auth` 即拒绝；输入只读（`RUN.json`、回执、门控、导出清单复制，求解后网络、对偶、`lp/`、`solution/` 以符号链接引用）；步骤：账本重做（`LEDGER_CMD` = `s4d_ledger_redo.py`，写新目录的 `V5_GATES.json` / `LEDGER_IDENTITY.json` / 账本三表 / `NODAL_PRICES.csv`）→ 违反分析（与原 `VIOLATIONS.json` 逐项比较）→ C1（本批参照）→ M12 → Owen → R5–R7 的右端项检查 → GATES_V6 → 分类；`REPOST.json`（原标签、原因、代码提交）、`REPOST_CHECK.json`（违反分析相同？C1 (a)(b) 相同？B16 / (c) / 标签前后）；导出到 `<新目录>/export/R9`，`results_*_repost_R9_*` | 分类只记录（`REPOST_CLASS` 行、`STOP_CLASS.json`），**不写** `STOP` / `UNUSABLE`；原目录、原标签、批次 `STATUS.txt` / `STOP` / 汇总不改（`STATUS`、`POSTPROC_ERRORS`、`tmp` 都在新目录） | 不求解；`.ended` 不存在的运行拒绝；新目录已存在拒绝 |
| `--summary-s1 --into <目录> --use R9=<目录>/R9` | `PY=… bash run_batch3.sh --summary-s1 --into runs/batch3_s1 --use R9=runs/batch3_s1/R9` | 用 `m10_batch3_summary.py summary --use/--into/--name` 重算批级汇总到 `<目录>/batch_s1/BATCH3_SUMMARY_S1.json / .md`：所有 `--use` 的运行从其重做目录读取，其余从原目录读取；敏感性 R8 − R2、R9 − R2、R10 − R1、R11 − R2 与信息项 R11 − R10（目标值、分国账本总额、Owen 份额）、B6、去一国、受益、第二级比较照原批结果；`reposts` 字段记录每个重做运行的原标签 → 新标签与 `REPOST_CHECK` | 汇总中 `stop_not_accepted` 仍列 R9（历史事实），`reposts` 说明已重做 | 不改原 `BATCH3_SUMMARY.json / .md` |

替身测试（`tests/research/test_m10r_s1_modes.py`，用 M10A 的合成替身流水线与真实的 GATES_V6 / 分类 / 汇总代码；8 个用例）：批次在 R9 的 B16 不可计算（G2.3）停批、R11 未启动、R10 跑完 → `--only R11` 正常（求解一次、`ref=batch`、ACCEPTED_LAYER2、其他目录与汇总的 SHA256 不变、再次 `--only R11` 被拒绝）；R11 无解 → `UNUSABLE:R11:nosol`、`STOP` 不变；R11 G2 不过 → `STOP` = R9、R11，退出码 3；`--repost R9`：无求解调用、账本步骤在无许可环境中运行、原 R9 目录逐文件 SHA256 不变、`REPOST_CHECK` 违反分析与 C1 (a)(b) 相同、标签 NOT_ACCEPTED → ACCEPTED_LAYER2；`--summary-s1`：R9 − R2 可用、R11 − R2 与 R11 − R10 可计算、原汇总不变；12 条拒绝（已结束运行、未登记运行、模式混用、缺 `--into`、`--auth` 与无求解模式、`--use` / `--arrays` 用错、缺本批参照、`STOP_SAFE`）均不写任何文件；账本步骤失败 → `POSTPROC_ERROR`、标签保持 NOT_ACCEPTED、分类 g2 只记录；`BUILD_ONLY --only R11` 干跑；预检 `guards` 节识别 `LEDGER_CMD`。`pack_results.sh` 增加子集打包参数；`preflight.sh` guards 增加 `LEDGER_CMD`。

### 3.2 `RUN_PLAN.md` 第 11 节（原文；提交 `ae7e3f6e`，登记于任何补做结果出现之前）

```markdown
## 11. 第三批补做（S1）——登记于任何补做结果出现之前（M10R，2026-10-24；第 3 节规则不变）

**背景（第三批结果，`work/p1_m10_20261022/M10_REPORT.md`）：** R1–R10 已求解，9 个 ACCEPTED_LAYER2；R9（不互联保留存量）求解正常（C1 (a)(b) 通过），但分国账本代码在"一体化派生、按不互联求解、保留跨境存量"的网络上 `KeyError: '59'`（跨境 FOM 账本 meta 里零容量候选线路的行指向被变体删除的设备），B16 不可计算 → C1 (c)、M12、Owen 不可计算、G2.3 不过 → 按 3.3 第 3 项停批；R11 未启动。缺陷在 M10R 中定位并修复（`scripts_project/s4d_ledger.py`、`m12_rhs_audit.py`；修复提交见 `research/06_scope_redesign/p1_m10r_20261024/M10R_REPORT.md`），修复对其余 9 个已接受运行的任何后处理结果不产生改变（56×3h 五个数据集逐项回归相同；365×24h 的 9 个运行与 R11 的网络都不走修复的代码路径，`XB_LEDGER_CHECK_365.json`）。

### 11.1 范围

1. **R9 后处理重做（不重新求解）：** 用修复后的代码对 R9 重做全部后处理（账本与 B16、违反分析、C1、M12 分摊、Owen 对偶形式、GATES_V6、分级分类），输出写到新目录；原运行目录、原标签（NOT_ACCEPTED）、批次 `STOP` 与原汇总不改。R9 的新标签**只能**由这条路径得到，并按 11.3 登记为"事后修复的代码缺陷"。
2. **R11（分国 WACC 不互联）单独补跑：** 此前从未启动；档案 A、Threads 8、TimeLimit 28,800 s、墙钟 30,000 s、许可间隔 330 s、变体（`EXPECTED_VARIANTS.json` 核对）、成本表（disconnected）、C1 参照（本批 `BATCH_REFERENCE.json`）、验收与分级停批规则——全部与第 2、3 节该运行的登记值相同。求解一次，不重试。
3. **批级补算：** 在新目录中重算 R9 − R2、R11 − R2 与信息项 R11 − R10，以及新的批级汇总 `BATCH3_SUMMARY_S1.json / .md`（B6、去一国、受益、第二级比较按原批结果照抄）；原 `BATCH3_SUMMARY.json / .md` 不改。

### 11.2 执行方式（`run_batch3.sh` 的按运行选择模式；默认关闭，批次模式行为未变）

| 步骤 | 命令（在包目录、运行批次的同一 tmux shell 中；`PY=<环境 python>`） | 许可 | 输出 |
|---|---|---|---|
| (a) R9 重做 | `PY=… bash run_batch3.sh --repost R9 --into runs/batch3_s1`（无 `--auth`；原实例以外需 `--arrays <含 lp/ 与 solution/ 的目录>`） | 不需要 | `runs/batch3_s1/R9/`、`runs/batch3_s1/export/R9/`、`REPOST.json`、`REPOST_CHECK.json`、`results_*_repost_R9_*` |
| (b) R11 补跑 | `GRB_LICENSE_FILE=<许可> PY=… bash run_batch3.sh --auth "<用户授权原文>" --only R11` | 需要 | `runs/batch3/R11/`、`runs/batch3/export/R11/`、`results_*_only_R11_*` |
| (c) 批级补算 | `PY=… bash run_batch3.sh --summary-s1 --into runs/batch3_s1 --use R9=runs/batch3_s1/R9` | 不需要 | `runs/batch3_s1/batch_s1/BATCH3_SUMMARY_S1.json / .md`、`results_*_summary_s1_*` |

- **`--only` 的语义：** 只求解所列的、从未启动过的运行；已结束的运行一律拒绝启动（不重试）。批次 `STOP`（R9 的 g2）在该模式下被**承认并记录**（`STATUS.txt` 的 `ONLY_MODE` 行），不阻止所选运行；所选运行自身按 3.3 第 3 项分级：G2 不过 → 追加 `STOP`、不再启动后续所选运行、退出码 3；无返回解或 C1 (a) 不过 → `UNUSABLE`，继续；只有 (b)/(c) 不过 → 不停。不做重评（本批参照已是最终参照）、不做第二级比较、不改批级汇总；结果包只含所选运行。启动前存在 `STOP_SAFE` 则拒绝（安全停止先由用户处理）。
- **`--repost` 的语义：** 无求解模式（不读许可、不留间隔、拒绝 `--auth`）；输入只读（求解后网络、对偶、回执、门控从原目录读取或链接，LP / 解数组链接），违反分析重算后与原结果逐项比较（代码未改 → 必须相同，`REPOST_CHECK.json`），C1 (a)(b) 数值必须与原值相同；分类只记录（`STOP_CLASS.json`），不写 `STOP` / `UNUSABLE`。
- **机器：** 优先原实例（同一 CPU，R11 与 R10 可比；R9 的 LP / 解数组仍在数据盘）。原实例开不了有卡模式时，可在任何 ≥ 25 核、≥ 64 GiB 的实例上做：R11 只依赖部署包（v6）；R9 重做所需的 LP 数组用 `s2_solve.py --stop-before-solve` 在登记网络上确定性重建（M10P / M10A 干跑已证明逐字节相同），解数组 `solution/` 从原实例取回，求解后网络与对偶从完整包中取（`--arrays`）。两种做法在报告中如实记录。
- **规则：** R11 求解一次、不重试；R9 不重新求解；阈值、档案、时限、网络、成本表与停批分级不改。

### 11.3 "事后修复的代码缺陷"的登记方式

R9 的标签变更在报告与台账中按以下格式登记，缺一不可：**原标签**（NOT_ACCEPTED，`STOP_NOT_ACCEPTED:R9:g2`，2026-10-24 00:27:53 SGT）；**原因**（后处理代码缺陷：跨境 FOM 账本 meta 的零容量候选行在保留存量变体中指向被删除的设备；求解本身正常）；**修复提交**（M10R 的提交 SHA）；**回归证据**（56×3h 五个数据集修复前后逐项相同；365×24h 结构核对 9 个运行不走修复路径；56×3h 保留存量复现：修复前同一 KeyError，修复后 B16 成立、C1 (c) 可计算、ACCEPTED_LAYER2）；**新标签**（由 `--repost` 得到，附 `REPOST_CHECK.json`：违反分析逐项相同、C1 (a)(b) 相同）。求解不重做，阈值不改。

### 11.4 演练要求（本次的教训）

每次打包前，对 **7 个变体加 2 个基础网络的每一种网络类型**（一体化、不互联、去 VN / TH / LA、b1、保留存量、分国 WACC 一体化 / 不互联）在 56×3h 上演练一遍完整的后处理链（账本与 B16、违反分析、C1、M12、Owen、GATES_V6、分类）：有真实 56×3h 求解结果的类型用真实结果，其余用维数正确的合成解只验证"能跑通、不报错、恒等式可算"，并注明哪些是合成数据（`DRILL_POSTPROC.json`；脚本 `research/06_scope_redesign/p1_m10r_20261024/scripts/drill_postproc.sh`；`make_package.sh` 要求 `DRILL_JSON` 指向当前提交的完整演练结果）。
```

### 3.3 演练（B3.3）：每一种网络类型的后处理全链

脚本 `research/06_scope_redesign/p1_m10r_20261024/scripts/drill_postproc.sh`（提交 `ae7e3f6e` / `cddc3f95` / `2a77f1b8`），对 2 个基础网络 + 7 个变体的每一种类型在 56×3h 上跑：账本重做（`s4d_ledger_redo.py`）→ 违反分析 → C1（smoke_s01 本批参照）→ M12 分摊 → Owen 对偶形式审计 → GATES_V6 → 分级分类；不调用求解器（`GRB_LICENSE_FILE` 移除）。记录 `results_project/m10r/drill/DRILL_POSTPROC.json`（证据 JSON `drill`）；`make_package.sh` 现在要求 `DRILL_JSON` 指向包提交的完整记录（`all_types_ran` 且 `code_commit` = 包提交），`tests/research/test_m10r_drill.py` 核对记录。授权的第 2、3 次求解优先补了最缺的两种类型：**分国 WACC 不互联（R11 的类型）** 与 **b1 不互联（R8 的类型）**；剩下的分国 WACC 一体化（R10 的类型，365×24h 上已有真实的 ACCEPTED_LAYER2 结果）用合成解。

| 类型 | 数据来源 | 账本 / B16（相对误差；差 EUR） | 违反分析 | C1 abc | M12 恒等式 | Owen 可用 | GATES_V6 | 分类 |
|---|---|---|---|---|---|---|---|---|
| 一体化基础 | 真实（M08b 冒烟 s01，optimal） | 7.9e-12；+2.44 | 0 | 111 | 通过 | 是 | ACCEPTED_LAYER2 | accepted |
| 不互联基础 | 真实（M08b 冒烟 s01，optimal） | 2.5e-12；+0.78 | 0 | 111 | 通过 | 是 | ACCEPTED_LAYER2 | accepted |
| 去 VN | 真实（M12b，optimal） | 7.8e-13；−0.19 | 0 | 111 | 通过 | 是 | ACCEPTED_LAYER2 | accepted |
| 去 TH | 真实（M12b，optimal） | 2.5e-12；+0.70 | 0 | 111 | 通过 | 是 | ACCEPTED_LAYER2 | accepted |
| 去 LA | 真实（M12b，optimal） | 1.6e-12；+0.49 | 0 | 111 | 通过 | 是 | ACCEPTED_LAYER2 | accepted |
| **保留存量** | 真实（本次求解 1，optimal） | 3.7e-12；+1.19（修复前不可计算） | 0 | 111 | 通过 | 是 | ACCEPTED_LAYER2 | accepted |
| **分国 WACC 不互联（R11 类型）** | 真实（本次求解 2，optimal） | 5.7e-12；−1.73 | 0 | 111 | 通过 | 是 | ACCEPTED_LAYER2 | accepted |
| **b1 不互联（R8 类型）** | 真实（本次求解 3，optimal） | 9.1e-12；−2.90 | 0 | 111 | 通过 | 是 | ACCEPTED_LAYER2 | accepted |
| 分国 WACC 一体化（R10 类型） | **合成**（`m10r_synthetic_solution.py`：真实 LP 构建 700,908 列 × 1,553,068 行，容量取标称值、流量 1e-9 MW、对偶 1.0、目标值 = 固定常数 10,059,334,783.64 EUR） | 2.0e-11；+0.20（可算） | 0（跑通） | 011（(a) 无真实 KKT，按设计不过） | 通过 | 否（合成） | NOT_ACCEPTED（c1a → unusable；合成数据无意义） | 只验证"能跑通、不报错、恒等式可算" |

- 合成类型的 meta 账本 67 行全部入账（一体化基础：设备都在网络中），`absent_zero = 0`；保留存量类型 `rows 67 / booked 17 / absent_zero 50`。
- 演练第一次在 `ae7e3f6e` 运行时合成类型在 LP 构建处失败（`s2_solve.py` 只接受 `SMOKE_TEST_ONLY` 标签的截断时段）、第二次在 NetCDF 回读处失败（PyPSA 导出时丢弃全为默认值 0 的序列）；两处都是演练脚本自身的问题，已修（`cddc3f95`、`2a77f1b8`），与模型代码无关。

## 4. v6 包与干跑（B4）

### 4.1 全量测试（B4.1）

`tests/research` 全量一次（提交 `2a77f1b8`，`GRB_LICENSE_FILE` 移除，`PYTHONHASHSEED=0`，`M10R_KEEPSTOCK_DIR` / `M10R_DRILL_JSON` 指向本机结果使两个真实数据测试不跳过；玩具 LP 测试按基线允许）：**631 passed / 67 skipped / 0 failed**，921.9 s（`evidence/tests/TESTS_full.log`）。基线（M10A 补充 01）615 passed / 68 skipped；新增 16 个通过：`test_m10r_keepstock_ledger.py` 5 个（玩具入账 / 跳过 / 报错、Owen 常数、重做工具、56×3h 真实数据）、`test_m10r_s1_modes.py` 9 个（含参数化 2 个）、`test_m10r_drill.py` 2 个；跳过的 67 个都是"本机无某步的构建 / 结果"的既有原因（S4E–S4L 构建、S4D 账本试验等）。

### 4.2 部署包 v6（B4.2）

`make_package.sh`（提交 `2a77f1b8` 的干净工作树；`DRILL_JSON` = 本提交的演练记录，脚本核对 `all_types_ran` 与 `code_commit` 后才继续；67 s）。v5 先改名为 `work/p1_m10p_20261022/cloud_package_dist_v5_e0a89f8e` 保留，v6 在 `work/p1_m10p_20261022/cloud_package_dist/`。证据 `evidence/package_v6/`（`PACKAGE_MANIFEST.json`、`SHA256SUMS`、`EXPECTED_VARIANTS.json`、`VARIANT_REPRODUCIBILITY.json`、`BUILD_INPUT_CHANGES.json`、`COMMIT`、`MAKE_PACKAGE.log`、`PACKAGE_V6_VS_V5.json`）。

| 项 | v6 | v5 |
|---|---|---|
| 提交 | `2a77f1b8541f0f0f092d3ab01d1e225afb1e5cbb` | `e0a89f8e7abe7e91132135b241766464890283cb` |
| 文件数 / 字节 | 24 / 148,650,102 | 24 / 148,612,515 |
| `PACKAGE_MANIFEST.json` SHA256 | `4113db646704f86154d24fe06d5965ecaf5ad632717c23e48a20b8de5ba9840c` | `6fb28a77…5f63` |
| `SHA256SUMS` SHA256 | `c2d77c496695658e4ef23b7b3f4f795bedfd80993d6d3a07fd8e1f579b98d3a8` | `f54f0d69…cf09` |
| 与 v5 逐字节相同（VERIFIED） | `networks/integrated_365_24h_unsolved.nc`、`networks/disconnected_365_24h_unsolved.nc`、两份 `*_BUILD_RECEIPT.json`、两份 `*_costs_active_research.csv`、`EXPECTED_VARIANTS.json`（`fixed_files_identical_to_v5 = true`） | — |
| 与 v5 不同的文件 | `code_2a77f1b8.tar.gz`（代替 `code_e0a89f8e.tar.gz`）、`COMMIT`、`RUN_PLAN.md`（第 11 节）、`run_batch3.sh`、`pack_results.sh`、`preflight.sh`、`BUILD_INPUT_CHANGES.json`（改动文件清单；构建路径不受影响） | — |
| 变体可复现 | 两遍逐字节相同（`VARIANT_REPRODUCIBILITY.json`），7 个 SHA256 与 v5 相同 | 同 |
| 清单新增字段 | `drill`（演练记录文件、SHA256、提交、真实 / 合成类型）、`supplement_s1`（新模式、计划第 11 节、账本修复） | — |

### 4.3 干跑（B4.3；本机，无 Gurobi；脚本 `scripts/dryrun.sh`，证据 `evidence/dryrun_v6/`）

| 步 | 内容 | 结果 |
|---|---|---|
| 预检 | v6 解包到 `/home/jin/m10r_dry/pkg`（代码解到 `./repo`：1,437 个文件，无 `research/`，含 `s4d_ledger_redo.py`）；`preflight.sh`：`guards`（干净 shell）OK，`guards` 在 shell 残留 `LEDGER_CMD` 时 **FAILED**（按要求）；`sha`：22 个文件 OK；`networks`（基础网络 = 构建回执、7 个期望变体）、`env`（关键包相同）、`profile`（两档案内点路径，Threads 8 / 16）、`code`（运行与后处理模块无许可导入）、`tools` 全部 OK → **PREFLIGHT OK**；`resources` 在本机 FAILED（16 核 < 25、内存 10 GiB < 64 GiB；仅作信息） | 通过 |
| 批次模式 BUILD_ONLY（R1–R11） | **未做**：本机计算累计约 71 分钟（下文），该步约 19 分钟、峰值 10 GiB，会触及指令第 7 条 1.5 小时上限 → 停下报告（第 7 节决定 4）。批次模式未变的现有证据：全量测试中 `test_m10p_batch3.py` 的 25 个批次替身用例全部通过且 `START` 行 `mode=batch`；`--only R11` 的 BUILD_ONLY 构建与 v5 干跑的 R11 逐项相同（下一行） | 待用户授权 |
| `--only R11` 的构建到求解前退出 | `BUILD_ONLY=1 … --only R11`（独立 RUN_DIR）：`mode=only(R11)`、`existing_stop=` 空；BASE_CHECK all_equal；只生成 R11 的变体，SHA256 `85ade73c…` = `EXPECTED_VARIANTS.json`；`--stop-before-solve` 构建 111 s、峰值 9.77 GiB，LP 9,705,916 行 × 4,357,448 列、22,556,267 非零元，BUILD_CHECK 13 项全过；**与 v5 干跑的 R11 相同**（LP 维数、求解参数含 TimeLimit 28,800、网络 SHA256；`ONLY_R11_VS_V5.json`）；无求解调用（许可绊线）；包 `results_light_only_R11_*`（13,855 B）；`DONE_ONLY` | 通过 |
| `--repost R9` 在 56×3h 保留存量结果上 | 求解 1 的结果以硬链接副本映射为 R9（smoke_s01 一体化 / 不互联映射为 R1 / R2，`BATCH_REFERENCE.json` 为 smoke_s01 参照；`TRUNCATE=56 ALLOW_UNREGISTERED=1`）：原 R9 目录逐文件（路径、字节、修改时间）**不变**；账本重做 B16 `'59'` → 3.7e-12；违反分析与原结果逐项相同；C1 `abc=111`（(a)(b) 的数值与原 PRECISION 相同，`c1_ab_equal`）；M12、Owen 退出 0；GATES_V6 **ACCEPTED_LAYER2**；`REPOST_CLASS:R9:label=ACCEPTED_LAYER2:class=accepted`（只记录）；`REPOST_CHECK_R9: violations_equal=True, c1_ab_equal=True, c1_c False→True, b16 False→True, label NOT_ACCEPTED→ACCEPTED_LAYER2`；包 `results_{light,full}_repost_R9_*`（442,881 / 28,492,638 B）；随后 `--summary-s1 --use R9=…/s1/R9`：`BATCH3_SUMMARY_S1.json`（B6 = 9.899 bn 即 smoke_s01 的 R2 − R1；R9 标签来自重做目录；原汇总不存在于该演示目录，不涉及） | 通过 |
| 全类型演练 | 3.3 节（`DRILL_POSTPROC.json`，包提交 `2a77f1b8`） | 通过 |

**本机计算用时（指令第 7 条，上限 1.5 h；VERIFIED 自各 STATUS 时间戳）：** 求解 1 含 v5 后处理 6.4 min；修复前 / 后回归 3.6 + 3.9 min；365×24h 变体生成与结构核对 1.5 min；单元与运行模式测试约 8 min；求解 2、3 含后处理 6.9 + 5.9 min（间隔 5 min 不计）；演练 8 + 1 + 1 min；全量测试 15.4 min；v6 打包 1.1 min；干跑预检 1 min、`--only` 2 min、`--repost` 2 min——合计约 **71 min**；用户补充授权的 365×24h 回归（2.3 节 (ii)）实际约 2 min（9 个运行各 10–13 s），合计约 **73 min**；磁盘新增约 6 GB（56×3h 三次求解与回归 / 演练目录、`/home/jin/m10r_dry/`、`/home/jin/m10r_365/`），低于 20 GB。BUILD_ONLY 批次干跑（约 19 min）按用户决定不做。

## 5. 云端补做执行指令需要的值与步骤

**前提：** 实例上原 `runs/batch3/` 完整（R9 的 `lp/`、`solution/`、求解后网络与对偶；`BATCH_REFERENCE.json`；`variants/R11/` 已在第 0 阶段生成并与 `EXPECTED_VARIANTS.json` 相同）；v6 部署包按 M10 的方式单路上传并全量核对；`preflight.sh` 把 v6 代码解包到 `./repo`（旧 `./repo` 自动改名保留，不删除）；许可只在 R11 步骤放置，用完即删。

| 步 | 命令（包目录；同一 tmux shell） | 许可 | 预计时长（INFERENCE） | 产出 / 回退 |
|---|---|---|---|---|
| 0 | 上传 v6（148,650,102 B，24 文件），`sha256sum -c SHA256SUMS`；`PY=… bash preflight.sh`（`PREFLIGHT_ONLY=guards,sha,networks,env,profile,code,tools,resources`；许可节放到第 2 步前） | 否 | 上传 0.73 MB/s 约 3.5 min；预检 1–2 min | 失败即停 |
| 1 | `PY=… bash run_batch3.sh --repost R9 --into runs/batch3_s1` | 否 | 账本重做约 1–2 min（365×24h 网络 160 MB 读入 + 账本）+ 违反分析 105 s + C1 72 s + M12 7 s + Owen 54 s + 导出与打包约 2 min ≈ **10 min**；峰值约 9–10 GiB | `runs/batch3_s1/R9/REPOST_CHECK.json`：`violations_equal` 与 `c1_ab_equal` 必须为 true，否则停下报告；标签预期 ACCEPTED_LAYER2 |
| 2 | 放置许可（M10 方式）→ `PREFLIGHT_ONLY=licence` → `GRB_LICENSE_FILE=… PY=… bash run_batch3.sh --auth "<用户授权原文>" --only R11` | 是 | 不互联类求解 0.4–0.5 h（R2 1,793 s、R4 1,423 s、R8 1,478 s、R9 3,255 s 墙钟；R11 的分国 WACC 变体与 R2 同规模）+ 330 s 间隔 + 后处理 6–8 min ≈ **0.5–1.5 h**；单会话峰值约 17 GiB | 无解 → `UNUSABLE`（不重试）；G2 不过 → `STOP` 追加、退出码 3、报告用户；之后 `shred -u` 删除许可并 `ls` 核实 |
| 3 | `PY=… bash run_batch3.sh --summary-s1 --into runs/batch3_s1 --use R9=runs/batch3_s1/R9` | 否 | < 1 min | `runs/batch3_s1/batch_s1/BATCH3_SUMMARY_S1.json / .md`；原汇总不改 |
| 4 | 回收：`results_light_repost_R9_*`、`results_light_only_R11_*`、`results_light_summary_s1_*`（各几十 MB）先取；`results_full_*`（R9 重做约 160 MB、R11 约 160 MB）后取；按 M10 的单路 + `sha256sum -c` | 否 | 链路 0.05–0.2 MB/s：轻量包各 1–5 min，完整包各 15–60 min | `export/R9/ARRAYS_MANIFEST.json` / `export/R11/…` 列出数组 |
| 5 | 365×24h 的 Owen 对偶形式回归（账本 / B16 / M12 已在本机完成，2.3 节 (ii)）：若原实例还在，对 R1–R8、R10 用 `--repost <编号> --into runs/batch3_s1`（每个约 10 min，无需许可；输出含 `m12_owen/`），再与原 `export/<编号>/m12_owen/` 逐数比较（本机 `compare_dirs.py`） | 否 | 实例每运行约 10 min | 列为必做项 |

**原实例不可用时的回退：** 任何 ≥ 25 核 / ≥ 64 GiB 的实例：上传 v6 → 环境安装（13.8 min 实测）→ `--only R11`（只依赖包）；R9 重做需要 `--arrays <dir>`：`lp/` 用 `s2_solve.py --stop-before-solve --network <包内一体化网络生成的 R9 变体> --scenario disconnected --solver gurobi --solver-profile formal_barrier --time-limit 28800 --costs-table networks/integrated_costs_active_research.csv` 重建（365×24h 约 70–150 s、10 GiB；M10P / M10A 已证明逐字节相同），`solution/`（X / Pi / RC，约 0.3 GB）从原实例数据盘取回，求解后网络与 `DUALS_BY_CONSTRAINT.nc` 从完整包解出放到 `runs/batch3/R9/`（或 `runs/batch3/export/R9/`），`RUN.json`、`SOLVE_RECEIPT.json`、`V5_GATES.json`、`EXPORTS.json` 从轻量包放到 `runs/batch3/R9/`，`BATCH_REFERENCE.json` 从轻量包 `batch/` 放到 `runs/batch3/`；`RUN.json` 中原实例的网络路径不存在时脚本自动改用包内同 SHA256 的登记网络（`NETWORK_PATH_R9` 行）。

## 6. 本机 Gurobi 使用记录

授权 3 次，使用 3 次，全部 56×3h（`s2_solve.py --truncate 56`，档案 A `formal_barrier` Threads 8，TimeLimit 1,750 s，墙钟 1,800 s，不重试）；没有求解任何 365×24h / 2920×3h 网络；许可只经 `GRB_LICENSE_FILE` 引用（未读取、未复制），后处理在移除该变量的环境中运行。时间为 UTC（SGT = +8 h，均在 2026-10-24 凌晨）。记录 `results_project/m10r/STATUS.txt`（证据 JSON `gurobi_local`）。

| 次 | 网络 | 变体 SHA256（前 16 位） | 开始 | 结束 | 与上次结束的间隔 | 终止 | 求解墙钟 | 峰值 | 目标值 EUR |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 保留存量（一体化 2920×3h 基础 → 不互联），v5 代码后处理 | `ffd7a691840dfb0b` | 18:32:58 | 18:38:39 | —（距 M12b 最后一次求解 2 天） | optimal | 341 s | 4.19 GiB | 318,479,975,461.52 |
| 2 | 分国 WACC 不互联（R11 类型；不互联 2920×3h 基础） | `058793c9d710efb0` | 19:19:51 | 19:25:46 | 2,472 s | optimal | 356 s | 4.38 GiB | 302,021,940,622.47 |
| 3 | b1 不互联（R8 类型；禁止区内 CO2 跨境运输） | `f824222b1d322674` | 19:30:50 | 19:35:55 | 303 s | optimal | 306 s | 4.09 GiB | 319,682,748,223.15 |

求解 2、3 用修复后的代码后处理（`smoke_s01` 本批参照）：B16 相对误差 5.7e-12 / 9.1e-12，C1 abc = 111，M12 与 Owen 可用，GATES_V6 **ACCEPTED_LAYER2**（变体回执 SHA256 为登记值）。三次之外本机没有任何 Gurobi 调用（干跑与演练的 LP 构建都以 `--stop-before-solve` 在许可绊线 `/nonexistent/…` 下进行）。

## 7. 发现但未处理；需要用户决定的事项

**发现但未处理**

1. **走廊表与存量定义：** 一体化构建把 50 条零容量候选走廊写进 `existing_cross_border_fom_ledger`（FOM 为 0，无数值影响）。更干净的做法是构建时只登记 2025 容量 > 0 的走廊，或 `apply_stock_mode` 像 `apply_remove_countries` 一样过滤 meta；两者都会改变变体网络字节（`EXPECTED_VARIANTS.json` 须重登记、R9 的 G2.1 登记值改变），本指令按"只修后处理"处理，留给第四批之前的构建层清理（PROPOSED）。
2. **`s2_solve.py` 的账本步骤在求解进程内执行：** 账本缺陷只能在求解后暴露；`s4d_ledger_redo.py` 现在能从求解后网络独立重算，但求解进程内的 B16 仍是 G2.3 的来源。建议后续把 S4D-3 导出块改为求解后独立步骤（PROPOSED，本指令不改）。
3. **`m08a_variants.py` 的脚本哈希写入变体 meta：** 同一基础网络、同一配置生成的变体在脚本改动后 SHA256 改变（本次 `ffd7a691…` 对 M08b 的 `f9c9a873…`，数据全同）。已登记为已知项（与 `s2_network.py:344` 同类），不改。
4. **替身测试的时序余量：** 停批场景需要另一条通道的运行在 `wait_gap` 的 5 s 轮询内先启动（`FAKE_SLEEP_R7=8`），与 M10A 的经验一致；记录在测试注释中。
5. **Owen 审计常数的新诊断键** `fom_ledger` 会出现在 `RHS_AUDIT.json` / `OWEN.json` 中（计数，不是结果数）；比较工具需忽略它。
6. **完整包：** 本指令主体结束时下载 83 %；之后由 M10 的续做下载完成并核对通过（SHA256 `46f1afbc…`，`FULL_VERIFY.json` 461 文件、0 问题，解包到 `full/unpacked/`），用户补充授权后已用于 2.3 节 (ii) 的 365×24h 账本 / B16 / M12 回归；Owen 审计仍需实例上的数组（第 5 节第 5 步）。
7. **演练脚本的两处自身问题（已修，`cddc3f95`、`2a77f1b8`）：** 合成解的 LP 构建必须用 `SMOKE_TEST_ONLY` 标签（`s2_solve.py` 的截断规则）；全为 0 的合成时间序列在 PyPSA NetCDF 导出时被丢弃，改为 1e-9 MW 流量 / 1.0 对偶。演练记录中 8 种真实类型的结果产生于 `ae7e3f6e`、合成类型产生于 `2a77f1b8`（两次提交之间后处理代码无改动，只改了合成解脚本），记录字段 `types_at_other_commits` 如实列出。
8. **预检 `guards` 节的提示措辞**（M10 发现 5）仍在：`NOTE: CGROUP_ROOT=… (operational override)` 总会打印；未改。
9. **干跑证据中的许可字样：** `evidence/dryrun_v6/PREFLIGHT.txt` 与各 `STATUS` 文件含预检 / 运行脚本自身的措辞（"no licence"、`licence_gap_s=`），不是许可内容；按结果包的扫描模式（`license[i]d|registered to|wls(secret|accessid)`）交付目录 0 处命中。

**需要用户决定**

1. **云端补做的执行与机器：** 按第 5 节在原实例（优先）或替代实例执行 `--repost R9` → `--only R11` → `--summary-s1`；是否同时在实例上对 R1–R8、R10 做 `--repost`（每个约 10 min，无需许可）以补齐 365×24h 的 Owen 对偶形式回归（账本 / B16 / M12 已在本机逐项相同，2.3 节 (ii)）。
2. **R9 新标签的登记：** 由 `--repost` 得到后，按 `RUN_PLAN.md` 11.3 的格式登记为"事后修复的代码缺陷"（原标签 NOT_ACCEPTED、原因、修复提交 `40ecdf57`、回归证据、新标签 + `REPOST_CHECK.json`）；请在看到云端结果后确认。
3. **构建层清理的时机（发现 1、2）：** 是否在第四批指令之前做（会改变 EXPECTED_VARIANTS 与 G2.1 登记值），还是第四批之后。
4. **批次模式 BUILD_ONLY 干跑（R1–R11）未做（用户 2026-10-24 决定不做）：** 本机计算在完成其余项目后已接近指令第 7 条的 1.5 小时上限，该干跑约需 19 分钟、峰值 10 GiB；用户改为授权约 40 分钟做 365×24h 账本 / B16 / M12 回归（2.3 节 (ii)，实际用时约 2 分钟）。批次模式未变的证据：全量测试中 25 个批次替身用例通过、`START` 行 `mode=batch`、`BUILD_ONLY=1 --only R11` 的构建与 v5 的 R11 相同；命令仍备好（`STEP=build bash work/p1_m10r_20261024/scripts/dryrun.sh`），需要时另行授权。
