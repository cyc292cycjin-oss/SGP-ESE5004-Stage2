# M12 报告：分摊分析流程——Owen 分配、线路净租金区间、燃料舱参与者、去一国检查、右端项审计（第 133 项；不求解）

**摘要（等级：VERIFIED = 实际数组 / 回执；INFERENCE = 机制解释；PROPOSED = 未执行）**
1. **⚠ 醒目发现（VERIFIED）：指令 §0 的成本形式（= 现行账本：资产成本 + 节点对偶下净买入 − 净卖出 ± 走廊净租金）不等于 Owen 的 y′bᵢ。** 差额几乎全部来自 KVL 回路约束：这些行右端项为 0、但同一回路含不同所有者的线路，其对偶把价值在所有者之间转移。S4N 试点 365×24h：VN +0.257、LA −0.257、MM +0.042、TH −0.036、ID −0.034、MY +0.034 bn（KVL 解释后剩余 ≤ 7 M EUR）；56×3h 冒烟：KH −0.91、TH +0.84 bn。右端项归属前提本身成立；未改模型，已实现 Owen 对偶形式，主值口径待审阅端决定（§6 D1）。
2. 右端项审计（VERIFIED，只构建不求解）：365×24h 一体化 LP 9,017,345 行，构建 42 s、峰值 8.05 GiB；非零右端项 1,005,680 行 = 国家 1,004,488 + 跨境对 97 + 燃料舱 730 + 池母线按负荷拆分 365；**无主 0、无法归属 0**。唯一跨参与者耦合族 = KVL（16,790 行，齐次）。
3. Owen 对偶形式在 365×24h 上闭合：y′b + 列界项 + 目标常数 − 目标值 = −6.4 万 EUR（相对 −1.2e-7）。
4. 去一国（VERIFIED）：11 国变体（`m08a_variants.py`）全部满足 b(N − i) = b(N) 在剩余参与者上的限制，变体中无任何行引用被移出国；VN 另在 365×24h 复核。
5. 玩具 3 国 LP（scipy HiGHS，穷举 7 个联盟）：Owen 在核心内、恒等式成立、α 不改变总量、无耦合时市场形式 = 对偶形式；退化例中 α ∈ [0, 1] 每点都在核心内，且核心允许的 α 恰为 [0, 1]；HiGHS 返回顶点 α = 1。
6. 修正前结果跑通（只验证流程）：S4N 一体化 + S4O-6 不互联，B16 7.2e-9 / 6.5e-7；α = 0.5 与现行账本逐实体偏差 ≤ 1.5e-5 EUR；S4P 第 8 方面规则表复现到 1.5e-13 bn；B6 69.243 bn；Owen 受益为负的只有燃料舱（−1.215 bn）；比例规则在 B6 > 0 时不可能给出负受益。
7. S4P 规则 (ii)(iii) 的投资与租金**不是同一比例**（租金 100 / 0、设施成本 50 / 50），与同比例规则之差 = 各走廊设施成本的一半；(i)、(v) 同比例且在区间内。
8. α 区间：市场形式下 TH 0.66、LA 0.64、VN 0.46 bn；Owen 对偶形式下只有 MY|TH 显著（MY 0.30、TH 0.31 bn），其余 ≤ 0.02 bn——LA|VN 等走廊的市场"净租金"实为 KVL 回路租，不是可任意拆分的退化对偶。
9. C3 已接入第三、四批运行脚本；`tests/research` 全量 544 passed / 64 skipped / 0 failed；分支 `codex/m12-allocation-20261021`，draft PR 见 §8。

---

## 1. 原理与公式

**Owen (1975) 线性生产博弈（成本版）。** 一体化 LP：min cᵀx，s.t. l ≤ Ax ≤ u，列界 cl ≤ x ≤ cu。右端项（负荷、潜力、存量容量、国家上限、入流……）分属参与者 i：b = Σᵢ bᵢ；联盟 S 的 LP 用同一矩阵、右端项 b(S)。取一体化 LP 的最优对偶 y*（行乘子 π、列乘子 rc）：

  φᵢ = Σ_{行 r 归 i} π_r · b_r（取有效界）+ Σ_{列 j 归 i} rc_j · 界_j + 目标常数ᵢ

弱对偶给出 φ(S) ≤ c(S)，强对偶给出 φ(N) = c(N)，所以 φ 在核心内（玩具测试 §4 逐联盟验证）。目标常数 = 存量 FOM（移出 LP 的常数列）− PyPSA 的 Σ capital_cost × p_nom（可扩建组件），按组件所有者归属；365×24h 合计 2.8867 bn，与导出 LP 的 offset 2,886,727,534.79 EUR 相同。

**市场结算形式（指令 §0 的写法，也是现行账本 `s4d_ledger`）：**

  φᵢ = 本国资产成本（新建年金、存量 FOM、VOM、燃料、区域外进口）+ Σ_载体 Σ_母线 π × (净买入 − 净卖出) − Σ_{跨境走廊 l ∋ i} s_{l,i} × (租金_l − 年化成本_l)

**两者的关系（精确分解，VERIFIED：56×3h 上逐参与者复算偏差 15 EUR）：** 由驻点条件 c_j = a_jᵀπ + rc_j + s_j，

  市场形式ᵢ − 对偶形式ᵢ = Σ_{非节点行 r} π_r [(A x_i)_r − 1(r 归 i) b_r] + Σ_{j∈i} rc_j (x_j − 界_j) + Σ_{j∈i} s_j x_j

右侧第一项对"只含本参与者变量"的行是互补残差（≈ 0），对**跨参与者耦合行**是价值转移；后两项是列互补与驻点残差。本模型唯一的耦合行是 KVL（Σ_l C_lc x_l s_l = 0，右端项 0）：回路含国内线与跨境线时，π_KVL × x × s 在线路所有者之间转移价值，总和为 0。所以 **Owen 定理本身成立（KVL 是齐次行，不需要归属），但市场形式公式只有在去掉 KVL 转移后才等于 Owen 分配**。

**前提与约定：**
- 每个非零右端项都有所有者（§3 审计：成立）。
- 跨境线"两半归属"：每国拥有本国一侧的半线、且两半都具有全额容量；线路只有两国同在联盟时才可用。LP 中的单行容量约束等价于两条系数相同的半行，乘子在两半之间的任何拆分都是最优对偶（对偶退化），记为 α = 按字母序第一国的份额，α ∈ [0, 1]。
- **同一比例原则：** 走廊的年化投资、存量 FOM、运行成本与拥塞租按同一 α 拆分，即拆分**净租金** = 租金 − 年化成本。
- **主值 α = 0.5（INFERENCE）：** 不带 crossover 的内点法收敛到最优面的解析中心；两条完全相同的半行在中心处对称，乘子五五分；这也与现行"拥塞租五五分"一致。带 crossover / 单纯形会返回顶点（玩具中 HiGHS 返回 α = 1）。
- 区域外贸易按固定价格：区域外进口为固定边际成本的发电机，无量上限（审计确认无"区域外进口总量上限"行）。
- 燃料舱需求不属于任何国家，作为第 12 个参与者 `BUNKER`（第 91 项）：其右端项 = 燃料舱母线负荷与燃料舱净零行（右端项 0）。
- 东盟液体池（ASEAN oil / oil non-fossil / methanol / ammonia）上的无主组件（区域外进口、池储罐）记为 `SHARED`：没有右端项权利，Owen 价值为 0；市场形式中的池盈余是恒等式差项（现行账本规则）。

## 2. 模块说明

### C1 `scripts_project/m12_allocation.py`（只读，不调用求解器）

| 子命令 | 输入 | 输出 |
|---|---|---|
| `run` | 求解后网络（或含 `*_solved.nc` 的运行目录）、情景、可选 `PRECISION.json` | `ALLOCATION.json/.csv/.md`、`ALLOCATION_LINES.csv`（逐走廊组件）；`--register` 登记到 `EXPORTS.json` |
| `benefit` | 一体化、不互联两个 `ALLOCATION.json`（可选两者的 Owen 对偶形式） | `BENEFIT.json/.csv/.md` |
| `loo` | 全体运行 + 若干 `CC=<去一国运行目录>`（+ 不互联分摊作单独成本代理） | `LOO_CHECK.json/.md` |

