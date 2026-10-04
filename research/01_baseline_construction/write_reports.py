"""Assemble the Phase 2 review from saved evidence, without recomputation."""
from pathlib import Path
import json
R=Path(__file__).resolve().parent
def read(name):return json.loads((R/name).read_text(encoding='utf-8'))
layers=read('LAYER_IDENTITIES.json');fixes=read('FIX_COMMITS.json');ind=read('INDUSTRIAL_RECOVERY_EVIDENCE.json')
P=layers['paper_sha'];U=layers['official_sha'];I=fixes[0]['sha'];C=fixes[1]['sha']
url=f'https://github.com/pypsa-meets-earth/pypsa-asean/blob/{U}'
def write(name,s):
    p=R/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s.strip()+'\n',encoding='utf-8')

write('BASELINE_ARCHITECTURE.md',f'''
# 三层基准架构 — 2026-10-01

**版本身份已冻结；Full-SC 科学边界尚未冻结。** 来源为官方 Git、作者网络内嵌配置及现有本地输入，非对数据的人工验收。

| 层/分支 | 完整 SHA | 当前状态 |
|---|---|---|
| Paper Reference / `codex/paper-reference-5bacad70` | `{P}` | 源码清洁；DAG预检到缺输入；未正式重建/求解 |
| Upstream SC / `codex/upstream-sc-baseline-a3616a68ee44` | `{U}` | 官方main固定源码；默认仍裁剪到电力案例，不能直接称已验证full-SC |
| Research / `codex/research-sc-main` | `{U}` | 从Layer 1分出；零研究修改、零研究求解 |
| 工业修复 / `codex/fix-industrial-gdp` | `{I}` | 独立工程提交及回归测试通过；未合入Layer 1/2 |
| 碳键修复 / `codex/fix-carbon-config` | `{C}` | 独立配置修复及回归测试通过；未合入Layer 1/2 |
| 拓扑诊断 / `codex/fix-topology-765-766` | `{U}` | 只读诊断；无修复提交 |

官方入口：[{layers['official_url']}]({layers['official_url']})，branch=`main`，抓取时刻 `{layers['captured_utc']}`。远端可能继续变化，本报告始终引用完整SHA。

隔离目录：`/home/jin/research/SGP_ESE5004_Stage2/phase2/`；每层都是独立工作目录，共享新建model-source对象库；原教程目录及commit `ce327bfae2abe5526d4c1976173f0f8d08366ba5` 未改。详细路径在 [LAYER_IDENTITIES.json](LAYER_IDENTITIES.json)。本轮没有force-push，没有覆盖旧结果。

研究代码/证据在 `research/01_baseline_construction/`；小型登记在其 `data_registry/`；大文件在既有cache或隔离工作区，仅提交身份/脚本。建议未来项目根层data/raw、processed、derived采用同一来源ID索引，当前未移动历史资产。所有修复先review再合入具名validation分支，未经检验不把修复后的网络冒充Paper Reference。

未来比较对象已由用户给定：同一个区域Full-SC模型，仅关闭跨境AC/DC电力连接；Baseline与DEC均保留，DEC仍为区域共享的电力口径预算；不拆国家碳配额。研究方向已确定，但可执行配置尚不具备冻结条件。
''')

