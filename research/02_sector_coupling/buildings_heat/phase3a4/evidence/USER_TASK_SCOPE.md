# SGP ESE5004 Stage2
# Phase 3A-4 — Buildings Demand Accounting Closure & Approved Fix Integration

## 0. 本轮定位

继续项目：

ASEAN renewable energy transition under sector coupling

本轮目标不是继续扩大 Buildings 数据搜索，也不是进入 Transport。

本轮只做两件核心工作：

1. 将已经通过独立 failing→passing 验证的 E1 / E2 / E4，
   安全整合到独立 Research Validation Branch，
   并进行组合回归、需求守恒和源码身份检查；

2. 正式解决 Buildings 当前最大 blocker：
   E3 — base electricity / Residential & Services direct electricity /
        historical electric heating / explicit heat service /
        endogenous conversion electricity
   之间的完整 demand-accounting closure。

完成后仍然不要启动正式 Integrated / Disconnected 大模型。

--------------------------------------------------
1. 固定代码版本
--------------------------------------------------

Paper Reference SHA：

5bacad702ccfed17ad19ab510fa710651e966f2c

Current Upstream SC Baseline SHA：

a3616a68ee44592af6527ca9024a90f1956646ae

必须继续保持：

Paper Reference
!=
Upstream SC Baseline
!=
Research Model

不要修改 Paper Reference。

不要追随 GitHub main 漂移。

本轮 Research Validation Branch 必须从固定的：

a3616a68ee44592af6527ca9024a90f1956646ae

或项目中已经明确建立的等价 Research validation 基线开始。

--------------------------------------------------
2. 当前 Human Scientific Acceptance 状态
--------------------------------------------------

以下内容已进入“允许工程整合测试”状态：

E1 — Residential / Services heat conservation

source commit：
92e9118be20f0b3802f385adac2f56650d57299d

validation commit：
59dbd34880bcdb367fed54cdee39a2ace40182fd


E2 — zero-HDD / NaN / silent heat-demand loss

source commit：
31037d60d69fa762c9ed8ec9ce8289d95bd6a181

validation commit：
1f9405720a873918614df5aad361580cff7cedde


E4 — service electricity / services electricity naming

source commit：
5d761eceeeb0d0519208d760224a41ff50ec1e30

validation commit：
78b23e7804ca05f2fd1f5ee5ec90f3fa6f8bbf7c


注意：

“允许整合测试”
!=
“Full-SC 已科学验收”

E3 仍是 blocker。

不得因为 E1/E2/E4 通过，就宣布 Buildings DATA ACCEPTED。

--------------------------------------------------
3. 已冻结的 Buildings 科学边界
--------------------------------------------------

### 3.1 Residential / Services

模型层继续分别表示：

Residential
Services

结果层可以汇总：

Buildings = Residential + Services


### 3.2 Heat

采用：

Fixed useful thermal service
+
Endogenous supply technology competition

即：

热服务需求外生；

Heat pump
Boiler
Resistive heating
CHP
TES
等供给路线可在后续模型中内生竞争。


### 3.3 Cooling

第一版：

Cooling ∈ Direct electricity demand

不新增：

cooling service bus
chiller
district cooling
cold storage
reversible cooling technology

本轮只确保 cooling 不被重复计算。


### 3.4 Cooking

Cooking 不建立独立模型模块。

状态：

NON-EXPLICIT
+
ACCOUNTING REQUIRED

必须防止：

cooking fuel
被误算成
space heating / water heating

也不能因不显式建模而把对应能源量无故删除。


### 3.5 District heating

暂不接受统一 ASEAN 默认值。

保留能力，但无区域证据前不得用统一：

potential = 0.3
progress = 1
loss = 0.15

作为正式科学 baseline。


### 3.6 Existing heating stock

欧洲 heating-stock 数据和 ASEAN 缺省 0：

不得解释为真实 ASEAN brownfield。

本轮不补造 heating stock。


### 3.7 UNSD 2019

UNSD Residential / Services：

可以作为：

base-year final-energy calibration source

但：

final energy
!=
useful heat service

不能直接把 fuel consumption 当 useful heat demand。


### 3.8 BDEW

BDEW：

仅用于原模型复现 / reference comparison。

不得作为 Research Full-SC 的自动 scientific default。

--------------------------------------------------
4. Track A — 整合 E1 / E2 / E4
--------------------------------------------------

建立独立分支，例如：

research/buildings-accounting-validation

不要直接污染 upstream-sc-baseline。

按清晰顺序整合 E1 / E2 / E4。

推荐：

1. E1
2. E2
3. E4

每一步都必须：

