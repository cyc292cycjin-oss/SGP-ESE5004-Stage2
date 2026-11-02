# V3 运行计划（RUN_PLAN_V3）——本机 56 时段冒烟

**登记时间：** 2026-11-02（SGT），在任何 v3 网络求解之前提交并推送。看到求解结果后，第 3、4、5 节不改。

## 1. 网络与代码

构建：分支 `codex/v3-20261102` 提交 `85095e7a`（`scripts_project`、`configs`、`research_inputs` 无未提交改动），`PYTHONHASHSEED=0`，`scripts_project/s2_network.py --scenario integrated`；`no_new_xb` 由一体化网络经 `scripts_project/m08a_variants.py --set cross_border.stock_mode=no_new_xb` 派生。状态文件 `results_project/v3/builds/BUILD_STATUS.txt`。

| 文件 | 分辨率 | 字节 | SHA256 |
|---|---|---|---|
| `integrated_2920_3h_unsolved.nc` | 2920×3h | 71,397,150 | `0d31054ba361c835dd3971c3d0b42380581a6002766475f4ff149f4fbcd4717c` |
| `no_new_xb_2920_3h_unsolved.nc` | 2920×3h | 70,770,713 | `43e79c8e30d49d3d105fed66106b3cde817a4ad5be12aa8f00f5e210a6a05e8f` |
| `integrated_365_24h_unsolved.nc` | 365×24h | 32,929,223 | `b484fd52c3ddf0fa7fe9f2e15825b3265bd0b731503c02298eb81047091805d4` |
| `no_new_xb_365_24h_unsolved.nc` | 365×24h | 32,302,786 | `c6702cbf36488976f04d8862e1cb2171f80144b5caebae7ded09111bb53f63aa` |

另有完全隔离版本 `disconnected_2920_3h_unsolved.nc`（`fec3c8d0…`）、`disconnected_365_24h_unsolved.nc`（`dff75fff…`），只用于确认开关仍能构建（`S2_SCENARIO_BUILT_STATIC_PASS`），不进入运行清单。

56 时段截短版不单独存盘：由 `s2_solve.py --truncate 56` 在 2920×3h 网络上现场截取前 56 个时段（与 DFX 冒烟相同），`SOLVE_RECEIPT.json` 记录输入网络 SHA256 和 `truncated_to`。

输入与配置：

| 文件 | SHA256 |
|---|---|
| `research_inputs/registry_v5/DATA_REGISTRY.csv`（2,317 行） | `ef1d6cdd872485b54e04df8f598c829665cc4803fe7332699d4dd83911455295` |
| `configs/research/baseline.yaml` | `9f854d27c08cafae7a3966618aeb7dd418ef1ff5fb7d1e797931284ee1df085e` |
| `configs/research/no_new_xb.yaml` | `02a744d0fff558c63387b279a6b26630d95ee13ac6f7311a86b4cbeef17034c7` |
| `V3_RULES.md`（构建之前提交的版本，提交 `85095e7a`） | `2681246cb6714a7e09b400e612595d65ca86370800ef9f732637c0638d3eb19d` |
| `V3_RULES.md`（补记第 8.1、8.2 节后，求解依据） | `a35f802e0abb62de916d6f9a4033a323fd30a597e33d9c8cf9199193e0eb42ca` |
| `scripts_project/v5/v5_gates.py`（B13 判据修改后） | `53f897a0a9314a229465ffb28563f8bfb1e81692736da13be567e1876ef10e3d` |

构建之后、求解之前只改了检查脚本（`v3_static.py`、新增 `v3_smoke_eval.py`、`tests/research/test_v3.py`）和 B13 判据（`v5/v5_gates.py`，见 `V3_RULES.md` 第 8.1 节），都不进入网络，四个网络未重建。

`V3_RULES.md` 在构建后补记了第 8.1、8.2 节和第 9 节 `oil pool` 一行，都在任何 Gurobi 求解之前；补记只写判据修改、截短假象和结构差异的解释，没有改任何数值规则或阈值。

## 2. 规模（LP，预处理之前）

构建检查用 `--stop-before-solve`，`GRB_LICENSE_FILE` 指向不存在的路径，未调用求解器。