write('PAPER_BASELINE_REPRO_STATUS.md',f'''
# 论文基准构建状态

**PARTIAL / BLOCKED_INPUT_IDENTITY：能够加载论文源码并展开部分DAG；没有完成最小正式案例的重建或求解。** 不能报告“Paper SHA已跑通”。

| 身份 | 恢复结果 |
|---|---|
| 实际运行SHA | `{P}`，两份作者NC metadata一致 |
| 最小目标 | baseline-aims-3H，2025，100 clusters，AIMS，lv2.0，myopic首期 |
| 时间 | 2013全年，3h，2920 snapshots；三种权重和均8760h |
| 技术成本 | v0.13.2 + 作者AEO8 append；作者逐文件input hash未给出 |
| 碳 | Baseline无显式CO2Limit；保留DEC对应六年轨迹作为另一组 |
| 作者环境 | PyPSA0.30.3，Gurobi；作者SHA含environment.yaml及linux-64.lock.yaml |
| 本机 | PyPSA0.30.3 / Python3.11 / snakemake7.32.4 / linopy0.5.5；完整pip freeze已保存 |
| 求解器 | gurobipy12.0.3可初始化，但受限license提示存在；大模型资格未验证 |

作者实际配置是 [PAPER_EFFECTIVE_CONFIG.yaml](evidence/PAPER_EFFECTIVE_CONFIG.yaml)，从作者NC metadata恢复，年份字典键恢复为整数，未缩小到教程分辨率。**其中使用`cutout-2013-era5`，不是当前ASEAN配置中的`asean-2013-era5`。** 不能只读论文SHA下config.asean模板就假定它等于作者有效配置。作者metadata的`retrieve_databundle=false`、`build_cutout=false`说明其运行假定已有输入。

## 已执行的构建检查

第一次dry-run缺EEZ/natura；本地已有这两个原始文件，因此仅以只读源链接供第二次dry-run使用并记录hash，未要求用户重新找它们。第二次停在：`cutouts/cutout-2013-era5.nc`、GEBCO2025、Copernicus LC100 2019等原始输入。日志为 [第一次](evidence/PAPER_DRYRUN.log)、[第二次](evidence/PAPER_DRYRUN_WITH_LOCAL_GEODATA.log)，命令、时间、返回码及输入哈希在 [PAPER_PREFLIGHT.json](PAPER_PREFLIGHT.json) 和 [PAPER_PREFLIGHT_FOLLOWUP.json](PAPER_PREFLIGHT_FOLLOWUP.json)。PROJ路径通过显式环境变量修正于第二次预检；不改论文代码。

沿论文bundle配置找到官方亚洲气象包。HTTP Range实测可访问，ZIP为27,611,570,291B，包含`cutout-2013-era5.nc`（27,693,617,591B，目录CRC32=8bc17e50）。文件名与作者metadata匹配。这里只读取目录及元数据；未下载完整NC、未验证其CRC/全文件SHA/时空坐标。目录时间2023-08-09不是发行版本保证。见 [WEATHER_ARCHIVE_DIRECTORY.json](WEATHER_ARCHIVE_DIRECTORY.json)。**因此“公开下载入口”缺口已关闭；“与作者当年输入逐字节同一”仍未关闭。** 用户不必先重新寻找所有源数据。

## 参考输出与差异

作者baseline-AIMS2025 objective=51,958,123,545.77296；objective_constant=8,754,735,116.417757；作者DEC-AIMS2050 objective=94,026,128,588.01077，CO2Limit=100,000,000t。两份作者网络哈希继承A0.5证据，登记为AUTHOR_OUTPUT_NOT_REPRODUCTION。

本轮正式输出、objective差值、constraint residual、solver status均为**N/A（未正式求解）**，绝不用0表示未测量，也未将作者已解网络重优化当成原始数据重建。没有重新运行全部44个网络。

最低下一步：确认官方候选输入家族的使用/与原作者不一致时的标注；取回并检查完整气象及缺失底图；核对author input manifest（若作者无法提供，则只能标“来源可重建参考”，不能声称字节级复现）；确认可用的正式求解器/环境容量后，才能按manifest工具启动该2025单案例。
''')

write('UPSTREAM_SC_BASELINE.md',f'''
# 当前官方SC母模型

官方main固定为 `{U}`。**源码冻结完成；完整SC运行与数据验收未完成。** 本轮没有把所有开关设为true，也没有关闭final_adjustment去构造一个未经核验的full-SC网络。

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

主要入口：[`prepare_sector_network.py`]({url}/scripts/prepare_sector_network.py)，其中add_hydrogen L384、add_co2 L1408、add_aviation L1545、add_shipping L1683、add_industry L1853、add_ammonia L2146、add_land_transport L2311、add_heat L2614、add_services L3033、add_agriculture L3142、add_residential L3247、add_co2_budget L3601、add_rail_transport L3696。电力与既有资产另经add_electricity/add_existing_baseyear/add_brownfield；最终裁剪见final_asean_adjustment。

血缘沿用A0.5已恢复历史：PyPSA-Earth的电力/GIS/聚类层，PyPSA-Earth-Sec并入Earth的部门构建层，ASEAN的预建网络、AIMS/ID项目、AEO8成本append和final adjustment。准确历史证据见 [SECTOR_COUPLING_PROVENANCE](../00_source_provenance/SECTOR_COUPLING_PROVENANCE.md)；本轮没有把“继承了功能”推为“论文验证了所有部门”。

## 扩张与成本边界

Link的p_nom通常为输入功率，Store的e_nom为能量；输出报价技术按效率换算。资本支出年化+FOM以capital_cost进入容量目标，VOM/燃料/部分输送成本以marginal_cost进入加权运行成本。需求Load本身通常固定，无投资变量；电动车队容量/份额可能由外生交通服务设定，不能笼统称所有储能无限扩张。既有资产下界、资源上限、lv2.0输电限制和myopic资产延续继续约束解。

主缺口：工业TL/增长/工艺；热、住户、服务之间服务需求对账；交通/航空航运配置与本地区来源；共享生物质/燃料/CO2池；电力裁剪与需求缩放错误；电力碳预算在full-SC的归属。详见 [NEXT_EXPERIMENT_READINESS](NEXT_EXPERIMENT_READINESS.md)。
''')

