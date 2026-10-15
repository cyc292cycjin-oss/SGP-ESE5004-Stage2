# S1 云端部署计划（已打包、未上传）

**状态：** 补充指令 01 的云端授权被补充指令 02 暂停（122 实例已到期，2026-10-15 09:45 SGT）。本计划在用户提供新实例的**主机地址、已核验的主机指纹、Python 绝对路径**后执行；在此之前不做任何连接尝试。

## 1. 部署包

| 项 | 内容 |
|---|---|
| 归档 | `work/p1_step1_20261015/S1_RELEASE.tar.gz`（成员均带 `release/` 前缀，mtime 固定为 0） |
| 清单 | `S1_RELEASE_MANIFEST.json`：逐文件 SHA256 与字节数；`S1_RELEASE_DELIVERY.json`：清单 SHA、归档 SHA、文件数 |
| 代码 | `scripts_project/s1_solve.py`（唯一 optimize 调用点）、`v5/`（KKT 代数、门槛）、`country_carbon.py`、`carrier_architecture.py`、`assembly_components.py`、`integrate_surviving_assets.py`、`scenario_network.py`（跨境 FOM 钩子）、`validation_dynamics.py`、`network_checks.py`、`build_research_network.py`、`s1_compare.py` 等 |
| 数据 | 两个情景的 365×24h 未求解网络、构建回执、已解析配置 JSON（`results_project/s1/resolved_config/*.json`，云端不需要上游 `_helpers` 依赖栈） |
| 不含 | 任何许可证文件、密钥、2920×3h 网络 |

## 2. 流程（沿用 D 阶段）

1. **身份固定：** 新实例的主机指纹写入专用 `known_hosts`；SSH 参数与 `c09_control.py` 相同风格（`StrictHostKeyChecking=yes`、按路径引用密钥、不读取不打印密钥）。
2. **部署：** 上传 `S1_RELEASE.tar.gz`，云端逐成员核验 SHA 与清单一致，写 `S1_DEPLOYMENT_RECEIPT.json`。
3. **准入：** 磁盘剩余 ≥ 20 GiB、cgroup 内存余量 ≥ 预估峰值 + 10 GiB（见 `CLOUD_RESOURCE_ESTIMATE.md`）、Python 版本与 `gurobipy/pypsa/linopy/numpy/pandas` 版本与本机一致（3.11.13 / 12.0.3 / 0.30.3 / 0.5.5 / 1.26.4 / 2.x）、许可证文件存在（只核验存在性与权限，不读内容）。不满足即停。
4. **求解：** 每个情景一次 `s1_solve.py --solver gurobi --label S1_DAILY_CLOUD --config-json ... --time-limit 14400`，参数为 D-5 集合（Method 2、Crossover −1、BarConvTol 1e-9、Aggregate 1、AggFill 0、PreDual 0、Seed 123、Threads 4、SoftMemLimit 65）。**与 D-5 的差别及理由：** 模型经 linopy 直接接口（`io_api=direct`）进入 Gurobi，而非 D-1/D-5 的原生 CSC 桥接——该桥接与 2920 Scheme-A 模型绑定；参数集合不变，检验数/对偶由 gurobipy 原生属性读出，KKT 由同一 V4 代数在原单位上独立核验。
5. **监控：** `RESOURCE.jsonl`（RSS 峰值、1 s 采样）、`gurobi.log`、`SOLVE_RECEIPT.json` 分阶段写入。
6. **回传：** 打包 `results_project/s1/cloud/<scenario>/`（求解网络、X/Pi/RC、V5_GATES、检验数/节点价格/跨境流量 CSV、日志、回执），本机逐文件核对 SHA；云端副本保留。
7. **不可行时：** `computeIIS` 写 `infeasible.ilp` + 结构性供给诊断 `INFEASIBILITY_DIAGNOSIS.json`，报告后停止；不放宽约束、不改容差、不改模型。

## 3. 本机已具备、等云端的部分

- `s1_solve.py` 已在本机用 HiGHS 对 56×3h 截断网络完成冒烟（`SMOKE_TEST_ONLY`），验证了：每国净零约束生成、B5/B6/B12 机制、检验数与节点价格导出；
- 云端只需替换 `--solver gurobi --label S1_DAILY_CLOUD` 与完整 365 时段网络。
