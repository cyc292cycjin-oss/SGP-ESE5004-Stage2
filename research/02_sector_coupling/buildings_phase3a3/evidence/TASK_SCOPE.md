# SGP ESE5004 Stage2
# Phase 3A-3 — Buildings + Heat Engineering Fixes + ASEAN Thermal-Service Data Recovery

## 0. 当前研究定位

项目主题：
ASEAN renewable energy transition under sector coupling

导师已经确认：
- 下一步重点学习 PyPSA-ASEAN 的输入数据、修改选项和 sector coupling；
- 多数既有 ASEAN 研究偏 power-system only；
- 我们要在 sector-coupling 背景下识别跨境电力互联的系统收益，并进一步识别国家层面的 benefits/losses；
- construction delay 当前忽略；
- carbon assumptions 保持 PyPSA-ASEAN 原有口径；
- 暂不进入 Myerson/Shapley/Core/Nucleolus。

当前禁止正式 Integrated / Disconnected 大模型求解。

---

## 1. 固定版本

Paper Reference SHA：
5bacad702ccfed17ad19ab510fa710651e966f2c

Current Upstream SC Baseline SHA：
a3616a68ee44592af6527ca9024a90f1956646ae

必须继续区分：

Paper Reference
!=
Upstream SC Baseline
!=
Research Model

不要追随 GitHub main 漂移。

---

## 2. 已冻结的 Buildings + Heat 科学原则

### 2.1 模型层结构

Residential 与 Services 分开建模。

结果层可以聚合：

Buildings = Residential + Services

### 2.2 Heat 建模原则

采用：

Fixed useful heat service demand
+
Endogenous supply technology competition

也就是说：

Heat service = exogenous

而供热技术如：

Heat pump
Boiler
Resistive heater
CHP
Thermal storage
Solar thermal

在相同技术、成本、碳约束下内生竞争。

### 2.3 Cooking

不建立独立 cooking 模块。

只需：
- 检查原模型是否显式处理；
- 检查是否被错误计入 heat/electricity；
- 检查是否造成 double counting。

如果原模型没有独立 cooking 模块，不新增。

只有当 cooking 在原模型中占比显著、足以改变 building energy balance 时，才返回用户讨论。

### 2.4 Cooling

第一版 Full-SC 中：

Cooling 保持在 direct electricity demand 中。

不新增：
- cooling service bus
- chiller
- district cooling
- cold storage
- reversible cooling

要求：
- 验证 cooling 是否已经包含在 base electricity；
- Residential / Services 是否再次增加同一 cooling demand；
- 禁止 double counting。

### 2.5 District heating

保留代码能力，但不接受统一 ASEAN 默认值。

例如：
- potential = 0.3
- progress = 1
- loss = 0.15

只有存在区域证据时才考虑启用。

### 2.6 Existing heating stock

欧洲 existing heating 数据或 ASEAN 默认 0 不能冒充真实 ASEAN brownfield。

当前不强行建立 ASEAN building heating stock。

### 2.7 UNSD 2019

UNSD 2019 Residential / Services energy balance：
可作为 base-year final-energy calibration source。

但：
final energy consumption
!=
useful heat service

不能直接把燃料消费等同于 heat demand。

### 2.8 BDEW

BDEW heat profile：
仅保留作原模型复现/对照。

不接受为 ASEAN scientific default，除非找到适用性证据。

### 2.9 需求会计

必须保持：

Accepted direct electricity demand
=
Residual base electricity
+
Explicit direct sector electricity

而：

Heat-pump electricity
Electrolyser electricity
Other conversion electricity

必须由优化内生形成。

禁止提前重复塞入 base load。

---

# 3. Track A — 实施工程修复

本轮只允许实施：

E1
E2
E4

E3 暂不实施。

每个 fix 必须独立 branch / commit，不能合并成一个大修改。

---

## E1 — Residential / Services heat conservation

已知问题：
add_residential 等逻辑可能覆盖 Residential / Services / central heat，导致服务量错配。

要求：

1. 建 failing test；
2. 确认修复前确实失败；
3. 最小修改；
4. 修复后分别验证每国：
   - Residential annual heat service
   - Services annual heat service
   守恒；
5. district heating loss 若存在，单独核算；
6. 不允许 Residential 剩余量覆盖 Services；
7. 不改变科学需求量。

建议 branch：

fix/buildings-rs-conservation

建议 commit：

fix: preserve residential and services heat demand separately

---

## E2 — zero-HDD / NaN / fillna(0) 静默丢量

已知问题：

annual heat > 0
但 temporal profile 因 zero-HDD 不可构造，
随后 NaN 被 fillna(0)，导致需求静默消失。

要求：

1. 建 failing test；
2. 明确证明：
   positive annual heat
   + invalid temporal profile
   -> current code loses demand；
3. 禁止静默 fillna(0)；
4. 工程上应：
   - fail / raise
   或
   - 强 diagnostic warning
   并保留 annual demand identity；
5. 科学上是否有 space heating 不由代码决定；
6. 不自动创造新 profile；
7. 修复后 annual heat demand 必须守恒。

建议 branch：

fix/heat-profile-zero-demand

建议 commit：

fix: prevent silent loss of positive heat demand

---

## E4 — service electricity / services electricity carrier inconsistency

要求：

1. 定位所有：
   service electricity
   services electricity
   相关 carrier 名称、过滤和 final adjustment；
2. 建 failing regression test；
3. 最小修复；
4. 修复后验证：
   - Services direct electricity 不丢失；
   - Residential/Services carrier accounting 正确；
   - Full-SC 中需求守恒；
