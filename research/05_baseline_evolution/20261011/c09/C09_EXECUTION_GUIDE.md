# C09 执行说明：精确分解后的主 LP 单次求解

**状态：C09_RELEASE_READY_AWAITING_USER_START。** 发布包已就绪，本地测试 10/10 通过。目前求解调用次数为 0，AutoDL 上尚未执行任何操作。

## 1. 本轮做什么、不做什么

- **做：** 对主 LP（1,565,533 列 / 3,839,021 行 / 7,868,836 非零）做**一次** Gurobi 原生求解，然后把结果与块的精确解合并，用**原 V4** 全量验收：KKT、物理、807/385、FOM、NetCDF 回读。
- **算法：** 154 项参数与 C06/C07A 相同，只把 Crossover 从 0 改为 −1，与 C07B 完全一致。因此 C09 与 C07B 的**唯一区别是去掉了零成本解耦块**，可以直接检验"块导致 C07B Status 3"这一推断。
- **不做：** 不改 V4、Scheme A、C01R、成本或任何科学约束；不重建网络，不做 warm start，不自动重试，不恢复 G6-05，不进入 2920 时段或任何情景。
- **资源与时限：** 沿用 C07 的保护链（独立 guard、supervisor、seal）；原生求解最多 3600 秒，整个 Run 最多 7200 秒。

## 2. 数学等价性依据

见 C08 报告第 2–3 节。原 LP 可以按块分离，块内成本恒为 0，所以最优解集 = 主 LP 最优解集 × 块可行集。

- 块原始解是预先构造的 binary64 点（`release/block/`），精确有理数残差 ≤ 1.1e−16（LP 单位）。
- 块对偶取 0，在块成本为 0 时这是合法对偶。
- 运行时会从冻结的 CSC 重新核验：块是否解耦、成本是否为 0、行集合是否一致、块原始解残差是否合格。任何一项不符都会阻断，**不进入求解**。

## 3. 预先写定的判定规则

| 结果 | 结论 | 下一步 |
|---|---|---|
| R1：Status 2 且全部 V4 门槛通过 | C09_DAILY_BASELINE_ACCEPTED（仅限日诊断，不等于 Gate6/2920） | 用同一分解准备 D 阶段，需另行授权 |
| R2：Status 2，块门槛通过，但主 LP 的 KKT 未通过 | 数值问题已隔离到网络部分 | 针对 Line-s/Link-p 做定点分析，不自动重跑 |
| R3：Status ≠ 2 或无解 | "块导致 C07B"的推断在主 LP 上被否定 | 重新分析，不重试 |
| R4：块门槛失败 | 分解实现有误，BLOCKED | 不重试 |
| R5：身份、资源或回读失败 | BLOCKED_WITH_SPECIFIC_EVIDENCE | 不重试 |

## 4. 你需要在 Windows 上执行的命令

在 PowerShell 中进入本目录：

```powershell
cd D:\ResearchWorkspaces\ASEAN\work\c09_exact_decomposition_20261013
python c09_control.py deploy
```

`deploy` 会上传发布包，做 SHA 核验和 122 号机准入检查，不调用求解器。成功后会输出 `C09_RELEASE_SHA_VERIFIED`。

```powershell
python c09_control.py start
```

**这是唯一一次求解授权的使用。** 执行它即表示最终确认。命令会立即返回，求解在云端后台进行，不会自动重试。

```powershell
python c09_control.py observe
```

`observe` 是只读快照，可以多次执行。快照保存在 `monitor_snapshots\`，我会直接读取。

当快照显示 `archive` 已生成（云端封存完成）后，执行：

```powershell
python c09_control.py fetch
```

`fetch` 会把新结果归档拉回本地，并核验 SHA。

每一步执行完后告诉我一声即可，所有回执都写在本目录，我会直接读取并验收。

## 5. 本地已完成的核验

| 测试 | 结果 |
|---|---|
| T01 块的解耦、零成本、可行性（真实 CSC） | PASS，跨块元素 0，块残差 1.1e−16 |
| T02–T05 篡改负例：成本、原始解、跨块元素、行集合 | 全部被拒绝 |
| T06–T07 主 LP 维度与逐位限制 | PASS |
| T08 加载 + 精确回读（模拟后端） | EXACT_READBACK_PASS |
| T09 参数门槛：只允许 Crossover | PASS（多改一项或漏改都会被拒绝） |
| T10 合并 + 原 V4 算法试运行（使用 C07A 主 LP 向量） | 行失败 0、符号失败 0、stationarity 3353 |

T10 只是流程测试，不是对 C07A 的验收。它说明块的问题已经完全由分解处理掉，剩下的门槛只有主 LP 的 stationarity，而这正是本轮 Crossover 要检验的内容。

发布清单 SHA 为 `779b8e259f27118e32b77e06f9263b2676e872e72d46028b74e7fa3383077466`，共 35 个文件，其中 22 个与 C07 发布包逐字节一致。
