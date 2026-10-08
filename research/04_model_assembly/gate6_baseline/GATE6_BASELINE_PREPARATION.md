# Gate6 Baseline 3h：本地工程准备

2026-10-08。本轮范围为文件检查、独立入口、合成小模型与 mock 测试。完整 100 节点 × 2920 时点优化矩阵未构建，真实 solver/presolve 调用均为 0。正式 Phase5 未启动。

## 身份与已有成果

研究分支 research/full-sc-baseline；起始 local/GitHub HEAD 为 7b26b2692ceafc3a97a85e42ff2a3b844b41c58c。本轮源码提交为 4db99a6f098fec954e7d30ec13c4c5b313ff3ea1，最终报告提交和 push 见 GATE6_GIT_STATE.json。测试按逐文件 SHA 绑定源码，报告提交不冒充求解代码。

Gate5 已关闭：唯一求解 cloud_gate5_20261007T151625Z，求解代码 711e18b3aad65dc9aa8083d16c06c1e6aa841e04；恢复代码 2970979645380a8505076910bf1af227d2a5632c；科学/lossless 冻结身份 8b6a50c75d688cd69ce360580d32dd80e8003ed7。原生 Optimal、初次导出失败、零次额外求解的恢复、元数据派生各自保留。没有重跑既有 9494 项验收。

本轮重新核对原交付网络 SHA d80385a582e1ca5a0b2f778ec8fc5406a9b5a3a8092ce35c58b5365122275e29 与元数据派生 SHA 0b8cdf96fe89b0da0b47f7da867563eb795e94325408a7fa1866c8028528d7ed，未改变。原生备份沿用既有 10 文件、238196306 字节的双端哈希回执；本轮没有重新连接云端验备份，也未复制这些大文件。

## 当前决定索引

CURRENT_DECISION_INDEX.json 记录来源、阶段与 SHA。NEXT_EXPERIMENT_READINESS 的旧数据阻塞描述属于早期阶段；其中“Baseline/DEC 均保留、首轮单一区域 Integrated/Disconnected、仅跨境 AC/DC、standalone 靠后”是已批准决定。CARBON_SCOPE_FREEZE 与 CROSS_BORDER_INTERVENTION_CONTRACT 继续约束当前工作。

Baseline 原 Power 预算 OFF；DEC 保留原 Power 范围与 1000/820/640/460/280/100 Mt 轨迹。Disconnected 仅针对规定跨境电力边，外部商品、非电物理边界和对应区域政策相同；不拆成 11 个独立模型或复制 11 份预算。本轮未施加拓扑干预。

本轮新增的执行顺序是“先准备全年 3h Baseline，同时审查 DEC”。上轮 closeout 对 Baseline/DEC 的笼统待决表述在当前索引中纠正；历史文件原样保留，不把新顺序冒充早期决定。已冻结需求、存量、掺混边界不重新开启。

## 实际输入与执行依赖

直接加载 results_project/assembly_v1/research_fullsc_2050_assembly_v1_unsolved.nc，SHA256=238262c9d52e9d087d116799cbba0e3b5140aade7f64e6b8ebc02a448cd1419d，72,082,285 字节。2013 全年 2920 个 3h 时点；三套权重均为 float64 3，总和各 8760h；96 个 AC 加 4 个 DC 地理节点；171 账户、1737 Loads、187400.4 MW 合格存量、807 外置固定项、200 null 政策权重保持。

GATE6_INPUT_LOCK.json 区分五个科学运行输入、Git 代码/配置闭包、三个仅供旧资源回归读取的历史小文件。五个科学输入是完整 NetCDF、allocation_manifest.json、allocations.npz、registry.json、BASE_RECONSTRUCTION.json。后续构模及回映重复读取同一完整输入，另外读取本次生成的 D/R、标签、mmap 原生向量和回执。历史 32 条依赖清单只作适配参考；NetCDF 中的旧 C 盘来源字符串不成为本轮执行路径。

运行环境保持 Python 3.11.13 / PyPSA 0.30.3 / Linopy 0.5.5 / HiGHS 1.11.0；没有升级环境、复制 conda 目录或重建科学输入。其余环境沿用已冻结 Linux spec（索引保存其 SHA）。

## 新入口与门禁

scripts_project/run_gate6_baseline.py 与 configs/research/gate6_baseline_3h.json 独立于 Gate5。默认 preflight；显式 mode=test/build/solve。preflight 在代码层拦截完整 create_model、Highs.run 和 presolve。无授权和旧 Gate5 授权在读取/构建生产模型前即拒绝。

