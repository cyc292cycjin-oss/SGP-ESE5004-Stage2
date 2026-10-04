# Buildings + Heat：来源与实现

固定版本、F/U/T/P 四层定义见 [README](README.md)。输入状态全部 UNVERIFIED；本文没有接受或替换任何参数。

## 1. 年度量不是现成的 ASEAN useful-heat 数据库

**直接读取（F/U）**：UNSD Energy Statistics Database → 下载链接表 `data/demand/unsd/paths/Energy_Statistics_Database.xlsx` → UNdata 文本 → `build_base_energy_totals.calc_sector` → `energy_totals_base.csv` → `prepare_energy_totals.py` → `energy_totals_{year}.csv` → `prepare_heat_data.py` → nodal totals / heat profiles → `add_heat` → `add_residential` / `add_services` → 最终 ASEAN adjustment。

| 环节 | 原始值/口径与转换 | 依据与限制 |
|---|---|---|
| UNSD 下载 | global country/commodity/transaction 表；U `demand_data.base_year=2019` | [下载注册表](evidence/UNSD_DOWNLOAD_REGISTRY.json)；U update_data=true 会重取，版本并未由此锁定。本轮未执行下载规则 |
| 本地原始输入 | 2025-05-02 命名的导出文件；2019 年 11 国建筑相关记录 92 条 | [原始行](evidence/UNSD_2019_BUILDINGS_ROWS.json)、[哈希](evidence/LOCAL_INPUT_HASHES.json)。文件日期不是 UNSD 官方数据发布版本；不能证明等于作者当时输入 |
| 国家与部门 | Country or Area → ISO2；households 与 services 的 transaction 字符串分别筛选 | 不以 GDP 或建筑面积推算国家年度量；11 国均有记录不等于所有燃料/终端服务完整 |
| 单位 | million kWh /1000；TJ /3600；thousand metric tons ×硬编码燃料因子 → TWh | [helpers](source_snapshot/upstream/scripts/_helpers.py) L1837–2009。质量/体积因子引用 UN balance 方法；国家特定热值、HHV/LHV、含水率不可从“已换成 TWh”自动接受 |
| base 热量 | 仅 `Heat`、`Direct use of geothermal heat`、`Direct use of solar thermal heat` 三类先合计，再按 0.6 / 0.4 分为 space/water | [base script](source_snapshot/upstream/scripts/build_base_energy_totals.py) L137–201。这不包含所有燃料供热，也不从电力总量识别空调/热水器 |
| future 居民热量 | 上述 heat commodity 加住宅油/气/生物质的假定供热份额、外生电气化份额和部分 0.9 转换；另有增长/效率默认值 | [fuel trace](BUILDINGS_FUEL_SHIFT_TRACE.md)。有用热/燃料输入/名为 electricity 的量混合，不能标成统一 measured useful heat |
| future 服务热量 | base 三类 heat commodity 按 growth × efficiency 外推；`electricity services space/water` 显式写 0 | 没有与居民相同的完整燃料→供热服务拆分；服务燃料还作为固定 fuel Load |

**隔离验证**：用固定 U 的 `calc_sector` 和 `_helpers` 对保留的 92 条原始行执行 households/services 两类汇总，11 国 ×12 列与既有 base CSV 在存储精度下完全一致（最大差 0 TWh）。这关闭了“base 表怎么算来”的缺口；没有验证输入本身科学完整。

**直接读取（T）**：11 国 residential base space/water 都为 0。services 只有泰国非零：原始记录为 **2019 年 Direct use of solar thermal heat，422.867 TJ**；base 脚本先四舍五入到 0.1175 TWh，再拆为 0.0705 / 0.047 TWh。它不是泰国建筑供暖总需求，更不是 ASEAN 真实采暖需求为零的证据。其余国家未来出现的居民热量主要来自 DEFAULT 燃料拆分，而非新获得的供热服务统计。

## 2. 0.6 的历史与地域适用性

