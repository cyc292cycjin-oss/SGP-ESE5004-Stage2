# 第四批汇总（run_batch4.sh 自动生成；只读，未调用求解器）

- 停批（RUN_PLAN_B4 3.5）：无；安全停止：无；不可用：无
- 后处理步骤异常或超时（只记录；`POST_ONLY=1` 补做）：无
- P1 探针：未记录
- 早期测速：{"F1": {"ready": true, "exceeded": false, "projected_total_s": 691.0, "seconds_per_iteration_11_20": 1.4}, "F2": {"ready": true, "exceeded": false, "projected_total_s": 312.0, "seconds_per_iteration_11_20": 1.0}}

## 运行

| 运行 | 作用 | 档案 | 状态 | Gurobi 状态 | 终止 | 迭代 | 目标 bn | 求解 s | 求解进程峰值 GiB | Gurobi MaxMemUsed GB | C1 abc | GATES_V6 | 求解后异常 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| F1 | 一体化 2920×3h：c(N)、Owen 分摊、B6 基准 | formal_barrier_1e6_t16 | ended | OPTIMAL | optimal | 113 | 340.6620 | 207 | 5.85 | 5.9 | 111 | ACCEPTED_LAYER2 | 无 |
| F2 | 不互联 2920×3h：B6 = F2 − F1 | formal_barrier_1e6_t16 | ended | OPTIMAL | optimal | 139 | 352.0913 | 215 | 4.44 | 4.6 | 111 | ACCEPTED_LAYER2 | 无 |

## B6（F2 − F1）与 Owen 对偶形式受益

- B6 = 11.4293 bn EUR2020（相对 +3.355e-02；门槛 `B6_INTEGRATED_COST_NOT_ABOVE_DISCONNECTED`：True；标签 F1 ACCEPTED_LAYER2，F2 ACCEPTED_LAYER2；可用 True）
- 分国账本差（F2 − F1，bn）：BN +0.189, ID +0.168, KH +0.817, LA +1.522, MM +0.432, MY +0.712, PH +0.240, SG +2.694, TH +1.381, TL +0.022, VN +1.170, ASEAN +2.084
- Owen 对偶形式受益（F2 份额 − F1 份额，α 主值，bn）：BN +0.189, ID +0.152, KH +0.482, LA +1.460, MM +0.467, MY +0.727, PH +0.240, SG +2.694, TH +2.063, TL +0.022, VN +0.851, BUNKER +2.084
- M12 受益与比例规则对照：B6 11.4293 bn；负受益 []（`M12_BENEFIT/`）

## 与第三批 365×24h 同名结果的对比（只描述，分辨率影响的证据；不判定）

- 未提供第三批导出目录（--batch3），或 F1 / F2 未完成

## 与登记参照值的对比（REFERENCE_VALUES.json：第三批 365×24h R3 / R4 主、R1 / R2 并列；DFX v2 365×24h V1 / V2；只描述，不判定）

- 本批 B6（F2 − F1）：11.4293 bn EUR

| 参照 | 运行 | 参照 B6 bn | ΔB6（本批 − 参照）bn | 目标值差 bn | Owen 受益差（本批受益 − 参照受益，bn）|
|---|---|---|---|---|---|
| 第三批 365×24h v1，R3 / R4（同档案 formal_barrier_1e6_t16，optimal；主参照） | R3 / R4 | 11.2998 | +0.1295 | F1_minus_R3 +90.8265, F2_minus_R4 +90.9560 | BN +0.154, ID -0.114, KH +0.243, LA +0.271, MM +0.206, MY -0.905, PH +0.081, SG -0.434, TH +0.976, TL -0.091, VN -2.254, BUNKER +1.999 |
| 第三批 365×24h v1，R1 / R2（档案 formal_barrier，suboptimal；并列） | R1 / R2 | 11.3001 | +0.1292 | F1_minus_R1 +90.8266, F2_minus_R2 +90.9558 | BN +0.154, ID -0.114, KH +0.243, LA +0.271, MM +0.206, MY -0.905, PH +0.081, SG -0.434, TH +0.976, TL -0.091, VN -2.254, BUNKER +1.998 |
| DFX 阶段 4 365×24h v2，V1 / V2（同档案，optimal） | V1 / V2 | 14.6153 | -3.1860 | F1_minus_V1 +69.8767, F2_minus_V2 +66.6907 | BN +0.112, ID -0.450, KH +0.223, LA +0.231, MM +0.161, MY -2.186, PH +0.092, SG -1.149, TH +0.294, TL -0.113, VN -2.722, BUNKER +2.320 |