- **所有者规则** 复用 `s4d_ledger.bus_entities / owners`（第 91a 项）：单端口组件按 `country` 列（ISO2）否则按母线；跨境线 / 链路（`border_class = cross_border`）→ 国家对 `A|B`；CO₂ 船运 → 出口国；燃料舱母线 → `BUNKER`；池 → `SHARED`。
- **逐走廊组件**重算新建年金、存量 FOM（含 `existing_cross_border_fom_ledger`）、运行成本、两端对偶结算与两向电量，与账本走廊表逐对核对（S4N：偏差 3e-7 EUR）。
- **分摊**：α = 0 / 0.5 / 1、按境内长度（规则 (v)）、每个参与者在各走廊 α 独立取值时的区间 [min, max]（各国端点不能同时达到）。α = 0.5 与现行 `COUNTRY_COST_LEDGER` 逐实体对账。
- **恒等式（B16）**：11 国 + 燃料舱 = 目标值（含常数），相对误差 ≤ 1e-6；池盈余单列。
- **货币**：EUR2020 与 USD2020，汇率 `s4d_ledger.report_currency` = 1 / `fx_usd_to_eur_2020` = 1 / 0.877228633 = 1.139954。
- **受益**：受益 = 不互联分摊 − 一体化分摊（α 0.5 与区间），标出为负者；读取重评后的 `PRECISION.json`；有 `m12_owen/RHS_AUDIT.json` 时并列给出对偶形式受益。
- **比例规则**：B6 = 不互联目标值 − 一体化目标值，按权重分给 11 国：SSP2 2050 人口（IIASA-WiC POP 2025）、SSP2 2050 GDP|PPP（OECD ENV-Growth 2025）、AEO8 D.1 2050 人口（TL 用 UN WPP 2024 1,889,249.5 人；对照列）、基础电力（负荷载体 `electricity`）、固定电力（+ `industry electricity`、`land transport EV`、`agriculture machinery electric`，S4R R1 口径）。燃料舱无权重，付其不互联分摊（受益 0）。
- **去一国**：c′(i) = c(N) − c(N − i)；检查 φᵢ ≥ c′(i) − 容差ᵢ（容差 = C1 (b) 分国阈值 max(1 % × |参照差额|, 0.01 bn)，取自全体运行重评后的 `PRECISION.json`）；同时报告区间下限是否仍通过、档案 / 分辨率是否相同、被删走廊存量 FOM 的另一半（沉没成本）；不可分成本 c(N) − Σ c′(i) 的符号；11 次齐全且有单独成本代理时给出 SCRB。
- **S4P 对照**：在本运行上重算 S4P 规则 (ii)(iii)（进口方 = AC + DC 净流向，无电力通道时全载体，与 `s4p_aspects.py` 相同）及其同比例对应（进口方 / 出口方 α = 1），列出差额。

### C2 `scripts_project/m12_rhs_audit.py`（LP 只构建，不求解）

- `audit`：经 `l23_violation_analysis.build_model`（与 `s2_solve.py` 导出 LP 前的模型相同，含研究约束钩子、移出目标常数列；要求 `PYTHONHASHSEED=0`）构建 linopy 模型，逐约束：右端项所有者（组件维 → 所有者；节点平衡行按 `Load.country` 拆分；标量行按名称后缀 / 组件名；仍无法确定时取行内变量的唯一所有者）、非零右端项计数、按所有者的右端项合计、跨参与者耦合行（行内变量所有者 > 1）。
- 有对偶时计算 Owen 对偶形式：导出数组（`lp/` + `solution/Pi, RC`）给出全部行与列界项；只有 `DUALS_BY_CONSTRAINT.nc`（只有行对偶）时，有界列（`StorageUnit-spill` ≤ 入流）的 rc 由驻点条件 rc = c − aᵀy 重建（56×3h 上与导出 RC 逐国一致）。并与 `ALLOCATION.json` 比较，用导出数组时做 §1 的精确分解；用求解后网络时按线路潮流计算 KVL 转移。
- `loo`：比较全体与去一国 LP 的（约束族，所有者）右端项合计；两类节点平衡族合并（去掉一国后邻国母线可能离开网状子网，行在两族间移动，权利不变）。

### C3 云端集成（`scripts_project/m08a_run_batch.sh`，第三、四批运行脚本）

- 每个运行：C1 精度检查之后、GATES_V6 验收之前（G2.3 要校验 `EXPORTS.json`），执行 `m12_allocation.py run --register`；有导出数组且 `M12_DUAL=1`（默认）时再执行 `m12_rhs_audit.py audit --solve-dir --register-dir` → `m12_owen/`，同样登记。
- 批级：level2 在 `batch_reference`（重评阈值）之后、formal 在两情景都通过之后（`STOP_NOT_ACCEPTED` 时跳过）执行 `benefit` → `OUT/M12_BENEFIT<后缀>/`。
- 去一国：`OUT/<全体运行标签>_minus<CC>/` 有 `SOLVE_RECEIPT.json` 时执行 `loo` → `OUT/M12_LOO_<标签>/`。
- 新测试钩子 `M12_CMD`、`M12A_CMD`；输入不可计算时批级步骤写出说明 JSON，不中断批次。

### 测试（`tests/research/test_m12_allocation.py`，11 项）

玩具 3 国 LP（α 0 / 0.5 / 1 三组）、α 与区间、对偶退化、共享右端项、SCRB / 比例；本机 56×3h 冒烟解上的网络分摊与审计（数据不在时跳过）；去一国右端项比对；运行脚本挂点（M08a 假流水线，无求解器）。

## 3. 右端项审计结果

**网络：** S4M-3 一体化 365×24h `integrated_365_24h_unsolved.nc`（SHA256 `4206ec5c…fdcf`，与 S4N 试点回执中的输入网络相同；M08a 后的网络尚未重建，见 M08b）。不互联网络 `disconnected_365_24h_unsolved.nc`（`b411223e…a403`，与 S4O-6 回执相同）。

| 约束族（有非零右端项或耦合） | 行数 | 非零右端项 | 国家 | 跨境对 | 燃料舱 | 按负荷拆分 | 耦合行 | 含义 |
|---|---|---|---|---|---|---|---|---|
| Bus-nodal_balance | 918,340 | 572,685 | 571,955 | 0 | 730 | 0 | — | 节点平衡；右端项 = 负荷 |
| Bus-meshed-nodal_balance | 98,550 | 45,260 | 44,895 | 0 | 0 | 365 | — | 同上；`ASEAN ammonia` 池母线 = BN、ID、MM、PH、SG、TH、VN 的工业氨负荷 |
| Generator-ext-p_nom-lower / upper | 1,449 / 1,157 | 9 / 1,157 | 全部 | 0 | 0 | 0 | 0 | 容量下限 / 潜力上限 |
| Generator-fix-p-lower / upper | 97,820 ×2 | 69,350 / 97,012 | 全部 | 0 | 0 | 0 | 0 | 存量 × 可用率 |
| Line-ext-s_nom-lower / upper | 148 ×2 | 102 / 148 | 86 / 86 | **16 / 62** | 0 | 0 | 0 | 线路存量 / 走廊上限（跨境：两半归属） |
| Link-ext-p_nom-lower / upper | 7,325 / 26 | 19 / 26 | 10 / 16 | **9 / 10** | 0 | 0 | 0 | 链路存量 / 上限 |
| Link-fix-p-lower / upper | 61,685 ×2 | 1,095 / 61,685 | 全部 | 0 | 0 | 0 | 0 | 不可扩建链路 |
| StorageUnit-energy_balance、fix 族、ext-p_nom-upper | — | 41,975 + 65,335 + 47 | 全部 | 0 | 0 | 0 | 0 | 入流、存量 |
| Store-energy_balance / Store-fix-e-upper / ext-e_nom-upper | 190,895 / 36,500 / 8 | 100 / 36,500 / 8 | 全部 | 0 | 0 | 0 | 0 | 生物质池 e_initial 等固定资源 |
| ResearchImportAnnual（19）、research_co2_storage_cap（8）、research_new_hydro_inflow（36） | 19 / 8 / 13,140 | 全部 | 全部 | 0 | 0 | 0 | 0 | 国产气年上限、国家封存上限、新水电入流 |
| **Kirchhoff-Voltage-Law** | 25,915 | 0 | — | — | — | — | **16,790** | 齐次；回路含国内线与跨境线（ID + ID|MY 2,190、MM + MM|TH 1,825、LA + LA|VN 1,460、MY + ID|MY 1,460、VN + LA|VN 1,460 …） |

