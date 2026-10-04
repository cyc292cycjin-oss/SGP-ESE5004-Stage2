# Buildings 时间分配：最低可接受方法

Material Passport: academic-research-suite / proposed method; Phase3A5 v1; 2026-10-02。本轮不生成11国8760曲线；当前仅有条件可执行的算法契约，数据尚不足。

## Water heating 与 HDD 解耦

对国家/地区、R/S、用途分别取得使用时刻曲线q_t，单位可为归一化活动强度，但来源的调查范围、工作日/周末、季节及本地时区必须明确。将本地曲线转换到共同UTC网格；先处理全年日历/缺测，再以**物理时长权重**w_t归一化：`p_t=Q_annual×q_t/Σ(w_t q_t)`。能量检查 `Σ(w_t p_t)=Q_annual`。归一化分母为零或无效且Q>0必须停止，沿用E2。

不能把洗浴用水升数直接当热能曲线：还需冷热水分离、进/出水温差、热水量和服务边界。住宅使用时刻与酒店/餐饮/医院/学校等Services时刻独立；不能继续把所有商业热水机械复制住宅曲线。

## 现有来源能支持的程度

| 来源 | 能用作什么候选 | 缺什么 |
|---|---|---|
| Hanoi九户、35人、December的用水研究 | 支持晚间/清晨使用活动与家庭作息相关；可做局地形状研究候选。 | 高收入小样本、冷热水/电能转换、全年/工作日季节代表性与当地年度扩展。不能复制全国。|
| BELDA2017四国若干城市/村庄、2014-10至2015-09 | 问卷包含月账单、设备和使用时间；支持寻找原问卷/逐月数据。 | 公开论文未恢复可执行的全国分部门小时原表；不能从图像估数补曲线。|
| MY官方end-use年表 | 给年度候选量与商业类别切入点。 | 没有可用的独立R/S热水小时分布、时区/周末/季节权重。|
| GEGIS/DemandCast | 综合电力形状的原始方法与时间轴可追踪。 | 不是独立水热形状；不能从总电力自动反推。|
| BDEW | 保留reference/reproduction benchmark。 | 没有ASEAN当地可迁移性接受，不进入科学基准。|

局地研究来源：[Toyosada等2018](https://www.scirp.org/journal/paperinformation?paperid=82791)、[BELDA2017](https://www.belda.asia/wp/wp-content/uploads/2017/06/170608ECEEE201_BELDA.pdf)。时刻信息只作候选，不用于填最终24小时向量。

## Space heating

仅对获接受正annual service的气候区构造温度响应：候选 `q_t=max(T_balance−T_t,0)` 还需建筑/使用时刻修正。T_balance、温度数据/版本、建筑热惰性/工作日修正必须有当地证据，不自动填18°C或欧洲参数。没有positive service与地区证据时不生成供暖曲线；unknown不替换为零。

未来实现前需验证：跨年/闰年时区转换；缺测不填零掩盖；R/S分开；权重单位为小时而非折现后的objective权重；年量守恒；正需求零曲线报错；未添加cooling/cooking额外Load。本轮只复用Phase3A4规范与E2验收，不再运行其1062个模型回归。