- key 为 `sector.space_heat_share`，同时用于 residential 和 services；在 U 对所有国家一致。它仅直接拆分上面三种 heat commodity。
- 另一个独立字段 `fuel_shares.csv["space to water heat share"]` 的 DEFAULT 也是 0.6；用于居民燃料推导的热量拆分。更改 config 的 0.6 不会同步更改 CSV 的 0.6。
- [原始提交](history/SPLIT_ORIGINAL_COMMIT.txt)：`174ae272e7e63c5783b3d8937f55a314fce2c7ce`（2023-08-29，Earth-Sec 开发历史）把脚本中的 0.6/0.4 改为 config 参数；不是 ASEAN 校准。
- `a8987468ceda152ed1152f6c7bfa2ffb79da0837`（2024-09-19）合入 Earth-Sec；`d965b422bb5624862cd3657ce5dab8cb7f53ddfe`（2026-03-30）在 ASEAN soft fork 中移动该键的位置，仍为 0.6。[历史](history/ASEAN_SPLIT_DIFF.txt)
- **分类：DEFAULT_WITHOUT_ASEAN_EVIDENCE**。源码出处为 RECOVERED_SOURCE；没有发现该 0.6 的原始实测/统计来源，不能仅凭欧洲框架继承就称它是“经欧洲验证的数值”，更不能称 ASEAN_SPECIFIC。
- T/P metadata 同为 0.6；参数出现不等于最终 power case 验证了供热。

## 3. BDEW、天气和逐时 shape

**F/U 真实路径**：Snakefile `prepare_heat_data` L1669–1714 直接把 `data/heat_load_profile_BDEW.csv` 传入，没有地区选择器。`custom_data.heat_demand=false` 虽在配置中，当前热规则没有对应替代分支；居民函数里相关替代代码也是注释。因此不能承诺只翻这个开关即可换 ASEAN 热曲线。