write('ENGINEERING_FIX_REGISTER.md',f'''
# 工程修复评审登记

| ID | Evidence → failure mechanism | 最小动作 | 修改前 / 修改后 | 状态 |
|---|---|---|---|---|
| ENG-IND-01 | 全球GDP NC有ASEAN值，缓存TIFF却为非洲范围；load_GDP直接复用缓存；分配函数未在国家内归一化 | 按源NC哈希/年份/尺寸/CRS验证缓存；从现有NC重建EPSG4326 TIFF；国家/行业内归一化；非法权重拒绝；缺国家总量拒绝隐式0 | 国家守恒/顺序测试失败，NaN/负数/无穷/零权重未拒绝 → 全部通过；真实10国572个已有工业单元格守恒 | 独立提交`{I}`；BASE_YEAR_ALLOCATION_PASS；非完整未来工业模型PASS |
| ENG-CO2-01 | 当前co2.budget.co2base_value未被消费，默认base_value=limit使2050读成7.75Mt | 仅把ASEAN键改为base_value，保留1e9与年份系数 | 错轨迹77.5→7.75Mt → 1000→100Mt；旧/新配置、8760/144h缩放测试通过 | 独立提交`{C}`；CONFIG_EQUIVALENCE_PASS，不代表SC排放范围等价 |
| ENG-GRID-01 | 0.1.1变更清单明确删bus766，仍保留变压器；765负荷及机组在simplify时消失 | 已追到版本和GIS；暂不改端点、不补bus、不删变压器 | 旧教程mean load损失80.84135264MW、generator损失1MW；尚无合法的after网络 | DIAGNOSED / FIX_NOT_APPLIED |
| ENG-CO2-SCOPE | 共享atmosphere store承接电与非电燃烧 | 提出专门power ledger或定制功率排放约束；共享H2/CHP/CC归属先确定 | 微型测试0.4t→加入非电热后0.65t | SCOPE_EXPANSION_VERIFIED；科学归属未决定、未改政策 |

代码补丁和哈希在 [FIX_COMMITS.json](FIX_COMMITS.json) 与patches/。分支源自同一个官方SHA，相互未合并；一项工程修复一个逻辑commit。所有母模型分支仍干净。测试入口位于各fix分支tests/，返回码见 [FIX_BRANCH_TESTS.json](FIX_BRANCH_TESTS.json)。

## 拓扑的新增闭合与剩余问题

[`138ea07b21c55727c937831c396e80286b5ef586`](https://github.com/pypsa-meets-earth/pypsa-asean/commit/138ea07b21c55727c937831c396e80286b5ef586)引入0.1.1；其`modification_list.txt`在Thailand段明确列出删除766和772。0.1原始bus766属于TH、station524、230kV、(99.1181,10.5022)，765是115kV、(99.1171,10.5012)。变压器两端GIS与之相符。**恢复旧端点不是缺坐标问题，而是会撤销上游明确记录的删除决定。** 需要作者说明删除后的替代连接意图或完整可追溯修正网络；有此前提才能决定恢复/重映射。

数据和网络链见 [TOPOLOGY_TRACE.json](TOPOLOGY_TRACE.json)。修复评审门槛：TH与ASEAN逐snapshot负荷守恒、发电容量按carrier守恒、Line/Link/Transformer端点存在性、孤立分量及765对应区域连通性；不能只消除警告。现阶段不声称上述after检查通过。
''')

