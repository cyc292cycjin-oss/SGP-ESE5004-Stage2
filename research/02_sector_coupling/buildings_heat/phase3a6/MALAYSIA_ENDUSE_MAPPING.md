# Malaysia 部门、地域与用途映射

**2016住宅和商业用途表均是 Peninsular Malaysia。** 全国外推不能由“Malaysia”书名推导。来源为NEB2016，SHA `64c1fb95c13b8767a320364a046f832e6072a7f1520fe77a1fd661572272e914`；官方原件与定位见来源账本。

## 住宅

PDF91为半岛住宅章；PDF92说明调查2000户、四大区域、十类房屋，含53种电器，图示历史2011–2014。这不能证明2016每个单元格来自新的一轮2016实测。Table42（PDF95）明确表年份2016，调查波次到该表的外推/权重方法仍待附录。

| 用途 | electricity，ktoe | 非电投入 | E3去向 |
|---|---:|---|---|
| space cooling | 327 | 原表破折号不转成零 | 保留在T_R内部direct electricity子账户 |
| water heating | 70 | 其他燃料未给出可用拆分 | 候选h_R,water的终端电输入；不是useful heat |
| lighting | 233 | kerosene 3ktoe | 电与直接燃料分别保留 |
| cooking | 117 | natural gas 1、LPG538ktoe | NON-EXPLICIT + ACCOUNTING REQUIRED；不进入space/water热 |
| appliances | 1586 | 未进一步拆分 | direct electricity；不假设无隐藏电热 |
| 总电力 | 2333 | 各燃料总量另记 | 父账户，不与用途子项再次相加 |

五项电力恰好合计2333ktoe；cooking三个燃料单元格合计656，而打印总数655，保留差异。没有space-heating专列，判定 **NOT SEPARATELY REPORTED / UNKNOWN**；不能用热带气候或原表加总恒等式证明零。非商业firewood/biomass在NEB notes明确排除，也不能填零。

## 商业到Services

PDF97为半岛商业章；PDF98说明5000处经营场所、按服务业GDP对12个地区/州及12类活动抽样。文字同时使用未来时态描述调查计划，进度图为100%；出版物没有足够的调查日期、扩样系数、误差和2016回推方法，因此记录调查简介，不把“样本达到目标”当全国代表性证明。

12类为批零、运输仓储、住宿餐饮、信息通信、selected services、专业科技、旅行社、公共行政、教育、医疗社会工作、艺术娱乐、other services。**Commercial→PyPSA Services是待验收的活动映射**。特别是运输仓储场所用电应与牵引用电分开，不能重复计入交通部门；selected/other services需代码表或调查说明。

Table47 PDF103：cooling16440.66、water1034.62、lighting8516.23、other13114.06GWh；打印总量39106.00GWh，子项合计39105.57，差0.43GWh。水热在个别类别中的破折号不擅自变零。空间采暖无专列，仍UNKNOWN。Table48 PDF104另有LPG679ktoe，全部列为other use；本轮不把它全塞入cooking或水热。

映射规则是保留已知烹饪电力为direct electricity，已知烹饪燃料为direct fuel；未知用途继续unclassified。cooling只是T_R/T_S的子账，不额外添加Load。不能说全国所有烹饪燃料已被完整识别，但原来源已知量没有删除或迁移到热需求。

## 单位与地域检查

NEB2016 PDF105选择NCV，1toe=41.84GJ；PDF108给1000toe=41.84TJ和electricity3.6TJ/GWh。因此1ktoe=11.622222…GWh，住宅water70ktoe=813.555556GWh。此系数是该原件的定义，不擅自改为国际常用41.868。

Table17 PDF59住宅半岛27119GWh，与2333ktoe转换的27114.644444GWh差4.355556，**符合整数ktoe舍入可能范围只是推断**。商业Table17半岛39484GWh与用途表39106差378GWh，未被同样解释。两组表仍分别保存。

本轮不向全国2019或其他ASEAN国家复制份额。每个row均保留地域、来源年、表、hash、父/子/替代来源角色与PENDING确认状态。
