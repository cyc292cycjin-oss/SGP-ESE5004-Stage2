# S4O 进度记录（防中断用；时间为 SGT；不含任何主机、端口、密码或许可内容）

指令 `S4O_CLAUDE_CODE_INSTRUCTION.md`（v1，2026-10-19 20:00 SGT），开始前核对 SHA256 = `b5f4d099f2afe2e4e4d93cd2dee94ce42857b3a26f62d2622657d78b068af6aa`，与 `S4O_INSTRUCTION_SHA256.txt` 及启动消息给出的值一致（VERIFIED）。模型 Opus 5.5。所有过程说明一律用中文。

## 用户授权原文（启动消息，原样记录）

> 授权：S4O-1 至 S4O-5 的本机部分（含 S4O-3 的 3 次本机 56×3h 运行）。云端部分（S4O-6）暂未授权——本机部分完成后停下报告，等待我提供实例与授权。
> 安全约束照旧：主机、端口、密码不写入任何文件或提交；非最优不重试、不改参数、不 warm start；不合并 main、不 force-push；上传只用单路 rsync。

## 步骤状态

| 步 | 内容 | 状态 | 时间（SGT） | 提交 / 说明 |
|---|---|---|---|---|
| S4O-0 | 核对与背景 | 完成 | | 指令 SHA256 一致；已读 S4N 报告全文、S4N 进度、补充 01 / 02 |
| S4O-1 | 整理与入库 | **完成** | 20:05–20:25 | ① `codex/s4n-calibration-20261019`（7c4f97fe）推送，draft PR [#39](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/pull/39)，base = #38 分支 `codex/s4m-mainline-pilot-20261019`；② S4N 交付物入库 `research/06_scope_redesign/p1_step4n_20261019/`（170 个文件，5.4 MB；试点轻量包 tar.gz 全量 + 解包成员 ≤ 500 kB，4 个较大成员只在 tar.gz 内；`sha256sum -c` OK），先扫描：许可特征串（只命中 `s4n1_evidence.sh` 的扫描模式本身）、IPv4 形（只命中包版本号）、AutoDL / SeetaCloud 主机名（只命中 `s4n_netdiag.sh` 的公开网站 `www.autodl.com`）、ssh / scp / rsync 端口、user@host、密码——无登录信息（`/home/jin/s4o_scan.sh`），提交 **f28772e6**；③ 注册表片段 `s4o_0`（`scripts_project/s4o_0_data.py`：第 118、119、120 项 + 问题来源，共 4 行；注册表 1,958 行；`test_d1_registry.py` 13 passed）、台账 S4N 条目，提交 **46135c52**，已推送；④ 自 46135c52 开 `codex/s4o-production-20261019`，S4O 指令与 SHA 文件放入 `research/06_scope_redesign/p1_step4o_20261019/` |
| S4O-2 | 生产档案定稿 | **完成** | 20:25–21:20 | ① `configs/research/baseline.yaml`：`pypsa_eur_default` = `{Threads: 8, Method: 2, Crossover: 0, BarConvTol: 1.e-5, Seed: 123, AggFill: 0, PreDual: 0, GURO_PAR_BARDENSETHRESH: 200}`（两处适配：键名大写、Threads 8；理由写在配置注释与注册表 `s4o_decision_120_production_profile`），缺省 `research.solver.profile` 改为 `pypsa_eur_default`，档案 A 不改；② `s2_solve.py`：`profile_parameters()`（键名与已知 Gurobi 参数只差大小写即拒绝，防止 S4N 发现第 10 条复现）、`interior_solution()`（门槛路径，行为不变）；③ C1 流水线模块 `scripts_project/s4o_c1_precision.py`（`run` / `reference` / `regrade`；输出 `PRECISION.json/.md` 写入 `EXPORTS.json`；验收 = optimal + (a)(b)(c)；门槛作数值信息；分国容差参照：本批两种 STEPS 都有结果前用 L23，之后用本批差额并重评）；在 S4N-1 结果上与 S4N 工具等价（影子目录，原结果未改；分国数值最大差 0.0，分级相同；用时 22 s / 1.7 GiB）；④ 测试 `test_s4o_2.py` 7 项（档案键名识别、内点路径、C1 玩具模型 KKT 项、分级 / 验收 / 参照、重评与 `EXPORTS.json`、无解时不可计算），`tests/research` 543 passed（原 536 + 7；两处旧测试的缺省档案断言改为 `pypsa_eur_default`）——提交 **d5b4eb96**；⑤ 部署运行脚本并入 C1（`research/06_scope_redesign/p1_step4o_20261019/cloud_package/run_365x24h.sh`：缺省档案 `pypsa_eur_default`；每次求解后 C1（`env -u GRB_LICENSE_FILE`）；批内参照与重评；serial 相邻求解间隔 `RUN_GAP_S` 330 s；一体化非最优且 C1 不通过则停止）、`preflight.sh`（档案节检查缺省档案与键名、新增 c1 节）；脚本测试 50/50、探针测试 9/9（`evidence/s4o_4/`） |
| S4O-3 | 本机标定复核（3 次 56×3h） | 未开始 | | |
| S4O-4 | 部署包更新 | 未开始 | | |
| S4O-5 | 资源估算修订 | 未开始 | | |
| S4O-6 | 云端整批 | **未授权** | | 等待用户提供实例与授权原文 |
| S4O-7 | 报告 | 未开始 | | |

## 发现但未处理

## 续行点

S4O-1 进行中。