其余族（容量-出力耦合、损耗代理、Store 方向、电池耦合、有损双向同步、国家净零与燃料舱净零 `research_*_co2_limit`，主配置右端项全为 0）为齐次行。没有 GlobalConstraint，`lv_limit` 未启用。

**"共享 / 无归属"清单（VERIFIED）：非零右端项中没有。** 逐项说明：
1. **`ASEAN ammonia` 池母线的节点平衡行**（365 行）：母线属东盟池，但右端项全部是 7 国的工业氨负荷（`Load.country`），已按负荷所有者拆分归属，不构成共享权利。
2. **燃料舱母线**（`ASEAN aviation international oil final`、`ASEAN shipping international methanol final`，各 365 行）：右端项 = 燃料舱负荷 → `BUNKER`。
3. **池上的无主组件**（区域外油品 / FT / 甲醇 / 氨进口发电机、池储罐）：`p_nom_max = inf`、无年上限，**没有右端项行**；它们的成本与结算之差（池盈余：一体化 −3,719 EUR、不互联 −377,753 EUR）只是 KKT 残差量级。**提议（交审阅端）：** (a) 维持现状，残差单列（推荐，金额可忽略）；(b) 归入燃料舱参与者；(c) 按各国在池的净购买量分摊。今后若给区域外进口加总量上限，该行将成为共享右端项，必须先定归属。
4. **列界：** 只有 `StorageUnit-spill` 有有限上界（= 入流），属水电所在国（365×24h：MM −0.644、LA −0.059、KH −0.030、PH −0.013 bn）。
5. **跨境对（97 行）**：跨境线 / 链路的存量下限与上限（含"s_nom + 20 GW"），按两半归属解释；变体检查确认任一端国家移出时整条走廊连同权利一起移出。
6. **耦合行：** 只有 KVL（齐次）。不影响 Owen 定理，但使市场形式 ≠ Owen（§1、§5.3）。

**去一国变体（VERIFIED）：** `m08a_variants.py --set coalition.remove_countries=[CC] --allow-stale-base`（S4M-3 网络早于 M08a 配置，只作结构证据；回执见 `evidence/c2/variant_receipts/`）。11 国在 24 时段截断模型上、VN 另在 365×24h 上：变体中引用被移出国的行 0；剩余参与者每个族的右端项合计与全体模型相同（变化 0）；被移出国的权利（含其走廊）全部消失；燃料舱负荷不变（第 12 个参与者在 N − i 中仍在）。

## 4. 玩具测试结果（`evidence/toy/TOY_EVIDENCE.json`）

3 国 A、B、C，4 个加权时段；可再生能源（容量潜力属本国）、固定价格区域外进口与兜底进口、可扩建跨境线 A–B（上限两半归属）、有损单向链路 B→C（效率 0.95）、存量固定线 A–C（容量 1，沉没年金 1.5 按 α 拆分）。c(N) = 463.60。

| α | φ_A | φ_B | φ_C | 最紧联盟余量（N 以外） |
|---|---|---|---|---|
| 0 | 91.51 | 198.48 | 173.61 | A+B 0.40、A 2.84 |
| 0.5 | 50.30 | 224.12 | 189.18 | A+B 16.71 |
| 1 | 9.09 | 249.76 | 204.75 | B 0.00、B+C 0.00 |

- 走廊净租金：A|B 51.28（上限绑定）、A|C 31.14（存量线）、B|C 0；三个 α 下市场形式与对偶形式逐国一致（≤ 1e-7 × c(N)），总量不变。
- 去一国：c′ = (A 7.59–9.09，B 174.06，C 171.71–173.21)（A 随 α 变，因 A|C 沉没成本按 α 归属），不可分成本 108.73 > 0；α 0.5 下 SCRB = (49.62, 210.08, 203.91)。
- 对偶退化：把 A–B 上限写成两条相同的半行，HiGHS 返回 y_A = −25.64、y_B = 0（顶点，α = 1）；α 以 0.05 步长扫描 [−5, 6]，核心成立的 α 恰为连续区间 [0, 1]——区间端点处 B 或 B+C 的余量为 0，区间外核心破坏。
- 共享右端项：加一条不属于任何参与者的进口总量上限后，其租金落入 SHARED，参与者之和 ≠ c(N)；按固定份额把右端项分给各国（联盟得其份额之和）后，Owen 重新在核心内。

## 5. 修正前结果的流程跑通对照（只验证流程；数值不作结论）

一体化 = S4N 试点（365×24h，optimal，C1 重评后 layer1_plus_nodal_price_settlement）；不互联 = S4O-6（365×24h，suboptimal，C1 (a)(b)(c) 通过）；两者来自同一网络版本（S4M-3 构建），都有燃料舱账户，本步作为第 12 个参与者。输出：`evidence/c43/`、`evidence/c2/`。

### 5.1 分摊（bn EUR2020，α = 0.5）

| 参与者 | 一体化市场形式 | 一体化 Owen 对偶形式 | 市场形式区间 | 不互联 | Owen 受益（对偶形式） | 市场形式受益 |
|---|---|---|---|---|---|---|
| BN | 0.765 | 0.765 | 0.765–0.765 | 0.879 | 0.114 | 0.114 |
| ID | 158.578 | 158.611 | 158.544–158.611 | 159.247 | 0.636 | 0.669 |
| KH | 2.779 | 2.785 | 2.715–2.843 | 5.205 | 2.420 | 2.426 |
| LA | −1.382 | −1.126 | −1.702 – −1.062 | 1.356 | 2.482 | 2.738 |
| MM | 2.702 | 2.660 | 2.647–2.757 | 3.833 | 1.173 | 1.131 |
| MY | 66.635 | 66.602 | 66.454–66.816 | 69.841 | 3.239 | 3.206 |
| PH | 22.463 | 22.463 | 22.463 | 22.472 | 0.010 | 0.010 |
| SG | 21.112 | 21.112 | 21.110–21.115 | 22.045 | 0.932 | 0.932 |
| TH | 54.391 | 54.428 | 54.062–54.721 | 61.905 | 7.477 | 7.513 |
| TL | −0.115 | −0.115 | −0.115 | 0.009 | 0.123 | 0.123 |
| VN | 110.631 | 110.375 | 110.403–110.859 | 162.226 | 51.852 | 51.595 |
| 燃料舱 | 77.692 | 77.692 | — | 76.477 | **−1.215** | **−1.215** |

- B16：一体化 7.2e-9、不互联 6.5e-7（≤ 1e-6）；α = 0.5 与 `COUNTRY_COST_LEDGER` 偏差 1.5e-5 / 0 EUR；按长度分摊与 `total_length_split` 偏差 1.2e-4 EUR。B6 = 69.243 bn。USD2020 见 `ALLOCATION.csv`（× 1.139954）。
- 负分摊（LA、TL）：出口收入（节点对偶下的净卖出）超过本国资产成本，即系统向其净支付。
- Owen 对偶形式下的 α 区间宽度：MY 0.298、TH 0.311、LA 0.021、KH 0.009、SG 0.006、ID 0.004、VN 0.002 bn。

### 5.2 与 S4P 结算规则表对照（`evidence/c43/C43_S4P_COMPARISON.md`）

本模块在同一结果上按 S4P 规则 (i)(ii)(iii)(v) 重算"不互联 − 一体化"分国差额，与 `ASPECT8_B6_BY_RULE.csv` 最大偏差：(i) 5e-14、(ii) 5e-14、(iii) 6e-14、(v) 1.5e-13 bn；Owen（α 0.5，市场形式）= 规则 (i)。**第 7 项结论：** S4P 规则 (ii)(iii) 只挪动租金（100 / 0）而设施成本仍五五分，**不是同一比例**；与同比例规则之差对每个国家对是 ± 走廊设施成本的一半（一体化分摊：VN (ii) − 同比例 = −1.675 bn、MY −1.066、TH +0.953、MM +0.684、PH +0.529、ID +0.408 bn）。规则 (i)（α = 0.5）与 (v)（α = 境内长度份额，同乘成本与租金）同比例，落在区间内；规则 (iv) 不计贸易结算，不属于 Owen 族。

