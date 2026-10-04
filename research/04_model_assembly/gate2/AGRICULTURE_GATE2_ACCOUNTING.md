# Agriculture Gate2

农业电力只在 A* 内，原始 UNSD 部门记录是 embedded 身份证据，不新建农业电 Load。没有农业技术竞争模型。

按 carrier 保留现有 2019 缓存全部正燃料候选：

| Carrier | 已观察缓存子合计 MWh/year |
|---|---:|
| oil | 79,679,600.0 |
| biomass | 4,446,600.0 |
| coal | 215,200.0 |

这些是 **不完整且未接受的缓存子合计**，不是完整 ASEAN 需求。单元 missing / cache-zero-unverified 仍留空；BN/SG/TL 等缺失不当作零。测试从源 cache 各 carrier 独立求和，与 ledger positive observations 核对，油、生物质、煤均未丢量。

其中 biomass/coal 在 upstream add_agriculture 未被完整消费，当前先建立清晰能源 owner 和 logical destination，实际 carrier Load/destination 实现留 Gate3。VN 基年煤保留；没有沿用未来 fillna 使其消失的链路。未来 agriculture fuels 为 PENDING_FUTURE_GROWTH。
