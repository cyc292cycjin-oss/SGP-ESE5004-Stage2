# Gate6 execution hold

状态：**PAUSED_BY_USER / NO_SOLVE_AUTHORIZATION_ACTIVE_FOR_THIS_AUDIT**（2026-10-11）。

用户以 Baseline Evolution Review 指令暂停 G6-05。此前 DualReductions=0、900秒原生/2700秒总窗的授权不得用于恢复执行；将来任何优化必须取得新的明确授权。

中断前本会话只读本地准备文件、查看登录/浏览器准入，未上传、创建新run/claim、执行生产入口或调用optimize。本次不操作AutoDL，也不把历史终态当作当前远端进程检查。远端当前进程/消费文件状态未重新读取；不能声称已实时确认实例状态。

第一运行：`gate6_gurobi379_scope_v3_20261009T230330Z_0c53736d`，真实OPTIMAL / V4 NOT_ACCEPTED。第二运行：`gate6_p2_v1_379_20261010T023736Z_2374a62a`，Status=4 INF_OR_UNBD、SolCount=0、Barrier=0。本地回执与封存索引保存不变；不清除任何消费标记。第二次完整归档仍有历史LOCAL_SYNC_PENDING，十份核心原件已保存。证据与SHA见 [S0_STATE.json](evidence/S0_STATE.json)。

既有gate6心跳配置读取为PAUSED；本次未修改自动化。允许：代码/配置/小型证据只读核查、审计文档和GitHub发布。禁止：optimize、presolve、IIS、feasRelax、365日构模、AutoDL控制、模型/成本/物理约束修改、情景实验、合并PR。

本文件是审计与执行权限记录，不改变已批准V3/V4科学定义，也不修改既有求解结果。
