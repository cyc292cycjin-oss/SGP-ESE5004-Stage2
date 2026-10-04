# SGP ESE5004 Stage2
# Phase 3A-2 — Buildings + Heat Baseline Alignment & ASEAN Data Validation

## 0. 本轮目标

继续项目：
ASEAN renewable energy transition under sector coupling

本轮不要扩展研究问题，也不要启动正式 Integrated / Disconnected 大模型。

目标是：

1. 以原 PyPSA-ASEAN / PyPSA-Earth Buildings + Heat 实现为基准；
2. 明确原模型到底如何处理 Buildings / Residential / Services / Heat；
3. 只对已经证明存在问题的工程实现、欧洲默认参数和ASEAN不适用数据提出修正；
4. 为后续 Full-SC Baseline 准备可接受的 Buildings + Heat 数据边界；
5. 不自行重新设计新的建筑能源系统模型。

---

## 1. 固定代码版本

Paper Reference：

5bacad702ccfed17ad19ab510fa710651e966f2c

Current Upstream SC Baseline：

a3616a68ee44592af6527ca9024a90f1956646ae

必须继续区分：

Paper Reference
!=
Upstream SC Baseline
!=
Research Model

不要追随 GitHub main 的后续漂移。

所有结论优先基于固定 SHA。

---

## 2. 已经冻结的科学原则

### Buildings 模型边界

模型层：

Residential
Services

继续分开。

结果层可以聚合为：

Buildings = Residential + Services

### Buildings thermal service

目标结构继续采用：

Fixed heat service demand
+
Endogenous supply technology competition

即：

Heat service = exogenous

供给技术可根据原模型实际能力竞争，例如：

Heat pump
Boiler
Resistive heater
CHP
Solar thermal
Thermal storage

但不要因为“框架支持”就自动启用没有数据依据的技术。

---

## 3. Cooking 的处理原则

本研究不把 cooking 作为独立研究模块。

原因：
当前研究主问题是 ASEAN renewable-energy transition、sector coupling 和 cross-border electricity interconnection value，不能因细小终端用途造成模型过度复杂。

Codex 只需：

1. 查清原模型是否显式处理 cooking；
2. 如果显式处理：
   - 记录其数据来源；
   - 记录它属于 residential/services 哪个 demand account；
   - 记录它使用 electricity / gas / LPG / biomass 等哪个 carrier；
3. 检查它是否被错误归入 space heating / water heating；
4. 检查是否和 base electricity / fuel demand 重复。

如果原模型没有独立 cooking 模块：

不要新增。

如果占比很小且不会显著影响 interconnection / electrification：
只保留 accounting note。

只有发现 cooking 在原模型里占据显著能源量或会明显影响 sector coupling，才返回用户讨论，不自行升级研究范围。

---

## 4. Cooling 的处理原则

第一版 Full-SC 暂时保持：

Cooling ⊂ Direct electricity demand

不新增独立：

- cooling service bus
- chiller
- district cooling
- cold storage
- reversible heat-pump cooling

前提是验证：

1. cooling 已包含在 base electricity；
2. Residential / Services 模块没有再次显式增加同一 cooling demand；
3. 没有 double counting。

输出中明确说明：

当前 Full-SC 结果包含 cooling electricity demand，
但不包含 cooling technology flexibility。

Cooling 的显式建模留作后续扩展，不在本轮实现。

---

## 5. Buildings 处理必须优先对照原模型

本轮核心原则：

Do not redesign before reproducing.

请先建立：

Original implementation
→ Data source
→ Transformation
→ Final load / component
→ Problem
→ Need modification?

不要先假设我们应该使用新的 building model。

每一项都先回答：

“原作者到底是怎么做的？”

然后再判断：

A. 可以直接继承；
B. 结构可继承、数据需ASEAN化；
C. 明确工程错误；
D. 欧洲默认，不适合直接用于ASEAN；
E. 暂无证据，需要保持PENDING。

---

## 6. 本轮需要重点关闭的 Buildings + Heat 数据问题

### 6.1 Annual Residential / Services demand

追踪：

- UNSD 2019
- residential
- services
- electricity
- heat
- gas
- oil
- coal
- biomass
- other carriers

回答：

1. annual total 来自哪里；
2. base year；
3. 单位；
4. country coverage；
5. 哪些是 final energy；
6. 哪些是 useful heat service；
7. 哪些需要 efficiency conversion；
8. 哪些进入 electricity base load；
9. 哪些进入 heat service；
10. 哪些只是 accounting residual。