未来 build、solve 各须明确 Gate6/BASELINE/对应 stage 的人工授权，绑定当前代码、输入锁、测试 SHA、唯一 run_id、一次尝试与批准的资源/成本预算。仓库没有附送授权文件。build-only 不调用 solver，不能被当成 solve 的授权；solve 从冻结输入独立构建。claim 先于完整构模持久化，任何失败不自动重试。授权字段校验是工程门禁，不能替代人类真实授权。

未来路径：独立输入审计 → 研究 hooks 与 native lv_limit → PROJECT_STREAMED_FLOAT64 精确传输 → D/R、标签和 SHA 落盘 → 源对象释放 → 两线程 IPM/标准 crossover/presolve → 一次原生解读取与资格 → float64 mmap → native 释放 → 冻结网络重载/同身份重建/逆映射 → 原单位动态和前缀验收 → 完整 float64 导出/回读 → 元数据派生收尾。不会退回 12-digit LP。

所有完整执行阶段使用独立 cloud_gate6_* 非覆盖目录。资源监控覆盖 build/transfer/solve/postsolve/rebuild/validation/export/finalization；保留 solver 日志、输入锁、代码 SHA、manifest、退出状态及失败 traceback。SIGKILL/断电可能没有最终退出回执，未完成 manifest 必须判为中断，不能推断成功。未来独立会话启动应重定向 stdout/stderr 到该任务的 supervisor 日志；本轮没有后台计算。

## 3h 数值审计与测试解释

inventory_audit_3h.py 不调用日均 reshape/mean，也不复用 daily SHA/证书。逐组验证来源→账户→节点的 2920 值精确一致、3h 积分和原初始库存；385 组、807 库存及全部 171 个账户进入报告。binary64 精确有理数关系显式保留：385 组年度差均非零，最大绝对差约 9.81672e-8 MWh。它们处于预先声明的运算链误差界内，绝不改库存或需求来制造等式。

界为 gamma_n × magnitude，n=(2T−1)+(4K−2)+(2T−1)，T=2920；分别覆盖原 3h 加权求和、商品份额/库存组合和独立前缀验收计算。没有日均运算项。最大能量界约 0.000260971369 MWh，功率界为相应能量界/3h；此界不等于 solver tolerance，也不是精确 binary64 可行性证明。完整解未来仍须逐时递推、方向、容量、终值、独立前缀与全网络动态验收。没有生产解可供本轮验收。

GATE6_3H_NO_SOLVER_TESTS.json 由实际新入口产生，绑定源文件与输入锁；包含错误 SHA/日输入/权重/缺时点拒绝、少组件 2920 步手工可行见证、真实短缺与错误效率负例、精确交接/D/R/标签、一次 getSolution、无效/占位/非有限解拒绝、FOM 一次、零列/负零/Unicode/NaN、1 ULP 损坏拒绝、导出后收尾以及资源/授权/DEC 拒绝门禁。所有见证与 mock 均标为测试数据。另跑九组旧无求解工程回归，未重做历史科学实验。

3h 与日尺度 Gate5 是不同优化问题；没有声明目标值、最优容量或数学规划相同。也没有构建完整 Gate6 矩阵来验证规模或资源足够。

## 后续比较与未运行项目

gate6_fixed_term_contract.py 按来源 ID、商品、数量、三套时间权重、真实接口连接、独占用途、未知价格边界、库存/计量方向及 hooks 形成可测试输入契约。比较任何字段变化均拒绝；相等仅证明输入结构条件，不代表未知费用已经抵消。未来两情景仍各需合格物理解。本轮不计算互联收益或福利。

DEC 来源审查已完成，两个方法家族仍待接受；200 权重继续 null，DEC_POLICY_READY=NO。详见 DEC_ATTRIBUTION_REVIEW.md。Baseline 准备不受该未决方法阻断。

用户明确要求保持云端关机。CLOUD_INPUT_SYNC 与 CLOUD_NO_SOLVER_TESTS 均 NOT_RUN；当前 cloud HEAD 未核实，最后已知 2970979645380a8505076910bf1af227d2a5632c。真正运行前还需开机后部署已提交代码、定向补齐缺失输入、校验全部 SHA、运行同一无求解测试和新鲜 cgroup 预检；批准资源/时间/费用；另行授权一次明确的 Gate6 build/solve。没有产生新 Gate5/Gate6 或正式 Phase5 授权。
