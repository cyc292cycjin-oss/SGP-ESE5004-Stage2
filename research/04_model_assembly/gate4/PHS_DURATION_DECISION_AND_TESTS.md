# 抽蓄时长、效率与年度边界

本轮新增人工方法ASSEMBLY_V1_PHS_6H_DURATION_PROXY；DecisionReference=GATE4-20261005-HYDRO-PHYSICAL-POLICY-SEPARATION。5个合格机组2686MW进入3个同国同分区组件。原始相容能量容量缺失，采用6h显式代理，合计E_max=16116MWh。参考max_hours=0未解释为真实零能量；6h不是实测或官方推荐。

源输入充/放效率各sqrt(0.75)=0.8660254037844386，乘积0.75；未再次开根或再乘往返损耗。p_min_pu=-1，纯抽蓄inflow=0，年度cyclic_state_of_charge=true，state_of_charge_initial输入0。循环模式实际约束首末SOC相接；初始输入不为年度提供净能量。

按冻结PyPSA口径E_max=p_nom*max_hours。无天然来水、standing_loss=0时，全年的循环状态方程给出Σw*p_dispatch/η_d=η_c*Σw*p_store。因此无充电不能产生全年净发电。该推导依赖年度循环和无额外自然来水；不是已求解的调度结果。

新测试覆盖6h能量、双向效率、p_min允许充电、导出回读、非循环/初始赠能/天然来水拒绝。实际导出网络核对5→3组件容量及16116MWh。储能时长敏感性保留，本轮未运行。
