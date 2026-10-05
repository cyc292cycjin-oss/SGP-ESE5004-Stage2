# 价格层验证

真实年度序列的KEY/FREQ/REF_AREA/STO/UNIT_MEASURE/PRICES/TRANSFORMATION/UNIT_MULT及EA20固定组成元数据逐项校验；缺年、重复年、非正值、错地区、未知币值年拒绝。原冻结cost表未覆盖。

新增测试检查已EUR2020精确保留、未知币值年拒绝、technology-data原年份元数据不触发二次平减、非上游过滤参数正确使用当前币值年、FOM百分比保持、货币FOM一次重算、FT输出能量口径。全部156项相关测试通过。

首次精确值测试识别到从raw×unit_scale再生成值引入浮点尾差；代码已改为对已核验的prepared值直接重用，保留原精度，未修改测试期望。初始测试失败日志保留。

重复执行从冻结原件生成独立JSON层，输出不含运行时间，因此同输入/代码输出hash一致；最终幂等检查见FINAL_GATES.json。没有任何solver输出或系统成本结论。
