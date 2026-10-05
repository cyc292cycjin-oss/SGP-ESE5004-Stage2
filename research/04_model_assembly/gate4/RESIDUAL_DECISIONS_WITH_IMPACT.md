# Gate4剩余原件与可执行选择

当前未求解诊断资产已可检查组装；完整模型仍未完成。以下只列未闭合事项。已批准寿命、映射、增长、Mtoe、EV embedded、bunker恒定、费用及七池水电方法不再待决。

## 1. 掺混原件：10项精确请求，影响18个物理账户

[EXACT_SOURCE_REQUESTS.csv](EXACT_SOURCE_REQUESTS.csv)包含可直接访问的官方查询、DSD代码、缓存父项hash/行号、已有失败回执、单位/脚注与受影响账户。只需2019同用途ZG/ZD的数量和包含关系；父项已缓存，不要求再找父项。

|国家|需要的memo与用途|
|---|---|
|ID|ZD/5222：121工业、1221道路、1235服务|
|PH|ZD/5222：121工业、1221道路、1222铁路、1232农业、1235服务；ZG/5212：1221道路|
|VN|ZG/5212：1221道路|

1235=Services、1232=Agriculture；ID服务请求此前已覆盖。本轮没有重复空查询。请求映射合格不代表去重合格，仍为NO_MATCHING_TRANSACTION_RETURNED。若新memo修订了父项，需同版父/子/memo联审；不将新版子项扣旧版父项，不用政策掺混比例，也不把missing写成0。PH铁路仍不能物化；Animal waste如在后续合格生物需求中出现，须单独验证供应/物理排放资格。

## 2. 覆盖范围：5个国家×燃料组与4国bunker

|来源组|冻结来源事实|影响目标数|最少原件或一次性选择|
|---|---|---:|---|
|BN煤炭|brown coal及子项lignite均记录341.064千吨进口、同量供给及全额自备电厂转换；两层商品不能相加；没有FEC父项|4|选择将这一限定统计范围的煤炭流量仅解释为转换投入、不给四个最终用途创建额外Load；或提供2019最终消费分部门原表。新覆盖解释尚未批准|
|TL天然气|原生产与出口均183311.18058TJ，原总能源供给为0；没有最终用途叶节点|3|选择以该源平衡范围的零总供给建立最终用途覆盖证明；或提供相容最终消费原表。未自动把零TES升级为部门零证明|
|KH/LA天然气、TL煤炭|冻结导出中相应商品族缺失|11|提供2019完整国家能源平衡相应燃料列（含零/不适用注释）；否则只能明确批准“缺来源的统计范围”边界并保留未知，不可声称实物零需求|
|BN/KH/LA/TL国际海运bunker|国内FEC不含国际bunker|4|各国2019国际海运燃料交付/国际bunker官方原表或明确来源化零/不适用证明；土地/港口印象与国内NEC不作为零证据|

前两组可形成一次覆盖决定，后三个缺来源燃料族可集中为一次明确的统计覆盖决定。上述选择均PENDING，当前没有删除未知需求。2019国际bunker一旦源量合格，沿用已批准constant2019；无需重新批准2050增长。原记录、单位、完整交易集合见evidence/diagnostic/REMAINING_SOURCE_FAMILY_SCOPES.json。

## 3. 五组原水电：684MW

|待接入组|已有候选输入（2013全年）|需明确的选择|
|---|---|---|
|ID Java-Bali ROR47MW|未使用`ID_Java-Bali1 2 ror`：原233291.836763MWh/年；按47MW包络可用223759.173794MWh/年|批准将这个原资源组用于该受限区域机组，或补其真实映射；这是新的水文空间代理，电网同区不证明同流域|
|ID Kalimantan水库110MW|互斥A：`ID_Kalimantan4 1 hydro`，789191.076448MWh/年、Emax8250MWh；B：`ID_Kalimantan4 4 hydro`，532286.028026MWh/年、Emax180MWh；均未使用|必须选择一个相容来源并说明覆盖，不相加；或提供原组映射/库容|
|MY Peninsular ROR54MW|无同类型区域参考输入|提供相容2013全年可用性与原覆盖，或提出另一个有来源代理后批准|
|PH Mindanao水库213MW、260MW|无同类型区域参考输入|提供各组相容全年来水及Emax/库容、原资产覆盖，或另行批准有来源代理；两组仍独立|