table='\n'.join('| '+ ' | '.join([r['country'], '缺失' if r['national_MWh'] is None else f"{r['national_MWh']:.9f}", '未分配' if r['node_sum_MWh'] is None else f"{r['node_sum_MWh']:.9f}", 'N/A' if r['absolute_error_MWh'] is None else f"{r['absolute_error_MWh']:.3g}", 'N/A' if r['relative_error'] is None else f"{r['relative_error']:.3g}"])+' |' for r in ind['countries'])
write('INDUSTRIAL_DEMAND_FIX_REPORT.md',f'''
# 工业GDP空间分配修复

**已通过10国2019基年已记录工业总量的节点分配守恒；尚未通过完整11国未来工业需求构建。** 没有应用增长因子，没有改国家总量，没有替代任何缺失的TL工业数值。

源NC：`GDP_PPP_1990_2015_5arcmin_v2.nc`，SHA256=`975ddfad5d2ee71aa227c269b530a4917f8305299b77d09ee0f9cfabc83e5e5b`。模型原有规则请求2020但数据仅到2015，继续使用原规则所选2015，并明确标记，不声称GDP年份为2020。单位constant 2011 international USD。

旧TIFF：289×289、无CRS、经度−1.667～22.417，完全不覆盖ASEAN。隔离副本由同一个NC恢复为2160×4320、EPSG4326、全球范围，记录raw SHA/year。原NC与旧TIFF均未改，前后hash一致。缓存单元测试还检验了值不变和有效缓存不被重复写入。

实际链：2015 GDP → 351个既有GADM区域（all_touched方式沿用上游）→ atlite气象网格几何 → 48个已有节点 → 原设施数据库432条已映射设施/无设施GDP回退 → 国家内行业权重归一化 → 2019基年工业量。这里复用教程的空间几何，**不代表六天气象结果成为正式输入**。

基年表hash=`{ind['national_source_sha256']}`；44个country/carrier行、572个数值单元格，表内已有0保持原样，未补值。每个country/carrier/industry分别检验，容差atol=1e-6MWh、rtol=1e-12。最大单元格误差 `{ind['max_cell_absolute_error_MWh']}` MWh。以下为全部载能的国家总和：

| 国家 | national MWh | node sum MWh | absolute error MWh | relative error |
|---|---:|---:|---:|---:|
{table}

[逐国CSV](INDUSTRIAL_CONSERVATION.csv)、[572项守恒证据](INDUSTRIAL_RECOVERY_EVIDENCE.json)、[节点已记录量](INDUSTRIAL_NODE_OBSERVED.json)及生成脚本validate_industrial_recovery.py均可审查。分配脚本不逐个手改processed CSV。

仍需评审：原设施locate_bus使用地理CRS最近邻（运行给出警告），设施空间合理性不由总量守恒证明；all_touched边界栅格共享也可能偏置权重。当前方法沿用上游，未擅自换分配假设。TL缺工业交易；未来DEFAULT CAGR与ammonia/process转换另行确认。新增缺国家检查会在11国数据缺失时显式报错，防止上游reindex(fill_value=0)把TL伪装为零。

代码提交：`{I}`；只应用于独立fix分支。下一步先核验数据边界再以正式空间分辨率回归，不把本次48节点诊断称为已完成100clusters/full-year工业模型。
''')