| 网络 | 列 | 行 | 非零 | 列 / 行 / 非零 相对 v2 |
|---|---:|---:|---:|---:|
| v3 一体化 56 时段 | 728,260 | 1,601,364 | 3,712,418 | +4.64 % / +3.90 % / +2.78 % |
| v3 `no_new_xb` 56 时段 | 706,906 | 1,553,782 | 3,562,184 | +5.15 % / +4.45 % / +3.37 % |
| v3 一体化 365×24h | 4,688,404 | 10,367,385 | 24,225,252 | +4.70 % / +3.93 % / +3.26 % |
| v3 `no_new_xb` 365×24h | 4,551,175 | 10,060,243 | 23,249,679 | +5.21 % / +4.48 % / +3.87 % |
| v3 一体化 2920×3h（**外推估计**） | ≈ 37,433,000 | ≈ 82,850,000 | ≈ 193,840,000 | — |
| v3 `no_new_xb` 2920×3h（**外推估计**） | ≈ 36,338,000 | ≈ 80,397,000 | ≈ 186,040,000 | — |

v2 对照：一体化 56 时段 695,950 × 1,541,222、非零 3,612,124；一体化 365×24h 4,477,801 × 9,975,377、非零 23,460,944；完全隔离 56 时段 672,300 × 1,487,648、非零 3,446,098；完全隔离 365×24h 4,325,607 × 9,629,180、非零 22,382,441。`no_new_xb` 这一行的相对值是对 v2 完全隔离，两者对照情景的定义不同，只看量级。

2920×3h 在本机放不下（WSL 10 GiB，365×24h 构建峰值已达 10.16 GiB），上表由 56 与 365 两点按时段数线性外推，用同一方法得到 v2 一体化 ≈ 35,748,000 × 79,714,000。

## 3. 冒烟运行清单

| 次序 | 情景 | 网络 | 截短 | 档案 | 成本表 |
|---|---|---|---|---|---|
| 1 | integrated | `integrated_2920_3h_unsolved.nc` | 前 56 时段 | 档案 A `formal_barrier`（Threads 8，BarConvTol 1e-8） | `builds/integrated/costs_active_research.csv` |
| 2 | no_new_xb | `no_new_xb_2920_3h_unsolved.nc` | 前 56 时段 | 同上 | 同上（派生网络沿用一体化成本表） |

- 每次求解调用一次 Gurobi：TimeLimit 3,000 s，墙钟止损 3,600 s（杀进程组）；串行，间隔 ≥ 330 s；不重试、不改参数。
- 脚本 `/home/jin/v3/smoke_v3.sh`（镜像 `scripts/wsl_v3/`）：缺确认参数即拒绝运行；工作区有未提交改动、已有求解进程或 pytest 在跑也拒绝运行。
- 调用前必须得到用户"WLS 会话空闲，可以求解"的确认。
- 许可只经 `GRB_LICENSE_FILE` 引用；`solve.log`、`solve.err` 留在 `results_project`，不进提交。
- 求解后链路（不用许可）：违反量 → C1 → M12 分摊 → Owen 对偶形式 → GATES_V6 → 停批分类 → `v3_smoke_eval.py`。`s4o_c1_precision.py reference` 和 `m12_allocation.py benefit` 的 `--disconnected` 参数指向 `no_new_xb` 运行：这是沿用的参数名，v3 的对照情景就是 `no_new_xb`。

## 4. 验收（指令阶段 3 第 4 条）

1. 两者都 optimal，或按第 119 项 (a)(b) 评估通过；
2. 账本恒等闸门 B16（`B16_LEDGER`）通过；
3. B6 = 目标值（`no_new_xb`）− 目标值（一体化）为正；
4. SG 船用燃料有来源：来自船运、东盟外进口、本地生产三项之和不小于 SG 船用甲醇负荷；
5. 无切负荷或松弛被使用：名称含 slack、shed、lost load、overflow 的发电机和链路零出力（静态检查：四个网络松弛发电机均为 0）。

报告项（不是验收项）：全部 277 条船运与过境链路的容量对偶，高于 1e-6 EUR/MWh 的逐条列出，见 D161-10；内点解没有交叉，对偶不是精确零，列表同时给最大利用率以便判断上界是否绑定。

**事先说明：两次冒烟的 B8 预期不通过。** 56 时段下 Transport 相对差 −4.1146e-05，超过 1e-6 门槛，是 EV 周型的截短假象，门槛不改（`V3_RULES.md` 第 8.2 节）。B8 不是上述验收项，是 GATES_V6 诊断项 D11，所以 `V5_GATES.json` 的 `all_passed` 也预期为 false。若 Transport 以外的部门超限，或相对差不等于这个值，不适用本说明，须另行报告。

