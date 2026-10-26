# DFX 一阶预测（v2 − v1，第三批 365×24h 对偶价格；INFERENCE，大变动外推）

## main (R1 / R2)

- ΔD = +481.0 TWh（未定价 +0.00 TWh）；ΔC_一体化 = +19.450 bn EUR；ΔC_不互联 = +22.510 bn EUR；**ΔB6 = +3.060 bn EUR（+3.488 bn USD）**；预测 B6 ≈ 11.300 + ΔB6 = 14.360 bn EUR

| 变动类别 | ΔD TWh | ΔC_int bn | ΔC_dis bn | ΔB6 bn |
|---|---|---|---|---|
| F1 NEU multiplier (coal) | +0.6 | +0.005 | +0.005 | +0.000 |
| F1 agriculture anchor (RAS) | -29.0 | -1.725 | -1.808 | -0.082 |
| F1 buildings anchors (RAS) | -132.9 | -7.323 | -7.349 | -0.026 |
| F1 industry multiplier (RAS) | +238.1 | +7.828 | +9.001 | +1.173 |
| F1 transport anchor (RAS) | +355.2 | +15.391 | +17.560 | +2.169 |
| F2 NEU gas (ammonia feedstock deduction) | -143.4 | -4.065 | -4.087 | -0.021 |
| F2 ammonia (production rule) | +66.3 | +4.884 | +4.732 | -0.153 |
| F3 NEU oil (HVC scope) + F1 multiplier | +126.2 | +4.455 | +4.455 | +0.000 |

| 国 | ΔD TWh | Δ Owen 份额 bn | Δ 单干成本 bn | Δ 受益 bn |
|---|---|---|---|---|
| BN | +3.1 | +0.105 | +0.134 | +0.029 |
| ID | +67.8 | +5.636 | +5.455 | -0.181 |
| KH | +0.2 | -0.089 | -0.085 | +0.004 |
| LA | +0.4 | -0.019 | -0.035 | -0.016 |
| MM | +6.3 | +0.094 | +0.104 | +0.010 |
| MY | +89.6 | +4.198 | +5.751 | +1.552 |
| PH | +5.1 | +0.043 | +0.061 | +0.018 |
| SG | +45.9 | +2.044 | +3.194 | +1.150 |
| TH | +251.4 | +7.081 | +7.196 | +0.115 |
| TL | +0.3 | +0.010 | +0.012 | +0.002 |
| VN | +11.0 | +0.346 | +0.722 | +0.376 |

## robustness (R3 / R4, optimal 1e-6)

- ΔD = +481.0 TWh（未定价 +0.00 TWh）；ΔC_一体化 = +19.450 bn EUR；ΔC_不互联 = +22.510 bn EUR；**ΔB6 = +3.060 bn EUR（+3.488 bn USD）**；预测 B6 ≈ 11.300 + ΔB6 = 14.360 bn EUR

| 变动类别 | ΔD TWh | ΔC_int bn | ΔC_dis bn | ΔB6 bn |
|---|---|---|---|---|
| F1 NEU multiplier (coal) | +0.6 | +0.005 | +0.005 | +0.000 |
| F1 agriculture anchor (RAS) | -29.0 | -1.725 | -1.808 | -0.082 |
| F1 buildings anchors (RAS) | -132.9 | -7.323 | -7.349 | -0.026 |
| F1 industry multiplier (RAS) | +238.1 | +7.828 | +9.001 | +1.173 |
| F1 transport anchor (RAS) | +355.2 | +15.391 | +17.560 | +2.169 |
| F2 NEU gas (ammonia feedstock deduction) | -143.4 | -4.065 | -4.087 | -0.021 |
| F2 ammonia (production rule) | +66.3 | +4.884 | +4.732 | -0.152 |
| F3 NEU oil (HVC scope) + F1 multiplier | +126.2 | +4.455 | +4.455 | +0.000 |

| 国 | ΔD TWh | Δ Owen 份额 bn | Δ 单干成本 bn | Δ 受益 bn |
|---|---|---|---|---|
| BN | +3.1 | +0.105 | +0.134 | +0.029 |
| ID | +67.8 | +5.636 | +5.456 | -0.181 |
| KH | +0.2 | -0.089 | -0.085 | +0.004 |
| LA | +0.4 | -0.019 | -0.035 | -0.016 |
| MM | +6.3 | +0.094 | +0.104 | +0.010 |
| MY | +89.6 | +4.198 | +5.751 | +1.552 |
| PH | +5.1 | +0.043 | +0.061 | +0.018 |
| SG | +45.9 | +2.044 | +3.194 | +1.150 |
| TH | +251.4 | +7.081 | +7.196 | +0.115 |
| TL | +0.3 | +0.010 | +0.012 | +0.002 |
| VN | +11.0 | +0.346 | +0.722 | +0.376 |

价格回退（v1 中不存在的负荷类）：R1 MY IndustryAmmonia industry ammonia: carrier average (all countries); R1 SG AgricultureFinalEnergy biomass final energy: carrier average (all countries); R1 SG AgricultureFinalEnergy gas final energy: country x carrier average; R1 TH CommercialFuel oil final energy: country x carrier average; R2 MY IndustryAmmonia industry ammonia: carrier average (all countries); R2 SG AgricultureFinalEnergy biomass final energy: carrier average (all countries); R2 SG AgricultureFinalEnergy gas final energy: country x carrier average; R2 TH CommercialFuel oil final energy: country x carrier average; R3 MY IndustryAmmonia industry ammonia: carrier average (all countries); R3 SG AgricultureFinalEnergy biomass final energy: carrier average (all countries); R3 SG AgricultureFinalEnergy gas final energy: country x carrier average; R3 TH CommercialFuel oil final energy: country x carrier average; R4 MY IndustryAmmonia industry ammonia: carrier average (all countries); R4 SG AgricultureFinalEnergy biomass final energy: carrier average (all countries); R4 SG AgricultureFinalEnergy gas final energy: country x carrier average; R4 TH CommercialFuel oil final energy: country x carrier average
