# 模型侧币值年份核验（一次性来源追踪）

已核验：原始costs_2030.csv/costs_2050.csv中相应EUR2020和EUR2023字段进入处理表后，只发生/kW→/MW等单位变换，没有统一真实价格年份。42条现有/水电技术investment、FOM、VOM对照保存在evidence/MODEL_FACING_COST_YEAR_EVIDENCE.json。

process_cost_data.py:377 load_costs、501 prepare_costs都调用同一apply_currency_conversion；247-288的函数只乘汇率，说明假设输入已统一到reference_year，并未将逐行currency_year变成通胀因子。append_cost_data.py:80附近将AEO8的USD2020转换为EUR，再写currency_year2020；DEA来源中仍有EUR2023。外汇货币统一不等于购买力基年统一。没有仅凭原始年份再做一遍通胀。

本轮无成本数字修改。既有FOM作为固定存量的常数项保留；既有VOM影响调度；新建投资/固定运维及外部燃料费用可影响容量与运行选择。因此当前不能声称统一真实价格的完整系统成本。

候选方法（未批准/未执行）：先共同选择一个真实EUR价格基年Y及相容官方平减序列；逐行核对既有上游已做的汇率/通胀转换，只对尚未实值调整的货币量应用P_Y/P_y。FOM百分比、效率、寿命不作价格通胀；货币型FOM由已统一投资基数与原百分比重算。保留原始值、源年、先前转换、最终model-facing年与hash。影响范围包括既有VOM、固定FOM账，以及新建和燃料费用，须在正式成本比较/求解前处理。
