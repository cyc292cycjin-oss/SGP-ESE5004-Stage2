# X20 C-2 规格：陆上风电格点内风速分布（L-C11；决策 252）

**状态：** 审阅端已确认（2026-11-12），附两点补充，见第 7 节（在计算任何 C-2 结果之前写入）。

## 1. 问题与改法

- **问题（L-C11，VERIFIED）：** v5 各国候选平均 CF 只有"GWA IEC3 毛值 ÷ r"的 0.53–0.74 倍（`ONWIND_SANITY_V5.csv`）。现在每个 ERA5 格点只用一个风速系数 f = 格点内 GWA 陆地像元平均风速 ÷ ERA5 年均风速，再按 CF(t) = PC(α_c · f · v(t)) 计算。低风速段的功率曲线是下凸的，所以用平均风速算出的 CF 低于逐像元 CF 的平均（INFERENCE）。
- **改法（决策 252）：** 每个 ERA5 格点取格点内 GWA 像元风速比 r_p = ws_GWA,p ÷ 年均 wnd100m_ERA5 的 **10 个等面积分位档**（按 cos 纬度 × 像元面积加权）：f_k = 第 k 档的面积加权平均比值（k = 0…9）。格点 CF(t) = (1/10) Σ_k PC(α_c · f_k · v(t))，替代 PC(α_c · f · v(t))。
  - Σ_k f_k / 10 = f（等面积档），所以格点平均风速不变，变化的只是分布。
  - 覆盖率 < 50 % 或无 GWA 值的格点照旧取 f_k = 1；每档同样截断到 [0.5, 3]。
- **不变：** 风场校准端（`s4b_3_wind_calibration.py --point-factor`，风场点位系数与 α 表 `WIND_CALIBRATION_ALPHA_V5.csv`）、等级划分规则、潜力（作者 layout）、海上风电与光伏、决策 251 的有效倍数核对（按 f × α，数值不变）。
- **开关：** `research.demand.v5.onwind_subgrid`：**quantile10**（v5 主值）| cell_mean（回退 = 当前 v5，即 X20 B 的 calibrated_gwa_v5）。只在 `onwind_calibration = gwa_cell_ember` 时起作用；取 ember_country 时记为"不适用"，不报错。

## 2. 改动位置

| 文件 | 改动 |
|---|---|
| `scripts_project/v5_wind_gwa.py` | 新增输出 `WIND_GWA_CELL_QUANTILES_V5.nc`（factor_k(k, y, x)，k = 0…9）与汇总 CSV。分两遍读 GWA 栅格：第 1 遍对每格点建风速直方图（0.02 m/s 一档，cos 纬度 × 面积加权），求 10 个等面积分位界；第 2 遍按分位界把像元分档，逐档累加 Σw、Σw·ws，得到 f_k。现有三个输出不改，逐字节复现作为回归检查。 |
| `scripts_project/s4a_profiles.py` | 新变体 `calibrated_gwa_v5q`（= calibrated_gwa_v5 + `cell_quantiles` 键）。逐档 k 用 `alpha_cutout(…, cell_factor=f_k)` 生成缩放副本，算格点年 CF，再取 10 档平均。等级划分与矩阵 M 用平均后的格点 CF。时间序列逐档用同一个 M 转换后取平均（矩阵聚合是线性的，所以等于格点级平均）。各档副本用完即释放，不缓存，因为 10 份副本在内存中放不下。`NON_ATLITE_KEYS` 加 `cell_quantiles`。 |
| `scripts_project/s4b_3_export.py` | 导出 `profiles_calibrated_gwa_v5q_c{1,3}_3h.nc`、`S4A_PROFILE_CLASSES_calibrated_gwa_v5q_c{1,3}.csv` 与日志（独立文件，v4 与 B 段文件一字不动）。 |
| `scripts_project/s4a_layers.py` | v5 且 gwa_cell_ember 时：quantile10 → 变体 calibrated_gwa_v5q，cell_mean → calibrated_gwa_v5。`V5_CLASS_TABLE_VARIANTS` 加新变体。 |
| `scripts_project/v5_common.py`、`configs/research/baseline.yaml` | 新键 onwind_subgrid（V5_OFF = cell_mean，V5_MAIN = quantile10）；主集开关 SHA 随之改变。 |
| `scripts_project/v5_x20_registry.py` | 新增：开关规则行、分位文件行、两个剖面文件与两个等级表文件行。重跑注册表链。 |
| `tests/research/test_v5_x20.py` | (a) 合成像元的分档：等面积、Σ f_k / 10 = f、截断与覆盖率规则；(b) 合成功率曲线上的 10 档平均（下凸段平均 CF ≥ 平均风速 CF）；(c) s4a_layers 按开关选变体，cell_mean 时与 B 段相同。 |