**来源恢复**：Earth-Sec 历史 `0ec4af7f7`（2022-04-22）已有该 CSV。官方 PyPSA-Eur-Sec `v0.7.0` 的相同文件与 U **数值完全一致，仅换行不同**，见 [比较](evidence/BDEW_COMPARISON.json)。该版本 [data source table](evidence/eur_sec_0.7.0/doc/data.csv) 指向 oemof/demandlib，但 source 一栏自身写 unknown。德国 BDEW（能源与水行业协会）的标准负荷法经 demandlib 提供；[demandlib 方法文档](https://demandlib.readthedocs.io/en/stable/bdew.html)说明温度、日因子、小时因子。尚未恢复生成这 24×8 固定数值的 demandlib 版本、建筑类别、温度分组及生成脚本，不能声称已经完全重建原始 BDEW 校准。

| 处理 | 固定代码实际行为 |
|---|---|
| 日内/周内 | residential/services 的 space 各有 weekday/weekend 两列，彼此不同；五个 weekday +两个 weekend；无公共假日表 |
| 热水 | 四个 water 列全部等于 1，因此热水 shape 恒定，没有早晚热水峰 |
| 天气 | `build_heat_demand` 从 ERA5 cutout 取温度，调用 `atlite.heat_demand`。本地 atlite 0.4.1 默认 threshold=15°C、a=1、constant=0、hour_shift=0；日平均温度低于阈值才有度日负荷 |
| 组合 | space：每日度日值 ffill 到小时 × BDEW 日内因子；water：仅日内模板；分别除以各节点 shape.sum 后乘年度 TWh ×10^6 |
| 时区 | BDEW 小时按 `pytz.country_timezones[ISO2][0]`；多时区国家统一取第一个时区。天气日平均仍 hour_shift=0（UTC），二者时区处理不同 |
| 时间聚合 | 先在电力输入网络 snapshots 上形成小时需求，再 `prepare_sector_network.average_every_nhours` 求均值、权重求和。这里 shape.sum 不是任意权重下的通用积分 |
| 功能边界 | BDEW 决定 shape，不决定年度量；当前做法也不等于执行了完整 BDEW sigmoid/建筑类别模型 |

**T 已观察到的失守**：2030 的 48 个节点有 41 个节点两类 space 曲线全部 NaN；居民分配量 246.781827 TWh 中，232.864522 TWh 对应这些 NaN 节点；泰国服务 space 的 0.079546 TWh 也全部落空。`add_heat` 读入后 fillna(0)。这些是教程中间量的守恒诊断，不是实际 ASEAN 用热估计；6 天教程把年度量分配进选中窗口，不能外推正式年度性能。U 存在同样零分母机制，但本轮没有生成 U 全年数据，因此不把教程的 41/48 数字移植到 U 年度案例。

**STOP：ASEAN_VALIDATION_PENDING + ENGINEERING_ISSUE**。不可用静默补零或人为制造度日来“修好”。Eur-Sec 历史树另有 Danish/Aarhus 候选曲线，但本 U 热规则没有地区替换接口，也没有 ASEAN 专用曲线。

## 4. 空间分配、集中供热

年度 heat 国家→节点直接乘 `pop_layout.fraction`（节点人口/国家人口）；residential/services 同一人口权重，没有建筑面积、建筑类型或 end-use GDP 分配。population layout 来自 GADM 区域的人口字段，U shape year=2020、WorldPop standard；城市人口比例来自 UNCTAD `US.PopTotal` 公共接口按 planning horizon 选择。按人口密度排序划分 rural/urban，时间版本未由下载 URL 锁定。[population scripts](source_snapshot/upstream/scripts/build_population_layouts.py)、[urban source](source_snapshot/upstream/scripts/prepare_urban_percent.py)

天气加权另须注意：`M=I.T @ diag(I @ population_grid)` 给每区域一个人口总量标量再作用于区域相交矩阵；**解析推导**：区域内网格没有逐格乘当地人口密度，归一化后区域人口标量会消掉。不能仅因变量名叫 population 就声称天气 shape 是完整的人口网格加权。温度/COP 脚本有相同矩阵形式。

| 假设 | U 值/入口 | 来源与效果 |
|---|---|---|
| 当前 DH share | `data/demand/district_heating.csv` DEFAULT current=0 | 表只有 DEFAULT/MA，无 ASEAN；不是证明 11 国 district heating 真实为零 |
| CSV potential | DEFAULT potential=0 | 未被这里消费；不能与 config potential 混为一谈 |
| 最大覆盖 | `sector.district_heating.potential=0.3` | Earth-Sec/Earth 继承，无 ASEAN 实证；城市供热份额上限假设 |
| progress | 1 | `D_new = D_current + (urban_fraction×0.3 − D_current)×1`。代码采用 1 达到目标，配置注释关于 -1 的说法不一致 |
| loss | 0.15 | urban central 热负荷乘 **1.15**，不是除以 0.85；是按交付热量附加量，若解释为管网输入损失率需重新澄清 |
| urban fraction | urban/(urban+rural)，且与分配后现有 DH share 取较大值 | 国家不同、节点不同；不是统一城市化率。现有资产脚本另有错误字段，见下节 |

`create_nodes_for_heat_sector` 的合成验证：current=0、urban=.6 时，progress=1 生成 DH share=.18，**零现有 DH 不会阻止模型外生配置集中热需求**。五类热区份额由假设确定；优化器只在给定热区选择技术，不内生决定所有 DH 接入比例。[源函数](source_snapshot/upstream/scripts/prepare_sector_network.py) L2552–2611。

0.3 /1 /0.15 可在 2024 Earth-Sec→Earth merge 追溯；没有恢复 ASEAN-specific 证据，也没有足够材料把三个数都认定为某份欧洲实证研究。归类 DEFAULT_WITHOUT_ASEAN_EVIDENCE，建议 REJECT_DEFAULT（直接采用层面）。T/P 同样配置，但最终裁剪不能验证它们。

## 5. 现有供热资产

**F/U**：规则生成 `heating/existing_heating_distribution...csv`。原始文件来自 EC 项目 WP2，源码指明 `WP2_DataAnnex_1_BuildingTechs_ForPublication_201603.xls`、**2012 年、建筑设备、排除 district heating**。[EC 官方研究](https://energy.ec.europa.eu/publications/mapping-and-analyses-current-and-future-2020-2030-heatingcooling-fuel-deployment-fossilrenewables-0_en)确认地域 EU28+3。原 CSV 六类：gas/coal/oil boiler、resistive、air/ground HP，单位 GW，代码 ×1000→MW；coal 并入 oil。无 11 国 ASEAN 行，DEFAULT 空值先填 0；缺失国家因而得到零容量。

节点按人口分配，R/S 按构造的年度热总量比例分；district existing share 固定 0，读入 district 文件只取索引；`urban_fraction = pop_layout['fraction']` 把节点全国人口份额误作城市率。ground HP 全移 rural、air HP 全移 urban。DEFAULT 在单位换算前保存，若将来 DEFAULT 非零，还会有 GW/MW 不一致隐患；当前全零使这个隐患不产生非零数值误差。[源码](source_snapshot/upstream/scripts/build_existing_heating_distribution.py) L55–172。

**关键可达性**：`add_existing_baseyear.py` L303–328 调用 existing heating capacities 的块**整体注释**；因此分配文件存在 ≠ 真实历史供热资产约束进入模型。其函数定义有按 grouping years 假设均匀安装、20 年默认寿命、按技术成本寿命与10 MW筛除的小资产处理，但当前未被 main 调用。不能把它报告成已完成 ASEAN brownfield。

若未来热组件保留，`add_brownfield` 的通用逻辑可以把上一期新建 Link/Store 的优化容量带入下一期并固定；build_year+lifetime < year 时删除，允许另建新 vintage，非随意提前退役。当前最终电力裁剪不保留这条热路径。源数据库没有现有 CHP 的 ASEAN 明细，不能由新建 CHP 菜单推断出已有存量。

## 6. 内生竞争的真实范围

**F/U 裁剪前**：五个热系统为 residential rural / services rural / residential urban decentral / services urban decentral / urban central；最后一类合并 R/S。每类有固定 heat Load、heat Bus。

| 技术 | 组件与扩张 | U 开关/成本 | 限制 |
|---|---|---|---|
| ground/air HP | Link electricity→heat，p_nom_extendable | heat=true；time_dep_hp_cop=true；sink 55°C | rural仅ground、urban仅air；COP为 Staffell 2012 回归，无 reversible cooling |
| resistive / gas boiler | Link，可扩张 | boilers=true；效率、年化 capital cost、gas燃料与CO2 | 并非整个建筑 gas consumption 都可被其替代 |
| gas CHP / biomass CHP | 多输出 Link electricity+heat，可扩张 | chp=true，biomass菜单；capital、VOM、fuel、CO2；cc=true时有捕集版本 | 主要仅 urban central；micro_chp=false |
| solar thermal | Generator heat，可扩张 | enable=true，成本与天气可用率 | 方向/校正系数仍待区域验证 |
| hot-water TES | heat Bus + charge/discharge Link + Store，可扩张、cyclic | tes=true；central/decentral tau=180/3天，储能年化成本、效率损失 | 热储能，不是 cold storage；周期与代表时间需另核 |

新建成本来自 workflow costs CSV（延续既有技术成本审计，未更新），`costs['fixed']` 等进入容量费用，燃料供应和 CHP VOM 进入运行费用。HP 的输入电功率由优化调度内生决定；输入容量/输出容量通过效率换算资本成本。`oil_boilers=false` 键在 add_heat 中没有新建 oil boiler 分支，不能把它当已接通的完整技术选项。

**结论**：技术接口可继承，但只有剩余热 Load 上存在这些技术的竞争；居民剩余燃料被固定、服务燃料被固定、DH 份额外生、居民函数又覆盖全部 heat，且最终 heat 被裁剪。当前整体是混合逻辑，达不到用户已冻结的 fixed heat service + endogenous full supply choice。
