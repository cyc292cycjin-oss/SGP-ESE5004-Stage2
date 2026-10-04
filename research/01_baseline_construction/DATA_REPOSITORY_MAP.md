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