不能把 fuel consumption 直接等同于 useful heat demand。

---

### 6.2 Space heating / water heating

继续追踪：

space_heat_share
water_heat_share
或等价参数。

原则：

不要自动接受统一 0.6 / 0.4 等默认值。

请优先判断：

- 原模型为什么这样设；
- 是否为欧洲默认；
- ASEAN fork是否区域化；
- 是否国家统一；
- 热带国家是否会产生明显不合理结果。

如果没有 ASEAN-specific evidence：

标记：

ASEAN_VALIDATION_PENDING

不要改值。

---

### 6.3 Heat temporal profile

继续确认：

BDEW profile
ERA5 / temperature
HDD
weekday / weekend

的组合逻辑。

重点验证：

1. BDEW 只承担 hourly shape 还是 annual quantity；
2. zero HDD 地区是否仍会导致正annual demand被丢失；
3. water heating 是否错误依赖 HDD；
4. Residential / Services 是否共用同一 shape；
5. Tropical ASEAN 是否存在明显不合理处理。

禁止：
用 fillna(0) 静默丢失正需求。

如果 annual heat > 0 但无法映射 temporal profile：

程序必须明确 fail / warn，
不能把需求变成 0。

---

### 6.4 Existing heating assets

先对照原模型。

如果当前 existing heating capacity 来自欧洲数据且 ASEAN 无对应行：

不能将“默认0”解释为“ASEAN没有既有供热设备”。

本轮不要求强行建立 ASEAN brownfield heating stock。

请输出：

- 原模型数据源；
- 适用区域；
- 是否实际进入 baseyear；
- 是否影响 capacity inheritance；
- 是否需要作为 Full-SC baseline blocker。

如果没有可信 ASEAN stock：

建议保持为“未显式表示existing heating stock”，
而不是伪造 brownfield。

是否最终采用 building greenfield competition，
返回用户决定。

---

### 6.5 District heating

继续追踪：

- current share
- potential
- progress
- losses
- urban share
- density assumptions

原则：

不要接受统一的：

0.3
1
0.15

等数值作为 ASEAN 科学基准，除非找到明确依据。

请优先判断：

- 原模型结构是否必须依赖DH；
- 哪些国家/地区现实上可能适用；
- 若关闭DH，是否影响其他分布式热技术运行；
- DH是否可以作为后续地区特异模块，而不是全ASEAN统一默认。

本轮只审计，不改。

---

## 7. Fuel shifting 必须重新分类

请建立 Residential / Services fuel accounting table。

对：

coal
gas
oil
biomass
electricity
heat

逐项标明：

A. 固定final demand
B. 外生shift to electricity
C. 外生shift to heat
D. 可在优化中内生替代
E. 被忽略
F. 当前不清楚

目标是明确区分：

External electrification assumption

和：

Endogenous sector-coupling substitution

如果某项在 preprocessing 已经被强制：

fuel → electricity

那么后续 heat pump / boiler 竞争可能不再是真正内生。

需要明确记录。

---

## 8. Demand accounting rule

继续执行已经冻结的规则：

Accepted direct electricity demand
=
Residual base electricity
+
Explicit direct sector electricity

而：

Heat-pump electricity
Electrolyser electricity
Other conversion electricity

必须由优化模型内生形成。

不能预先塞入 base load。

请建立国家级 + sector级 accounting check。

至少输出：

country
base electricity
residential direct electricity
services direct electricity
explicit heat-related electricity
residual electricity
endogenous conversion electricity
annual total
double-count flag

正式 Full-SC 前必须守恒。

---

## 9. 数据来源搜索规则

本轮可以主动搜索公开权威来源，但优先级必须是：

1. ASEAN / AEO
2. 国家能源统计/能源平衡
3. UNSD / IEA / World Bank / UN 等国际统计
4. 官方 building energy / end-use studies
5. peer-reviewed literature
6. 全球统一数据库

不要优先用欧洲参数填ASEAN。

如果只能找到国家子集：

不要自动拼成11国统一表。

先报告覆盖情况。

如果没有统一来源：

返回用户共同决定是否：

- 保留原模型；
- 使用全球统一数据；
- 按国家异质数据；
- 缩小某项显式建模范围。

---

## 10. 数据版本原则

不要因为“更新”就自动采用最新值。

