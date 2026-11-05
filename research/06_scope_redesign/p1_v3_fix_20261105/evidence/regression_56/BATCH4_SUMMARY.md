# 第四批汇总（run_batch4.sh 自动生成；只读，未调用求解器）

- 停批（RUN_PLAN_B4 3.5）：无；安全停止：无；不可用：无
- 后处理步骤异常或超时（只记录；`POST_ONLY=1` 补做）：无
- P1 探针：未记录
- 早期测速：{"F1": {"ready": true, "exceeded": false, "projected_total_s": 517.0, "seconds_per_iteration_11_20": 1.3}, "F2": {"ready": true, "exceeded": false, "projected_total_s": 336.0, "seconds_per_iteration_11_20": 1.1}, "F3": null, "F4": null}

## 运行

| 运行 | 作用 | 档案 | 状态 | Gurobi 状态 | 终止 | 迭代 | 目标 bn | 求解 s | 求解进程峰值 GiB | Gurobi MaxMemUsed GB | C1 abc | GATES_V6 | 求解后异常 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| F1 | 一体化 v3 2920×3h（S-A）：c(N)、Owen 分摊、B6 基准 | formal_barrier_1e6_t16 | ended | OPTIMAL | optimal | 96 | 329.7056 | 189 | 6.14 | 6.0 | 111 | ACCEPTED_LAYER2 | 无 |
| F2 | no_new_xb v3 2920×3h（S-A）：B6 = F2 − F1 | formal_barrier_1e6_t16 | ended | OPTIMAL | optimal | 81 | 342.2687 | 138 | 4.63 | 4.4 | 111 | ACCEPTED_LAYER2 | 无 |
| F3 | 一体化，EV 车队代理 ×0.5（第 186 项） | formal_barrier_1e6_t16 | not_started | — | — | — | — | — | — | — | — | — | 无 |
| F4 | no_new_xb，EV 车队代理 ×0.5：B6 = F4 − F3（第 186 项） | formal_barrier_1e6_t16 | not_started | — | — | — | — | — | — | — | — | — | 无 |

## B6（F2 − F1）与 Owen 对偶形式受益

- B6 = 12.5631 bn EUR2020（相对 +3.810e-02；门槛 `B6_INTEGRATED_COST_NOT_ABOVE_DISCONNECTED`：True；标签 F1 ACCEPTED_LAYER2，F2 ACCEPTED_LAYER2；可用 True）
- 分国账本差（F2 − F1，bn）：BN +0.184, ID -0.704, KH +0.654, LA +1.359, MM +0.239, MY +0.861, PH +0.130, SG +2.770, TH +1.986, TL +0.026, VN +1.759, ASEAN +3.297
- Owen 对偶形式受益（F2 份额 − F1 份额，α 主值，bn）：BN +0.184, ID -0.712, KH +0.366, LA -0.108, MM +0.298, MY +0.870, PH +0.130, SG +2.770, TH +4.073, TL +0.026, VN +1.369, BUNKER +3.297
- M12 受益与比例规则对照：B6 12.5631 bn；负受益 ['ID', 'LA']（`M12_BENEFIT/`）

## 第 B 对（F4 − F3）

- 不可计算（F3 或 F4 无目标值）

## 与第三批 365×24h 同名结果的对比（只描述，分辨率影响的证据；不判定）

- 未提供第三批导出目录（--batch3），或 F1 / F2 未完成

## 与登记参照值的对比（REFERENCE_VALUES.json：第三批 365×24h R3 / R4 主、R1 / R2 并列；DFX v2 365×24h V1 / V2；只描述，不判定）

- 本批 B6（F2 − F1）：12.5631 bn EUR

| 参照 | 运行 | 参照 B6 bn | ΔB6（本批 − 参照）bn | 目标值差 bn | Owen 受益差（本批受益 − 参照受益，bn）|
|---|---|---|---|---|---|
| v3 365×24h 重跑（第 182 项后，S-B；主参照，只用于 B6 符号与程序对照，第 176 项第 7 条） | V1 / V2 | 14.5738 | -2.0107 | F1_minus_V1 +63.4328, F2_minus_V2 +61.4221 | BN +0.118, ID -1.299, KH +0.173, LA -0.884, MM +0.053, MY -2.306, PH +0.068, SG -1.149, TH +3.060, TL -0.125, VN -3.133, BUNKER +3.414 |
| v3 365×24h 第一次筛查（第 182 项前，S-B；并列） | V1 / V2 | 14.3481 | -1.7850 | F1_minus_V1 +66.1089, F2_minus_V2 +64.3240 | BN +0.121, ID -1.271, KH +0.169, LA -0.889, MM +0.098, MY -2.270, PH +0.072, SG -1.074, TH +2.976, TL -0.111, VN -3.113, BUNKER +3.507 |
| v3 本机 56 时段冒烟（S-A，本包网络的截短） | F1-56 / F2-56 | 12.5631 | +0.0000 | F1_minus_F1-56 -0.0000, F2_minus_F2-56 -0.0000 | BN -0.000, ID +0.000, KH -0.000, LA +0.000, MM +0.000, MY +0.000, PH -0.000, SG -0.000, TH +0.000, TL -0.000, VN -0.000, BUNKER -0.000 |
| v3 补充 05 冒烟（S-B，第 180 项网络的截短） | S5-I / S5-R | 12.5665 | -0.0034 | F1_minus_S5-I +0.5057, F2_minus_S5-R +0.5023 | BN +0.000, ID +0.119, KH -0.001, LA -0.007, MM +0.003, MY +0.023, PH -0.043, SG +0.002, TH +0.007, TL +0.000, VN +0.003, BUNKER -0.110 |
