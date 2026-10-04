# 来源家族验收表（待共同填写）

| 家族 | 本轮已恢复/验证 | 关键核验 | Human decision |
|---|---|---|---|
| technology-data v0.13.2→DEA/manual→AEO8→model | 固定SHA/原表/覆盖次序/当前成本hash | H2 storage FOM MW/MWh；燃料LHV/HHV/地区口径；battery/solar/wind/HP/transmission关键值 | PENDING |
| electrolyser manual override | 作者公开表值及private communications标签 | 允许保留作者值已由用户说明；原始通信仍不可验证 | SOURCE_PARTIALLY_VERIFIED |
| UNSD national sector demand | 52导出、base2019、十国工业量 | TL工业缺失；其他部门交易定义；未来增长 | PENDING |
| GDP/facility spatial mapping | 全球NC、EPSG恢复、十国守恒 | 2015空间代理、all_touched与设施最近邻适用性 | PENDING |
| paper weather/geography | 官方27.6GB亚洲ZIP目录；本地EEZ/natura | 完整文件坐标/hash/作者一致性；土地覆盖来源 | PENDING |
| grid + AIMS/ID projects + fleet | 0.1.1来源和765→766缺陷原因 | 删除意图、国内/跨境分类、资产容量与连通性守恒 | PENDING |
| full-SC service/growth/resource families | 当前开关和处理入口 | 热/住户/服务不重复；交通服务份额；biomass/global defaults适用性 | PENDING |

不是要求逐条批准10,139个参数。一个来源家族可整体接受，但必须记录版本、変换、manual overrides和关键例外。`technical PASS`、`SOURCE_RECOVERED`、`source publicly available`都不等于人工接受。