write('CARBON_EQUIVALENCE_TEST.md',f'''
# 碳约束等价性

**键和值的等价性通过；Full-SC排放范围的等价性未通过。** Baseline与DEC两组均保留；本轮未新增碳政策、未分配国家配额。

| 年 | 论文DEC MtCO2/年 | 混合键实际 Mt | 修复后 Mt |
|---|---:|---:|---:|
|2025|1000|77.5|1000|
|2030|820|63.55|820|
|2035|640|49.6|640|
|2040|460|35.65|460|
|2045|280|21.7|280|
|2050|100|7.75|100|

旧入口：`co2_budget.co2base_value`；正式新入口：`co2.budget.base_value`；当前ASEAN混合入口：`co2.budget.co2base_value`。`_helpers.migrate_config`迁移旧顶层入口，但不迁移混合入口；消费函数`prepare_sector_network.add_co2_budget`读取base_value，默认limit会引用co2.limit=77.5e6。修复只重命名ASEAN配置键，不改变1e9基数/系数/enable=false。

测试执行了实际迁移与实际budget/add_co2limit函数，创建PyPSA GlobalConstraint并核对六个年限额；另测8760h/144h缩放。`constant = base × year_factor × snapshot_weight_sum/8760`。旧legacy和修复后的新配置一致。混合用户自有配置仍须显式迁移；没有宣称改了helper以支持任意混合配置。

## 实际统计范围

作者网络中不为0的carrier因素是geothermal=0.12、co2=−1；CO2 atmosphere为非循环Store。电源CCGT/OCGT/coal/oil/lignite等通过多端Link排放到atmosphere，保留的SMR/SMR CC也在此记账；作者Baseline样本还含biomass Link。最终作者电力案例包括服务其电力/H2转换链的排放，因此不能把口径简化成“仅名字为coal/gas的Generator”。作者DEC2050实际GlobalConstraint为primary_energy/co2_emissions/100e6，Baseline没有CO2Limit。直接读取证据见 [PAPER_CARBON_ACCOUNTING.json](PAPER_CARBON_ACCOUNTING.json)。

当前add_co2建立共享大气Bus/Store；非电热锅炉、工业燃料、交通等部门也接入同一排放记账，燃料carrier因素可能置零避免重复计数。primary_energy约束对非循环Store末期碳变化及有非零carrier因素的Generator等计数，并不知道“电力研究口径”。关闭H2/CO2 network并不能阻止共享排放Store扩张范围。

单时段合成单元测试（HiGHS，非ASEAN实验）保持一单位电力服务：电力燃烧排0.4t；加入一单位非电热服务后同一GlobalConstraint记账为0.65t，+0.25t来自非电燃烧。两例optimal。见 [CARBON_SCOPE_TEST.json](CARBON_SCOPE_TEST.json)。此证据验证机制，未量化ASEAN新增排放。

## 保持电力口径的最小候选修复（未实施）

1. 在项目层为电力供应链建立独立排放ledger或独立线性约束，限额沿用上述区域轨迹；保留full-SC总排放账作报告，不将其直接用作原DEC预算。
2. 显式标识电力燃烧、地热、供电H2的制氢排放与capture credit；不得遗漏论文已有SMR/SMR CC链，也不得对燃料输入和大气Store重复计数。
3. CHP电/热联合产出、共享H2/合成燃料服务电与非电、DAC/CC信用如何归属，是保持原口径时必须阐明的边界。需要共同确定或恢复作者等价处理，不能凭技术carrier名称自动分摊。
4. 最小验收测试：paper裁剪网络预算表达相等；只增加非电服务不改变power账；燃料和CO2守恒；捕集/负排放不重复；Integrated与Disconnected拥有相同区域预算及排放定义。

这项范围修复没有执行。不能因所有六个数字一致就宣布DEC等价；也不能给每个standalone国家复制100Mt。未来Disconnected仍是同一个区域模型，保留区域CO2共享约束。Baseline无显式总碳上限，但其他CC/资源上限也需同样冻结。
''')