### 5.3 市场形式 − Owen 对偶形式（KVL）

| 参与者 | 市场 − 对偶 | 其中 KVL 转移 | 其余（KKT 残差等） |
|---|---|---|---|
| VN | +0.2567 | +0.2637 | −0.0070 |
| LA | −0.2566 | −0.2571 | +0.0006 |
| MM | +0.0420 | +0.0443 | −0.0022 |
| TH | −0.0363 | −0.0383 | +0.0020 |
| ID | −0.0336 | −0.0322 | −0.0013 |
| MY | +0.0336 | +0.0338 | −0.0002 |
| KH | −0.0058 | −0.0075 | +0.0017 |

（bn；KVL 用求解后网络的线路潮流计算，线损代理使 `p0` 与 LP 变量 `Line-s` 略有不同，56×3h 上与导出 X 的精确值相差 0.5–7 %；"市场 − 对偶"本身由对偶直接算出，不受影响。）按走廊看，市场形式净租金 LA|VN 0.384、LA|TH 0.231、KH|VN 0.072、MM|TH −0.101 bn 在对偶形式中分别只有 ≈ 0、0.017、0.002、0.001 bn：这些"租金"来自回路约束而非容量稀缺。MY|TH（0.289 bn）是真正的容量租，两种形式一致。不互联运行没有跨境对，KVL 回路全在国内，两种形式之差 < 1 M EUR（VERIFIED）。

## 6. 待审阅端决定的事项

- **D1（主值口径）：** Owen 主值用对偶形式 y′b（推荐：严格满足 Owen 定理与核心），还是指令 §0 的市场结算形式（= 现行账本；与 Owen 差 KVL 转移，S4N 试点 VN / LA ±0.26 bn）。选对偶形式时，运行链已在 C1 之后计算（`M12_DUAL=1`）；云端需再构建一次模型（365×24h：本机 42 s / 8 GiB；2920×3h 约 8 倍规模，INFERENCE）。也可以"市场形式 − KVL 转移"表述，数值相同。
- **D2（α）：** 主值 0.5（内点中心，见 §1）；按长度（规则 (v)）可作敏感性。对偶形式下区间实质上只来自 MY|TH。
- **D3（东盟池无主组件）：** 维持池盈余单列（推荐）/ 归燃料舱 / 按净购买量分国。
- **D4（比例规则口径）：** 指令写"分摊 B6"；B6 > 0、权重为正时任何比例规则都不会给出负受益（燃料舱无权重、受益 0，各国吸收其 −1.215 bn）。若本意是按比例分摊一体化总成本、或以其他基准判断"受益为负"，请明确。
- **D5（权重来源）：** 人口与 GDP 主用 SSP2 2050（11 国同源）；AEO8 D.1 人口（TL 用 UN WPP）作对照。
- **D6（SCRB 单独成本）：** 暂以"不互联运行中该国分摊"作 c({i}) 代理（不互联保留液体池、CO₂ 船运与区域外进口，不是严格单独），或另行安排 11 次单国运行。
- **D7（去一国运行）：** 运行脚本尚不能直接运行 `m08a_variants.py` 的产物（`integrated_minus<CC>_<res>_unsolved.nc` 与脚本的 `<scenario>_<res>_unsolved.nc`、`BUILD_RECEIPT` / `costs` 文件命名不对应）；钩子约定读取 `OUT/<全体运行标签>_minus<CC>/`。需决定第四批的去一国清单（11 次、同分辨率、同档案）与目录约定；本步未改运行逻辑。
- **D8（沉没成本）：** 变体删除通往被移出国的走廊及其存量 FOM，另一国的那一半不在 c(N − i) 中；`LOO_CHECK` 逐国列出（S4M-3 网络跨境存量 FOM 合计约 9.4 M EUR，低于 0.01 bn 容差下限）。是否在 c′(i) 中加回，请决定。
- **D9（formal 模式阈值）：** `m08a_run_batch.sh` 的 formal 分支不调用 `batch_reference`，正式运行的 C1 (b)(c) 阈值（也是去一国检查的容差）一直是 L23 默认参照（M08a 现状，本步未改）。
- **D10（燃料舱受益为负）：** 一体化下燃料舱多付 1.215 bn。这不等于违反个体理性——燃料舱的单独成本不是不互联运行的数值——列出供判断。

## 7. 边界、偏离与说明

- 未求解模型网络、未调用 Gurobi（含许可检查）、未连云；未改模型、配置、网络与既有结果；新结果都在新目录（`evidence/`、`/home/jin/m12_local/`）。
- 单元测试中的玩具 LP 用 scipy `linprog`（HiGHS），指令允许；全量测试排除了其他步骤的 5 个玩具求解用例（与 M08a 相同）。
- 本机只构建 365×24h LP 共 7 次（一体化 4 次——审计脚本迭代、不互联 2 次、去 VN 1 次），每次 < 1 min、峰值 ≤ 8.05 GiB；未超 1 h、未超内存。另在 56×3h 冒烟模型与 24 时段截断模型上多次构建（< 20 s、≤ 1.6 GiB）。
- 去一国变体用 `--allow-stale-base`，只作结构检查；变体网络（每个约 25 MB）留在本机未提交，回执已提交。
- 修改了 `scripts_project/m08a_run_batch.sh`（C3 范围内：只加 M12 步骤与钩子，原有步骤与顺序不变）。
- S4N 试点的 `PRECISION.json` 不在其完整导出中，C4.3 用 S4O 批重评后的副本（`top/pilot_integrated/PRECISION.json`）。
- 主机、端口、密码与许可内容未写入任何文件。

## 8. 交付

- 代码：`scripts_project/m12_allocation.py`、`scripts_project/m12_rhs_audit.py`、`scripts_project/m08a_run_batch.sh`（C3）、`tests/research/test_m12_allocation.py`。
- 文档与证据：`research/06_scope_redesign/p1_m12_20261021/`（镜像 `work/p1_m12_20261021/`）：本报告、`M12_PROGRESS.md`、指令及 SHA256、`evidence/c43/`（分摊、受益、S4P 对照）、`evidence/c2/`（审计、对偶形式、去一国）、`evidence/toy/`、`scripts/`（运行与证据脚本）、全量测试日志。
- 测试：`tests/research` 全量 544 passed、64 skipped（worktree 中没有历史构建）、0 failed（头 dbb63113）。
- 分支 `codex/m12-allocation-20261021`（自 M08a 头 820c2cae）；提交 493018ae（C1 通用 + 玩具）→ f573efae（C1 网络 + C4.3）→ c94c1cbc（C2）→ dbb63113（C3）→ dd7d2efe（证据补充、全量测试）→ c863a941（报告、台账）→ 收尾提交（本节 PR 链接）；draft PR：https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/pull/46（base `codex/m08a-corrections-20261021`，叠在 #45 上）。
- 审阅包：`work/p1_m12_20261021/M12_REVIEW.zip`（work 目录内全部文件 + `code/` 下 4 个仓库文件；逐成员 SHA256 / CRC32 清单 `M12_REVIEW_MANIFEST.csv`，ZIP 自身 SHA256 见 `M12_REVIEW_ZIP_SHA256.txt`；三者不入库）。

---

## 补充 01（第 136 项）：D1–D10 落实、运行脚本修正、M08b 网络复核（不求解）

`M12_SUPPLEMENT_01.md` v1（SHA256 d8f36a14…8ad4，与 `M12_SUPPLEMENT_01_SHA256.txt` 一致）。规则同 M12：未求解模型网络、未调用 Gurobi（含许可检查）、未连云；只构建 LP 与 scipy / HiGHS 玩具 LP。

