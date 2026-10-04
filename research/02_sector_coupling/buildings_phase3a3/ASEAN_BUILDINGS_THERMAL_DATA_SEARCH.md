# ASEAN Buildings thermal-service data recovery

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent (evidence interpretation)
- Mode: validate; Version: Phase3A3-1; Date: 2026-10-01 Asia/Shanghai
- Verification Status: ANALYZED; all candidates UNVERIFIED / human PENDING

## 结论

找到了可继续核验的官方端用途来源族，尤其是马来西亚能源委员会居民/商业表；找到了区域样本层的 space/water 区分和河内热水时间观测。**未找到已核实、同年、覆盖 11 国 Residential 与 Services 的 useful-heat 或全年小时曲线。** 本轮没有拼接或采用新需求量，没有替换 0.6/BDEW。

本轮是有界快速检索：先复用 Phase3A2 的 AEO8、ESDM2019、KH 统计、NEA、IEA/ACE 元数据，再沿官方和原作者来源追踪 B1/B2/B3。检索轨迹见[SEARCH_LOG](evidence/SEARCH_LOG.md)。停止条件是能够判断候选可用性、覆盖与关键缺口；“未找到”只指本次检索范围，不是证明资料不存在。

## B1：年度端用途/热数据

### 马来西亚：本轮最重要的原始统计恢复