write('DATA_REPOSITORY_MAP.md','''
# 数据仓库与来源身份

数据登记采用来源家族验收 + 关键参数核验。不是逐行审批旧10,139条台账，也不把本轮技术检查转换成人工CONFIRMED。

| 层 | 当前存储/处理 | Git处理 |
|---|---|---|
| upstream tracked small raw | 官方data/中的0.1.1网络CSV、变更说明、AEO8成本附表、映射/配置 | 已存在模型Git历史，保留固定SHA与版权/来源；不复制成来源不明CSV |
| previous source recovery | research/00_source_provenance中的冻结源码/手工表/旧DEA工作簿 | 复用原审计身份；发布前分别核对原始来源条款，仓库代码license不自动覆盖每个数据源 |
| large raw | GDP NC、UNSD导出、EEZ/土地覆盖、气象 | 留在原位置，DATA_HASHES逐文件登记；原始获取时间未知即明确写未知 |
| processed | 国家工业基年量、cluster geometry、GDP layouts | 记录输入哈希和生成链；已有国家工业值未手改 |
| derived engineering | 修复工作区resources/phase2-industrial下新GDP栅格/GADM/keys | 大文件不入Git；validate_industrial_recovery.py从已有raw重建；便携JSON保存节点量和守恒证据 |
| author results | 两份已缓存作者NC；其他ZIP成员只有目录 | 参考证据，不是本项目再生输出；大文件不新发布 |
| formal outputs | 当前无 | 未来结果必须带run manifest，output hash与作者reference分开 |

[DATA_SOURCES.csv](data_registry/DATA_SOURCES.csv)列出来源ID、官方入口、版本、日期含义、预期文件、许可说明、用途、处理入口及状态。[DATA_HASHES.csv](data_registry/DATA_HASHES.csv)列具体字节哈希。SOURCE表sha256是**该家族已登记文件SHA排序后逐行拼接再SHA256**，hash_kind明确区分；它不是官方ZIP的哈希。空值表示尚未取得文件，绝不拿CRC或URL冒充SHA256。

retrieve_registered_input.py只对显式指定URL/版本/目标/大小上限下载到staging；已知SHA时检验，不匹配不采用，未知SHA时只记录UNVERIFIED。官方巨大气象ZIP目录已验证能访问，但未下载完整文件。压缩包解压仍需单独的文件清单、安全路径及checksum检查；工具不会自动将staging提升为模型输入。

本地输入包不等于作者输入manifest。当前登记覆盖本轮诊断和既有审计输入，**不是完整Full-SC运行input manifest**。缺失/未采用的数据家族仍阻塞正式运行。数据接受记录在 [DATA_DECISIONS](data_registry/DATA_DECISIONS.md) 与 [SOURCE_FAMILY_APPROVAL](data_registry/SOURCE_FAMILY_APPROVAL.md)。

GitHub发布状态以交付收据为准；本轮不会把“本地commit/已配置origin”写成“已上传GitHub”。大文件和未核明许可的数据不借发布绕过来源验收。
''')

write('data_registry/DATA_DECISIONS.md','''
# 数据决定记录

| Decision | 本轮依据 | 决定/状态 |
|---|---|---|
| D01 | 用户明确保持作者成本链 | 锁定technology-data v0.13.2及AEO8；未改参数；来源家族验收PENDING |
| D02 | 用户明确允许保留作者manual override | 保留电解投资曲线，SOURCE_PARTIALLY_VERIFIED；不伪造private communications，不用DEA原表550替换2030的1500 EUR2020/kW_e |
| D03 | 用户禁止更新DEA2026 | August2026/sheet80仅候选；不覆盖sheet86或模型表 |
| D04 | 现有GDP原始NC完整、缓存不匹配 | 仅在独立fix工作区重建；保留2015选择，不更新GDP年份/数值 |
| D05 | 十国基年量已有；TL缺行业记录 | 十国逐项守恒；TL=MISSING_NOT_ZERO；未来growth未决定 |
| D06 | 用户冻结Baseline+DEC及电力口径 | 碳键只改入口；不把预算扩到全社会；共享链路归属待共同决定 |
| D07 | 官方全年气象包可下载且文件名匹配metadata | AVAILABLE_CANDIDATE，完整字节/坐标/作者input hash未验；不宣称正式复现 |
| D08 | 上游明确删除bus766 | 不擅自撤销删除、改端点或删变压器；作者意图/可信修正方案待恢复 |
| D09 | 用户选择电力互联为第一干预 | 未来仅关跨境AC/DC；其他载能/外部商品边界保持同一；不生成国别碳配额 |

所有决定区分“用户已经规定的研究原则”和“仍需人工接受的数据”。无任何来源被Codex标成CONFIRMED。未来接受记录必须包含来源家族、固定版本/hash、允许的变换/override、关键参数检查、批准人/日期、适用场景和仍保留的局限。
''')

write('data_registry/SOURCE_FAMILY_APPROVAL.md','''
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
''')

