# S4M：主算设置更新（第 114、115 项）、冒烟、部署包重建与 365×24h 试点（第 116 项）

**版本：** v1，2026-10-19 12:20 SGT，由 Claude（审阅端）写入。开始前核对本文件 SHA256，与同目录 `S4M_INSTRUCTION_SHA256.txt` 一致才执行；不一致就停下报告。
**模型：** Fable 5.1（或 Opus 5.5），最高强度。**所有过程说明、进度汇报和思考要点一律用中文输出**（代码、命令、文件名、配置键保持原样）。
**用户授权：** 第 114、115、116 项已确认（2026-10-19 12:12 SGT）；本指令中的本机冒烟与条件性本机试点由用户在启动时的授权原文覆盖。工作原则第 3、6、7、8 条照常适用。

## 背景

S4L（PR #37）：近零量清理（修正规则）满足事先固定的全部标准；crossover 失败，放弃；BN、SG、VN 生物质需求恰等于潜力（零余量）是 L23 最大原始违反与高影子价格的来源，98 % 余量诊断两情景最优、门槛全过。

## 收敛规则

只做本指令列出的内容。其他发现写入"发现但未处理"，不修改。

## 通用规则

档案 A 不改；非最优不重试；不改历史结果与 SHA 定点；不合并 main，不 force-push；Gurobi 许可只通过 `GRB_LICENSE_FILE` 只读引用；学术 WLS 同时最多 2 个会话，运行期间不得另开 Gurobi 求解。
- **分支：** 从 PR #37 最新提交（S4L，先核实）开出 `codex/s4m-mainline-pilot-20261019`，draft PR 叠在 #37 上。每个子步骤一次提交，更新 `work/p1_step4m_20261019/S4M_PROGRESS.md`。

## S4M-0 登记

注册表登记第 114 项（`dust_cleanup` 主算 on，off 为对照；crossover 不作正式或核验档案）、第 115 项（`biomass_overflow_cap_share` 主算 0.98，理由：需求恰等于潜力为规则造成的边界情形，潜力为 C 级、每年 100 % 采收不现实；1.0 列入第二批敏感性）、第 116 项（先试点再整批）。

## S4M-1 主算设置与构建

1. `configs/research/baseline.yaml`：`research.numerics.dust_cleanup: on`；`research.s2.industry.biomass_overflow_cap_share: 0.98`。其余不变。
2. 构建一体化 STEPS、不互联 STEPS、一体化 NZE、不互联诊断（56×3h 与 365×24h），静态校验通过；用 S4I 审查脚本复核（A 节无新增问题；NZE 与一体化只差燃料价格；不互联恰好移除全部跨境组件）；核对三国生物质比值为 0.980、清理后各池母线余量 ≥ 0。

## S4M-2 冒烟（本机，56×3h，档案 A，已授权）

一体化 STEPS、不互联 STEPS、一体化 NZE，各 30 分钟止损、不重试。报告状态、门槛、目标值、B6、分国差额，与 S4K-3 及 S4L-5 诊断对比；三国生物质影子价格。任一运行非最优或门槛不通过即停下报告。

## S4M-3 部署包重建（S4L 版脚本）

1. 以 `p1_step4l_20261019/cloud_package/` 的脚本为基础（`setsid` 进程组终止、等待退出再导出、回执版本核对、cgroup 配额检查），重建部署包到 S4M 最终代码提交；四个 365×24h 网络与冒烟网络逐组件一致。
2. TimeLimit 与墙钟上限做成运行参数（`GUROBI_TIME_LIMIT_S`、`WALL_CAP_S`），缺省按 L23 实测放大为 14,400 s / 15,300 s，写入资源估算。
3. 新增速度探针脚本 `speed_probe.sh`：在实例上用部署包内的 56×3h 一体化网络跑一次档案 A（单运行，30 分钟止损），输出 Gurobi 每 work unit 秒数与每次迭代秒数，并与本机 S4M-2 的同一运行对比，给出速度比。探针需要用户单独授权后才在云端运行。
4. 第二批敏感性清单沿用 S4K 的 14 项，并加入 `numerics.dust_cleanup=off`、`s2.industry.biomass_overflow_cap_share=1.0`；不打包、不运行。
5. 更新 `CLOUD_RESOURCE_ESTIMATE.md` 与 `CLOUD_DEPLOY_STEPS.md`（含选机建议：求解只用 CPU，按 CPU 型号与探针速度选机；先探针、再试点、后整批）；写明 S4K 部署包（56d28358）作废。

## S4M-4 本机资源核对与条件性本机试点（第 116 项 (1)(2)）

1. **核对（只读）：** WSL 内 `/proc/meminfo` 的 MemTotal 与 MemAvailable、`nproc`；Windows 物理内存（例如 `powershell.exe -NoProfile -Command "(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory"`）；`.wslconfig` 中的内存设置（如存在）。写入进度文件。
2. **条件：** 仅当 WSL 的 MemTotal ≥ 24 GiB 且 MemAvailable ≥ 20 GiB、可用磁盘 ≥ 20 GB 时，执行本机试点；否则不执行，报告核对结果，试点改在云端（另行授权）。不要修改 `.wslconfig` 或重启 WSL。
3. **本机试点（用户授权原文覆盖）：** S4M 构建的一体化 STEPS 365×24h，档案 A，8 线程，Gurobi TimeLimit 14,400 s，墙钟上限 15,300 s，不重试、不改参数、不 warm start；运行期间不得启动其他 Gurobi 求解；每 15 分钟记录进度（迭代、残差、RSS、MemAvailable）。若 MemAvailable 降到 3 GiB 以下，记录后立即终止该运行（保护本机），写明原因。
4. **试点报告：** 终止状态、迭代轨迹（有无停滞或"跳开"）、用时与峰值内存、门槛（含 `all_passed_solver_tolerances`）、目标值；若非最优，按 L23 §6 的方法做只读违反分析，与 L23 一体化对比（违反的约束族、量级，生物质池行是否消失）。

## S4M-5 报告

`work/p1_step4m_20261019/S4M_REPORT.md`（开头 10 行以内摘要）与 `S4M_EVIDENCE.json`：S4M-1 至 S4M-4 结果；"发现但未处理"；需要用户决定的事项（试点结果的含义；整批运行的地点、硬件与授权；若试点仍非最优，正式结果验证口径的讨论材料）；上云前清单。完成后停止，等待审阅。

## 停止条件

- 静态复核发现新错误；冒烟非最优或门槛不通过；
- 部署包网络与冒烟网络不一致；
- 本机资源不满足 S4M-4 条件（此时不执行试点，正常写报告）；
- 本机试点中 MemAvailable < 3 GiB（终止该运行并报告）。
