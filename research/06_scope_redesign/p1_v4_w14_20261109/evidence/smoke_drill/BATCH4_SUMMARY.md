# 第四批汇总（run_batch4.sh 自动生成；只读，未调用求解器）

- 停批（RUN_PLAN_B4 3.5）：无；安全停止：无；不可用：无
- 后处理步骤异常或超时（只记录；`POST_ONLY=1` 补做）：无
- P1 探针：未记录
- 早期测速：{"F1": {"ready": true, "exceeded": false, "projected_total_s": 683.0, "seconds_per_iteration_11_20": 1.6}, "F2": {"ready": true, "exceeded": false, "projected_total_s": 421.0, "seconds_per_iteration_11_20": 1.2}}

## 运行

| 运行 | 作用 | 档案 | 状态 | Gurobi 状态 | 终止 | 迭代 | 目标 bn | 求解 s | 求解进程峰值 GiB | Gurobi MaxMemUsed GB | C1 abc | GATES_V6 | 求解后异常 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| F1 | 一体化 v4 主算 2920×3h：c(N)、Owen 分摊、B6 基准 | formal_barrier_1e6_t16 | ended | OPTIMAL | optimal | 89 | 363.1900 | 217 | 6.07 | 5.9 | 111 | ACCEPTED_LAYER2 | 无 |
| F2 | no_new_xb v4 主算 2920×3h：B6 = F2 − F1 | formal_barrier_1e6_t16 | ended | OPTIMAL | optimal | 80 | 376.1437 | 127 | 4.66 | 4.5 | 111 | ACCEPTED_LAYER2 | 无 |

## B6（F2 − F1）与 Owen 对偶形式受益

- B6 = 12.9536 bn EUR2020（相对 +3.567e-02；门槛 `B6_INTEGRATED_COST_NOT_ABOVE_DISCONNECTED`：True；标签 F1 ACCEPTED_LAYER2，F2 ACCEPTED_LAYER2；可用 True）
- 分国账本差（F2 − F1，bn）：BN +0.210, ID +1.146, KH +0.669, LA +1.037, MM +0.289, MY +1.323, PH -0.540, SG +2.996, TH +1.631, TL +0.023, VN +1.401, ASEAN +2.770
- Owen 对偶形式受益（F2 份额 − F1 份额，α 主值，bn）：BN +0.210, ID +1.136, KH +0.348, LA -0.195, MM +0.360, MY +1.333, PH -0.540, SG +2.996, TH +3.408, TL +0.023, VN +1.106, BUNKER +2.770
- M12 受益与比例规则对照：B6 12.9536 bn；负受益 ['LA', 'PH']（`M12_BENEFIT/`）

## 与第三批 365×24h 同名结果的对比（只描述，分辨率影响的证据；不判定）

- 未提供第三批导出目录（--batch3），或 F1 / F2 未完成

## 与登记参照值的对比（REFERENCE_VALUES.json：第三批 365×24h R3 / R4 主、R1 / R2 并列；DFX v2 365×24h V1 / V2；只描述，不判定）

- 本批 B6（F2 − F1）：12.9536 bn EUR

| 参照 | 运行 | 参照 B6 bn | ΔB6（本批 − 参照）bn | 目标值差 bn | Owen 受益差（本批受益 − 参照受益，bn）|
|---|---|---|---|---|---|
| v3.1 2920×3h HPC 主算（第 195 项；v3.1 基线 BASELINE_V31.md，主对照） | F1 / F2 | 11.9764 | +0.9772 | F1_minus_F1 +58.1375, F2_minus_F2 +59.1148 | BN +0.154, ID +0.772, KH +0.223, LA -1.007, MM +0.102, MY -0.529, PH -0.556, SG +0.057, TH +2.806, TL -0.102, VN -2.825, BUNKER +1.884 |
| v4 D2c 本机 56 时段冒烟（本包网络截短后与之逐组件相同；HPC 冒烟期望值来源） | v4d2c_F1 / v4d2c_F2 | 12.9536 | +0.0000 | F1_minus_v4d2c_F1 +0.0000, F2_minus_v4d2c_F2 +0.0000 | BN +0.000, ID +0.000, KH +0.000, LA +0.000, MM +0.000, MY +0.000, PH +0.000, SG +0.000, TH +0.000, TL +0.000, VN +0.000, BUNKER +0.000 |
| v3.1 本机 56 时段回归（第 195 项修正后，截短） | F1-56 / F2-56 | 12.5631 | +0.3905 | F1_minus_F1-56 +33.4845, F2_minus_F2-56 +33.8750 | BN +0.027, ID +1.848, KH -0.019, LA -0.087, MM +0.062, MY +0.463, PH -0.670, SG +0.225, TH -0.665, TL -0.003, VN -0.263, BUNKER -0.528 |