**摘要**
1. **⚠ 新发现（玩具 VERIFIED，机制 INFERENCE；S3）：** Owen 定理保证的是"矩阵博弈"（联盟 LP = 同一矩阵、右端项 b(S)，KVL 行保留）的核心。去一国变体按剩余拓扑重定回路，断开的回路没有 KVL 行（物理联盟），c_P(S) ≤ c_M(S)，**对偶形式不一定在物理博弈核心内**：玩具三组参数中对偶形式都违反 {A, B}（超出 9.9–39.5），市场形式一组违反（2.3）。M08b 网络去 VN / TH / LA 后每日 KVL 回路 71 → 57 / 42 / 43。所以第三批去一国检查是真正的经验检验；两种形式并列报告。交审阅端（S9 D11）。
2. **D1（S2）：** 主值改为对偶形式 y′b（`OWEN.json/.csv/.md`），市场形式并列，差额 = KVL 转移 + 残差；C1 (c) 扩展到对偶形式（恒等式 ≤ 1e-6 + 各参与者残差影响）。S4N 试点 365×24h：恒等式 1.24e-7、残差影响 ≤ 0.007 bn、可用；S4O-6 不互联 1.30e-6、56×3h 冒烟 2.8e-5（不通过，如实标为不可用）。`benefit`、`loo` 主值改为对偶形式。
3. **D2–D6（S4）：** α 0.5 主值、对偶形式按组件按长度拆分（差 ≤ 0.006 bn）；前提标记 `premise_failed`；比例规则 (A) / (B) 两种口径与检验；权重改为 AEO8 D.1 人口与 AEO8 **D.2** GDP（M08b 同一文件、同一 TL 规则；交接计划写的 D.6 不是 M08b 所用）；3 次去一国不算 SCRB。
4. **D7 / D9（S5）：** 第三批运行脚本在云端由基础网络生成 VN / TH / LA 变体（不加 stale 开关，记 SHA256），档案 A 各求解一次、重评、验收（`--registered-sha256` = 变体回执，`gates_v6.py` 未改）；formal 先临时参照、两次运行后本批参照重评与最终验收。停批细节交审阅（S9 D12）。
5. **D8 / D10（S6–S7）：** c(N − i) 加回剩余一方走廊存量 FOM（S4N：VN 0.18 / TH 3.30 / LA 2.12 M EUR）；燃料舱严格单独成本 106.446 bn，S4N 对偶形式份额 77.692 bn 在其内，负受益照实报告并解释。
6. **第 5 项（S8）：** 用 M08b 补充 01 重建网络（ec80668f；PR #47 原网络与现 M08b 代码配置不一致，见 S9 D13）：一体化 10,052,113 行、峰值 9.98 GiB，无主 0、无法归属 0，唯一耦合仍是齐次 KVL；不互联无耦合；11 国去一国结构检查全部通过（VN / TH / LA 为 365×24h）。
7. **测试（S10）：** D1、D2、D3、D4、D5、D6、D7、D8、D9、D10 各有单元测试（`test_m12_allocation.py` 11 → 22 项）；`tests/research` 全量 **555 passed、64 skipped、0 failed**（排除其他步骤 5 个玩具求解用例）。

### S1. 落实情况一览

| 编号 | 决定 | 落实（代码位置） | 测试 | 状态 |
|---|---|---|---|---|
| D1 | 主值 = Owen 对偶形式 y′b；市场形式并列；差额 = KVL 转移 + 残差 | `m12_rhs_audit.py audit` 写 `OWEN.json/.csv/.md`（`owen_summary`、`write_owen`）；C1 (c) 对偶形式扩展（恒等式 ≤ 1e-6 + 每个参与者残差影响）；`benefit`、`loo` 主值改用对偶形式（`_dual_alloc`） | 玩具 KVL 回路；冒烟网络 OWEN；合成受益 | 完成 |
| D2 | α 主值 0.5；按长度作敏感性；报告 [0, 1] 全区间 | 对偶形式按组件记录国家对行 y′b 与组件目标常数，`length_split` 按组件长度份额拆分 | 合成按组件拆分；冒烟（总量不变、在区间内） | 完成 |
| D3 | 池盈余残差单列；区域外进口总量上限须先定归属 | 规则写入两模块文档与 `PROPOSALS`；`owen_premise.passed`；OWEN `premise_failed` | 合成无主右端项 | 完成 |
| D4 | 比例规则两种口径：(A) 分 B6 + 去一国边际贡献检验（主）；(B) 分总成本 + 个体理性（对照） | `benefit --loo-check`；运行脚本先 `m12_loo` 后 `m12_batch` | 合成 (A)(B) | 完成 |
| D5 | 权重与模型同源；SSP2 作对照 | `socio_weights`：AEO8 D.1 人口 + UN WPP（TL）、AEO8 **D.2** GDP（TL 按 M08b 规则）、模型固定 / 基础电力 | 与源数值核对 | 完成 |
| D6 | 不计算 SCRB（只 3 次去一国） | `loo`：少于 11 次不算并写明；11 次时自动给出（注明代理） | 3 次 / 11 次 | 完成 |
| D7 | 去一国只在第三批：VN、TH、LA，365×24h，档案 A | `m08a_run_batch.sh`：`loo_runs`（云端由基础网络生成变体并记 SHA256）、`one_run` 可选网络 / 成本表、`loo_accept`、`batch_reference` 重评去一国运行 | 假流水线（3 次去一国） | 完成 |
| D8 | 加回剩余一方那一半存量 FOM（按 α） | `loo(..., alpha)`：加回值用于检查，原值并列 | α 0.5 / 0.2 | 完成 |
| D9 | formal 阈值用本批自己的分国差额，之前只作临时判定 | formal：临时参照 → 两次运行后 `batch_reference ""` 重评 → `*_PROVISIONAL.json` → 最终验收 | 假流水线（三种情形） | 完成（停批细节交审阅，见 S9） |
| D10 | 燃料舱负受益照实报告；严格单独成本检验 | `bunker_standalone`（纯算术）；OWEN 与 BENEFIT 的燃料舱一节 | 玩具 4 参与者；冒烟网络；合成受益 | 完成 |
| 第 2 节第 5 项 | M08b 网络上重跑 C2 与去一国结构检查 | `scripts/m12_s01.sh`（`--repo` = M08b worktree；M08b 补充 01 重建网络） | — | 完成（S8；网络版本见 S9 D13） |

### S2. D1：对偶形式成为主值（`OWEN.json/.csv/.md`）

- **输出：** 每个运行的 `m12_owen/OWEN.*`（运行脚本在 C1 之后、GATES_V6 验收之前生成并登记 `EXPORTS.json`）：对偶形式 α 0 / 0.5 / 1、分国区间、按长度、USD2020；市场形式（现行账本）并列；**市场 − 对偶 = KVL 转移 + 残差**——有导出数组时按所有者精确分解为 KVL 行、其余行互补、列互补、驻点残差；只有行对偶时 KVL 由求解后线路潮流计算，残差 = 差额 − KVL。`benefit`、`loo` 主值读 `OWEN.json`（没有时退回市场形式并标明）。
- **C1 (c) 对偶形式扩展：** 恒等式 |Σ 12 个参与者 y′b − c(N)| / c(N) ≤ 1e-6；每个参与者的"残差影响"（= 市场 − 对偶 − KVL，即返回解的 KKT 残差按所有者的份额，合计 = 恒等式差额）与其 C1 (b) 分国阈值并列（信息，不作判定）。`usable_for_allocation` = 恒等式通过 ∧ 运行本身 C1 (c) 通过 ∧ Owen 前提成立。
- **S4N 试点 365×24h 重跑（VERIFIED，`evidence/s01/s4n_pilot_365x24h/`；只构建 LP，35 s，峰值 8.08 GiB）：** 恒等式相对误差 1.24e-7（通过）；前提成立；可用。各国残差影响 |·| ≤ 0.007 bn（VN −0.007、ID −0.001、MM −0.002，均在 C1 (b) 阈值内）；KVL 转移 VN +0.264、LA −0.257、MM +0.044、TH −0.038、ID −0.032、MY +0.034 bn。主值（对偶形式，α 0.5，bn EUR2020）：BN 0.765、ID 158.611、KH 2.785、LA −1.126、MM 2.660、MY 66.602、PH 22.463、SG 21.112、TH 54.428、TL −0.115、VN 110.375、燃料舱 77.692。
- **56×3h 冒烟（导出数组，精确分解）：** 恒等式相对误差 2.79e-5（**不通过** 1e-6，可用 = False）——冒烟解的 KKT 残差（各国合计 −0.018 bn）；如实记录，冒烟只验证流程。
- **2920×3h 估算（INFERENCE）：** 行数 ≈ 365×24h 的 8 倍——修正前网络 ≈ 72.1 M、M08b 补充 01 重建网络 ≈ 80.4 M（365×24h 实测 10,052,113 行、构建 65 s、峰值 9.98 GiB，见 S8）；按本机比例只构建约 5–9 min、峰值约 64–80 GiB。C1（`s4o_c1_precision.py`）已经用同一个 `build_model` 为每个运行构建一次同样的模型，`m12_owen` 是第二次构建；如云端内存或时间紧张，可把两步合并为一次构建（PROPOSED，本步未改 C1）。
- **S4O-6 不互联 365×24h（`evidence/s01/s4o6_disconnected_365x24h/`）：** 恒等式相对误差 1.30e-6（**不通过** 1e-6，可用 = False；该运行为 suboptimal，C1 (a)(b)(c) 曾通过）。如实记录：正式运行若出现这种情况，对偶形式受益会被标为不可用，市场形式仍并列。

