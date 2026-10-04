# 定向证据检索记录

日期2026-10-02；优先复用既有9份原件与12份UNSD导出。目标为E3，不是ASEAN全面文献综述；未扩展到无既有候选的新国家研究，也未从图中反推数值。

| 对象/检索 | 结果与停止点 |
|---|---|
| AEO8主报告与November2024勘误 | 已有原件；检查PDF48/49/82及勘误3，确认发电口径、BAS假设和2050总量不变。未搜更新版替代。|
| DemandCast arXiv2510.08000v1、Zenodo18374352、paper-cited GitHub v0.9.0 | 取得论文HTML、ZenodoJSON、Git tree和4个相关blob；未得到导出manifest/Ember历史CSV。|
| Ember方法官方PDF | 下载当前v1.6；只用来识别方法风险，不冒充历史数据版本。|
| GEGIS作者仓库、PyPSA-Earth demand官方文档 | 定向核实GEGIS normalized-hourly vs annual角色；当前网页不等于P的历史生产环境。链接见边界报告。|
| MY NEB2016官方缓存和现行官网旧版文件 | 定位Tables39–42/47、R/S调查覆盖，目视核对PDF95/103；查转换/efficiency未恢复历史设备能量份额。|
| SG NEA2017官方release及历史水热器方法线索 | 7295GWh与典型户11%不能混用分母；现行设备法规不是2017存量季节性能，未采纳。|
| PH DOE Compendium1990–2021、2011 HECS、2023 HECS技术说明 | 搜索索引可见Table2与六个月脚注；legacy下载DNS失败，current同路径返回HTML；PSA native403。没有原表hash，没有把索引数字变成input。|
| ERIA2013、BELDA2017、VN Toyosada2018、ID HEESI2019、KH2019/20 | 全部复用候选/官方缓存，定向读取用途、覆盖、年份和定义。地方mixed-fuel与冷热水量不视为国家electric heat。|

下载成功/失败与时间戳见SOURCE_REGISTRY；最初受网络沙箱限制的一次失败另存INITIAL_NETWORK_ATTEMPT，不把网络失败说成“数据不存在”。搜索索引线索只作为INDEX_ONLY；没有全文/原表时停在确切缺口。

当前网页辅助来源：
- https://github.com/niclasmattsson/GlobalEnergyGIS
- https://pypsa-earth.readthedocs.io/en/latest/tutorials/use-cases/3-demand-data/
- https://legacy.doe.gov.ph/sites/default/files/pdf/energy_statistics/doe_compendium_energy_statistics-1990-2021.pdf
- https://psa.gov.ph/statistics/technical-notes/1684076304

所有数值候选只能来自本地有SHA的原件；本轮没有联系作者或申请新数据账户。
