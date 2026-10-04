# 当前官方SC母模型

官方main固定为 `a3616a68ee44592af6527ca9024a90f1956646ae`。**源码冻结完成；完整SC运行与数据验收未完成。** 本轮没有把所有开关设为true，也没有关闭final_adjustment去构造一个未经核验的full-SC网络。

配置证据：[UPSTREAM_EFFECTIVE_CONFIG.json](evidence/UPSTREAM_EFFECTIVE_CONFIG.json) 是default + plotting/solving/bundle/powerplantmatching + config.asean合并并迁移后的审计快照；它不冒充Snakemake实际执行时完成国家展开、cutout更新、wildcard注入的最终run config。实际run需另存最终生效配置。

## 四种边界必须区分

| 对象 | 可核实边界 |
|---|---|
| Framework capability | 多能流与电力转换、存储、部门服务需求的通用实现 |
| 当前官方配置 | heat/biomass/industry/shipping/aviation/land/rail/agriculture/residential/services=true；ammonia=true；H2 turbine=true；H2、gas、CO2网络=false；地下H2储存=false |
| 最终当前案例 | `final_adjustment.only_elec_network=true`，仍会裁剪部门组件；不是已冻结Full-SC系统 |
| 教程 / 论文 | 教程六天50clusters、land_transport=false；论文全年100clusters、land_transport=true，最终电力案例；两者均不能作为已验证full-SC证据 |

当前`demand_data.update_data=true`意味着正式运行还可能刷新外部数据；研究层必须使用固定文件/哈希与显式project override。这里只记录风险，未自动运行下载或修改上游默认值。新上游已包含ammonia/H2 turbine等能力；是否纳入本项目范围要明确，并非本轮新增技术。

## 实际启用与数据清单

[SECTOR_ENABLEMENT.csv](SECTOR_ENABLEMENT.csv)含16行、11列：Sector、Service demand、Carrier、Conversion technology、PyPSA component、Expandable、Cost source、Demand source、Config switch、Source code、Validation status。它分别标识配置启用、源代码能力和数据验证状态。当前未生成full-SC最终网络，故不能把表内能力描述当成实际组件计数。

主要入口：[`prepare_sector_network.py`](https://github.com/pypsa-meets-earth/pypsa-asean/blob/a3616a68ee44592af6527ca9024a90f1956646ae/scripts/prepare_sector_network.py)，其中add_hydrogen L384、add_co2 L1408、add_aviation L1545、add_shipping L1683、add_industry L1853、add_ammonia L2146、add_land_transport L2311、add_heat L2614、add_services L3033、add_agriculture L3142、add_residential L3247、add_co2_budget L3601、add_rail_transport L3696。电力与既有资产另经add_electricity/add_existing_baseyear/add_brownfield；最终裁剪见final_asean_adjustment。

血缘沿用A0.5已恢复历史：PyPSA-Earth的电力/GIS/聚类层，PyPSA-Earth-Sec并入Earth的部门构建层，ASEAN的预建网络、AIMS/ID项目、AEO8成本append和final adjustment。准确历史证据见 [SECTOR_COUPLING_PROVENANCE](../00_source_provenance/SECTOR_COUPLING_PROVENANCE.md)；本轮没有把“继承了功能”推为“论文验证了所有部门”。

## 扩张与成本边界

Link的p_nom通常为输入功率，Store的e_nom为能量；输出报价技术按效率换算。资本支出年化+FOM以capital_cost进入容量目标，VOM/燃料/部分输送成本以marginal_cost进入加权运行成本。需求Load本身通常固定，无投资变量；电动车队容量/份额可能由外生交通服务设定，不能笼统称所有储能无限扩张。既有资产下界、资源上限、lv2.0输电限制和myopic资产延续继续约束解。

主缺口：工业TL/增长/工艺；热、住户、服务之间服务需求对账；交通/航空航运配置与本地区来源；共享生物质/燃料/CO2池；电力裁剪与需求缩放错误；电力碳预算在full-SC的归属。详见 [NEXT_EXPERIMENT_READINESS](NEXT_EXPERIMENT_READINESS.md)。
