# Buildings demand accounting after candidate fixes

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Mode: validate; Version: Phase3A3-1; Date: 2026-10-01 Asia/Shanghai
- Verification Status: ANALYZED accounting interpretation; synthetic engineering checks VERIFIED; scientific acceptance PENDING

## “After fix” 的精确含义

E1、E2、E4 存在于各自独立分支，并在隔离组合源码中通过 1,062 项检查；R 仍为 `a3616a68ee44592af6527ca9024a90f1956646ae`。没有正式年度网络求解或被新数据改写的“修复后科学结果”。

| 账户 | 候选修复后可核实的变化 | 仍未关闭 |
|---|---|---|
| R/S heat service | central Load 分离，R 不再覆盖 S；国家积分和 DH loss 分开核对 | 当前原始输入混合 fuel/service 口径，需冻结 final→useful 转换 |
| 正年度量+无效profile | 构网被明确阻止，原年度需求身份未被抹掉 | 不能由代码补造空间采暖或热水形状 |
| Services direct electricity | power-filter 正确保留复数 carrier；无筛选分支不改数量 | E3 final electricity calibration 仍缺完整部门桥接 |
| heat-pump electricity | 由已有 Link 供热时形成，不作为新固定电负荷加入 | 原有 meter 内历史电热是否正确扣回尚未闭合 |
| fixed fuels | E1 保留原值；不改变 cooking 或其他用途分配 | 不能把 fuel final-energy 直接称 useful heat |

## 应保持的会计恒等式

接受后的 direct electricity 总量 = residual base electricity + explicit direct sector electricity。Residual 必须从相同国家/年份/电力边界的基准中扣除已单列的 **direct** 电量，不能同时保留并再次加入同一项。

若把原 meter 内的历史 **electric heating** 改为单列 useful heat，则需先用被接受的端用途和效率/COP证据识别并扣出其历史用电，再由供热技术形成新的内生用电。不能把所有“historical electric end uses”都扣掉；cooling 本轮仍在 direct electricity 中。Electrolyser 和其他转换用电同样不得预先再塞入 base Load。

2019 各国 `national − R − S` 的残差是构造的算术恒等式，不是独立证明实际网络无重复。`prepare_heat_data` 里 electric-heat subtraction 仍被注释，且最终调整仍存在 E3。因此本轮不能给出真实 11 国全网络的无重复量化验收。

## Cooling：结构已核实，数量验收仍未完成

读取冻结 U 的需求、年度处理、`add_heat/add_residential/add_services`、配电和 final adjustment：没有独立 cooling Load/Bus、chiller、district cooling、cold storage 或 cooling technology optimization；本轮也未新增这些组件。既有 heat pump 是供热 Link，并非可逆制冷模块。

原 Buildings 输入用的是未按 cooling 端用途拆分的电力总量。官方/调查证据支持制冷属于这些终端电量的用途之一，这是 **source-based interpretation**；模型代码本身没有可供逐国量化的 cooling 列。R/S 没有再次追加一个名为 cooling 的显式需求。

因此可使用边界说明：**Cooling embedded in direct electricity demand + no endogenous cooling technology flexibility**。其“无单独 cooling 模块重复追加”可确认；但“完整 Full-SC 11 国电力数量无 double count”**尚不能确认**，仍受 E3、meter/base 校准和历史电热桥接限制。这两种判断不能混为一谈。

## Cooking：保持非显式；不能默认为不重要

1. 冻结 Buildings 源码没有独立 cooking bus/load/technology。
2. 其消费可能嵌于 Residential/Services 的 electricity、oil/LPG、gas、biomass 等商品总量中；没有统一的 cooking carrier。
3. 原 DEFAULT 燃料热份额会把部分总燃料送往 space/water 账户，因此含 cooking 的燃料存在被误归热用途的风险；不能据此断言原输入已完成用途剥离。
4. 电烹饪应只保留在 direct electricity 一次；代码没有额外 cooking electricity Load，但与整体电力会计一样，国家数量闭合仍待证。
5. [马来西亚2016原表](https://www.st.gov.my/resources/national-energy-balance-2016) 的居民 cooking 为 655/2,875 ktoe，按表列舍入值计算约 22.8%；这是该来源范围内的 final-energy 份额，不是 useful heat，也不是 ASEAN2019份额。它已足以阻止“先认为烹饪很小”的接受路径。
6. 先前印尼 UNSD household oil 含 motor gasoline、与 ESDM 同年定义/数量不一致的问题未解决，不重新分类、不补数。

**建议维持用户冻结的非显式处理，同时把“烹饪燃料如何保留且不被误当 space/water”交回人工科学验收。** 不新增 cooking 模块，也不宣称对互联收益影响很小；后者需要后续经接受数据支持，工程回归不能回答。

## 固定边界与未实现内容

R/S 在模型层分开，结果层可聚合 Buildings。Fixed useful heat service + endogenous supply competition 是用户已冻结的目标；当前修复只使已有账户保持身份，未自动把整个旧混合模型重构成该目标。

DH 保留能力，未自动改开关或采用统一 0.3/1/0.15。未把欧洲 stock 或 ASEAN 默认零称作真实 brownfield；未强建存量。UNSD2019 可作为 final-energy calibration 来源，具体量/转换仍须确认。BDEW 不作为已接受 ASEAN 默认。

Paper P、Upstream U、Research R、Tutorial T 继续区分；本轮只针对冻结 U 的局部工程函数。Carbon、技术集合、其他部门、跨境网络边界均未修改。