B13 在新判据下预期通过（`V3_RULES.md` 第 8.1 节）。

任一条不通过、不可行、或非 optimal 且 (a)(b) 不通过：停下报告，不改规则、阈值、预测，不重试。

## 5. 方向性预测（看结果前固定）

原文取自 `V3_DESIGN.md` 第 8 节，按审阅决定第 1 条只把"EV 选项 E2/E3 部分抵消"改为"E2 部分抵消"，其余不改。

| 项 | 预测 | 理由 |
|---|---|---|
| B6 相对 v2（14.6153 bn） | **下降**，符号保持为正；主要驱动是对照情景放宽 | v1 中保留存量比完全隔离低 0.576 bn；v2 需求更高、气管存量 33.9 GW，下降量级可能 0.6–1.5 bn；船运两情景都付，净效应小（±0.1 bn 量级） |
| 总成本 | 两情景都上升 | 船运运费 0.4–1.2 bn；E2 部分抵消 |
| SG 船用燃料 | 95 % 以上靠船运进口，来源以 ID 为主、TH 次之，东盟外进口接近 0 | V1 中 SG 甲醇产量 0；ID、TH 占 94 %；进口价 145 远高于对偶价约 98 + 运费 |
| 液体对偶价 | 各国分化，SG 最高；幅度在运费量级（1–3 EUR/MWh） | 运费相对货值小 |
| 印尼工业节点分布 | 爪哇份额下降，苏拉威西（Morowali 一带）明显上升 | GEM 水泥 `ID_Sulawesi0 4` 21 %，Dexin 7 Mt；镍集中 |
| 跨境互联 | H₂、电扩建与 v2 相近；液体不走管网 | 船运不属跨境开关 |
| LP | 规模 +7–8 %，一体化迭代次数不下降 | 新增近退化结构 |

预测的 B6 和总成本数值是 365×24h 口径；56 时段冒烟只看符号和方向。v2 同样 56 时段的 B6 为 11.43 bn（对完全隔离，档案 `formal_barrier_1e6_t16`），档案和对照情景都不同，只作量级参考。

LP 规模这一行在构建后已知：第 2 节显示实际 +3.9 %（行）、+4.7 %（列），低于预测的 +7–8 %。预测保留原文，差异在阶段 3 报告中说明。

## 6. 求解前代码路径检查（不占 WLS 会话）

Gurobi 只有两次且不重试，所以先用 HiGHS 走一遍求解后的链路：截短前 8 个时段，`--solver highs --highs-ipm`，时限 1,800 s。这一步只看账本、Owen 主体、导出等程序是否走通，不进入验收；8 时段的经济结果不作任何解读，预测不因此改动。

| 轮次 | 代码 | 情景 | 结果 |
|---|---|---|---|
| 第一轮（`results_project/v3/path_check/`） | `19b6eaf4` | 一体化 | 程序走通；B8、B13 不通过，由此发现下述两项 |
| 第二轮（`results_project/v3/path_check2/`） | `19b6eaf4` + B13 修改（与 `67c84596` 的 `v5_gates.py` 相同） | 一体化、`no_new_xb` | 求解、违反量、C1、M12、Owen、批次参照、GATES_V6、停批分类、效益、`v3_smoke_eval.py` 全部退出码 0 |

第二轮的程序层面结果：两情景 B16 相对误差 4e-14 量级；B13 通过；B8 不通过（Transport +1.4977e-02，即 `V3_RULES.md` 第 8.2 节的 8 时段值）；`no_new_xb` 的 G2.1 网络 SHA256 一致、回读通过，解后 B5 通过；277 条链路的 `mu_upper` 都读得到。

由此改动：B13 判据（`V3_RULES.md` 第 8.1 节）。B8 不改，只作说明（第 8.2 节）。四个网络未重建。

既有测试：全部 `tests/research` 在路径检查运行期间跑过一次（45 项失败、677 项通过、58 项跳过）。替身运行器在有真实 `s2_solve.py` 进程时拒绝启动，所以这 45 项在无求解时重跑判定：42 项通过，余 3 项与 v3 无关。其中 4 项通过是因为测试期望值随 v3 更新：`test_s4c_3.py` 两项（主配置改为 `asean_account_nodal`，第 162 项）、`test_m08a_a8.py` 一项（`SUBSET_KEYS` 增加 `liquids`，`V3_RULES.md` 第 8 节）、`test_dfx_demand.py` 一项（DFX 阶段的文件清单不含 V3 新文件）。

