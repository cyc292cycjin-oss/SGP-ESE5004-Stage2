import math, json
r56, r365 = 1393079, 9017345; c56, c365 = 629144, 4048847; z56, z365 = 3209723, 20952716
out = {}
for name, a, b in (("rows", r56, r365), ("cols", c56, c365), ("nnz", z56, z365)):
    per = (b - a) / (365 - 56); st = a - 56 * per
    out[name] = dict(per_snapshot=per, static=st, n2920=st + 2920 * per, ratio_2920_over_365=(st + 2920 * per) / b)
R = out["rows"]["n2920"]; k = R / r365
m56, m365 = 4.10, 15.1
slope = (m365 - m56) / ((r365 - r56) / 1e6); icpt = m56 - slope * r56 / 1e6
exp_obs = math.log(m365 / m56) / math.log(r365 / r56)
mem = dict(proportional=m365 * k, affine=icpt + slope * R / 1e6, observed_power=m365 * k ** exp_obs, observed_exponent=exp_obs,
           superlinear_1_15=m365 * k ** 1.15, superlinear_1_3=m365 * k ** 1.3)
# barrier time on 8470Q (r=0.74): 365x24h profile A 11470 s / 408 it = 28.1 s/it
spi = 11470.32 / 408
t = {}
for e in (1.0, 1.15, 1.3):
    s = spi * k ** e
    t[f"s_per_iter_exp{e}"] = s
    for it in (150, 250, 408, 600):
        t[f"h_exp{e}_it{it}"] = it * s / 3600
disk = dict(solved_network_gb=0.1664 * k, duals_gb=0.0767 * k, bundle_gb=0.1589 * k, run_dir_gb=1.85 * k, solve_dir_gb=1.43 * k, export_gb=0.2566 * k,
            c1_mem_gib=8.9 * k)
print(json.dumps(dict(sizes=out, k=k, mem=mem, time=t, disk=disk), indent=1))
