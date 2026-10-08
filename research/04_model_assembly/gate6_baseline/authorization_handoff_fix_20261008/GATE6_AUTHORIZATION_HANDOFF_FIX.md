# Gate6 内部执行许可传递修复验收

状态：GATE6_EXECUTION_LOCK=PASS；LOCAL_NO_SOLVER_TESTS=PASS；CLOUD_NO_SOLVER_TESTS=PASS；CLOUD_PREFLIGHT=PASS（资源实测，非运行授权）。工程上可以申请新版本的一次执行；RUN_AUTHORIZED=false。旧授权已消耗，不复用。

## 根因与旧现场

失败 run 为 cloud_gate6_baseline_20261008T035607Z，代码 49879ff02777a81d261077ecdfd3092bb441d8be。外部人工授权、代码/输入/锁/测试身份、资源准入和一次性 claim 已通过；基础 PyPSA 构模返回后，实际 hook 入口只看到冻结网络 solver_allowed=false，拒绝安装。源对象释放后的重读也存在相同遗漏。不是用户未授权，也不是资源不足。原 failure_traceback、runner 日志、FAILED_ENGINEERING manifest、授权和 consumed claim 及备份均保留；本地/云端共 53 项历史文件逐项 SHA 相符。

旧 claim SHA256：a7bbd537d9fd11b7db23a7920cdb731bb7dad4323bd2d6a30345da8f7657be6f。云端生产 evidence 根仍只有这个旧 claim，本轮没有新生产 claim。

## 最小代码变化

- 新增 gate6_execution_context.py：复用并收紧实际授权校验；通过代码、输入、锁、测试、阶段、资源与排他 claim 后产生仅本进程有效的上下文。只写本次运行溯源，不更改冻结输入布尔值。
- run_gate6_baseline.py：把上述上下文传入初次构模/真实 hooks、唯一 native run 边界及结果消费；build-only 和 solve 分开。
- assembly_components.py：原保护保留；Gate6 hooks 需要绑定该网络对象的活上下文。手写 true、伪对象、诊断网络和导出元数据不能替代上下文。保护之后的科学约束代码 AST 完全相同。
- lossless_gate5_lifecycle.py 与 gate6_result.py：同一个已消费上下文允许结果重建、真实 hooks/标签/mmap 映射；不申请第二个 claim，不能再次求解；导出前关闭上下文，保存独立父输入状态，solver/scientific/Phase5 许可均 false。

数值配置、资源门槛、IPM/crossover/presolve、线程、时间预算、科学输入、映射数值函数、原生解资格检查均未改变；见 SCIENTIFIC_NONCHANGE_PROOF.json。没有模型降规模或政策修改。

## 正向和反向测试

本地和 915 云端均通过 11 个测试组 / 94 个检查，加 72 项原有资产与诊断网络回归（0 skipped）。全部 Highs.run / presolve / getSolution 硬拦截且实际调用计数 0。

新增四时点、两母线 TEST_ONLY 模型有 22 变量、52 约束；真实安装：ResearchImportAnnual-supply、ResearchStoreDirection-inventory、ResearchBatteryNominal-0。真实授权/claim/状态转换和 hook 函数未 mock。测试执行精确传输与 D/R、标签持久化，确认源网络弱引用已释放；用明确标识为 TEST_ONLY 的零向量走真实重读、hooks、标签匹配与 mmap 映射，再关闭结果许可。这里在真实映射之后截获完整系统动态验证入口，未声称这些合成向量是最优解或完整科学验收。既有结果资格、物理检查与完整导出序列回归另行通过。

16 个有名负例全部拒绝：错 run/input/code/stage、旧 Gate5 授权、缺少人工授权、未批预算、错锁/测试、资源不足、重复 claim、claim 后修改授权/claim/代码、已重新冻结但 diagnostic 或手写放行的输入。另验证原始 false/手写 true/伪上下文拒绝，重复构模/hooks/run/results 拒绝，build-only 与 TEST_ONLY 不能调用真实 solver，封存导出不能复用为下一次许可。元数据派生前后科学数组的名称、顺序、dtype、值和原签名一致。

## 冻结身份

- 实际执行修复代码提交：3e8a71ad7ffa7c55632acd01246911defc897bac。
- 新执行锁：6072585d5e214812c27c89be0e358fe958e30d76132d6d74ea350ef169fa5870，50 项（保留旧 48 项，新增上下文和集成测试两个源码；五项科学输入全相同）。
- 本地真实测试绑定：d3f50814764f54fed4dfbaa7b4685924e97a93f52816b9acfd7b22b90d376be9。
- 云端真实测试回执：33bf49ac010af4e79fb59e4702d84cb8310e91648169b28750e9af9f4bf60be9。源码/锁/测试项与本地一致。
- 原 3h 输入：238262c9d52e9d087d116799cbba0e3b5140aade7f64e6b8ebc02a448cd1419d，solver_allowed=false、scientific_results_allowed=false，未写回。

测试是在提交前源字节上运行，回执保留当时父 HEAD；tested_code_sha256 是实际测试绑定。工程提交及最后文档部署提交均须保持这组字节不变；最终三端 HEAD 以 GIT_DEPLOYMENT_RECEIPT.json 为准，不能把旧回执 HEAD 改写成新测试。

## 资源与下一步边界

资源时间 2026-10-08T04:48:18.738669+00:00：有效 cgroup CPU=25，memory.max=90 GiB，可用 89.315 GiB，磁盘剩余 43.811 GiB，swap=0；原 83 GiB / 2 CPU / 30 GiB 候选准入通过，OOM/oom_kill 均 0。不保证全年构模及 postsolve 一定成功。关闭/重启或真正执行前必须重新实测资源，并绑定最后部署 HEAD、同一输入/锁/测试、预算和新的人工授权；不能重用已消耗 claim。

冻结环境核对 PASS：Python 3.11.13 / PyPSA 0.30.3 / Linopy 0.5.5 / HiGHS 1.11.0；538 conda build、284 Python distribution 对照通过。没有安装环境或重新上传科学输入。

云端工程证据包 243570 bytes / 36 members，SHA256 352b6ff7bc80b1e445230e2ad987d5ffec527abd79fe88d87d02a3b0360d7994，已逐成员校验回 D 盘。原件保留。当前无遗留研究/测试进程，可由用户安全关机；本轮未关机、未删实例。

本轮完整 Gate6 构模=0，solver=0，presolve=0，getSolution=0，DEC=0，Integrated/Disconnected=0，Formal Phase5=0。旧失败事实不改写成成功；本修复验收只证明小型工程链。停止，等待用户对新版本另行授权一次执行。
