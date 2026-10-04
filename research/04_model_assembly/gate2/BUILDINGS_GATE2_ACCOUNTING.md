# Buildings Gate2

22 个 country×R/S direct-electricity 身份分别保存，均留在 A*。选用原始 UNSD electricity 部门记录，不复用可能带 coal.shift_to_elec 的电力缓存作为父账。

44 个 space/water heat contract 保持 EMBEDDED，ConvertedMWh 为空且不创建 service Load；缺服务数据不会变成零热需求。22 个 cooling 记录只保留直接电身份，不扣 A*。22 个 cooking 记录 non-explicit，燃料在 R/S 原 carrier 账户中保持；不并入 space/water heat。

R/S oil/gas/biomass 正缓存值作为 FROZEN_UPSTREAM 候选保留；零筛选不证明 observed zero。原 cache 没有独立 R/S coal 列，显式登记 missing，而非把煤自动改为电。没有统一 district-heat share、虚构 heating stock 或热服务效率。2030/40/50 的 R/S fuel/growth 全部 pending。

验证：44 thermal embedded、无 embedded posting、无未转移 A* 子账 posting；真实数值仍未接受。热结构未被科学升级为 explicit，烹饪燃料也未被重新分配用途。