[能源委员会 NEB2016](https://www.st.gov.my/resources/national-energy-balance-2016) 的现行官方 PDF 已缓存，版本为 2016 edition、2018 年发布。PDF/印刷第 92 页说明居民调查基于半岛 2,000 户；第 95 页 Table42 给出 2016 final energy by fuel/end-use；第 98 页商业调查说明半岛范围和 12 类，Table47（第 103 页）给出商业 final electricity 分解。

原表例值：R water heating 70 ktoe、cooking 655 ktoe、总量 2,875 ktoe；商业 water heating 1,034.62 GWh、总电量 39,106.00 GWh。原始单位分别保存，**未转换成 useful heat 或写入 PyPSA**。这些值尚有年份、半岛到全国、调查推算方法以及模型 Services 分类对应问题。没有 space-heating 列不能解释为全国真实采暖为零。

[ERIA 2021 商业建筑指南](https://www.eria.org/uploads/Technical-Guidelines-Energy-Efficiency-and-Conservation-Commercial-Buildings.pdf) Table2.2（PDF16–17）转引相同 GWh 表，但 Figure2.2（PDF18）把 39,106 标为 ktoe。原表和转引表共同支持 **GWh 是该电力表口径**；图标题错误疑点保留，不采用图上的 ktoe。两页已视觉检查，不是只凭搜索摘要判断。

### 区域试点与其他国家来源

[ERIA 2013 修订试点](https://www.eria.org/RPR_FY2012_No.19_chapter_1.pdf) section5 / Table11 覆盖 KH、LA、VN、ID、PH、TH、MY、SG；112 名受访者主要由工作组同事/邻居选取，时间为 2011 年 9 月至 2012 年 2 月。表含燃料/端用途与 space/water 区分，但属于小样本估算，不能年化外推各国总需求。2013 修订本处理了早期额定功率造成的高估；不应沿用未修订版本而不说明。

[菲律宾 DOE HECS 汇编](https://legacy.doe.gov.ph/sites/default/files/pdf/energy_statistics/doe_compendium_energy_statistics-1990-2021.pdf) 的官方索引可见 2004/2011 按地区和用电端用途表。旧域名本地解析失败，机构给出的现域名返回非 PDF；本轮只恢复到官方索引/元数据，未取得可哈希原始 PDF，也未确认回忆期。没有把 kWh/household 擅自视作年度量。

[Murakoshi 等 ECEEE2017 原作者关联副本](https://www.belda.asia/wp/wp-content/uploads/2017/06/170608ECEEE201_BELDA.pdf) 覆盖 MY/TH/VN/KH 选定城市与村庄的 1,190 户，能源账单期为 2014-10 至 2015-09。适合检验用途差异与调查方法；样本区域不能代表全部国土。原文讨论河内/Hoa Binh 样本采暖小于总能耗 1%，不支持全 ASEAN 统一采暖份额或一律置零。

[Le & Pitts 2019](https://doi.org/10.1016/j.enbuild.2019.05.051) 的出版社/大学元数据说明 Tuy Hoa 的 60 户 2017 年调查，样本 LPG cooking 占比不可忽略。大学 PDF 返回 403，未绕过限制；本轮只以摘要支持用途核查，不提取新的 thermal input。

[ACE 马来西亚调查公告](https://www.aseanenergy.org/articles/malaysias-energy-survey-benchmarking-effort-gains-insights-from-the-asean-centre-for-energy) 是官方调查线索，不是可直接计算的数据库。先前 AEO8/NEA/ESDM/KH 来源继续沿用其版本限制，不重下载、不覆盖。

## B2：space / water split 的证据能到哪一步

有 **ASEAN 地区样本证据**，没有可直接采用的统一 11 国比例。

- 马来西亚官方表明确列 water heating；无独立 space-heating 列，不能反推严格零。
- ERIA 修订试点提供 space 与 water 栏，但便利样本、旧期和估算方法限制其适用性。
- ECEEE2017 的越南北部与南部选区有气候差别；少量采暖与热水不能混为一个固定 60/40 比例。
- 为 useful heat 还需要最终燃料/电热到服务的效率、COP、热值基准和用途映射。该转换没有由官方 final-energy 表自动完成。

## B3：比 BDEW 更适合 ASEAN 的 temporal basis

[Toyosada 等 2018 河内受控生活实验](https://www.scirp.org/journal/paperinformation?paperid=82791) 给出局地热/冷水使用观测：9 个高收入家庭、35 人、冬季短时住宿，section2.2 / Fig3–5 有用水时序。**这是比欧洲曲线更贴近当地行为的研究线索，不是可立即替换 BDEW 的热服务曲线。** 热冷水混合体积不等于 thermal MWh；短时入住/离开造成的峰值不能直接当典型日；缺少全年、weekday/weekend、Services 和原始时间序列。

可讨论的方法是：各地区接受的年度服务量 × 当地 R/S 用途时间形状，并用当地温度/进水温度等独立证据控制必要的季节变化。该方法是 **PROPOSED METHOD**，本轮未生成任何新 profile、温度阈值或效率数值。采暖只能在真实需求有证据的地区讨论；E2 报错不能代替这个科学决定。

本次未恢复可覆盖 ASEAN Services 类别的统一热水日型，亦未找到已验收的全区域 space-heating 温度阈值。BDEW 只保留作原模型对照。

## 11 国覆盖矩阵

“有来源”不表示本国科学输入已足够。UNSD2019 的各国 R/S final-energy 底表继续保留；下表专指额外 thermal/end-use 证据。

| 国家 | Residential 候选 | Services 候选 | temporal / split 覆盖限制 |
|---|---|---|---|
| BN | 本轮未恢复明确热端用途表 | 未恢复 | 不补为零 |
| KH | ERIA试点、ECEEE样本；既有MME/ERIA燃料统计 | 既有燃料统计，非useful heat | 局地样本，无已验hourly |
| ID | 既有ESDM2019、ERIA试点 | 尚无完整thermal表 | UNSD商品/部门冲突仍在 |
| LA | ERIA试点 | 未恢复 | 极小样本，非全国量 |
| MY | NEB官方R用途表 | NEB商业电力用途表 | 半岛、旧年；缺全年R/S形状 |
| MM | 本轮未恢复明确热端用途表 | 未恢复 | 不以其他国替代 |
| PH | ERIA试点；HECS官方索引 | 未恢复 | HECS原始PDF未获取 |
| SG | 既有NEA2017、ERIA试点 | 未恢复完整thermal表 | 家庭电力份额非全国R/S曲线 |
| TH | ERIA试点、ECEEE样本 | 本轮未取得可验thermal时序 | 不用商业推广材料构造负荷 |
| TL | 本轮未恢复明确热端用途表 | 未恢复 | ASEAN10材料通常不覆盖 |
| VN | ERIA、ECEEE、TuyHoa摘要、河内用水观测 | 未恢复统一thermal表 | 区域/收入/季节限制明显 |

## 身份、版本和采用门槛

[候选表](ASEAN_BUILDINGS_DATA_CANDIDATES.csv) 8 项，新下载成功 6 项；2 项本地原始文件缺失，hash 留空并记录失败，绝不写伪 hash。[更新登记表](BUILDINGS_DATA_REGISTRY_UPDATED.csv) 保留上轮 42 项并新增 8 项，共 50 项。全部 UNVERIFIED/PENDING。

URL、缓存字节数、SHA256、读取日期、迁移地址和失败尝试见[下载清单](data/raw/buildings/RETRIEVAL_MANIFEST.json)。数据只位于研究层 `data/raw/buildings/`；processed/derived 只存来源定位、候选元数据和合成验证结果。没有生成科学模型输入。公开可读不自动等于开放数据许可，逐来源记录许可已核实程度；不将二进制推送 GitHub。

没有要求用户重找本轮已恢复的文件。只有未恢复的原始表/微观或小时数据，以及研究范围和转换接受决定，才保留为后续缺口。
