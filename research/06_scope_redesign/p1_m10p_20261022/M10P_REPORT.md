# M10P 报告（中途停止）：第三批上云准备——第 1.4 节网络重建 SHA256 与 `ec80668f` 构建不同

**摘要（2026-10-22，进行到 M10P-2 后按指令停下）**
1. 指令 SHA256 `bd2461e7…bbd1` 核对一致；只做本机准备，未连云、未上传、未调用 Gurobi。
2. 整合分支 `codex/m10-batch3-20261022` 自 M12b 头 `1f46517d` 开出；#45、#47、#46、#48 与 S4Q #41（含 `FIXED_RUNS`）全部提交已在其中，**无需补 merge**。
3. `tests/research` 全量：**582 passed、67 skipped、0 failed**。
4. 在干净提交 `b46fc23d` 上重建四个网络：**四个文件 SHA256 都与 `ec80668f` 构建不同 → 按第 1.4 节停下**。
5. **原因（VERIFIED）：** 网络数据逐项相同（全部组件静态表、全部时间序列、快照、快照权重），唯一差别是元数据 `n.meta.s2_layers.geothermal.bus_mapping_source.path` 中构建所在 worktree 的绝对路径（`/home/jin/wt_m08b_20261021/…` → `/home/jin/wt_m10p_20261022/…`），由 `scripts_project/s2_network.py:344` 写入；所指文件的 SHA256 相同。
6. 需要你决定用哪组网络文件入包（第 5 节）；决定前不做运行清单、部署包与干跑。

等级：网络内容比较、回执比较为 VERIFIED（逐列数组比较与 SHA256）；"路径是唯一原因"为 VERIFIED（元数据逐键比较只有这一处不同）。

---

## 1. 整合结果

- 分支 `codex/m10-batch3-20261022`，worktree `/home/jin/wt_m10p_20261022`，自 `1f46517d`（M12b 头，已含 M08a、M08b 补充 01、M12、M12 补充 01）。
- 逐 PR 核对（`evidence/M10P_PR_COMMIT_CHECK.json`，PR 提交列表 `evidence/pr_*.json`）：

| PR | 内容 | 提交数 | 缺失 | 头在分支中 |
|---|---|---|---|---|
| #45 | M08a | 23 | 0 | 是 |
| #47 | M08b（含补充 01） | 14 | 0 | 是 |
| #46 | M12（含补充 01） | 20 | 0 | 是 |
| #48 | M12b | 20 | 0 | 是 |
| #41 | S4Q（`FIXED_RUNS` 提交 `84532e78`、两个 1e-6 档案） | 5 | 0 | 是 |

- 无需补 merge；未 rebase、未 force-push。
- 被 git 忽略、测试与构建会读取的 2 个输入文件（`research_inputs/finance_v5/COUNTRY_WACC_PUBLIC_SOURCES.csv`、`DISCOUNT_RATE_IN_USE.csv`）自 M12 worktree 复制（与 M12b 测试所用相同）。WACC 分国变体用的 `COUNTRY_WACC_REAL_M08A.csv` 已入库，`git archive` 会带上。

## 2. 测试

- `tests/research` 全量（头 `1f46517d`，tracked 改动 0）：**582 passed、67 skipped、0 failed**，155.9 s（`evidence/M10P_FULL_TESTS_m10p1.log`）。
- 指令允许玩具 LP，故不再排除 5 个玩具求解用例：其中 3 个运行并通过（HiGHS / scipy），2 个因缺本机数据跳过（`test_s3b_r4`、`test_s4c_3`）。与 M12b 的 579 passed / 65 skipped / 5 deselected 对得上（582 = 579 + 3，67 = 65 + 2）。未调用 Gurobi。

## 3. 网络重建与 SHA256（第 1.4 节）

**做法（`/home/jin/m10p_build.sh`，同 M08b 的构建方式）：** 干净提交 `b46fc23d`（dirty 0，构建后仍为 0），`PYTHONHASHSEED=0`，`s2_network.py` 两次构建（integrated / disconnected，每次写 2920×3h 与日均 365×24h）；输入经临时符号链接指向主检出 `results_project/{assembly_v1,s1}`（构建后已删除链接）；输出到主检出 `results_project/m10p/builds/`（不入库）。两次均 `S2_SCENARIO_BUILT_STATIC_PASS`，各 87 s / 76 s，峰值 0.75 GiB。

