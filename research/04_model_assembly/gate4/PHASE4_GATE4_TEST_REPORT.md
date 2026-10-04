# Gate4验证证据

18项新增来源/方法/分层门禁/guarded入口测试；17项输入回归；20项Gate1、70项Gate2、60项Gate3、9项拓扑回归：共194项通过。另有实际数组preflight、真实构网入口调用、Research DAG dry-run与配置审查。门禁/入口返回2为生产输入仍未闭合的结果，不是完整网络验收。

正向测试使用明确标注的合成数值夹具：数值就绪→仅分配阻断→真实NPZ数组就绪可进入下一门；也验证单位/缺失/重复/来源错误、数组篡改、无证据排除及已知无去向正值继续失败。它们不代替真实研究模型。旧accepted_target_demands=0断言仅作用冻结旧夹具。

本轮最终131组真实数组逐组回读检查，NPZ hash、registry hash、物理快照/权重、国别与积分均通过。源国家总量来自批准方法，实际网络检查仍NOT_RUN。

完整测试命令、退出码、日志hash见evidence/CONTINUE_TEST_RECEIPTS.json。环境已有PROJ数据目录告警；本次最近节点计算采用经纬度球面距离公式，无坐标重投影。Snakemake dry-run的后端可用性导入产生Gurobi license/参数探测告警，DAG仅1条未执行构网规则；未调用优化求解。Gate3旧配置报告的topology_fix_required描述字段不是本轮状态门；既有修复未重做，9项拓扑回归通过。

补充：131项raw-to-target独立复算通过，证据见CONTINUE_TARGET_REDERIVATION.json；12个CSV逐值回读等于authoring矩阵。输入胶囊和审计路径以.gitattributes限定-text保留精确字节，避免Git换行归一化破坏源hash；Python/YAML/工作流使用LF。