### S3. ⚠ 新发现：Owen 定理保证的是"矩阵博弈"的核心；KVL 回路在去一国（物理）联盟中断开时，对偶形式不一定在核心内

- **机制（INFERENCE，玩具 VERIFIED）：** Owen (1975) 的联盟 LP = 同一矩阵、右端项 b(S)。KVL 行（齐次）因此在联盟 LP 中保留：回路中不属于 S 的线路容量为 0，KVL 迫使回路上其余线路的潮流也为 0。去一国变体（`m08a_variants.py`）删除被移出国的组件后，PyPSA 按剩余拓扑重新确定回路，断开的回路**没有** KVL 行，剩余线路成为辐射状、可以自由输电。所以物理联盟成本 c_P(S) ≤ 矩阵联盟成本 c_M(S)，等号只在 S 不切断任何回路时成立。对偶形式由定理保证 φ(S) ≤ c_M(S)，**不保证** φ(S) ≤ c_P(S)。D1 的理由"由定理保证在核心内"对矩阵博弈成立。
- **玩具证据（`evidence/s01/toy/TOY_S01_EVIDENCE.json`，scipy HiGHS）：** 3 节点、三条线 A–B / B–C / A–C 构成回路。三组参数下：两种形式都在矩阵博弈核心内；市场 − 对偶 = 回路转移（逐国 ≤ 1e-7 × c(N)）；物理博弈中**对偶形式三组都违反 {A, B}**（超出 9.93、17.23、39.51，c(N) 约 445–477），市场形式两组在核心内、一组违反 {A, B}（超出 2.33）。即两种形式在物理博弈中都没有保证，对偶形式在玩具中更容易越界。测试 `test_toy_kvl_loop_dual_form_in_core_market_minus_dual_is_loop_transfer` 把这一点固定下来。
- **对本模型的含义：** 跨境回路（C2 审计：LA + LA|VN、MM + MM|TH、ID + ID|MY、MY + ID|MY、VN + LA|VN …）正好经过第三批去一国的 VN、TH、LA，所以去一国检查 φ_i ≥ c(N) − c_P(N − i) 是**真正的经验检验**，不是定理的推论。`LOO_CHECK` 同时报告对偶形式与市场形式是否通过（`passed`、`market_form_passed`），供比较。输电博弈文献中有"回路潮流可使核心为空"的讨论（如 Hobbs & Kelly 1992，具体结论待核实）。
- **提议（PROPOSED，交审阅端，见 S9 D11）：** (a) 维持 D1，把去一国检查作为对偶形式的经验核心检验，未通过时如实报告；(b) 若要定理意义上的保证，联盟网络须保留被移出国线路作为零容量支路（矩阵博弈），这要改变体生成规则，属模型改动，本步未做；(c) 两种形式都报告去一国检查结果（已实现）。

### S4. D2–D6

- **D2（α）：** 主值 α = 0.5；对偶形式的按长度分摊（规则 (v)）：国家对行（`Line-ext-s_nom-*`、`Link-ext-p_nom-*`）的 y′b 按组件记录，加上该组件的目标常数（存量 FOM、−capital_cost × p_nom），用 `s4d_ledger.load_length_shares()` 的组件长度份额拆分（"-reversed" 用孪生份额；缺份额 0.5，与账本相同；无法归到组件的对值 0.5）。S4N 试点：按长度与 α 0.5 的差 ≤ 0.006 bn（MY 66.596 vs 66.602），全部在区间内；区间宽度 MY 0.298、TH 0.311 bn，其余 ≤ 0.021 bn。
- **D3：** 规则写入 `m12_allocation.py` / `m12_rhs_audit.py` 文档与审计提议文本；审计 `owen_premise.passed` = 无主与无法归属的非零右端项都为 0；不成立时 OWEN 标 `premise_failed`、不可用。S4N、S4O-6、冒烟以及 M08b 网络（S8）都成立。
- **D4（两种口径）：** (A) 规则受益 s_i·B6，检验 支付 = φ_i^不互联 − s_i·B6 ≥ c′(i)（D8 加回后），等价于"给某国的好处 ≤ 其边际贡献 φ_i^不互联 − c′(i)"；只对有去一国运行的国家，容差 = C1 (b) 分国阈值。(B) 11 国按比例分 c(N) − φ_燃料舱 − 池残差，检验个体理性 支付 ≤ φ_i^不互联。Owen 主值同样两项检查。修正前流程跑通（`evidence/s01/benefit_pre_correction/`）：(A) 无去一国运行、不可计算；(B) 每种权重都有国家违反个体理性（人口：ID、KH、LA、MM、PH、TL；GDP：ID、LA、MM、PH、TL；固定电力：ID、MM、TH、TL；基础电力：BN、KH、LA、MM、PH、TH、TL），Owen 主值全部通过。数值只验证流程。
- **D5（权重同源）：** 读 M08b `m08b_demand.py` 后确认：其工业增长用的是 AEO8 **表 D.2**（实际 GDP PPP 2017），不是交接计划所写的 D.6；所以 GDP 权重 = D.2 的 2050 值，TL（不在 AEO8）= KH / LA / MM 人均 GDP（D.2 / D.1）的均值 × TL 人口（与 M08b 对人均量的 TL 规则相同）。D.2 文件按原字节复制到本分支同一路径（SHA256 9189d862…，与 PR #47 相同，合并无冲突；注册表行 `demand_aeo8_d2_real_gdp` 在 M08b 分支）。人口 = AEO8 D.1 2050（TL = UN WPP 2024 中位 1,889,249.5，与需求锚定同一组数）。主用：AEO8 人口、AEO8 GDP、固定电力、基础电力；对照：SSP2 人口、SSP2 GDP。份额（%）：AEO8 人口 ID 40.19、PH 20.01、VN 13.56、TH 8.60、MM 7.59、MY 5.19、KH 2.57、LA 1.24、SG 0.75、TL 0.24、BN 0.06；AEO8 GDP ID 38.88、VN 16.20、PH 13.89、TH 12.26、MY 10.52、SG 4.72、MM 1.99、KH 0.74、LA 0.58、BN 0.13、TL 0.08。
- **D6：** 只有 3 次去一国时 `scrb.computed = False` 并写明理由；11 次齐全且有不互联分摊时自动计算，注明"单独成本以不互联分摊代理"。

### S5. D7 / D9：运行脚本（`scripts_project/m08a_run_batch.sh`）