write('REPRODUCIBILITY_RULES.md','''
# 本轮复现规则与运行manifest

1. 固定完整模型SHA，paper/upstream/research严格分层；修复与研究变化分开commit。不要force-push，不要覆盖原教程/作者输出。
2. 正式配置由base + project override合并，保留最终有效配置、修改来源、文件hash；数据下载刷新要关闭或严格固定文件身份。仅改配置的路径不证明物理边界不变。
3. 正式run在清洁模型工作区启动，结果输出到独立run目录。登记所有实际输入（含component overrides）、config、环境锁/完整freeze、solver/version、时间/权重、场景/规划年、输出hash。
4. run_manifest.py已实现并用合成命令验证：成功、命令失败、旧输出拒绝、dirty checkout拒绝。它不自动选择实验、不批准数据、不把命令exit0当成optimal。见RUN_MANIFEST_TEMPLATE.json和RUN_MANIFEST_TESTS.json。
5. solver adapter必须输出JSON字段`objective`、`solver_status`、`constraint_residual`。residual定义为同一约束单位下最大绝对违反值（等式abs(lhs-rhs)，<=为max(lhs-rhs,0)，>=反向）；应另报类别/尺度与采用容差。工具记录有限测量值，但**不代定科学容差**；COMPLETED表示执行与记录完整，不等于实验验收。
6. 声明的input清单完整性仍需workflow审查；工具可检测清单内输入被改写，无法证明调用程序没有读未声明文件。正式运行前需从完整DAG生成输入清单并核对。
7. 守恒/约束/目标差异比逐文件hash更适合验证重新生成的NetCDF语义；压缩或时间戳差异可导致相同物理内容但不同hash，需同时保留两类证据。

## 重新执行本次工程核验

在已固定的官方源码上，分别应用patches中的两个git format-patch（独立分支，不混成一个提交）；使用既有pypsa-earth环境运行各分支tests/test_*.py。真实数据复算由validate_industrial_recovery.py执行，需要原始GDP、基年表、地区/设施/人口文件，路径可通过ASEAN_PHASE2_ROOT、ASEAN_TUTORIAL_ROOT配置。该脚本仅对48节点已有几何做诊断，不启动求解。

engineering_review.py是首次在干净官方worktree创建补丁及before/after证据的一次性脚本，带HEAD/dirty保护；不要在已修复分支再次运行。保存的tests可反复运行。prepare_model_layers.py和commit_fixes.py保留首次建层/提交痕迹；已经存在的交付分支优先复用，不重新造重复分支。

数据台账的确定性提取在prepare_registry.py，CSV由export_registry.mjs通过artifact-tool生成；大GDP派生文件留在fix工作区，节点量/误差在便携JSON/CSV。报告由write_reports.py从证据生成。所有再生工作都应先核对输入hash，发现漂移停止对应步骤。
''')

