# Road：聚合能源代理与外生电气化

**没有独立passenger-km/tonne-km需求，也没有道路客货技术投资竞争。** 原始量为UNSD国家final-energy TWh；客货、车型及燃料混合进入total road。道路客货在汇总账户中未拆分，不能标作两个已验证显式服务模块。

## 需求及效率

`U/scripts/build_base_energy_totals.py:203–222`生成total road和电/油/气/生物质子项；`prepare_energy_totals.py:35–109,260–270`按DEFAULT增长及EV/FCEV/ICE份额加权效率趋势预测。具体文件来源和缺失处理见需求溯源。

`prepare_transport_data.py:128–180`非custom路径：

`E_land = E_road + E_rail − E_rail,electric`

`g = average_fuel_efficiency / (bev_plug_to_wheel_efficiency × bev_charge_efficiency)`

`q_t = 10^6 × Nyears × E_land × normalized_profile_t × EV_temperature_factor / (g × ICE_temperature_correction)`。

其中q后续作为MW使用，却未具备可接受的服务/能耗单位链：`prepare_transport_data_input.py:115–140`把2014交通CO₂占燃烧CO₂比例变为`(100−share)/100`，其结果无量纲；`config.default.yaml:873`的0.2却注明kWh/km，来自Tesla Model S参考。两者不能直接构成所声称的燃油/电动能耗转换。注释MWh/100km与kWh/km亦未有显式换算。**这是系统级输入定义问题，不是需要补全所有车型。** custom分支仅跳过该转换，不自动提供真实交通服务数据，也不是本轮认可的修复。

## 九项机制结论

| 项目 | 核实结论 |
|---|---|
| 客/货 | 不分开；没有occupancy/load-factor将客公里/吨公里转能耗 |
| ICE | 外生剩余份额`1−EV−FCEV`，固定油Load=q/0.3；不是优化出的车辆选择 |
| EV渗透 | ASEAN DEC 2025/2030/2035/2040/2045/2050为0.05/0.20/0.45/0.70/0.85/1.00；手工scenario override，未科学接受 |
| FCEV | 函数支持固定H₂ Load=q/0.5；DEC份额全0，当前不活跃 |
| 代换 | 车辆能源份额外生；供电、制氢与燃料供给/调度可内生 |
| Charger | 固定`cars×0.011 MW×EV share`；η0.9；availability上界；非扩张投资 |
| EV Store | 固定`cars×0.05 MWh×0.5×EV share`；循环SOC，DSM下界；不是车队投资选择 |
| Profile | 德国BASt周曲线+人口/温度，q与前1、2时间步均值形成EV Load；并非ASEAN实测充电 |
| V2G/DSM | 构造支持，但作者两份final保留V2G Link、删除全部EV Store；无此EV跨时存储机制 |

代码：`U/prepare_sector_network.py:2388–2548`（完整路径为`scripts/prepare_sector_network.py`）；参数`U/config.default.yaml:873–890`、`U/configs/config.asean.yaml:216–239`。dynamic_transport分支还须与prepare_energy_totals用的普通share保持一致；本轮不启用。

## Stock、成本与first-baseline候选

WHO注册车辆+Wikipedia补充/硬编码fallback表用于charger与Store上限。没有车辆年份统一、车龄、EV/ICE独立brownfield存量、turnover或充电站数据库。现有cars是混合注册车辆口径，不等于乘用车；`European_countries_car_ownership.csv`虽存在，不能以文件名推断被此实际路径消费。

构造器未设置有效车辆/charger资本投资项；作者charger/V2G的capital_cost均0、p_nom均固定，但marginal_cost存在约0.009–0.011的小正值。源码默认成本与保存网络实际值分别记录。energy-system objective不等于完整汽车拥有成本。

候选：先审阅一个可追踪的aggregate road能耗/服务边界，必要时EXPLICIT EV转换、FIXED外生渗透与残余燃料；关键单位/历史扣除未闭合前标SYSTEM_RELEVANT_PENDING。不自动赋予未经接受的DSM/V2G灵活性；其可移峰能力是互联价值的重要通道，不能将其潜力解释为零。无需先建车型级模型；本轮不选择或实施任何方案。