精确源ID、原父项/机组、未使用状态与hash见evidence/diagnostic/FIVE_HYDRO_CHOICES.json。七个已接入资源池770MW不重开。新来源及资源归属未获批准，以上数值没有进入生产合同。水库参考约6h仍是冻结原输入代理，不属于PHS6h决定的扩展。

## 4. GPD条件存续与缺年份库存

原待核2656.09MW中，本轮确认两座柬埔寨水电366MW重复；不新增、也不叫退休。EAC报告的厂址、许可证及容量与GEM已表示的站点一致；Tatay运行2014/商业运行2015的区别解释年份差异。原418MW重复保留。GPD表共列116行，包括先前418MW复用行；已接入44.4MW油电未重复审计。

剩余2290.09MW：

- 水电108个GPD记录1615.09MW：缺强身份闭合，且独立身份成立后仍缺GPD专属水资源合同。名称/业主/容量/坐标候选关系已批量登记；不同ID或无近邻不作为独立证明。
- Avion100MW：官方市政府资料写明开式循环、97MW，冻结派生表却为CCGT100MW。需要原DOE机组记录确认容量口径，并选择相容既有OCGT性能/寿命/成本处理；没有自动改技术或套2050新建参数。
- MM Ngam Tae230MW：Gas标签不能证明CCGT，需原配置/运营状态；Malamyine45MW与GEM40MW mothballed的候选存在容量/业主/状态差异，需原记录辨认。
- PH SCPC U1 300MW：GPD业主名称指向Malita关联方、坐标却在Limay；SMC原报告区分两处法人及机组。需原DOE电厂/机组标识行，不能凭300MW或最近位置选一个GEM站点。现有两站均已由GEM表示。

最少请求为相应来源的机组标识、运行状态/技术、容量口径及对照ID，不要求逐台未来退役公告。不符合条件的参数不填虚值；本轮实际新增容量0MW。

缺年份集合分开：GEM108条4092.52MW；GPD178条15477.503MW。仅用缓存完成30条跨来源名称/父项候选关系，尚不证明独立或重复，不能直接相加。evidence/diagnostic/MISSING_YEAR_GROUPED_CHOICES.json按国家×技术列明容量、原ID与待决选择；可补相容投运/运营证据，或明确选择带不确定性的库存情景边界。本轮未批准剔除、无限寿命或假年份。128条1861.5MW上界证明保留。

## 证据身份

UNSD1234定义核验入口：[官方UNdata LPG1234](https://data.un.org/Data.aspx?d=EDATA&f=cmID%3ALP%3BtrID%3A1234)。原始LPG数量始终来自冻结本地源文件。

EAC原报告2015版汇编2014监管数据，恢复于[报告存档镜像](https://data.opendevelopmentcambodia.net/en/dataset/ff4caebf-1b83-4ac6-81a7-efeed27025db/resource/cb27c380-4f6d-4d11-9b1d-77e5d5822527/download/report-on-power-sector-of-the-kingdom-of-cambodia-2015-edition.pdf)，PDF第27–28、89页；不是新电厂库。

Avion技术核对：[Batangas市政府官方落成记录](https://batangascity.gov.ph/web/current-news/1168-san-gabriel-and-avion-power-plants-inauguration)。SCPC身份冲突核对：[SMC原2018年度申报](https://www.sanmiguel.com.ph/storage/files/reports/SMC_17A_04.12_.2019_-_Full_Report_.pdf)，PDF第13–14页。新取文件仅用于身份/交易/技术拒绝检查，没有把其中新数值自动替换为模型参数。原件及hash见evidence/diagnostic/source_identity。