| 余下失败 | 原因 |
|---|---|
| `test_s4c_0.py` 两项 | worktree 缺被 git 忽略的 `research_inputs/finance_v5/COUNTRY_WACC_PUBLIC_SOURCES.csv`，已知基线 |
| `test_s1_built_networks.py::test_static_validation_passes_on_reload` | `static_validate_s1` 把 `stock_mode` 键算进开关比较；该键和这段代码在基点 `0a20aefd` 已有，v3 未改；这个 worktree 的 `results_project/s1` 有链接，测试才没有跳过 |

冒烟运行期间不跑 pytest。

## 7. 资源记账

本机 Gurobi 调用：第一轮 2 次均未取得令牌，用户决定不计入额度（见第 8、9 节）；第二轮额度 2 次。本机计算上限 6 小时、磁盘新增上限 40 GB；到第一轮结束约用 1.7 小时，`results_project/v3` 约 3.1 GB。

## 8. 第一轮冒烟记录：未进入求解

用户 2026-11-02 18:46（SGT）确认 WLS 会话空闲。提交 `dd47744b`，档案 A，顺序和间隔按第 3 节执行。

| 运行 | 开始（UTC） | 结束（UTC） | 用时 | 结果 |
|---|---|---|---:|---|
| integrated | 11:11:36 | 11:30:13 | 1,118 s | `gurobipy.Env()` 报 `GurobiError`，连不上 `token.gurobi.com:443`（code 28） |
| no_new_xb | 11:35:45 | 11:54:17 | 1,113 s | 同上；两次间隔 331 s |

- 两次都是 LP 建好（21.9 s、19.4 s，规模与第 2 节相同）之后，在建立 Gurobi 环境时失败。**没有取得令牌，没有占用 WLS 会话，没有开始求解，没有任何解或目标值。** 第 4 节五条验收都无从评估，`evidence/smoke_attempt1/V3_SMOKE_RESULT.json` 的全 false 表示"无结果"，不是模型不可行。
- 原因：WSL 外连 TCP 全部超时，包括 `token.gurobi.com`、`github.com`、`1.1.1.1` 的 443 端口和 Windows 网关；DNS 正常；WSL 为 NAT 模式。Windows 本身能连上令牌服务器，出口网卡是 Cisco AnyConnect 虚拟网卡。AnyConnect 是否就是根因尚未验证。
- 这个外连中断今天早些时候已经发现（推送因此改走 Windows，审阅决定第 3.2 条），我在启动冒烟前没有检查 WSL 到令牌服务器的连通性，属于本步骤的疏漏，第二次调用本可避免。
- 按指令这是 2 次调用，限额已满，不重试。规则、阈值、预测都未改动，网络设置也未改动。
- 后续若获新授权：网络、档案、验收、预测不变；`smoke_v3.sh` 已加入求解前的令牌连通性预检（只做 TCP 连接，不读许可），输出到 `results_project/v3/smoke_r2`，第一轮目录保留不动。

## 9. 第二轮冒烟授权（求解前登记）

用户 2026-11-02（WSL 时钟约 12:00 UTC，20:00 SGT）的决定，原话："已断开 AnyConnect VPN。两次未取得令牌的调用不计入额度，授权重跑 2 次（一体化、no_new_xb，间隔 ≥ 330 s），结果写到 results_project/v3/smoke_r2。先测 WSL 到令牌服务器的连通性，通了再启动。HPC 冒烟尚未提交，WLS 会话空闲。冒烟期间我不会连 VPN。"

- 连通性：12:01 UTC 从 WSL 到 `token.gurobi.com:443`、`github.com:443`、`1.1.1.1:443` 的 TCP 连接全部成功。断开 AnyConnect 后外连恢复，第 8 节的原因由此确认。
- 第二轮与第 3 节相同：同一网络（SHA256 见第 1 节）、档案 A、TimeLimit 3,000 s、墙钟止损 3,600 s、串行、间隔 ≥ 330 s、不重试、不改参数。第 4、5 节不变。
- 脚本的改动只有预检和输出目录，求解参数未动。
