# 内存生命周期审查 — 有界工程修复

| 阶段/对象 | 当前证据 | 本轮处理 |
|---|---|---|
| PyPSA输入、Linopy约束与变量 | run04 model_build采样峰值3201.746MiB；模型必须保留以映射同一套标签/hook | 未释放模型或删减约束 |
| 流式直接传递、约束切片/CSR/读回CSR | 已逐块验证，未构造全局稠密矩阵；临时对象函数结束释放 | 保留全部float64精确检查 |
| 摘要计算a.tobytes() | 每次产生全数组bytes副本 | 改为连续内存视图分块哈希；dtype/shape/字节流不变；非连续数组仍需一次合法连续化 |
| vl/cl及D/R | 标签与缩放向量是必要回映资料 | 保留，未提前释放 |
| HiGHS原/预处理/恢复模型 | run04最后到original-LP postsolve；内部内存分配没有堆分析 | 不归因到某个具体分配，不改冻结后端，不取消crossover |
| frozen Linopy _solve -> h.getSolution() -> Series | 原生向量/列表与Series可能并存；随后资格检查再次getSolution | 记录风险，未删除value_valid检查或替换冻结求解后端 |
| 固定库存primal/dual回映 | 旧实现保留全raw副本并产生完整inverse中间数组 | 改为200000元素块，保留Series与全部标签；逐块原浮点乘除与exact检查 |
| PyPSA写回/动态检查/NetCDF回读 | run04未执行；同时存在网络、模型、原生对象及回读网络的峰值未知 | 新预算明确覆盖；尚未验证全面释放solver_model不会影响诊断，故未擅自释放 |

600000元素小型数据、相同float64运算的tracemalloc实测（只代表该调用的可跟踪分配，不是全模型RSS）：哈希旧4,800,467bytes→新1,114bytes；回映旧10,204,682bytes→新5,004,090bytes。回映使用生产默认200,000元素块，结果、逆映与标签相同。不能把这项局部节省宣称为run04后处理数GiB增长的根因或充分修复。

监控现在分别记录model_build、handoff，以及从增量日志识别的presolve/IPM/crossover/simplex_cleanup/original_model_postsolve；无法识别时UNKNOWN。后端返回后代码记录native_result_return，回映前记录original_unit_mapping，再记录PyPSA_assignment、export和dynamic_validation。native_result_return表示冻结后端返回，不能据此推断h.run返回与Series创建之间的精确时间。旧日志的solve总阶段不重写。

Linux每2秒读取Guest量与父/子RSS，约30秒读取一次PSS；RSS求和可能重复共享页，PSS独立列出。Windows使用一个持久只读轻量采样进程每10秒写小JSON，运行中不反复CIM、不并发调用原生求解器取解。主机探针超过30秒未更新拒绝继续。保护先写小型停止回执与manifest，再终止；不会为保存大模型继续耗尽内存。

未来若采用分进程方案，必须先证明：以分块float64二进制保存CSR/边界/目标及标签和D/R、逐块hash与读回一致；求解进程退出前保存合格原生状态及解；后验进程重建相同hook和账户身份并在原单位验收。不得把12位LP变成实际交接。本轮仅提出此方案，未实现或用于真实求解。

验证范围：RESOURCE_PREFLIGHT_TESTS.json中的资源/阶段/停止/小数据/4变量4行直接交接测试，优化器调用被明确禁止；GATE5_RESULT_QUALIFICATION_TESTS.json保留12项模拟接口正反例。没有完整模型重构试跑、presolve或求解。首次新夹具错误与Windows路径问题及修复记于ENTRYPOINT_AND_HOST_MONITOR_TESTS.json。PROJ提示仍出现在导入过程，未做地理投影、不据此宣称本次内存根因，也未更改环境。