需要区分：

Paper reproduction data

和：

Research model data

Paper Reference：
保持作者原始数据。

Research Model：
如果存在更新且统一、可比、定义一致的数据，
可以作为候选。

任何更新必须记录：

old source
new source
reason
definition compatibility
unit compatibility
country coverage
expected model impact

并等待 human acceptance。

---

## 11. 本轮允许做的工程修复

仅对已经有明确证据的问题，可以提出fix patch，但不要未经确认合并到 research main。

包括候选：

E1
Residential覆盖Services/Central heat的问题

E2
zero-HDD → NaN → fillna(0) 静默丢量

E3
existing electric heating / residual electricity扣减不闭合

E4
service electricity / services electricity命名不一致

每一个fix必须：

Evidence
→ failing test
→ minimal patch
→ passing test
→ demand conservation

使用独立branch / commit。

不要把多个fix合成一个大commit。

---

## 12. Git / data management

用户明确要求：

所有正式研究数据必须在项目GitHub工作目录中有明确身份和用途。

建议：

data/
  raw/
    buildings/
  processed/
    buildings/
  derived/
    buildings/
  README.md

data_registry/
  DATA_SOURCES.csv
  DATA_HASHES.csv
  DATA_DECISIONS.md

每项至少记录：

source_id
name
official_url
version
year
filename
sha256
unit
countries
sector
purpose
transformation_script
status

大文件如ERA5/GIS：

二进制可gitignore，
但必须保存：

URL
version
hash
retrieval script
manifest

---

## 13. 本轮禁止事项

禁止：

- 启动正式 Integrated / Disconnected 求解；
- 进入 Transport/Agriculture；
- 新增独立 cooling module；
- 单独建立 cooking module；
- 自动采用新 building demand；
- 自动修改 space_heat_share；
- 自动启用/关闭 district heating；
- 自动修改 existing heating stock；
- 用欧洲默认替代 ASEAN；
- 修改 carbon policy；
- 加跨境 H2；
- 做 Myerson/Shapley；
- 添加研究新技术；
- 用未验证数据跑科学结果。

---

## 14. 本轮交付

请产出：

1. BUILDINGS_HEAT_BASELINE_MAP.md
   - 原模型完整Buildings/Heat路径
   - Paper vs Upstream SC 对照

2. BUILDINGS_DEMAND_ACCOUNTING.csv
   - R/S annual demand
   - direct electricity
   - thermal service
   - fuel accounting
   - double-count flags

3. BUILDINGS_SOURCE_FAMILY_REVIEW.md
   - 每个数据来源族的适用性

4. BUILDINGS_ASEAN_DATA_CANDIDATES.md
   - 只列可验证、权威候选源
   - 不自动采用

5. HEAT_PROFILE_VALIDATION.md
   - BDEW / HDD / water heating / climate适用性

6. BUILDINGS_ENGINEERING_FIX_PLAN.md
   - E1–E4
   - tests
   - patch boundaries

7. BUILDINGS_DATA_REGISTRY.csv
   - GitHub数据身份登记

8. BUILDINGS_BASELINE_READINESS.md

最终状态逐项给：

ACCEPT_STRUCTURE
ACCEPT_SOURCE_FAMILY
DATA_UPDATE_CANDIDATE
ASEAN_VALIDATION_PENDING
ENGINEERING_FIX_REQUIRED
SCIENTIFIC_DECISION_REQUIRED
NOT_IN_SCOPE

---

## 15. 最终必须回答

A. 原模型Buildings/Heat到底属于什么建模模式？

B. Residential / Services是否真的分开保持到最终network？

C. 哪些heat demand来自真实数据，哪些来自默认分摊？

D. 是否可以构建不重复的：

base electricity
+
building thermal service
+
endogenous conversion electricity

会计体系？

E. Cooling保持在direct electricity是否可行？

F. Cooking不独立建模是否不会破坏主研究结论？

G. District heating是否必须进入第一版Full-SC？

H. Existing heating stock是否足够可信做brownfield？

I. 哪些工程问题必须修复？

J. 哪些数据需要新的ASEAN-specific来源？

K. 当前Buildings + Heat是否可以进入：
DATA ACCEPTED
状态？

若不能，最少还差哪几项？

---

完成后停止。

不要自动进入Transport。

把结果返回用户 + ChatGPT，
由双方共同决定是否冻结Buildings + Heat。