- 记录 cherry-pick / patch 身份；
- 确认没有冲突或静默修改；
- 重跑各自原 validation；
- 运行组合回归；
- git diff --check；
- working tree clean；
- 保存最终整合 commit SHA。

如果出现冲突：

STOP
→ document
→ do not invent resolution

除非冲突只是可以明确证明的机械上下文差异。

--------------------------------------------------
5. Track A 的组合验证
--------------------------------------------------

整合 E1/E2/E4 后必须重新测试：

### R/S annual service conservation

对每国：

Residential annual heat
Services annual heat

分别检查：

before
expected
after
absolute error
relative error


### Carrier identity

检查：

service electricity
services electricity

是否统一且所有调用位置一致。


### zero-HDD behavior

对于：

annual heat > 0
+
invalid / zero temporal shape

必须：

fail explicitly

而不是：

NaN → fillna(0)


### No demand mutation

E1/E2/E4 不得改变：

- 原始年度服务量；
- 需求数据本身；
- technology cost；
- carbon assumptions；
- spatial scope。

--------------------------------------------------
6. Track B — E3 Demand Accounting Closure
--------------------------------------------------

这是本轮最高优先级。

不要先写 patch。

必须先写清楚会计恒等式。

--------------------------------------------------
6.1 定义需求账户
--------------------------------------------------

至少区分：

A. Original base electricity demand

B. Residential direct non-thermal electricity

C. Services direct non-thermal electricity

D. Historical electric space heating

E. Historical electric water heating

F. Cooling electricity
   （第一版继续留在 direct electricity）

G. Other direct building electricity

H. Explicit useful space-heat service

I. Explicit useful water-heat service

J. Endogenous heat-pump electricity

K. Endogenous resistive-heating electricity

L. Endogenous CHP / conversion flows

M. Cooking energy
   （非显式技术模块，但保持能源会计）

--------------------------------------------------
6.2 必须建立的原则
--------------------------------------------------

Accepted direct electricity demand 应满足：

Accepted direct electricity
=
Residual base electricity
+
Explicit direct electricity components

其中：

Heat-pump electricity
Resistive-heating electricity
Electrolyser electricity
Other conversion electricity

不得提前包含在 exogenous load 中。

它们必须由优化内生生成。

--------------------------------------------------
6.3 Historical electric heat 的处理
--------------------------------------------------

如果原 base electricity 已包含历史：

electric space heating
electric water heating

而我们把：

space heat service
water heat service

显式化，

则对应的历史电热必须：

从 base electricity 中扣除恰好一次。

但禁止：

- 扣除全部 Residential electricity；
- 扣除全部 Services electricity；
- 猜测 heating share；
- 直接使用 0.6 等 Europe/default split；
- 将 cooling 一并扣除。

只允许扣除：

有来源证据、可识别的 historical electric heating component。

--------------------------------------------------
6.4 Cooling
--------------------------------------------------

Cooling 暂时继续保留于：

Residual / direct electricity

不得因为建立 heat service 就从 base electricity 中删除 cooling。

除非已有源数据明确分离。

--------------------------------------------------
6.5 Cooking
--------------------------------------------------

Cooking 不显式建模。

但其：

electricity / gas / LPG / biomass 等 final energy

必须有明确去向：

- 保留在 direct/fuel demand；
或
- 明确从 thermal service 映射中排除。

不能把 cooking final energy 自动转成：

space heat
或
water heat。

--------------------------------------------------
7. E3 必须先产出会计设计，再决定是否实施 patch
--------------------------------------------------

第一步先产出：

BUILDINGS_E3_ACCOUNTING_SPEC.md

内容包括：

- 所有 demand accounts；
- 数据来源；
- transformation；
- subtract/add 顺序；
- yearly identity；
- country identity；
- snapshot identity；
- cooling treatment；
- cooking treatment；
- endogenous conversion treatment。

只有当：

会计恒等式
+
数据来源
+
转换顺序

全部能够明确时，

才允许 Codex 建 E3 patch。

如果缺关键输入：

STOP

不要写“合理默认值”。

--------------------------------------------------
8. Useful Heat Conversion Method
--------------------------------------------------

本轮允许设计方法，但不得自动生成最终科研输入。

目标：

把：

final energy by fuel/end-use

转换为：

useful space heat
useful water heat

概念上：

UsefulHeat
=
FinalEnergy
×
EndUseShare
×
DeviceEfficiency

但不要自动填：

EndUseShare
DeviceEfficiency

--------------------------------------------------
8.1 必须记录的数据字段
--------------------------------------------------

至少：

Country
Sector (Residential / Services)
Fuel
FinalEnergy
FinalEnergyUnit
EndUse
EndUseShare
DeviceType
Efficiency_or_COP
UsefulService
Source
SourceYear
Status