## 3. 计算量与资源（估计，INFERENCE，依据 B 段实测）

| 步骤 | B 段实测 | C-2 估计 |
|---|---|---|
| GWA 栅格（5,900 万个陆地像元） | 39–47 s，峰值 1.69 GB | 两遍约 2 min；直方图 25,550 格点 × 约 1,000 档 × 8 B ≈ 0.2 GB；峰值约 2 GB |
| 陆上风电剖面（每种等级设定） | 约 13 s，峰值 1.87 GB | 10 档 × 13 s ≈ 2.2 min；c1 + c3 合计约 5 min；一次只留一份缩放副本，峰值约 2 GB |
| 导出、注册表链、定向测试 | — | 约 3 min |
| 重建 F1 / F2（另加 v5off 对照） | 每次约 2.5 min，1.07 GB | 约 8 min |
| 静态检查、零松弛门、桥表 | — | 约 6 min |
| 56 时段回归（Gurobi 2 次，Q18 门槛同前） | 约 25 min | 约 25 min |
| 全量单元测试（冻结前） | 31 min | 31 min |

合计约 1.5 h 本机计算，D 盘新增约 1 GB，WSL 家目录新增 < 50 MB（新剖面文件进 git，c3 约 9 MB、c1 约 3 MB）。无下载，不连 HPC。

## 4. 对资源等级划分的影响（INFERENCE）

- 等级仍按节点内格点 CF 在 [cf_min, cf_max] 间线性三分（c3），格点 CF 改用 10 档平均值。格点内风速分布越宽（山脊、海岸）、平均风速越低的格点，CF 上升越多。所以节点的 cf_min / cf_max 和格点归档都会变，各级潜力份额随之重分，节点潜力合计不变。
- 最好等级（c2）的曲线随之改变，存量风电取的曲线也随之改变（①2 机制不变，数值变）。
- 小份额等级可能越过或跌破 S4L-1 灰尘门槛（1 MW / 1 GWh/a），例如 SG。
- 时间序列：10 档平均使小时出力更平滑，满发与零出力的小时更少。这一点会影响储能与备用需求的方向，在网络层面才能看到。

## 5. 验收标准（事先写定，不调参数）

- **主标准：** 重建后的 F1 网络上，按 `x20_bridge.onwind_sanity` 同一公式（候选潜力加权年 CF ÷（GWA IEC3 毛值 ÷ r），r 同 `ONWIND_SANITY_V5.csv`），**11 国全部落在 [0.8, 1.25]** → 继续；**任一国越界 → 停下报告，不改档数、截断、α 或参数。**
- **预检：** 剖面导出后、建网之前，先用等级表（潜力加权 `cf_annual_weighted`）按同一公式算一遍。任一国越界即停，不建网络，不求解。
- 报告同时列出 v4、X20 B（cell_mean）、C-2（quantile10）三种口径下各国候选 CF 与比值，以及各级潜力份额的变化。

## 6. 顺序（审阅端确认后）

C-2 实施并提交 → 剖面与预检 → 重建 F1 / F2 与 v5off → 静态检查与零松弛门 → 主标准核对 → 桥表与报告更新 → 56 时段回归（Gurobi ≤ 2 次）→ 全量测试 → 审阅包。C-1 已实施（提交 `b9852d22`），随这次重建一起进入网络。

## 7. 审阅端确认时的补充（2026-11-12，写于计算任何 C-2 结果之前）

1. **门槛只对候选潜力 ≥ 1 GW 的国家设置。** 第 5 节主标准与预检的 [0.8, 1.25] 门槛，只适用于陆上风电候选潜力 ≥ 1 GW 的国家；潜力 < 1 GW 的国家照列比值，不设门槛。
   - 潜力 = 该国陆上风电候选 p_nom_max 合计。预检时用等级表的 `potential_mw` 合计，主标准用重建后 F1 网络的值。C-2 不改节点潜力合计，两者应与 X20 B 桥表一致。
   - 按 X20 B 桥表，只有 SG（34.7 MW）低于 1 GW，其余 10 国都在 1 GW 以上（最小 BN 10,466 MW）。所以门槛适用于 BN、ID、KH、LA、MM、MY、PH、TH、TL、VN。
   - 越界即停下报告，不调参数。
2. **报告补两处：**
   - 存量风电改用新曲线后的各国 CF，与 Ember 实测 CF 对照。Ember 实测取风电校准用的同一套数（`WIND_CALIBRATION_ALPHA_V5.csv` 的 `cf_obs`，即 2019–2025 中位数），列出 v4、X20 B 与 C-2 三种口径。
   - 分档使用格点内的全部陆地像元（国家陆地掩膜），没有限定在可用地（作者 layout 的排除规则）上。这一点写入局限：可用地的风速分布可能不同于整个格点。
