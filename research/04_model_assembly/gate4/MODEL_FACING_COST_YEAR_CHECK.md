# EUR2020模型侧价格年核验与前轮更正

前轮“EUR2020与EUR2023仍混合”的总体结论证据不足，现予更正。仅看到currency_year和处理表数值相等，不能推断未通胀。证据：technology-data v0.13.2 SHA ec22a1843632fd28ecb9a139ee5156faf23324a3，compile_cost_assumptions.py:4165-4178最终执行adjust_for_inflation；_helpers.py:236-305仅对investment/VOM/fuel调整到config eur_year2020，同时不重写原currency_year。当前冻结值与同版本输出逐项核对。ASEAN append_cost_data.py:80-140追加AEO8 USD2020经冻结汇率转EUR2020，保留技术递减情景。

本轮决定ASSEMBLY_V1_COMMON_PRICE_YEAR_EUR2020，官方指数只用于尚未调整的EUR货币量。原currency_year保留为SourceCurrencyYear，新增EffectivePriceYearBefore和ModelCurrencyYear；SourcePublicationYear未知留空，绝不代入价格年。SourceCurrency指冻结成本表所载币种，上游更早转换保留源码链，不冒充重新恢复全部原始报价。

序列：MNA.A.N.I9.W2.S1.S1.B.B1GQ._Z._Z._Z.IX.D.N。index2020=100.0。下载hash=77a6cea533abe6318da7482e90dc8429c38953221d9363a1ae3add2e327dcf4c。元数据确认年度、EA20固定组成、GDP deflator、Eurostat来源。

官方定义：https://ec.europa.eu/eurostat/cache/metadata/en/nama_10_gdp_esms.htm

官方入口：https://data.ecb.europa.eu/data/datasets/MNA/MNA.A.N.I9.W2.S1.S1.B.B1GQ._Z._Z._Z.IX.D.N

公式value_EUR2020=value_EUR_y×index2020/index_y。不改变已转换成2020的历史EU27通胀结果，也不以新指数反算替换它们。本轮宏观代理不是技术专属价格预测。

本层746货币项保持；2制粒费用实际转换，因子=1.0181126154701645；488百分比保持；534货币FOM只用统一投资×原百分比一次。固定年化项沿用原寿命/折现率/年度权重。10非EUR项保持PENDING，未使用发表年份或暗中换汇。

新建投资/变动运维/可变燃料价可影响优化。既有固定FOM独立常数账，未重复CAPEX；既有VOM按发电输出/Link输入效率口径处理。当前配置边际费用涉及onwind/solar/offwind-ac/offwind-dc及DC/B2B：需一次明确货币年或数值正则化定义，不能将微小数值自动当已批准EUR2020价。无求解开发可保留，但价格资格明确待决。

FT已知VOM接线修复独立于本平减方法：原EUR2020/MWh_FT×效率进入Link.marginal_cost，100个组件。数量、物理排放及载能路径不变。
