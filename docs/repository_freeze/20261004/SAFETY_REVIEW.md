# Remote publication safety review

审计日期：2026-10-04。结论：12个工程/参考ref允许推送；完整研究归档ref保持 **HOLD — FILE_RIGHTS_UNRESOLVED**。这是本轮上传规则的执行判断，不是认定历史使用违法，也不否定科学结果。

## 范围与方法

在推送前，以origin已有分支为排除集，枚举8个候选分支和14个里程碑的新增可达历史对象，包含后来删除或改写的blob。扫描 **879个新增blob，42,278,028字节**；最大为DATA_LEDGER.csv 7,162,387字节，新增对象无大于10MB文件。完整对象列表在evidence/NEW_REACHABLE_OBJECTS.json；每ref的对象集合在CANDIDATE_REFS.json，供复核真实归属，不能将同内容blob的所有别名误当作每个ref都有该路径。

检查大小、原始/二进制文件、NetCDF/ZIP/天气cutout/环境目录、常见token/私钥/凭据赋值模式、通信标签。受检新增对象没有发现token/私钥，没有NetCDF、9.9GB作者包、weather cutout或本地环境缓存。有限模式扫描不是零泄漏的普遍证明。原有远程历史未重新发布或改写。

通信匹配9项经定位分别为8个git format-patch头、1份用户基础设施任务书中的`Subject`写作要求。不是导师私人邮件正文。任务说明与公开源码中`private communications`来源标记不能混同实际私有通信。没有据此制造隐私阻断。

## 暂缓归档的精确文件

| Path | Git blob | Bytes | Reason |
| --- | --- | --- | --- |
| research/00_model_audit/input_snapshot/data/industry/us_cities.csv | b1165513d87cd4ff809fd75a4bdf64f74602795d | 4,081,899 | U下载脚本指向Simplemaps Basic v1.93；现有副本仅hash，尚无与来源ZIP的身份/许可对应证明。本轮固定URL返回403。网站产品页称Basic为CC BY 4.0，通用许可页却有不同限制，不能靠字段与URL推定现有字节适用哪一份条款。 |
| research/00_source_provenance/official/technology-data/inputs/data_sheets_for_renewable_fuels.xlsx | f41a96401278bf4a50acf2ef09dcb4834791b40e | 1,129,971 | 含xl/media/image1.png、image2.png；原数据身份已知，但DEA通用复制条款排除图片。当前无这些嵌入媒体的单独授权证据。 |
| research/00_source_provenance/official/technology-data/inputs/technology_data_catalogue_for_energy_storage.xlsx | bf686797d7c72c296536b7709ef8c21ffe732a07 | 307,918 | 含xl/media/image1.png；同上，整工作簿上传的媒体许可尚未关闭。 |
| research/00_source_provenance/official/technology-data/inputs/technology_data_for_el_and_dh.xlsx | ce07675ba570a3b6376910505bd2bebcf163c0ba | 707,234 | 含xl/media/image1.png；同上。 |

上述文件在真实研究链最早的基线审计状态已经存在，后续Phase3A/B/C和health分支均继承。仅在HEAD删文件仍会上传历史blob，因此本轮没有删除、过滤历史、生成替代合并或偷偷跳过风险。

## 原始条款核查

- [固定technology-data README](https://github.com/PyPSA/technology-data/blob/ec22a1843632fd28ecb9a139ee5156faf23324a3/README.md)明确GPL针对脚本，输入数据可有不同条款。原文保存于evidence/license_review/TECHNOLOGY_DATA_README.txt。
- [DEA数据政策](https://ens.dk/om-os/datapolitik)：允许署名、不歪曲的材料复制；图片、图示、插图与logo另需许可。本轮只读ZIP目录确认嵌入媒体存在，不推定其单独许可。
- [Eurostat政策](https://ec.europa.eu/eurostat/help/copyright-notice)：统计数据一般允许署名复用，仍有第三方等例外。本轮没有把Eurostat工作簿单独认定为阻断项；整个归档已因上表暂缓，不宣称所有二进制都违法。
- [Simplemaps产品页](https://simplemaps.com/data/us-cities)和[通用条款](https://simplemaps.com/data/license)均于本轮只读核查；前者标Basic CC BY 4.0，后者描述不同使用/发布条件。源码固定URL是`https://simplemaps.com/static/data/us-cities/1.93/basic/simplemaps_uscities_basicv1.93.zip`。取证收到HTTP403，未进行数据替换。精确响应在evidence/license_review/CITY_SOURCE_CHECK.json。

## 安全部分与未完成部分

已推12个ref的新增历史只含源码、配置、测试、文档和有意提交的合成/离线验证记录；它们没有继承上表4个blob。这些验证记录是工程审阅证据，不是新增运行或本地缓存倾倒。已有main中的上游输入未变。

归档暂缓符合用户本轮第10节要求。若要完成备份，最小处理是确认这4份既有文件适用于私有研究远端的保存授权，或另行批准一种不改写原史的分离存档方案。不能仅删除最新树中的文件后再推其祖先。代码LICENSE不能代替数据许可，也不因GitHub仓库私有就自动忽略用户明确的上传规则。
