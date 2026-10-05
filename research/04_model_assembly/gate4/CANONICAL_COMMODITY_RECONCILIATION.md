# 规范商品身份与限定源范围覆盖修复

直接复算冻结UNSD行：119个原始名称控制项归并为100个规范商品控制项。92项精确闭合；1项在声明的浮点精度界内闭合；7项仍有实际差额，重复指向MM LPG与TL LPG两个国家/商品。没有新增源值、残差Load或数值归一化。

MY LPG：父项1212.702千吨，用途合计由旧匹配329.071恢复为1212.702。MY Natural Gas：父项364167.199TJ，用途合计由1081.691恢复为364167.199。匹配使用现有commodity()的已证实别名，不模糊归并油品与生物燃料。原标签、文件hash、PhysicalLine/RowID保留；国家、年份、单位、来源文件版本、用途叶节点与唯一性继续检查。

VN硬煤原差额约4.65e-11千吨保留。规则为8×float64 epsilon×max(|父项|, Σ|互斥用途|)，无绝对数据量级的宽容差；它只处理已有浮点读入链的算术尾差，不用于源统计差异。MM LPG原差额29千吨、TL LPG0.92千吨均未闭合，不能生成已知用途残差。

现有SOURCE_BOUNDED_ZERO规则已作用于BN、LA、MY、SG、VN的TransportEmbeddedFuelParent非电铁路空组合。此前fuel=unclassified_fuel不能匹配真实商品载能身份，是机械覆盖障碍。逐商品FEC耗尽证明成立，保持原限定统计范围，不把部门缺行当作物理零，不把NEC存在当零证明。registry保留全部组合、Value=null、不产生Load。五项机械阻断关闭，33来源组合中仍有28项待决；51物理目标待决降为46。国际BN/KH/LA/TL海运bunker四项保持独立。

来源：research_inputs/assembly_v1/sources/UNSD_2019_SOURCE_CAPSULE.json；规范控制的原行列表在evidence/selected/CANONICAL_COVERAGE.json。MY/TH混合油去重和152个正需求值未变。合格数组逐字节复用，manifest重新绑定新registry hash。

DSD仍为1235=Services、1232=Agriculture。ID服务业请求此前已执行，动态十项请求都已有回执；本轮新网络查询0、掺混数值新恢复0。请求映射合格不代表memo数量合格。

工程提交：2a722b8d18a755c983a07778daa25b69b3944044。新增别名正例、原标签/RowID保留、重复拒绝、版本/单位/国家拒绝、相似但不同商品拒绝和浮点边界测试已实际执行。
