# 国家与地区的 Space / Water 证据映射

Material Passport: academic-research-suite / evidence map; Phase3A5 v1; 2026-10-02。observed只表示相应源范围有报告，非全国数据验收。没有国家在本轮被赋予space heat=0。

| 国家 | R space | R water | S space | S water |
|---|---|---|---|---|
| BN | unknown | unknown | unknown | unknown |
| KH | region-specific：ERIA城市便利样本报2.1Mcal/户；定义/燃料待核 | local observed：ERIA城市173、乡村134.2Mcal/户，混合燃料 | unknown | unknown |
| ID | unknown：样本四舍五入0不推全国零 | local observed：ERIA城市373.7、乡村570.9Mcal/户 | unknown | 定义包含water heat，数量unknown |
| LA | unknown | local observed：ERIA城市456.5Mcal/户 | unknown | unknown |
| MY | unknown：NEB表无space列 | observed：2016官方R电水热70ktoe；Peninsular覆盖桥待定 | unknown：other不等于排除space | observed：2016商业电水热1034.62GWh；覆盖/表内差待定 |
| MM | unknown | unknown | unknown | unknown |
| PH | unknown | 国家调查索引有2011水热用电，原件未得；ERIA地方混合燃料为补充 | unknown | unknown |
| SG | region-specific：ERIA城市便利样本2.1Mcal/户，不能视为全国需求；NEA未给space值 | observed share：NEA典型户电水热11%；国家加权量unknown | unknown | unknown |
| TH | unknown：BELDA所选Bangkok/SamutSakorn不能代表全国 | local observed：ERIA城市10.6、乡村144Mcal/户；BELDA行为补充 | unknown | unknown |
| TL | unknown | unknown | unknown | unknown |
| VN | region-specific：BELDA Hanoi/HoaBinh样本有space heat且占样本能耗<1% | local observed：ERIA、BELDA、Hanoi九户用水时序；全国电热量unknown | unknown | unknown |

ERIA数字严格保留Table11的Mcal/household，未年化，非电力专属值。BELDA2017 PDF6地区供暖证据不能扩展为全国电加热；作者对热带普遍不需供暖的概括不能覆盖北部/高地或微小正值样本。没有明确测量及检测下限/代表性时不标negligible。

建模映射顺序：源中明确用途→原覆盖区→供能燃料→设备输入份额→交付服务。无法分类的直接能耗继续留原账户，不强行按space/water二分。没有ASEAN universal60/40，也不把总电力GDP/population0.6/0.4当热用途份额。

对应逐项来源、哈希和待定字段见44行历史电热矩阵及140行候选。冻结模型的统一默认份额仅为框架行为，不是本图接受的数据。