- **D7（第三批 level2）：** A 档两情景运行之后、CAND 运行之前执行 `loo_runs _A`：对 `LOO_COUNTRIES`（默认 "VN TH LA"）用 `VAR_CMD`（默认 `m08a_variants.py`，`PYTHONHASHSEED=0`，**不加** `--allow-stale-base`）由 `NETS/integrated_365_24h_unsolved.nc` 在云端生成 `OUT/variants/integrated_minus<CC>_365_24h_unsolved.nc` 与回执；STATUS 记录基础网络 SHA256 与 `VARIANT_<CC>:sha256=…`（回执 `output.sha256` 与文件实测一致才运行，否则跳过该国并记录）；每国求解**一次**，标签 `integrated_A_minus<CC>`、档案 A、365×24h，成本表用一体化基础的 `integrated_costs_active_research.csv`（去掉一国不改成本表）。之后的链条与普通运行相同（违约分析、C1、M12 分摊与对偶形式）；`batch_reference _A` 同时重评去一国运行；`m12_loo integrated_A` 在 `m12_batch _A` 之前（D4）；`loo_accept _A` 做 GATES_V6 验收。第四批（formal）不做去一国。
- **GATES_V6 与变体回执：** 读 `gates_v6.py` 后确认：`accept --build-receipt` 只认 `network` / `daily_network` 字段，不认变体回执；但 `accept` 本来就有 `--registered-sha256`。运行脚本从变体回执取 `output.sha256` 传入，G2.1 即比对"求解输入网络 SHA256 = 变体回执记录"——**`gates_v6.py` 未改**（M08b 补充 01 对该文件的修改不受影响）。G2.2 由 `s2_solve.py` 按网络记录的覆盖项重放配置，去一国覆盖项 `coalition.remove_countries` 在其中。
- **D9（第四批 formal）：** 每个运行的 C1 用临时参照（`PROVISIONAL_REFERENCE` 环境变量，否则同一 OUT 下第三批的 `BATCH_REFERENCE_A.json`，都没有时用 L23 默认并在 STATUS 记为"provisional only, never final"）。两次运行都完成后 `batch_reference ""`：本批自己的分国差额、两次运行重评（`grade_history` 保留）；`V6_ACCEPTANCE.json`、`FORMAL_DECISION.json` 先复制为 `*_PROVISIONAL.json`，再重新验收与 formal-check 得最终标签（STATUS `FINAL_<sc>:`）；最终 NOT_ACCEPTED 时停批，不做 M12 批级步骤。`benefit` 中对偶形式的"可用"按重评后的 C1 (c) 重新判断。
- **D9 停批细节（交审阅端，S9 D12）：** 原规则"NOT_ACCEPTED 即停批"若对临时标签执行，等于让临时阈值作出最终决定，与 D9 矛盾。现实现：临时 NOT_ACCEPTED 只有在**不依赖参照**时（C1 (a) 或任一 G2 不通过）才立即停批；只因 C1 (b) 在临时阈值下不通过时记 `PROVISIONAL_NOT_ACCEPTED` 并继续第二个运行（不重试、不改参数），由重评后的最终标签决定。
- **测试（假流水线，无求解器）：** level2 三次去一国（顺序、SHA256、网络与成本表、重评、验收、`M12_LOO_integrated_A:…:runs=3`）；formal 三种情形（临时 NOT_ACCEPTED → 最终 ACCEPTED_LAYER2；最终 NOT_ACCEPTED 停批；C1 (a) 不通过立即停批）。M08a 原运行脚本测试按 D7 更新（level2 增加 3 次去一国求解）。假流水线增加 `variants` 与有记录的 `regrade`。

### S6. D8：c(N − i) 加回剩余一方的走廊存量 FOM

- `loo`：c(N − i)_adj = c(N − i) + Σ_{随 i 删除的走廊} 剩余一方份额 × 存量 FOM（`ALLOCATION_LINES.csv` 的 `fom_existing`）；剩余一方份额 = α（被移出国为对内第二国）或 1 − α（被移出国为第一国），主值 α = 0.5。检查用加回值，原值（`c_N_minus_i_raw`、`marginal_cost_raw`、`passed_raw`、不可分成本原值）并列；`benefit` (A) 取加回值。
- 修正前 S4N 试点的数额（α 0.5，M EUR）：VN 0.18、TH 3.30、LA 2.12（其余 BN 0、ID 0.36、KH 0.86、MM 0.04、MY 2.07、PH 0、SG 0.49、TL 0）；跨境存量 FOM 合计 9.42 M EUR，远低于 0.01 bn 容差下限。

### S7. D10：燃料舱的严格单独成本

- `m12_allocation.bunker_standalone(n)`（纯算术，不求解）：燃料舱没有资源，单独时只能用区域外进口——逐燃料舱负荷母线、逐时段取最便宜的可行路线"池上区域外进口发电机 → 计量链路 → 燃料舱母线"，单位成本 = 进口边际成本 / 计量链路效率 + 链路边际成本（可扩建且有资本成本时按峰值加容量成本）。向燃料舱 CO₂ 账户排放的计量链路（化石油品）被排除：燃料舱净零行与"没有任何移除路线进入该账户"（已核对）使化石供应不可行。它是矩阵博弈中 c({燃料舱}) 的上界。
- **数值（VERIFIED）：** S4M-3（修正前）与 M08b 补充 01 重建网络都是 **106.446 bn EUR**：航空 239.55 TWh × FT 燃料进口 150.11 EUR/MWh = 35.959 bn；航运 485.59 TWh × 甲醇进口 145.16 EUR/MWh = 70.487 bn（燃料舱需求仍是 UNSD 2019 常量，两版网络相同）。S4N 试点对偶形式份额 77.692 bn ≤ 106.446 bn（余量 28.75 bn）；不互联份额 76.477 bn 也在其内。
- 受益为负（−1.215 bn）照实报告；`BENEFIT.md` 燃料舱一节写明解释：一体化改变液体燃料池价格，燃料舱作为没有资源、不能退出的纯价格接受者承担这一金钱外部性，不视为违反个体理性。
- 玩具：燃料舱型参与者（只有需求，经 A 的计量链路或区域外进口供应）4 参与者 15 个联盟全部在核心内，份额 91.54 ≤ 严格单独成本 187.5。

### S8. 第 2 节第 5 项：M08b 重建网络上的 C2 审计与去一国结构检查（`evidence/s01_m08b/`）

- **网络与代码（VERIFIED）：** M08b 补充 01（第 137 项，分支 `codex/m08b-demand-20261021` 提交 572d76fa，在 ec80668f 重建）的 365×24h 网络：integrated `75704334…b19e`、disconnected `888a009b…bee4`（`work/p1_m08b_20261021/evidence/M08B_S01_NETWORK_FILES.csv`）；本地冻结副本 `/home/jin/m12_local/m08b_s01_nets/`。模型钩子与变体脚本用 M08b worktree（`--repo /home/jin/wt_m08b_20261021`，头 6c960ca7、无未提交改动，每步前后记录一致）。**偏离交接计划：** 计划写的是 PR #47 原网络（d9fab9aa… / 7234216e…），但 M08b worktree 的配置已随其补充 01 改变（`s2.industry` 中温档拆分），原网络在不加 stale 开关时被 `m08a_variants.py` 拒绝（research_config_sha256 不同）；为满足"不加 stale 开关"，改用与该代码一致的补充 01 重建网络（交审阅端，S9 D13）。
- **一体化 365×24h：** LP 10,052,113 行（修正前 9,017,345），构建 65 s，峰值 9.98 GiB（接近本机 WSL 10 GiB 上限）。非零右端项：国家 1,104,691、跨境对 97、燃料舱 730、`ASEAN ammonia` 池按负荷拆分 365；**无主 0、无法归属 0，Owen 前提成立**。唯一耦合族仍是齐次 KVL（16,790 行；ID + ID|MY 2,190、MM + MM|TH 1,825、LA + LA|VN 1,460、MY + ID|MY 1,460、VN + LA|VN 1,460）。燃料舱母线与池母线的情形与修正前相同。燃料舱严格单独成本 106.446 bn（需求未变）。
- **不互联 365×24h：** 9,705,916 行，构建 38 s，峰值 9.97 GiB；无主 0、无法归属 0；没有任何耦合行（回路全在国内）。
- **去一国结构检查（VERIFIED）：** 变体用 M08b worktree 的 `m08a_variants.py` 由一体化 365×24h 网络生成，**不加 stale 开关**（11 份回执 `stale_config = false`，见 `variant_receipts/`；每个 3–5 s）。VN、TH、LA 在 365×24h 上（各约 50 s、峰值 9.9 GiB），其余 8 国在 24 时段截断模型上：**11 国全部通过**——变体中引用被移出国的行 0；剩余参与者每个族的右端项合计与全体相同（变化 0）；被移出国的权利连同其走廊一起消失（VN：KH|VN、LA|VN；TH：KH|TH、LA|TH、MM|TH、MY|TH；LA：KH|LA、LA|MM、LA|TH、LA|VN）；燃料舱权利不变；变体中 Owen 前提仍成立。
- **与 S3 的关系（VERIFIED 计数，INFERENCE 含义）：** 右端项检查不覆盖齐次 KVL 行。每日 KVL 回路数：全体 71 → 去 VN 57、去 TH 42、去 LA 43（KVL 行 25,915 → 20,805 / 15,330 / 15,695）；跨所有者回路（如 LA + LA|VN、VN + LA|VN）在去 VN 变体中消失。消失的回路既有被移出国的国内回路，也有经过其线路、牵连剩余国家线路的跨境回路——后者正是 S3 所说"物理联盟中剩余线路的 KVL 约束解除"的情形；逐回路区分两类本步未做。