5. 不改变需求数值本身。

建议 branch：

fix/services-electricity-carrier

建议 commit：

fix: align services electricity carrier naming

---

# 4. 工程修复验证规则

每个 fix 必须遵循：

Evidence
→ failing test
→ minimal patch
→ passing test
→ annual/national conservation

至少输出：

country
sector
before
after
expected
absolute_error
relative_error
test_status

禁止：

“跑通了所以认为正确”。

必须用守恒和回归测试证明。

---

# 5. Track B — ASEAN Buildings Thermal-Service Data Recovery

只寻找三类数据。

不要扩展到 Transport / Agriculture。

---

## B1 — Residential / Services annual end-use / thermal data

目标：

寻找能够帮助构建：

Residential useful thermal service
Services useful thermal service

的数据来源。

重点关注：

- annual final energy
- space heating
- water heating
- direct electricity
- fuel use
- end-use split

优先来源：

1. ASEAN / ASEAN Centre for Energy / AEO
2. 各国官方能源统计
3. 各国 building energy surveys
4. UNSD / IEA / UN
5. peer-reviewed studies
6. global harmonized databases

要求记录：

source
year
country coverage
sector definition
end-use definition
unit
final energy vs useful energy
public/private
license
source URL
file/hash

不要自动采用。

---

## B2 — Space heating / water heating split

重点寻找：

- ASEAN-specific
- country-specific
- climate-zone-specific

的 space heating / water heating 依据。

不要直接采用统一：

space_heat_share = 0.6

如果没有统一 11 国来源：

报告覆盖情况。

不要拼凑成伪统一数据集。

---

## B3 — ASEAN-compatible temporal basis

寻找：

### Water heating
- daily profile
- residential/services差异
- weekday/weekend patterns

### Space heating
- only for regions with real heating needs
- local climate / temperature threshold
- seasonal shape

目标不是一定找到完美 hourly demand，
而是判断：

是否存在比 BDEW 更适合 ASEAN 的统一方法或数据来源。

---

# 6. Cooking 处理

本轮只做 accounting trace。

回答：

1. 原模型是否独立表示 cooking？
2. cooking 用什么 carrier？
3. 是否归入 heat？
4. 是否归入 electricity？
5. 是否与 base demand 重复？
6. 占 Buildings energy balance 是否实质性？

如果影响很小：

建议保持 non-explicit treatment。

不要新增模块。

---

# 7. Cooling 处理

只验证：

1. cooling 是否已包含在 base electricity；
2. 是否有 Residential/Services explicit cooling；
3. 是否存在 double count；
4. 是否有独立 cooling technologies。

不新增 cooling 模块。

最终状态只需明确：

Cooling embedded in direct electricity demand
+
No endogenous cooling technology flexibility

是否成立。

---

# 8. 数据接受规则

所有候选数据状态保持：

UNVERIFIED
PENDING

不得自动标 CONFIRMED。

执行链：

Source
→ Raw value
→ Unit/year
→ Transformation
→ Current PyPSA value
→ Human scientific acceptance

如果出现：

- 多版本
- 单位不清
- country coverage不完整
- Europe-specific
- DEFAULT
- HHV/LHV不清
- final energy/useful energy不清

必须记录并停止自动采用。

---

# 9. 数据与 GitHub 管理

所有正式/候选研究数据都必须在项目目录中有明确身份。

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

大文件可不进Git二进制，但必须保存：

URL
version
hash
retrieval script
manifest

processed / derived 必须能由脚本重建。

---

# 10. 本轮禁止事项

禁止：

- 正式 Integrated / Disconnected 求解；
- 进入 Transport；
- 进入 Agriculture；
- 新增 cooling 模块；
- 新增 cooking 模块；
- 自动修改 space_heat_share；
- 自动采用新 Buildings demand；
- 自动开启/关闭 district heating；
- 自动构造 existing heating stock；
- 修改 carbon policy；
- 新增跨境 H2；
- 做 Myerson / Shapley；
- 添加研究新技术；
- 用未验证数据产生正式科学结果。

---

# 11. 本轮交付

请产出：

1. BUILDINGS_FIX_E1_REPORT.md

2. BUILDINGS_FIX_E2_REPORT.md

3. BUILDINGS_FIX_E4_REPORT.md

4. BUILDINGS_FIX_TEST_MATRIX.csv

5. ASEAN_BUILDINGS_THERMAL_DATA_SEARCH.md

6. ASEAN_BUILDINGS_DATA_CANDIDATES.csv

7. BUILDINGS_DEMAND_ACCOUNTING_AFTER_FIX.md

8. BUILDINGS_DATA_REGISTRY_UPDATED.csv

9. BUILDINGS_PHASE3A3_READINESS.md

---

# 12. 最终必须回答

A. E1 是否通过 failing → passing test？

B. E2 是否通过 failing → passing test？

C. E4 是否通过 failing → passing test？

D. 哪些 patch 建议人工合并？

E. 是否找到可用于 ASEAN Residential / Services thermal/end-use 的高质量来源族？

F. space heating / water heating split 是否有 ASEAN-specific 证据？

G. 是否找到比 BDEW 更适合 ASEAN 的 temporal basis？

H. Cooling 是否确认只在 direct electricity 中且无 double count？

I. Cooking 是否可以维持非显式处理？

J. Buildings + Heat 是否达到 DATA ACCEPTED？

K. 若没有，最少还差哪 3–5 项？

完成后停止。

不要自动进入 Transport。

把结果返回用户 + ChatGPT 做人工科学验收。