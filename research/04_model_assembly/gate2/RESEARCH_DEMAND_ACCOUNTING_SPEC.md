# Gate2 demand accounting specification

账本是 **observation + ownership + acceptance contract**，不是已经接受的运行输入。`Posting=true` 表示候选物理义务 owner；只有 `NumericAccepted=true`、`Status=HUMAN_ACCEPTED`、合格来源和 destination 均成立，`materialise` 才生成年度义务。本轮没有任何 accepted numeric row。

## 数据结构

用户要求的全部 24 个字段保留；另有 RowID、OwnerAccount、Posting、Required、NumericAccepted、ZeroEvidence、LogicalDestination、ExistingEnergyLoad、EmissionsPresent、SourceLocator、Group 和四个 parent-transfer 字段。`SourceYear=2019` 在未来 pending 行只标记基年锚点，不是未来预测来源；此类行 Source/RawValue/ConvertedMWh 均为空。

- 唯一 RowID：country:year:sector:account:carrier。
- 同一 country/year/carrier/owner 不允许两条 posting 义务。
- embedded 行不 posting；included-in-A* 子账未明确转移不可 posting。
- endogenous conversion input 不能同时 fixed、带预填 MWh、或属于 direct A*。
- BUNKER_FUEL 只能属于 Bunker sector；国内船/航空属于 Transport。
- 明确的 reported zero / not applicable 才能 ConvertedMWh=0。空值和未经原始记录证明的 cache zero 保留 unknown。
- 所有未来 direct/fuel 数值为空；未来表结构是输入接口，不是情景。

## 所有权与转移

`parent_transfer` 和 `apply_astar_transfers`：ParentBefore=ParentAfter+TransferredChild，并与独立读取的原父账核对。children 不得重复、超额；历史子账的 VALUE_AND_ASTAR_MEMBERSHIP_ACCEPTED 缺一不可。一次完整原子批次；修改成员须从源重建。不得事后补 residual 让等式成立。

未来 road 使用 accepted R、final-energy electric share s、明确 residual carrier vector：EV=R*s，F_k=R*(1-s)*w_k。这只证明共同 final-energy 基准守恒，不证明交通服务/效率不变。不给 passenger-km、tonne-km 或隐含 efficiency credit。调用者不能用车辆占比替代能量占比。

## 四层校验

1. 原始记录/明确命名缓存 → MWh：独立 Decimal 控制值核对账本。
2. sector ledger → 唯一 country/year/carrier ownership；保留来源偏差与缺失。
3. country → nodes：国家身份完整，有限非负权重加总 1，否则失败。
4. nodes → snapshots：P_nt=E*a_n*q_t/Σ(w_t*q_t)，物理时间权重严格正、key 完整，并独立校验总小时数；年度 MWh 加回。

合成数据证明四层机制；真实输入目前只到来源/账本部分闭合，空间与时序未接受。CSV matrix 明确 PENDING；不能把 217 个 source-to-ledger PASS 说成完整 source→node→time PASS。缓存转换通过仅证明缓存数值未丢失，不证明原始热值、筛选或统计完整性。

## Research entry point

`build_research_demand.py` 从带 SHA256 的来源切片重建六表及三张审计表；`check_research_demand.py` 消费 baseline 控制字段，逐表核对派生内容。`materialise` 在任一 required 值/接受/destination 缺失时整国整年失败，不筛掉缺失部门后宣称成功。

没有执行旧 `add_heat`、`add_land_transport`、`add_rail` 或工业新 Load；因此 Research 层不会继承虚构 heat/rail 重复义务。上游 workflow 尚未改接：只使用这里的静态入口，不能把旧 Snakefile 当作本轮可运行 Full-SC baseline。