| 网络 | 大小（B） | 本次重建 SHA256（`b46fc23d`） | `ec80668f` 构建 SHA256 | 相同 |
|---|---|---|---|---|
| `integrated_2920_3h_unsolved.nc` | 64,106,133 | `5a47e15b8a56417819c0adf95f9b94a456bc618907070dda623d4290124384f4` | `bca20fc08a149772074b620e1f587e86b0306c29e81d138fa67f4a9b9ae53cab` | 否 |
| `integrated_365_24h_unsolved.nc` | 31,524,926 | `4406fc652a9101a40223c0b69364296572e6cf0b1f4d56e241583d739dd63c0e` | `75704334dc11deeb06fc80f84ef197d65c3ac5bd658ab450e4ee1a93a3ccb19e` | 否 |
| `disconnected_2920_3h_unsolved.nc` | 63,439,167 | `117d816899c3812602a2141fe58f6cb9916b1be08739e74fc268a23b8969dd44` | `b401a68729524c885a8245962bc2a46706a1760c42ef40bdd9943e60a859bcc7` | 否 |
| `disconnected_365_24h_unsolved.nc` | 30,857,960 | `1695487e3363532cf57b53696f152c910fce3ac7fbc25288ef10ad04c1c3853a` | `888a009b5f19eb34f7f1c24e36f7c8370617a9c405b1097a9caed0599cecbee4` | 否 |

**原因诊断（只读；`evidence/M10P_NETWORK_REBUILD.json`、`evidence/M10P_NETWORK_CONTENT_DIFF.json`）：**
- 四个网络逐个加载比较：全部组件的静态表逐列相同（数值列按 NaN 相等的逐元素比较，文本列逐字）；全部时间序列逐元素相同；快照与快照权重相同。数据差异 0 处。
- 元数据逐键比较：每个网络只有 1 处不同——`s2_layers.geothermal.bus_mapping_source.path`：
  - `ec80668f`：`/home/jin/wt_m08b_20261021/results_project/assembly_v1/final_assets/SELECTED_INTEGRATION_CONTRACT.json`
  - 本次：`/home/jin/wt_m10p_20261022/results_project/assembly_v1/final_assets/SELECTED_INTEGRATION_CONTRACT.json`
- 来源：`scripts_project/s2_network.py:344` `geo["bus_mapping_source"] = dict(path=str(contract_path), sha256=sha(contract_path))`——记录了构建所在 worktree 下的绝对路径；同一行记录的文件 SHA256 两边相同。两个路径等长，故文件字节数也相同。
- 构建回执的差异同样只有路径（输入、输出、契约）与 `code_sha`；全部输入文件的 SHA256 相同。`S1_CARRIER_FRAGMENT_MANIFEST.json` 的差异是 `code_sha` 与成本表路径，成本表 SHA256 相同。
- INFERENCE：网络的数学内容相同；`ec80668f` 构建与本次重建在同一 worktree 路径下应逐字节相同（M08b 补充 01 的试构建与正式构建在同一 worktree 中逐字节相同，与此一致）。
- 这一路径依赖只影响本机构建；云端不重建网络，变体由上传的基础网络派生，不受影响。

## 4. 停止状态

- 已提交：M10P-1 `b46fc23d`；M10P-2 证据提交（见进度文件）。
- 未做：运行清单 `RUN_PLAN.md` 与 `run_batch3.sh`、部署包、本机干跑、draft PR、台账条目。
- 本机产物：`results_project/m10p/builds/`（重建网络，未删除）。

## 5. 仍需用户决定的事项

1. **入包网络用哪一组（第 1.4 节）：**
   - (A) `ec80668f` 原构建（主检出 `results_project/m08b/builds_s01/`）：数据与本次重建逐项相同；SHA256 与 M08b 补充 01 冒烟、M12b 去一国运行登记的 G2.1 网络 SHA 一致。本次重建作为"内容相同"的复核证据。
   - (B) 本次重建（`b46fc23d`，`results_project/m10p/builds/`）：内容相同，但 SHA256 是新的，与此前冒烟证据登记的 SHA 不同。
   - (C) 先改 `s2_network.py`，让元数据不记录绝对路径（例如记录仓库相对路径），再重建：属构建代码改动，四个网络 SHA256 全部改变，须重新登记；超出本步范围。
2. 是否把该路径依赖记为后续修正项（不影响本批：云端不重建网络）。
