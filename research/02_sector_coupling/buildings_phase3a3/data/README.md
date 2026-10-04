# Buildings data identity

`raw/buildings/`：本轮6份公开候选原文件及8项检索清单（含2项失败）。不可覆盖。原文件不进Git二进制；URL、版本、hash、retrieval script与manifest进Git，交付包附本地已取得的缓存供核验。公开下载与科学接受、开放许可分别记录。

`processed/buildings/`：只记录可复核的原表位置/读取方法，不生成模型新需求。`derived/buildings/`：测试矩阵、候选元数据、50项登记的构建JSON，可由 `build_evidence.py` 重建。没有缺失国家补值或final→useful转换。

上轮42项身份按原记录保留；为使新CSV可定位，仅将旧的本地相对文件名前加 `../buildings_heat_alignment/`。旧原始值、hash、接受状态不改。候选文件不复制到上游workflow的`data/`或正式网络路径。

所有候选 `UNVERIFIED`、所有人类科学接受 `PENDING`。`RETRIEVED` 只表示文件取得成功。无文件则filename/hash留空，不用0或伪哈希补齐。
