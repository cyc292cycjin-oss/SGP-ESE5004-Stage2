# Domestic / international fuel separation

每国每年四个独立 account：DomesticShippingFuel、InternationalShippingBunker、DomesticAviationFuel、InternationalAviationBunker。11 国×4 基年记录；未来三个 horizon 各留同样四种身份。国内属于 Transport/DIRECT_FUEL，国际属于 Bunker/BUNKER_FUEL，不并进普通 domestic final demand 或 A*。

均是 FIXED FUEL OBLIGATION 候选。FT/synthetic-fuel 是后续供给选项，不能把燃料需求删掉，也不能本轮预填合成过程电力。carrier=oil 是现有液体燃料模型类别，原 commodity/transaction 差别保留在来源 review capsule，不宣称统一喷气/船用燃油性质已接受。

重用 Phase3B2 COUNTRY_ACCOUNT_OBSERVATIONS：原始 selected/omitted records、文件 SHA 和行号均保留。缓存正值候选仍非 numeric acceptance。尤其 domestic navigation 的 `Consumption in domestic navigation` 与 upstream `Consumption by domestic navigation` 筛选不一致，及其他遗漏 commodity/transaction，均逐行 BLOCKER；本轮不静默将遗漏值加回。cache zero 无精确选中源记录时 MISSING，不给零义务。

Shipping allocation engineering 17 tests PASS 只保证给定合法需求/空间权重的分配，不批准 annual demand 值、港口年份或 future growth。当前没有完整真实 bunker 四层空间/时间证据。