### S9. 待审阅端决定的事项（补充 01 新增）

- **D11（S3，KVL 与物理联盟）：** 对偶形式的核心保证只对矩阵博弈成立；去一国变体是物理联盟。选 (a) 维持 D1 并把去一国检查作为经验检验（推荐，已实现，两种形式并列报告）；(b) 改为矩阵博弈口径（变体保留零容量支路，属模型改动）；或其他。
- **D12（S5，formal 停批）：** 临时 NOT_ACCEPTED 只在不依赖参照时立即停批（现实现），还是维持"任何临时 NOT_ACCEPTED 即停批"。
- **D13（S8，M08b 网络版本）：** 本步第 5 项用的是 M08b 补充 01 的重建网络（`ec80668f`，integrated 75704334…、disconnected 888a009b…），不是交接计划所写的 PR #47 原网络（d9fab9aa… / 7234216e…）：M08b worktree 的配置已随补充 01 改变，原网络在不加 stale 开关时被 `m08a_variants.py` 拒绝（research_config_sha256 不同，差异在 `s2.industry` 的温度档）。若 M08b 补充 01 被退回，须在其最终网络上再跑一次（`scripts/m12_s01.sh`，约 10 min）。
- **2920×3h 内存（S2）：** 对偶形式在云端需再构建一次 LP（约 64–80 GiB，INFERENCE）；可选择与 C1 的构建合并（PROPOSED）。
- **D5 口径说明：** 交接计划写"AEO8 D.6 人均 GDP"，M08b 实际用 D.2（实际 GDP 水平）；本步按 M08b 实际所用实现。如审阅端另有所指，请明确。

### S10. 测试

| 决定 | 测试（`tests/research/test_m12_allocation.py`，另 `test_m08a_a8.py`） |
|---|---|
| D1 | `test_toy_kvl_loop_dual_form_in_core_market_minus_dual_is_loop_transfer`（矩阵博弈核心、市场 − 对偶 = 回路转移、物理博弈越界）；`test_benefit_main_value_is_dual_form`；冒烟 `test_rhs_audit_and_dual_form_on_local_smoke`（OWEN 输出、差额分解） |
| D2 | `test_dual_length_split_by_component`；冒烟（按长度总量不变、在区间内） |
| D3 | `test_premise_failed_flag_d3` |
| D4 | `test_proportional_rule_bases_d4` |
| D5 | `test_weights_same_source_as_model_d5` |
| D6 | `test_scrb_only_with_all_11_d6` |
| D7 | `test_runner_hooks_after_c1_before_acceptance`（3 次去一国）；`test_m08a_a8.py::test_runner_level2_then_formal`（按 D7 更新） |
| D8 | `test_loo_addback_remaining_side_fom_d8`（α 0.5 / 0.2） |
| D9 | `test_formal_provisional_then_batch_reference_d9`（三种情形） |
| D10 | `test_toy_bunker_player_within_strict_standalone_cost`；冒烟（严格单独成本）；`test_benefit_main_value_is_dual_form`（燃料舱一节） |

- `tests/research` 全量（`/home/jin/m12_full_tests.sh`，排除其他步骤 5 个 HiGHS / scipy 玩具求解用例；M12 的 scipy 玩具 LP 属允许范围）：**555 passed、64 skipped（worktree 中没有历史构建）、0 failed**，128.9 s；日志 `evidence/s01/m12_full_tests_s01.log`（运行时头 5fc8dadf + 未提交的审计 `--precision` 选项，即最终代码）。

### S11. 边界、偏离与说明

- 未求解模型网络、未调用 Gurobi（含许可检查）、未连云；未改模型、配置、网络与既有结果；`gates_v6.py` 未改。新证据都在新目录：`evidence/s01/`（修正前运行的对偶形式主值、受益、玩具）、`evidence/s01_m08b/`（M08b 网络审计、去一国）；旧证据（`evidence/c2/`、`evidence/c43/`、`evidence/toy/`）未改写。
- 本机只构建 LP：365×24h 共 7 次（S4N 试点 1、S4O-6 不互联 1、M08b 一体化 / 不互联 2、M08b 去 VN / TH / LA 3），每次 ≤ 73 s；M08b 网络峰值 9.9–10.0 GiB，贴近本机 WSL 上限（10 GiB + 4 GiB 交换），未超；另有 56×3h 冒烟 1 次、24 时段截断 9 次。变体网络（每个约 30 MB）与网络副本留在本机 `/home/jin/m12_local/` 未提交，回执已提交。如实记录：最初按交接计划用 PR #47 原网络（d9fab9aa…）生成变体，11 次都被 `m08a_variants.py` 拒绝（"built with another config"，各约 2 s，未产生文件），据此改用补充 01 重建网络（S9 D13）。
- 修改的仓库文件：`scripts_project/m12_allocation.py`、`scripts_project/m12_rhs_audit.py`、`scripts_project/m08a_run_batch.sh`（D4 / D7 / D9 范围内）、`tests/research/test_m12_allocation.py`、`tests/research/test_m08a_a8.py`（D7 后 level2 多 3 次去一国求解，断言随之更新）、`tests/research/fixtures/m08a_fake_pipeline.py`；新增 `research_inputs/demand_v5/sources/m08b/AEO8_TABLE_D2_REAL_GDP_PPP2017.csv`（M08b 源文件原字节副本）。
- 主机、端口、密码与许可内容未写入任何文件。

### S12. 交付

- 代码与测试：见 S11 修改清单；证据 `evidence/s01/`（`toy/TOY_S01_EVIDENCE.json`、`smoke_56x3h/`、`s4n_pilot_365x24h/`、`s4o6_disconnected_365x24h/`、`benefit_pre_correction/`、全量测试日志、证据链日志 `S01_CHAIN.log`）与 `evidence/s01_m08b/`（`integrated_365x24h/`、`disconnected_365x24h/`、`minus_{VN,TH,LA}_365x24h/`、`loo_trunc24/`、`variant_receipts/`）；脚本 `scripts/m12_s01.sh`、`scripts/m12_s01_chain.sh`、`scripts/m12_s01_toy_evidence.py`、`scripts/m12_review_zip.py`（代码清单增加补充 01 改动的仓库文件）。
- 分支 `codex/m12-allocation-20261021`：5a4acd84（S01-1 D1）→ 53934e31（D2）→ a5be10aa（D3）→ 8e458984（D4）→ d75913f3（D5）→ 51c362dc（D6）→ 7a03fcd5（D7）→ a54f1718（D8）→ 5eefb6c4（D9）→ 5fc8dadf（D10）→ 〔证据提交〕（S01-11 / S01-12 证据、审计 `--precision`）→ 收尾提交（报告交付节、审阅 ZIP 清单）；draft PR #46 正文已更新：https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/pull/46 。
- 审阅包：`work/p1_m12_20261021/M12_REVIEW.zip`（work 目录全部文件 + `code/` 下 7 个仓库文件；逐成员 SHA256 / CRC32 清单 `M12_REVIEW_MANIFEST.csv`，ZIP 自身 SHA256 见 `M12_REVIEW_ZIP_SHA256.txt`；ZIP 不入库）。
- 完成后停止，等待审阅。
