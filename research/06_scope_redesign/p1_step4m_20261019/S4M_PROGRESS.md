# S4M 进度记录（防中断用；每个子步骤提交后更新）

指令 `S4M_CLAUDE_CODE_INSTRUCTION.md`（v1，2026-10-19 12:20 SGT），开始前核对 SHA256 = `e791015e2135845746e0ef47a50e15fae1d45d0cc586c723cc5c8197cc4c567c`，与 `S4M_INSTRUCTION_SHA256.txt` 一致（2026-10-19 12:25 SGT，VERIFIED）。所有过程说明一律用中文。

- **分支：** `codex/s4m-mainline-pilot-20261019`，自 PR #37（S4L）最新提交 4b4eb92c 开出（已核实 = 远端 `codex/s4l-numerics-20261019` 头 `4b4eb92cfe99dfd7717a7ef1f3c1c7e2b4712ad6`）；draft PR 叠在 #37 上。
- **仓库：** `cyc292cycjin-oss/SGP-ESE5004-Stage2`；WSL 路径 `/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model`；交付目录 `research/06_scope_redesign/p1_step4m_20261019/`，镜像 `D:\ResearchWorkspaces\ASEAN\work\p1_step4m_20261019\`。
- **授权（用户 2026-10-19 12:12 SGT）：** 第 114、115、116 项；本机 56×3h 冒烟 ×3（档案 A，各 30 分钟止损，不重试）；满足 S4M-4 资源条件时的本机 365×24h 一体化试点（单次、档案 A、TimeLimit 14,400 s、墙钟 15,300 s）。**云端连接与任何云端运行均未授权。**
- **规则：** 档案 A 不改；非最优不重试、不改参数、不 warm start；不改历史结果与 SHA 定点；不合并 main、不 force-push；许可只经 `GRB_LICENSE_FILE` 只读引用；WLS 最多 2 个会话，运行期间不另开 Gurobi。
- **停止条件：** 静态复核发现新错误；冒烟非最优或门槛不通过；部署包网络与冒烟网络不一致；本机资源不满足 S4M-4 条件（不执行试点，正常写报告）；试点中 MemAvailable < 3 GiB（终止并报告）。

## S4M-4 第 1 点：本机资源核对（只读，2026-10-19 12:27 SGT，VERIFIED）

| 项目 | 值 | 来源 |
|---|---|---|
| WSL `MemTotal` | 11,214,484 kB = **10.7 GiB** | `/proc/meminfo` |
| WSL `MemAvailable` | 10,419,128 kB = 9.9 GiB | 同上 |
| WSL `SwapTotal` | 4 GiB | 同上 |
| WSL `nproc` | 16 | |
| 磁盘 | `/`（ext4，仓库所在）900 GB 可用；`D:` 340 GB 可用 | `df` |
| `.wslconfig`（`C:\Users\20122\.wslconfig`） | `[wsl2] memory=11GB, swap=4GB, swapFile=D:\WSLDistros\wsl-swap\swap.vhdx` | 文件内容 |
| Windows 物理内存 | 16,890,519,552 B = **15.7 GiB**（当时空闲 7.2 GB） | `Get-CimInstance Win32_ComputerSystem` / `Win32_OperatingSystem` |

**判定：** 条件要求 WSL `MemTotal` ≥ 24 GiB 且 `MemAvailable` ≥ 20 GiB、磁盘 ≥ 20 GB。实际 `MemTotal` 10.7 GiB（`.wslconfig` 上限 11 GB，而本机物理内存总共只有 15.7 GiB，即使改 `.wslconfig` 也达不到 24 GiB）。**不满足 → 本机试点不执行**，试点改在云端（另行授权）。未修改 `.wslconfig`，未重启 WSL。

## 子步骤状态

| 节 | 内容 | 状态 | 提交 | 说明 |
|---|---|---|---|---|
| S4M-0 | 登记第 114–116 项 | 完成 | 921e050b | 注册表片段 `s4m_0`（5 行：114、115、116、问题来源、范围规则） |
| S4M-1 | 主算设置（`dust_cleanup: on`、`biomass_overflow_cap_share: 0.98`）与四个网络构建、S4I 复核、比值与余量核对 | 完成 | 921e050b（配置）；构建在 921e050b 干净树 | `baseline.yaml` `biomass_overflow_cap_share` 1.0 → 0.98（`dust_cleanup` 自 S4L-6 为 on）。四个网络（2920×3h + 365×24h）静态校验通过（`results_project/s4m/s4m1/`，各约 1 min / 0.71 GB）；S4I 审查（static + followups）重跑，`s4k_2_review.py` 对 S4K-2 网络逐项比较：差异 413 行（A10 情景差异 57、每个网络 A1 3 / A3 6 / A4 60 / A5 10 / A9 4 / components 6）全部是清理与 0.98 上限的预期结果（组件数、单侧母线、重复链路、全零负荷、BN/SG/VN 生物质需求与气需求）；交流线损代理不变（λ 全线、公式一致、求解 `transmission_losses` 0）；NZE 与一体化只差燃料价格；不互联跨境组件 0。**发现：** 0.98 上限给 BN、SG 带来的 2 % 余量使它们的小池不再被固定需求锁定，清理把 7 个 < 1 GWh 的池全部删除（S4L 修正规则只保证余量 ≥ 0）：清理后 BN 余量 1,412 MWh（需求 / 剩余池 = 0.9877）、SG 157 MWh（0.9949）、VN 2,515,451 MWh（0.9800）；指令期望的 0.980 只在 VN 成立（见报告发现与决定事项） |
| S4M-2 | 本机冒烟 ×3（56×3h，档案 A） | 完成（三项最优、门槛全通过） | 结果不进 git；证据 `evidence/s4m_2/` | 一体化 648,381,181,410.45 EUR（141 次迭代，235 s，4.10 GiB）、不互联 698,979,557,971.29（151 次，197 s）、NZE（330 s 墙钟）；`all_passed_solver_tolerances` 全 True；LP 行 1,393,079 / 1,339,505（比 S4K 少 7.2 % / 7.5 %）。与 S4K-3 参照、S4L-5 诊断的对比与生物质影子价格见报告 |
| 补充 01 | 分摊输出完整性（只改导出） | 代码与重跑完成；报告节待写 | b15ea69c + 本次 | S4M-S1 清单在 S4M-2 一体化冒烟上核对（之前：1b/1c/1d 缺、3 部分）；S4M-S2 只改导出：`s2_solve.py` `assign_all_duals=True` + `s4m_duals.write_duals`（逐约束对偶 `DUALS_BY_CONSTRAINT.nc` + `DUALS_INDEX.csv`，维度名加约束前缀，因为 `m.dual` 在本模型上抛 MergeError）、`--costs-table` → `COMPONENT_COST_BREAKDOWN.csv` + `_SUMMARY.json`、`EXPORTS.json`（字节与 SHA）；一次一体化冒烟重跑（`results_project/s4m/s4ms2/solves/s4m_A_integrated_rerun`，已授权）最优、门槛通过、目标值与 S4M-2 相对差 0.0；重跑时对偶导出失败（修前代码走 `m.dual`），对偶文件由 `s4m_duals.py` 从 `solution/Pi.npy` + `lp/clabels.npy` 离线重建（需 PYTHONHASHSEED=0，见"发现"），与 `buses_t.marginal_price` 交叉核对精确（相对差 0.0，2,516 + 270 条母线；LP 行 1,393,079 = 重建模型行）；清单之后：1a–1d、2、4 已保存，3 部分（86.6 % 组件精确匹配成本表行，其余为复合资本成本）；新增导出磁盘外推：365×24h 单次 3.2 GB（`evidence/s4m_s2/EXPORT_DISK_ESTIMATE.json`） |
| S4M-3 | 部署包重建（S4L 版脚本）、TimeLimit / 墙钟参数化（14,400 / 15,300）、`speed_probe.sh`、敏感性清单 +2、资源估算与部署步骤更新 | 完成 | b15ea69c（脚本）；包在 f50c8850 干净树上生成 | 四个网络在 f50c8850 重建，2920×3h 与 365×24h 共 8 个文件与 S4M-1 构建（921e050b）SHA256 逐一相同；`make_package.sh` → `work/p1_step4m_20261019/cloud_package_dist/`（22 个文件，260,720,379 B，`code_f50c8850.tar.gz`、探针网络 + `PROBE_REFERENCE.json`、每情景成本表）；`SHA256SUMS` 全部 OK、预检分节（sha / networks / profile / versions / tools）OK、`run_365x24h.sh --dry-run` OK（缺省 14,400 / 15,300 s）、许可特征串扫描无命中；本机脚本测试 30/30、探针测试 9/9；敏感性 16 项（+ 清理关、上限 1.0）；S4K 包 56d28358 作废。`CLOUD_RESOURCE_ESTIMATE.md` §22、`CLOUD_DEPLOY_STEPS.md` 填好 |
| S4M-4 | 本机资源核对与条件性试点 | 核对完成；**试点不执行（条件不满足）** | | 见上表 |
| S4M-5 | 报告与证据 | 进行中 | | `S4M_REPORT.md`、`S4M_EVIDENCE.json`（`s4m_5_collect_evidence.py`，含补充 01 块）、台账、镜像 |

## 提交记录（分支 `codex/s4m-mainline-pilot-20261019`）

| 提交 | 内容 |
|---|---|
| 921e050b | S4M-0 / S4M-1：注册表片段 `s4m_0`、`biomass_overflow_cap_share` 0.98、进度文件（资源核对）、汇总与链式脚本 |
| b15ea69c | 补充 01 导出代码第一版（`assign_all_duals`、`--costs-table`、`EXPORTS.json`、清单脚本）、S4M 部署脚本（缺省 14,400 / 15,300、`speed_probe.sh`、成本表入包）、脚本测试、部署步骤与资源估算草稿、证据收集脚本 |
| 8aa2fea0 | 逐约束对偶导出 `s4m_duals.py`（运行内 + 离线重建，PYTHONHASHSEED=0、交叉核对精确才写文件）、导出磁盘估算、单元测试 |
| f50c8850 | 成本拆分复合规则（海上风电接入、海底系数、碳捕集、电制生物燃料、反向孪生）→ 清单第 3 项"已保存"；单元测试 |
| 3d7bada8 | §22、部署步骤、报告、证据、台账、进度；推送，draft PR #38（叠在 #37 上） |
| a31f9bfe | `S4M_EVIDENCE.json` 的全量测试结果字段（第一次全量测试因不支持的 `--timeout` 参数未启动；重跑 1 失败 / 535 通过：失败的是新测试 `test_s4m_cost_breakdown.py` 自身——玩具线路未设 `carrier="AC"`，导出代码无误） |
| f6096752 | 修正该测试（线路 `carrier="AC"`），全量重跑 **536 通过 / 0 失败**，证据与报告更新 |

**状态（2026-10-19 13:45 SGT）：S4M-0 至 S4M-5 与补充 01 全部完成，draft PR #38 已建（叠在 #37 上）；停止，等待审阅与 §9 决定。**

## 续行点

S4M-0 至 S4M-4 与补充 01 全部完成；包在 f50c8850 生成（`results_project/s4m/s4m3/STATUS.txt`，证据 `evidence/s4m_3/PACKAGE_STATUS.txt`）。S4M-5：报告 → `S4M_EVIDENCE.json` → 台账 → 镜像到 `D:\ResearchWorkspaces\ASEAN\work\p1_step4m_20261019\` → 提交、推送、draft PR（叠在 #37 上）→ 停止等待审阅。

## 发现但未处理（执行中随时记录，交付时写入报告）

- **对偶离线重建依赖 PYTHONHASHSEED=0（已处理，写入报告）：** PyPSA `get_strongly_meshed_buses` 用 `pandas.value_counts` 排序强网状母线（本模型 270 条），同计数母线的先后随字符串哈希种子变化；另一种子下 `Bus-meshed-nodal_balance` 的约束标签被置换（每个时段的数值集合相同，199/270 条母线错位）。`s4m_duals.py` 现在无种子 0 即拒绝运行，交叉核对不精确或 LP 行数不等就不写文件。求解脚本一直导出种子 0（`run_365x24h.sh`、`s4m_chain.sh`、`s4ms2_rerun.sh`），既有结果不受影响；运行内导出（`write_duals(m, out)`）直接读 linopy 的 `con.dual`，不依赖重建。
- **S4M-1 清理后 BN、SG 生物质比值不是 0.980：** 见 S4M-1 行（需用户决定）。

## 用户中途指示

- **2026-10-19 约 13:50 SGT（报告交付后）：** "接受 BN / SG 清理后比值现状（0.9877 / 0.9949，余量 > 0），第二批照 f50c8850 的部署包运行。" → 报告 §9 第 1 项记为已决定；规则、网络、部署包不改。云端连接与运行仍未授权（§9 第 2 项待定）。
