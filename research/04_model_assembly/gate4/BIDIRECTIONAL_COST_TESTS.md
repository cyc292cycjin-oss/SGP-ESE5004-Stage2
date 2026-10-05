# 双向费用无求解测试

SYNTHETIC_TEST_ONLY：两母线、一条双向Link，单时段3h，c=0.01。实际调用PyPSA0.30.3的create_model，检查目标中Link-p系数为0.03；+100MW贡献+3，-100MW贡献-3。反转bus0/bus1后，同一a→b物理输送以负p表示，贡献变为-3。没有调用solver，模型状态为initialized，调度输出为空。

真实13个组件的源费用与固定seed174噪声逐值相等；12条允许负向流量，1条不允许。详见evidence/closure/BIDIRECTIONAL_COST_EVIDENCE.json。生产费用未改，测试证明方向问题，不假称已经修复科学方法。

19项新测试与156项既有保留性回归，共175项通过。新测试也覆盖官方交易代码反转、漏请求、国家/年份/商品错误、父子重复、跨版本总账与固定FOM包含关系。测试日志/hash随包保留。
