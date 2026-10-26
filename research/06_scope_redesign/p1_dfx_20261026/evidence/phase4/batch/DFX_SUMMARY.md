# DFX 365×24h 筛查汇总（run_dfx.sh 自动生成；只读，未调用求解器）

- 停批（RUN_PLAN_DFX 3.3：任一运行 G2 不通过；V1 / V2 无返回解或 C1 (a) 不通过）：无；安全停止：无
- 后处理步骤异常或超时（只记录，不改变调度；可用 `POST_ONLY=1` 补做）：无

## 运行

| 运行 | 作用 | 档案 | 状态 | 终止 | 目标 bn | 求解 s | 峰值 GiB | C1 abc | C1 参照 | 重评次数 | GATES_V6 | 临时标签 | Owen 可用 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| V1 | 本批参照（一体化，v2 需求）、Owen 分摊 | formal_barrier_1e6_t16 | ended | optimal | 270.7852 | 5615 | 22.29 | 111 | batch | 1 | ACCEPTED_LAYER2 | ACCEPTED_LAYER2 | True |
| V2 | 本批参照（不互联，v2 需求）、B6 = V2 − V1 | formal_barrier_1e6_t16 | ended | optimal | 285.4006 | 1168 | 18.86 | 111 | batch | 1 | ACCEPTED_LAYER2 | ACCEPTED_LAYER2 | True |

## B6（V2 − V1）

- B6 = 14.6153 bn EUR2020（门槛 `B6_INTEGRATED_COST_NOT_ABOVE_DISCONNECTED`：True；标签 V1 ACCEPTED_LAYER2，V2 ACCEPTED_LAYER2）
- M12 受益与比例规则对照：B6 14.6153 bn；负受益 ['BUNKER']（`M12_BENEFIT/`）

## 与第三批及一阶预测的对比（只描述，不作验收依据；RUN_PLAN_DFX 3.4 第 5–6 项；主参照 R3 / R4 同档案 optimal，R1 / R2 并列）

- 主参照 B6（R4 − R3）11.2998 bn；本批 B6 14.6153 bn；ΔB6 实际 +3.3155 bn，一阶预测 +3.0596 bn，差 +0.2558 bn
- 并列参照 B6（R2 − R1）11.3001 bn；ΔB6 对其 +3.3152 bn
- 目标值差（bn）：V1 − R3 +20.9498；V2 − R4 +24.2653；V1 − R1 +20.9498；V2 − R2 +24.2650（一阶 ΔC_一体化 +19.4500，ΔC_不互联 +22.5096）
- Owen 对偶形式（α 主值）分摊差 V1 − R3：BN +0.113, ID +5.354, KH -0.139, LA -0.115, MM +0.020, MY +4.862, PH -0.048, SG +2.904, TH +6.883, TL -0.017, VN +0.298, BUNKER +0.835
- Owen 对偶形式（α 主值）分摊差 V2 − R4：BN +0.155, ID +5.690, KH -0.119, LA -0.075, MM +0.064, MY +6.143, PH -0.059, SG +3.619, TH +7.564, TL +0.004, VN +0.766, BUNKER +0.513
- Owen 对偶形式（α 主值）分摊差 V1 − R1：BN +0.113, ID +5.355, KH -0.139, LA -0.115, MM +0.020, MY +4.862, PH -0.048, SG +2.904, TH +6.883, TL -0.017, VN +0.298, BUNKER +0.835
- Owen 对偶形式（α 主值）分摊差 V2 − R2：BN +0.155, ID +5.690, KH -0.119, LA -0.075, MM +0.064, MY +6.143, PH -0.059, SG +3.619, TH +7.564, TL +0.004, VN +0.766, BUNKER +0.513
- 一阶预测的分国受益变化（bn EUR）：BN +0.029, ID -0.181, KH +0.004, LA -0.016, MM +0.010, MY +1.552, PH +0.018, SG +1.150, TH +0.115, TL +0.002, VN +0.376