write('NEXT_EXPERIMENT_READINESS.md',f'''
# 下一阶段就绪性与A–F回答

**目前不能冻结Full-SC可执行实验设计，也不能启动Integrated/Disconnected正式研究求解。** 可以继续已有方向下的边界讨论、来源家族验收和单元/守恒验证。

| 用户问题 | 回答 |
|---|---|
| A Paper SHA真正可运行？ | 尚未证明。源码解析/DAG部分展开成功，但原始输入未齐且作者input身份不完整；正式reference未求解 |
| B 官方SC baseline冻结？ | 官方源码、branch、完整SHA `{U}`已冻结；“可信Full-SC物理/数据基准”未冻结 |
| C 哪些fix通过？ | GDP缓存重建/十国基年工业分配守恒；碳配置键/六年轨迹/时间权重兼容；另有碳范围与manifest单元测试。均不等同于完整模型通过 |
| D sector/data blockers？ | TL工业、增长/工艺、热/住户/服务与交通需求、共享资源/commodity及key costs；final电力裁剪/缩放；拓扑损失 |
| E 能冻结Integrated SC vs Disconnected SC设计？ | 干预概念已冻结为跨境AC/DC电力；可执行配置与数据/碳边界尚未冻结，故否 |
| F 最少剩余blockers？ | 以下五项 |

## 最少五项闭合条件

1. **正式参考输入/环境身份**：取回并核对完整气象、土地覆盖等原始输入；接收作者input manifest或明确“可重建但非字节级同一”的复现标准；完成2025单一reference及正式solver资格验证。
2. **Full-SC服务需求边界**：解决TL工业缺项（提供可信资料或共同决定并明确标记范围处理）；确认增长/工艺、热住户服务需求不重复、交通/航运/航空及现有能力来源。不填假设零。
3. **Power-sector碳等价表达**：专属排放账/约束与SMR、CHP、共享燃料、capture信用归属；Baseline/DEC均保留，预算值不改，不扩为社会全部门限额。
4. **网络与终端需求守恒**：作者对766删除的后续意图/可信修正网络；验证765负荷/容量保留、连通性、正式分辨率。同时对final_adjustment需求缩放/载能名称和取消电力裁剪后的需求总账做回归。
5. **来源家族验收与研究边界表**：冻结成本/手工覆盖/燃料口径、共享生物质等资源与外部commodity边界；对新上游已有ammonia/H2 turbine能力明确是否纳入；Integrated/Disconnected除跨境AC/DC外相同。

## 已经不需要用户重新找的材料

- 官方SC/论文完整SHA、代码历史与作者有效配置。
- 旧DEA sheet86和technology-data v0.13.2 SHA、manual override处理链。
- 原全球GDP、十国工业基年量、设施/空间分配失败机制；正确缓存与守恒修复已形成。
- 旧/新碳键与错误限额来源；独立修复及测试。
- bus766旧坐标、国家/电压及0.1.1明确删除记录；缺的是删除后的网络意图。
- 官方全年亚洲气象包入口、文件清单与可下载性；缺的是完整取回/作者字节对应。

## 真正需要用户资料或共同决定的事项

原始资料：若已有作者完整input manifest/全年输入/环境运行记录，可缩短核验；TL工业原始分项；bus766修改意图或作者修正版本。用户无需再重找已恢复DEA旧表。private communications拿不到时遵从用户要求保留作者电解值、SOURCE_PARTIALLY_VERIFIED。

共同决定：来源家族接受；TL数据不足的透明研究范围处理；工业增长；热/服务定义；共享资源与commodity供应；电力碳账中联合技术归属；复现误差/残差容差。它们不是可以由Codex“补齐”的数字。

已经决定、无须再问：先Integrated vs Disconnected（单一区域模型），只变跨境AC/DC；Baseline和DEC都保留；standalone靠后；不做博弈、延迟、新技术研究或新碳政策。本轮没有正式科学求解，没有CONFIRMED数据条目，没有采用DEA2026。
''')

write('README.md','''
# Phase 2 — 基准分层与工程修复交付

建议先读 [NEXT_EXPERIMENT_READINESS](NEXT_EXPERIMENT_READINESS.md)、[BASELINE_ARCHITECTURE](BASELINE_ARCHITECTURE.md)、[ENGINEERING_FIX_REGISTER](ENGINEERING_FIX_REGISTER.md)。

本轮形成两个独立fix commit、十国基年分配守恒证据、碳键/范围测试、论文DAG预检、固定官方SC来源、来源家族登记及manifest工具。正式论文重建尚未完成；未运行Integrated/Disconnected或standalone。

交付文档：

- [PAPER_BASELINE_REPRO_STATUS](PAPER_BASELINE_REPRO_STATUS.md)
- [UPSTREAM_SC_BASELINE](UPSTREAM_SC_BASELINE.md) / [SECTOR_ENABLEMENT.csv](SECTOR_ENABLEMENT.csv)
- [INDUSTRIAL_DEMAND_FIX_REPORT](INDUSTRIAL_DEMAND_FIX_REPORT.md) / [INDUSTRIAL_CONSERVATION.csv](INDUSTRIAL_CONSERVATION.csv)
- [CARBON_EQUIVALENCE_TEST](CARBON_EQUIVALENCE_TEST.md)
- [DATA_REPOSITORY_MAP](DATA_REPOSITORY_MAP.md) / [DATA_SOURCES.csv](data_registry/DATA_SOURCES.csv) / [DATA_HASHES.csv](data_registry/DATA_HASHES.csv)
- [REPRODUCIBILITY_RULES](REPRODUCIBILITY_RULES.md) / [RUN_MANIFEST_TEMPLATE.json](RUN_MANIFEST_TEMPLATE.json)
- [SOURCE_FAMILY_APPROVAL](data_registry/SOURCE_FAMILY_APPROVAL.md) / [DATA_DECISIONS](data_registry/DATA_DECISIONS.md)

证据标签：直接读取=固定Git/已有文件/作者metadata；实测=脚本回归和微型单元测试；结构推断=full-SC对互联的响应途径；候选方案=尚未实施的power carbon scope修复。技术测试通过不等于人工接受数据。
''')
print('Wrote Phase 2 reports from saved evidence')