--------------------------------------------------
8.2 End-use mapping
--------------------------------------------------

优先使用：

country-specific
或
climate/region-specific

证据。

不得再寻找或强制使用统一：

ASEAN 60/40

这样的比例。

--------------------------------------------------
8.3 Device efficiencies
--------------------------------------------------

如果效率来自：

- DEA
- national survey
- literature
- PyPSA default
- engineering assumption

必须分别标明。

不得因为已有 config efficiency 就自动视为 ASEAN calibrated。

--------------------------------------------------
9. Temporal Service Method
--------------------------------------------------

本轮只设计方案，不生成最终 11 国小时热曲线。

### Water heating

应与 HDD 解耦。

可考虑：

usage-based daily profile

但必须有来源。

### Space heating

仅在存在实际采暖需求的国家/区域构造。

不能：

annual space heat > 0
但 HDD=0
然后静默清零。

### BDEW

仅作为 reference benchmark。

--------------------------------------------------
10. 不再进行无限数据搜索
--------------------------------------------------

本轮不再以：

“找到一个统一 11 国完美热需求数据库”

作为目标。

转而建立：

透明、可追踪的数据构造方法。

原则：

Official final-energy balance
→ End-use mapping
→ Efficiency conversion
→ Useful service
→ Spatial allocation
→ Temporal allocation

每一步都必须有来源和转换记录。

--------------------------------------------------
11. Data acceptance 状态
--------------------------------------------------

沿用状态：

SOURCE_RECOVERED
ACCEPT_STRUCTURE
ASEAN_VALIDATION_PENDING
ENGINEERING_FIX_REQUIRED
SCIENTIFIC_DECISION_REQUIRED
DATA_UPDATE_CANDIDATE
REJECT_DEFAULT
HUMAN_ACCEPTED

Codex 不得自行标：

HUMAN_ACCEPTED

--------------------------------------------------
12. Git / Data 管理
--------------------------------------------------

E1/E2/E4整合后：

必须保存：

- branch
- source commits
- merge/cherry-pick commits
- validation commits
- combined commit
- diff
- test receipt

数据方法文件放：

research/.../buildings_heat/
data_registry/

不要：

- 修改 Paper Reference；
- 修改 upstream baseline；
- force-push；
- 删除历史审计文件；
- 生成 final2/backup/temp-final 等垃圾目录。

--------------------------------------------------
13. 本轮禁止事项
--------------------------------------------------

禁止：

- Transport
- Agriculture
- Shipping
- Aviation
- 正式 Integrated / Disconnected 求解
- E3 无会计设计先改代码
- cooling module
- cooking module
- district heating scientific adoption
- heating-stock伪造
- 新 carbon policy
- cross-border H2
- Myerson / Shapley
- 新研究技术
- 未验证参数自动写入正式模型

--------------------------------------------------
14. 本轮交付
--------------------------------------------------

请产出：

1. BUILDINGS_FIX_INTEGRATION_REPORT.md

2. BUILDINGS_FIX_COMBINED_TEST_MATRIX.csv

3. BUILDINGS_E3_ACCOUNTING_SPEC.md

4. BUILDINGS_E3_DATA_REQUIREMENTS.csv

5. BUILDINGS_USEFUL_HEAT_METHOD.md

6. BUILDINGS_USEFUL_HEAT_INPUT_SCHEMA.csv

7. BUILDINGS_ELECTRICITY_CLOSURE_TEST.md

8. BUILDINGS_DATA_DECISION_UPDATE.md

9. BUILDINGS_PHASE3A4_READINESS.md

如果 E3 证据已经足够并实施：

10. BUILDINGS_FIX_E3_REPORT.md

否则不要为了完成清单强行生成 E3 patch。

--------------------------------------------------
15. 最终必须回答
--------------------------------------------------

A. E1/E2/E4 是否成功整合到 Research Validation Branch？

B. 组合测试是否全部通过？

C. 三个 fix 是否仍然没有改变科学需求量？

D. E3 的完整 demand-accounting identity 是否已经明确？

E. 是否能够准确识别 historical electric heating？

F. Cooling 是否被保留且未重复？

G. Cooking 是否保持非显式但能源会计不丢失？

H. E3 是否已经具备实施 patch 的数据条件？

I. Useful heat 的 final-energy → service 转换方法是否已经可执行？

J. 哪些字段仍缺 Human Acceptance？

K. Buildings + Heat 是否已经达到：
READY FOR FULL-SC ASSEMBLY？

如果没有：

最少还差哪 3–5 项？

完成后停止。

不要自动进入 Transport。