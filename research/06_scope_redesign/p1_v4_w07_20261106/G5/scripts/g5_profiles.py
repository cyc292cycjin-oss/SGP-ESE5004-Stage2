"""G5 (V4_W07 section B-G5): industrial hourly profiles for the v4 subsectors - design and data only.

    PYTHONHASHSEED=0 python g5_profiles.py --s0 <work/p1_v4_data_20261105> --repo /home/jin/wt_v4_g5 --network <F1 integrated_2920_3h_unsolved.nc> --out <G5 dir>

Read-only: no network, code, config, registry or T_v2 change; no solver.  Writes into --out:
  evidence/G5_FFE_CLOCK_TESTS.json, evidence/G5_FFE_HOLIDAY_DAYS.csv, evidence/G5_SHAPE_STATS.csv
  WEEK_TEMPLATES_168.csv      local-clock 168-hour week (Monday 00:00 = 0, mean 1) of every shape
  PROFILE_MAPPING.csv         v4 subsector x energy type -> main shape, sensitivity shapes, reasons
  PROFILES_8760.parquet       distinct normalised curves (annual mean 1.0) on the model clock (2013, UTC, hour starts, tz-naive like the network)
  PROFILE_INDEX.csv           (variant, subsector, etype, zone) -> curve id in PROFILES_8760.parquet
  TIMEZONE_NODES.csv          every AC node: UTC offset, rule, province (ID), multi-time-zone area check

Conventions (VERIFIED in g5_probe_network.py): model snapshots are tz-naive UTC (2013); a 1-hour value at UTC hour u is the mean over [u, u+1);
the 3-hour snapshot t is the mean of hours t, t+1, t+2 (same as v3_ev.ev_series).
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.dataset as pads
import pyarrow.parquet as pq

FFE_NAMES = {1: "Iron & steel", 4: "Non-metallic minerals", 5: "Transport equipment", 6: "Machinery", 7: "Mining and quarrying", 8: "Food and tobacco",
             9: "Paper, pulp and print", 10: "Wood and wood products", 11: "Construction", 12: "Textile and leather", 13: "Non-specified (industry)"}
FFE_SHAPES = {"FFE_STEEL_PAPER": 1, "FFE_NMM": 4, "FFE_TRANSPORT_MACH": 5, "FFE_MINING": 7, "FFE_FOOD": 8, "FFE_NONSPEC": 13}
# NREL groups: name -> NAICS prefixes (all NAICS codes in the parquet that start with one of them)
NREL_GROUPS = {"NREL_311": ["311", "312"], "NREL_313_316": ["313", "314", "315", "316"], "NREL_321": ["321"], "NREL_322": ["322"], "NREL_325": ["325"],
               "NREL_327": ["327"], "NREL_331": ["331"], "NREL_333": ["333"], "NREL_336": ["336"],
               "NREL_3311": ["3311"], "NREL_327310": ["32731"], "NREL_325311": ["32531"], "NREL_325110": ["32511"], "NREL_3254": ["3254"],
               "NREL_3313": ["3313"], "NREL_331410": ["3314"], "NREL_3272": ["3272"], "NREL_3274": ["3274"], "NREL_322_MILLS": ["3221"]}
ZONES = [6.5, 7.0, 8.0, 9.0]
GERMAN_HOLIDAYS_2017 = {  # INFERENCE (from memory, to be checked): national + widespread regional holidays 2017
    "2017-01-01": "Neujahr", "2017-01-06": "Heilige Drei Koenige (BW, BY, ST)", "2017-04-14": "Karfreitag", "2017-04-17": "Ostermontag", "2017-05-01": "Tag der Arbeit",
    "2017-05-25": "Christi Himmelfahrt", "2017-06-05": "Pfingstmontag", "2017-06-15": "Fronleichnam (BW, BY, HE, NW, RP, SL)", "2017-08-15": "Mariae Himmelfahrt (SL, part BY)",
    "2017-10-03": "Tag der Deutschen Einheit", "2017-10-31": "Reformationstag (national 2017)", "2017-11-01": "Allerheiligen (BW, BY, NW, RP, SL)",
    "2017-12-25": "1. Weihnachtstag", "2017-12-26": "2. Weihnachtstag"}
# Holiday sensitivity (design only): major 2013 holidays / shutdown windows on the local calendar. INFERENCE from memory - all dates to be checked
# against official 2013 gazettes (MISSING_DATA); the Python 'holidays' package is not installed in the environment.
HOLIDAYS_2013 = {
    "ID": [("2013-01-01", "Tahun Baru"), ("2013-08-05", "cuti bersama Lebaran"), ("2013-08-06", "cuti bersama Lebaran"), ("2013-08-07", "cuti bersama Lebaran"),
           ("2013-08-08", "Idul Fitri 1434 H"), ("2013-08-09", "Idul Fitri 1434 H"), ("2013-08-12", "cuti bersama Lebaran"), ("2013-08-13", "design choice: factory restart day after Lebaran (not a gazetted holiday)"),
           ("2013-12-25", "Natal")],
    "MY": [("2013-01-01", "New Year (most states)"), ("2013-02-11", "Chinese New Year"), ("2013-02-12", "Chinese New Year (2nd day)"), ("2013-08-08", "Hari Raya Aidilfitri"),
           ("2013-08-09", "Hari Raya Aidilfitri"), ("2013-08-31", "Hari Merdeka"), ("2013-12-25", "Christmas")],
    "SG": [("2013-01-01", "New Year"), ("2013-02-11", "Chinese New Year"), ("2013-02-12", "Chinese New Year (observed)"), ("2013-08-08", "Hari Raya Puasa"),
           ("2013-08-09", "National Day"), ("2013-12-25", "Christmas")],
    "TH": [("2013-01-01", "New Year"), ("2013-04-15", "Songkran"), ("2013-04-16", "Songkran (substitute)"), ("2013-04-12", "Songkran bridge"), ("2013-12-05", "King's Birthday"),
           ("2013-12-31", "New Year's Eve")],
    "VN": [("2013-01-01", "Tet Duong lich"), ("2013-02-11", "Tet Nguyen Dan"), ("2013-02-12", "Tet"), ("2013-02-13", "Tet"), ("2013-02-14", "Tet"), ("2013-02-15", "Tet"),
           ("2013-04-19", "Gio To Hung Vuong"), ("2013-04-30", "Reunification Day"), ("2013-05-01", "Labour Day"), ("2013-09-02", "National Day")],
    "PH": [("2013-01-01", "New Year"), ("2013-03-28", "Maundy Thursday"), ("2013-03-29", "Good Friday"), ("2013-12-24", "Christmas Eve"), ("2013-12-25", "Christmas"),
           ("2013-12-30", "Rizal Day"), ("2013-12-31", "New Year's Eve")],
    "MM": [("2013-01-04", "Independence Day"), ("2013-04-15", "Thingyan"), ("2013-04-16", "Thingyan"), ("2013-04-17", "Myanmar New Year"), ("2013-04-12", "Thingyan eve")],
    "KH": [("2013-01-01", "New Year"), ("2013-04-15", "Khmer New Year"), ("2013-04-16", "Khmer New Year"), ("2013-10-03", "Pchum Ben"), ("2013-10-04", "Pchum Ben"),
           ("2013-11-18", "Water Festival")],
    "LA": [("2013-01-01", "New Year"), ("2013-04-15", "Pi Mai"), ("2013-04-16", "Pi Mai"), ("2013-12-02", "National Day")],
    "BN": [("2013-01-01", "New Year"), ("2013-08-08", "Hari Raya Aidilfitri"), ("2013-08-09", "Hari Raya Aidilfitri"), ("2013-08-10", "Hari Raya Aidilfitri"), ("2013-12-25", "Christmas")],
    "TL": [("2013-01-01", "New Year"), ("2013-03-28", "Holy Thursday"), ("2013-03-29", "Good Friday"), ("2013-11-28", "Proclamation of Independence"), ("2013-12-25", "Christmas")],
}
# Indonesian legal time zones by province (Keppres 41/1987; GADM 4.1 NAME_1 spelling). INFERENCE from memory, to be checked.
ID_PROVINCE_TZ = {7.0: ["Aceh", "Sumatera Utara", "Sumatera Barat", "Riau", "Kepulauan Riau", "Jambi", "Bengkulu", "Sumatera Selatan", "Bangka-Belitung", "Bangka Belitung", "Lampung",
                        "Banten", "Jakarta Raya", "Jawa Barat", "Jawa Tengah", "Yogyakarta", "Jawa Timur", "Kalimantan Barat", "Kalimantan Tengah"],
                  8.0: ["Bali", "Nusa Tenggara Barat", "Nusa Tenggara Timur", "Kalimantan Selatan", "Kalimantan Timur", "Kalimantan Utara", "Sulawesi Utara", "Gorontalo",
                        "Sulawesi Tengah", "Sulawesi Barat", "Sulawesi Selatan", "Sulawesi Tenggara"],
                  9.0: ["Maluku", "Maluku Utara", "Papua", "Papua Barat"]}
COUNTRY_TZ = {"MM": 6.5, "TH": 7.0, "VN": 7.0, "KH": 7.0, "LA": 7.0, "MY": 8.0, "SG": 8.0, "PH": 8.0, "BN": 8.0, "TL": 9.0}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def zone(off: float) -> str:
    return f"UTC+{off:g}"


def stats168(t: np.ndarray) -> dict:
    w = t.reshape(7, 24)
    return dict(peak_over_mean=float(t.max()), min_over_mean=float(t.min()), weekday_over_weekend=float(w[:5].mean() / w[5:].mean()),
                saturday_over_weekday=float(w[5].mean() / w[:5].mean()), sunday_over_weekday=float(w[6].mean() / w[:5].mean()),
                weekday_diurnal_max_over_min=float(w[:5].mean(0).max() / w[:5].mean(0).min()), weekday_peak_local_hour=int(w[:5].mean(0).argmax()))


# ---------------------------------------------------------------- FfE
def ffe_curves(s0: Path) -> dict:
    d = json.loads((s0 / "downloads/08_ffe_profiles/opendata.customization").read_text(encoding="utf-8"))
    return {int(r["internal_id"][0]): np.asarray(r["values"], dtype=float) for r in d["data"]}


def ffe_tests(vec: dict, R: dict) -> tuple[set, str]:
    """Day alignment, holiday days and clock (DST) tests on the file index (hour i = 2017-01-01 00:00 + i h on the unknown file clock)."""
    days = pd.date_range("2017-01-01", periods=365, freq="D")
    v13 = vec[13]; dm = v13.reshape(365, 24).mean(1)
    # 1. day alignment: which labelling offset k puts the two lowest weekday means on Saturday and Sunday?
    al = {}
    for k in range(7):
        dow = (days.dayofweek.to_numpy() + k) % 7
        al[k] = float(pd.Series(dm).groupby(dow).mean().loc[[5, 6]].mean() / pd.Series(dm).groupby(dow).mean().loc[[0, 1, 2, 3, 4]].mean())
    k_best = min(al, key=al.get)
    # 2. holiday days: Mon-Fri days below 0.85 x median of the same weekday within +-28 days (non-specified curve, strongest weekly contrast)
    s = pd.Series(dm, index=days); flagged = []
    for d in days[days.dayofweek < 5]:
        ref = s[(s.index.dayofweek == d.dayofweek) & (abs((s.index - d).days) <= 28) & (s.index != d)]
        r = s[d] / ref.median()
        if r < 0.85:
            flagged.append(dict(date=str(d.date()), weekday=d.day_name(), ratio_to_local_median=float(r), german_holiday_2017=GERMAN_HOLIDAYS_2017.get(str(d.date()), "")))
    H = pd.DataFrame(flagged)
    hol = set(H.date) if len(H) else set()
    # 3. clock test: workday diurnal cycle (each day / its mean), winter (09 Jan - 24 Mar) vs summer (24 Apr - 29 Sep); best lag of summer vs winter
    clk = {}
    for sid in (4, 5, 7, 8, 13):
        x = vec[sid].reshape(365, 24); x = x / x.mean(1, keepdims=True)
        ok = (days.dayofweek < 5) & ~days.strftime("%Y-%m-%d").isin(hol)
        win = x[ok & (days >= "2017-01-09") & (days <= "2017-03-24")].mean(0); summ = x[ok & (days >= "2017-04-24") & (days <= "2017-09-29")].mean(0)
        cc = {lag: float(np.corrcoef(win, np.roll(summ, lag))[0, 1]) for lag in range(-3, 4)}
        best = max(cc, key=cc.get)
        thr = lambda c: float(np.argmax(c > (c.min() + c.max()) / 2))   # first hour above the half range (morning ramp)
        clk[FFE_NAMES[sid]] = dict(best_lag_summer_to_winter_h=int(best), corr=cc, ramp_hour_winter=thr(win), ramp_hour_summer=thr(summ),
                                   max_abs_diff_win_summer=float(np.abs(win - summ).max()))
    lags = sorted({v["best_lag_summer_to_winter_h"] for v in clk.values()})
    verdict = "local_clock_with_DST" if lags == [0] else ("fixed_offset_clock" if lags == [1] else "mixed")
    R["ffe_tests"] = dict(day_alignment=dict(labelling_offset_best=k_best, weekend_over_weekday_by_offset=al,
                                             note="offset 0 = file day 0 is 2017-01-01 (Sunday) as the metadata reference date says"),
                          holiday_days=dict(n=len(H), threshold="Mon-Fri daily mean < 0.85 x median of same weekday within +-28 days (curve 13)",
                                            matched_german_holidays=int((H.german_holiday_2017 != "").sum()) if len(H) else 0),
                          clock=clk, clock_verdict=verdict,
                          clock_note=("lag 0: the workday cycle has the same index hours in winter and in summer -> the file is on the German local clock "
                                      "(CET/CEST) or the regression used local-clock hours; lag +1 would mean a fixed-offset clock (UTC or CET) with local-clock behaviour"))
    return hol, verdict, H


def ffe_template(v: np.ndarray, hol: set, interp: str) -> np.ndarray:
    """168-hour German local-clock week (Monday 00:00 = 0, mean 1) from the 2017 file; holiday days excluded; all weeks averaged (season removed)."""
    t = pd.date_range("2017-01-01", periods=8760, freq="h")
    if interp == "local":            # file index is the German local clock (DST included)
        loc = t
    elif interp == "utc":            # file index is UTC -> convert to Europe/Berlin
        loc = t.tz_localize("UTC").tz_convert("Europe/Berlin").tz_localize(None)
    elif interp == "cet":            # file index is CET (UTC+1) all year
        loc = t.tz_localize("Etc/GMT-1").tz_convert("Europe/Berlin").tz_localize(None)
    else:
        raise ValueError(interp)
    keep = ~loc.strftime("%Y-%m-%d").isin(hol)
    s = pd.Series(v[keep], index=pd.MultiIndex.from_arrays([loc.dayofweek[keep], loc.hour[keep]]))
    w = s.groupby(level=[0, 1]).mean().reindex(pd.MultiIndex.from_product([range(7), range(24)])).to_numpy()
    if np.isnan(w).any():
        raise ValueError("FfE template incomplete")
    return w / w.mean()


# ---------------------------------------------------------------- NREL
def nrel_templates(s0: Path, R: dict) -> tuple[dict, pd.DataFrame]:
    ds = pads.dataset(s0 / "extracted/09_nrel_heat/heat_loadshapes_20190927/all_heat_loadshapes_20190927", partitioning="hive")
    t = ds.to_table(columns=["month", "dayofweek", "hour", "emp_size", "fraction_annual_energy", "hours_type", "NAICS"]).to_pandas()
    t = t[t.hours_type == "mean"].copy(); t["naics"] = t.NAICS.astype(str)
    dim = pd.Series([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31], index=range(1, 13), dtype=float)
    shapes = {}
    for (n, es), g in t.groupby(["naics", "emp_size"]):
        g = g.sort_values(["month", "dayofweek", "hour"])
        if len(g) != 2016:
            continue
        x = g.fraction_annual_energy.to_numpy().reshape(12, 168)
        x = x / x.mean()
        wk = (x * dim.to_numpy()[:, None]).sum(0) / dim.sum()      # day-weighted annual mean week: month component removed
        shapes[(n, es)] = wk / wk.mean()
    out, rows = {}, []
    for name, pref in NREL_GROUPS.items():
        ks = [k for k in shapes if any(k[0].startswith(p) for p in pref)]
        if not ks:
            raise ValueError("no NREL shape for " + name)
        w = np.mean([shapes[k] for k in ks], axis=0); out[name] = w / w.mean()
        rows.append(dict(shape=name, naics_prefixes="|".join(pref), naics_codes=len({k[0] for k in ks}), shapes_averaged=len(ks)))
    # all manufacturing: equal weight per NAICS3 group present
    n3 = {}
    for k, v in shapes.items():
        n3.setdefault(k[0][:3], []).append(v)
    allm = np.mean([np.mean(v, axis=0) for v in n3.values()], axis=0); out["NREL_ALL"] = allm / allm.mean()
    rows.append(dict(shape="NREL_ALL", naics_prefixes="all NAICS3 (equal weight)", naics_codes=len({k[0] for k in shapes}), shapes_averaged=len(shapes)))
    R["nrel"] = dict(hours_type="mean", weighting="equal weight over NAICS x employment-size shapes in a group (no energy weights on disk)",
                     month_removal="day-weighted mean of the 12 monthly typical weeks", dayofweek="0 = Monday (VERIFIED: weekday_single schedules are lower on 5, 6)",
                     shapes=len(shapes), naics3_groups=len(n3))
    return out, pd.DataFrame(rows)


# ---------------------------------------------------------------- mapping
def mapping() -> pd.DataFrame:
    """v4 subsector key x energy type -> shapes. main / source (sensitivity S1) and the reason. PROPOSED."""
    C = "continuous process"
    rows = [
        # key, aliases, etype, main, source, continuous, reason
        ("steel", "v3 steel; UNSD iron and steel; GEM steel (BF-BOF, DRI-EAF, scrap EAF)", "elec", "FLAT", "FFE_STEEL_PAPER", 1,
         C + "; FfE itself assumes a near-constant profile for iron & steel (metadata; peak/mean 1.035). EAF melt shops can shift to off-peak under TOU tariffs (INFERENCE, no ASEAN data)"),
        ("steel", "", "heat", "FLAT", "NREL_3311", 1, C + "; NREL iron & steel mills shape is near flat"),
        ("cement", "v3 cement; GEM cement; clinker kilns + grinding", "elec", "FLAT", "FFE_NMM", 1,
         "kiln line runs 24/7; FfE non-metallic minerals is a sample of mainly small processes (metadata), not kiln plants; grinding may move off-peak (INFERENCE)"),
        ("cement", "", "heat", "FLAT", "NREL_327310", 1, C + " (rotary kiln)"),
        ("ammonia", "v3 ammonia; GEM chemicals ammonia; PyPSA-Eur Ammonia", "elec", "FLAT", "FFE_NONSPEC", 1, C + "; FfE has no chemicals curve (S0 suggestion: FfE 13 as sensitivity)"),
        ("ammonia", "", "heat", "FLAT", "NREL_325311", 1, C),
        ("nickel", "v3 nonferrous_nickel; RKEF / NPI / ferronickel / matte", "elec", "FLAT", "FLAT", 1,
         "electric furnaces (RKEF) and smelters run continuously; FfE has no non-ferrous curve -> no source shape"),
        ("nickel", "", "heat", "FLAT", "NREL_331410", 1, C),
        ("aluminium_primary", "v3 nonferrous_aluminium_primary; Hall-Heroult; PyPSA-Eur Aluminium - primary production", "elec", "FLAT", "FLAT", 1,
         "potlines cannot be cycled without freezing the bath; FfE has no non-ferrous curve"),
        ("aluminium_primary", "", "heat", "FLAT", "NREL_3313", 1, C),
        ("alumina", "v3 nonferrous_alumina; Bayer; PyPSA-Eur Alumina production", "elec", "FLAT", "FLAT", 1, C + " (Bayer digestion / calcination)"),
        ("alumina", "", "heat", "FLAT", "NREL_3313", 1, C),
        ("copper", "v3 nonferrous_copper; smelting + refining", "elec", "FLAT", "FLAT", 1, C),
        ("copper", "", "heat", "FLAT", "NREL_331410", 1, C),
        ("pulp_paper", "SFI pulp & paper; PyPSA-Eur Pulp production, Paper production; UNSD paper pulp and print", "elec", "FLAT", "FFE_STEEL_PAPER", 1,
         C + "; FfE assumes near-constant for paper, pulp & print (metadata)"),
        ("pulp_paper", "", "heat", "FLAT", "NREL_322_MILLS", 1, C + "; NREL pulp / paper mills near flat"),
        ("printing", "PyPSA-Eur Printing and media reproduction (UNSD paper pulp and print)", "elec", "FLAT", "FFE_STEEL_PAPER", 0,
         "follows the FfE branch 'Paper, pulp and print' (near-constant); small"),
        ("printing", "", "heat", "FLAT", "NREL_322", 0, "as pulp_paper"),
        ("ethylene", "SFI ethylene / steam crackers; PyPSA-Eur HVC; GEM chemicals olefins", "elec", "FLAT", "FFE_NONSPEC", 1, C + " (steam cracker)"),
        ("ethylene", "", "heat", "FLAT", "NREL_325110", 1, C),
        ("methanol", "PyPSA-Eur Methanol; GEM chemicals methanol", "elec", "FLAT", "FFE_NONSPEC", 1, C),
        ("methanol", "", "heat", "FLAT", "NREL_325", 1, C),
        ("chlorine", "PyPSA-Eur Chlorine (membrane electrolysis)", "elec", "FLAT", "FFE_NONSPEC", 1, C + " (electrolysis)"),
        ("chlorine", "", "heat", "FLAT", "NREL_325", 1, C),
        ("chemicals_other", "PyPSA-Eur Other chemicals; v4 chemicals (MY GEM chemicals, aromatics)", "elec", "FLAT", "FFE_NONSPEC", 1,
         "mostly continuous plants; NREL chemicals shape 1.03 peak/mean; FfE has no chemicals curve"),
        ("chemicals_other", "", "heat", "FLAT", "NREL_325", 1, "NREL 325 is near flat"),
        ("pharma", "PyPSA-Eur Pharmaceutical products etc.", "elec", "FLAT", "FFE_NONSPEC", 1, "kept with chemicals (S0 6.3); batch plants -> source shape as sensitivity"),
        ("pharma", "", "heat", "FLAT", "NREL_3254", 1, "kept with chemicals"),
        ("glass_lime", "PyPSA-Eur Glass production; lime kilns (v4 non-metallic minerals other)", "elec", "FLAT", "FFE_NMM", 1, C + " (glass furnaces, lime kilns)"),
        ("glass_lime", "", "heat", "FLAT", "NREL_3272", 1, C),
        ("aluminium_secondary", "PyPSA-Eur Aluminium - secondary production", "elec", "FLAT", "FFE_NONSPEC", 1, "remelting furnaces kept hot; small"),
        ("aluminium_secondary", "", "heat", "FLAT", "NREL_331", 1, "small"),
        ("nonferrous_other", "PyPSA-Eur Other non-ferrous metals", "elec", "FLAT", "FFE_NONSPEC", 1, "smelting; small"),
        ("nonferrous_other", "", "heat", "FLAT", "NREL_331", 1, "small"),
        ("ceramics_nmm", "PyPSA-Eur Ceramics & other NMM (UNSD non-metallic minerals, dispersed)", "elec", "FFE_NMM", "FFE_NMM", 0,
         "bricks, tiles, ceramics: the small-process sample of FfE non-metallic minerals fits"),
        ("ceramics_nmm", "", "heat", "NREL_327", "NREL_327", 0, "NREL non-metallic minerals"),
        ("food", "PyPSA-Eur Food, beverages and tobacco; UNSD food and tobacco", "elec", "FFE_FOOD", "FFE_FOOD", 0, "FfE food and tobacco"),
        ("food", "", "heat", "NREL_311", "NREL_311", 0, "NREL food + beverages (311, 312)"),
        ("textiles", "PyPSA-Eur Textiles and leather; UNSD textile and leather", "elec", "FFE_NONSPEC", "FFE_NONSPEC", 0, "FfE uses the non-specified curve for textiles"),
        ("textiles", "", "heat", "NREL_313_316", "NREL_313_316", 0, "NREL textiles, apparel, leather"),
        ("wood", "PyPSA-Eur Wood and wood products; UNSD wood and wood products", "elec", "FFE_NONSPEC", "FFE_NONSPEC", 0, "FfE uses the non-specified curve for wood"),
        ("wood", "", "heat", "NREL_321", "NREL_321", 0, "NREL wood products"),
        ("machinery", "PyPSA-Eur Machinery equipment; UNSD machinery", "elec", "FFE_TRANSPORT_MACH", "FFE_TRANSPORT_MACH", 0, "FfE machinery (= transport equipment)"),
        ("machinery", "", "heat", "NREL_333", "NREL_333", 0, "NREL machinery"),
        ("transport_equipment", "PyPSA-Eur Transport equipment; UNSD transport equipment", "elec", "FFE_TRANSPORT_MACH", "FFE_TRANSPORT_MACH", 0, "FfE transport equipment"),
        ("transport_equipment", "", "heat", "NREL_336", "NREL_336", 0, "NREL transport equipment"),
        ("mining", "UNSD mining and quarrying", "elec", "FFE_MINING", "FFE_MINING", 0, "FfE mining and quarrying (peaky: 2.53 peak/mean)"),
        ("mining", "", "heat", "FLAT", "FLAT", 0, "NREL covers manufacturing only; mining fuel is mostly diesel on fuel buses"),
        ("construction", "UNSD construction", "elec", "FFE_NONSPEC", "FFE_NONSPEC", 0, "FfE uses the non-specified curve for construction"),
        ("construction", "", "heat", "FLAT", "FLAT", 0, "NREL covers manufacturing only; construction fuel is mostly diesel"),
        ("other", "v3 / v4 'other' bucket (UNSD industries not elsewhere specified and unsplit rows)", "elec", "MIX_DISPERSED", "MIX_DISPERSED", 0,
         "residual of unknown composition: energy-weighted mix of the main shapes of the ASEAN dispersed rows (v3 2050 composition); flat and FfE 13 as sensitivities"),
        ("other", "", "heat", "MIX_DISPERSED", "MIX_DISPERSED", 0, "as electricity, with the NREL heat shapes of the dispersed rows"),
    ]
    M = pd.DataFrame(rows, columns=["subsector", "aliases", "etype", "shape_main", "shape_source", "continuous", "reason"])
    M["aliases"] = M.groupby("subsector").aliases.transform("first")
    M["shape_other_flat"] = np.where(M.subsector == "other", "FLAT", M.shape_main)
    M["shape_other_ffe13"] = np.where(M.subsector == "other", np.where(M.etype == "elec", "FFE_NONSPEC", "NREL_ALL"), M.shape_main)
    M["grade"] = np.where(M.shape_main == "MIX_DISPERSED", "D", "C")   # C: German / US shapes transferred, or flat assumption; D: constructed mix
    M["status"] = "PROPOSED"
    return M


SECTOR_KEY = {"Ammonia": "ammonia", "Chlorine": "chlorine", "HVC": "ethylene", "Methanol": "methanol", "Other chemicals": "chemicals_other",
              "Pharmaceutical products etc.": "pharma", "Food, beverages and tobacco": "food", "Machinery equipment": "machinery", "Transport equipment": "transport_equipment",
              "Textiles and leather": "textiles", "Wood and wood products": "wood", "Paper production": "pulp_paper", "Pulp production": "pulp_paper",
              "Printing and media reproduction": "printing", "Alumina production": "alumina", "Aluminium - primary production": "aluminium_primary",
              "Aluminium - secondary production": "aluminium_secondary", "Other non-ferrous metals": "nonferrous_other", "Ceramics & other NMM": "ceramics_nmm",
              "Glass production": "glass_lime"}


def mix_weights(s0: Path) -> pd.Series:
    D = pd.read_csv(s0 / "evidence/V3_DISPERSED_BY_UNSD_ROW.csv")
    D["key"] = D.pypsa_eur_sector.map(SECTOR_KEY)
    if D.key.isna().any():
        raise ValueError("unmapped dispersed sector " + str(D[D.key.isna()].pypsa_eur_sector.unique()))
    w = D.groupby("key").twh_2050.sum()
    return w / w.sum()


# ---------------------------------------------------------------- model clock
U = pd.date_range("2013-01-01", periods=8760, freq="h")   # UTC hour starts, tz-naive like the network snapshots


def to_model(T: np.ndarray, off: float, shift: float = 0.0, hol_dates: set | None = None) -> np.ndarray:
    """Hourly model curve for nodes at UTC+off: value at UTC hour u = mean of the local week over local [u+off-shift, u+off-shift+1)
    (linear interpolation for half-hour offsets, as v3_ev.ev_series). Holiday local dates use the Sunday row of the week. Mean 1."""
    x = (U.dayofweek.to_numpy() * 24.0 + U.hour.to_numpy() + off - shift) % 168.0
    if hol_dates:
        ld = (U + pd.to_timedelta(off - shift, unit="h")).strftime("%Y-%m-%d")
        h = np.isin(ld, list(hol_dates))
        x = np.where(h, 6 * 24.0 + (x % 24.0), x)
    i = np.floor(x).astype(int); f = x - i
    y = (1.0 - f) * T[i % 168] + f * T[(i + 1) % 168]
    return y / y.mean()


def sat_work(T: np.ndarray) -> np.ndarray:
    w = T.reshape(7, 24).copy(); w[5] = w[:5].mean(0)
    w = w.ravel(); return w / w.mean()


# ---------------------------------------------------------------- time zones
def tz_nodes(repo: Path, network: Path, out: Path, R: dict) -> pd.DataFrame:
    import xarray as xr
    tz = pd.read_csv(repo / "research_inputs/transport_v3/EV_NODE_TIMEZONE_V3.csv")
    idp = pd.read_csv(repo / "research/06_scope_redesign/p1_v3_20261102/evidence/ID_NODE_TIMEZONE_PROPOSAL.csv")
    ov = pd.read_csv(repo / "research_inputs/industry_v3/ADM1_NODE_OVERLAP_V3.csv")
    ds = xr.open_dataset(network)
    B = pd.DataFrame({c: ds[f"buses_{c}"].values for c in ("x", "y", "country", "carrier")}, index=[str(i) for i in ds["buses_i"].values])
    L = pd.DataFrame({c: ds[f"loads_{c}"].values for c in ("bus", "carrier", "p_set")}, index=[str(i) for i in ds["loads_i"].values])
    ie = L[L.carrier == "industry electricity"].groupby("bus").p_set.sum() * 8760 / 1e6
    p2tz = {p: o for o, ps in ID_PROVINCE_TZ.items() for p in ps}
    unknown = sorted(set(ov[ov.country == "ID"].name) - set(p2tz))
    rows = []
    for _, r in tz.iterrows():
        n = r.node; c = r.country
        rec = dict(node=n, country=c, utc_offset_h=float(r.utc_offset_h), basis_v3=r.basis, x=float(B.at[n, "x"]), y=float(B.at[n, "y"]),
                   solar_time_offset_h=float(B.at[n, "x"]) / 15.0, industry_electricity_2050_twh_v3=float(ie.get(n, 0.0)))
        if c == "ID":
            prov = idp.set_index("Bus").at[n, "NAME_1"]
            rec.update(province=prov, legal_tz_of_province=p2tz.get(prov, np.nan))
            o = ov[(ov.country == "ID") & (ov.node == n)].copy(); o["tz"] = o.name.map(p2tz)
            fr = o.groupby("tz").frac_of_node.sum(); tot = fr.sum()
            rec.update(area_share_in_assigned_tz=float(fr.get(rec["utc_offset_h"], 0.0) / tot) if tot > 0 else np.nan,
                       area_shares_by_tz=";".join(f"{k:g}:{v / tot:.3f}" for k, v in fr.items()) if tot > 0 else "",
                       provinces_overlapping=";".join(f"{a}:{b:.3f}" for a, b in o.sort_values("frac_of_node", ascending=False)[["name", "frac_of_node"]].itertuples(index=False)))
            rec["rule"] = "ID: province (GADM 4.1 NAME_1) of the node representative point -> legal zone WIB +7 / WITA +8 / WIT +9 (decision 165)"
            rec["check"] = "PASS" if rec["legal_tz_of_province"] == rec["utc_offset_h"] else "FAIL"
        else:
            rec.update(province="", legal_tz_of_province=COUNTRY_TZ[c], area_share_in_assigned_tz=1.0, area_shares_by_tz="", provinces_overlapping="",
                       rule="single national zone (decision 165)", check="PASS" if COUNTRY_TZ[c] == rec["utc_offset_h"] else "FAIL")
        rows.append(rec)
    T = pd.DataFrame(rows)
    T["flag_multi_tz_area"] = (T.area_share_in_assigned_tz < 0.95)
    T.to_csv(out / "TIMEZONE_NODES.csv", index=False, float_format="%.6f")
    f = T[T.flag_multi_tz_area]
    R["timezones"] = dict(nodes=len(T), by_offset={f"{c}@{o:g}": int(n) for (c, o), n in T.groupby(["country", "utc_offset_h"]).size().items()},
                          checks_failed=int((T.check != "PASS").sum()), id_provinces_unmapped=unknown,
                          id_nodes_multi_tz_area=len(f), id_multi_tz_industry_elec_twh=float(f.industry_electricity_2050_twh_v3.sum()),
                          id_multi_tz_nodes=f[["node", "utc_offset_h", "area_share_in_assigned_tz", "area_shares_by_tz", "industry_electricity_2050_twh_v3"]].to_dict("records"))
    return T


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--s0", type=Path, required=True); ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--network", type=Path, required=True); ap.add_argument("--out", type=Path, required=True); a = ap.parse_args()
    ev = a.out / "evidence"; ev.mkdir(parents=True, exist_ok=True)
    R = dict(script="scripts/g5_profiles.py", inputs={})
    for p in (a.s0 / "downloads/08_ffe_profiles/opendata.customization", a.s0 / "evidence/V3_DISPERSED_BY_UNSD_ROW.csv",
              a.repo / "research_inputs/transport_v3/EV_NODE_TIMEZONE_V3.csv", a.repo / "research/06_scope_redesign/p1_v3_20261102/evidence/ID_NODE_TIMEZONE_PROPOSAL.csv",
              a.repo / "research_inputs/industry_v3/ADM1_NODE_OVERLAP_V3.csv", a.network):
        R["inputs"][str(p)] = sha256(p)
    # FfE
    vec = ffe_curves(a.s0)
    hol, verdict, H = ffe_tests(vec, R)
    H.to_csv(ev / "G5_FFE_HOLIDAY_DAYS.csv", index=False, float_format="%.4f")
    # the clock test is not conclusive unless every curve shows lag +1; main = German local clock (S0 6.4 proposal, same as the RAMP EV curves), UTC as sensitivity S4
    main_interp = "cet" if verdict == "fixed_offset_clock" else "local"
    alt_interp = "utc"
    R["ffe_interpretation"] = dict(main=main_interp, sensitivity=alt_interp)
    shapes, shapes_alt = {"FLAT": np.ones(168)}, {}
    seas = []
    for name, sid in FFE_SHAPES.items():
        shapes[name] = ffe_template(vec[sid], hol, main_interp)
        shapes_alt[name] = ffe_template(vec[sid], hol, alt_interp)
        mm = pd.Series(vec[sid]).groupby(pd.date_range("2017-01-01", periods=8760, freq="h").month).mean()
        seas.append(dict(shape=name, removed_month_max_over_min=float(mm.max() / mm.min())))
    nrel, NR = nrel_templates(a.s0, R)
    shapes.update(nrel)
    # mixed shape for 'other'
    M = mapping()
    w = mix_weights(a.s0)
    for et in ("elec", "heat"):
        mm_ = M[M.etype == et].set_index("subsector").shape_main
        t = sum(w[k] * shapes[mm_[k]] for k in w.index); shapes[f"MIX_DISPERSED_{et}"] = t / t.mean()
    R["mix_dispersed_weights"] = w.round(6).to_dict()
    R["mix_dispersed_note"] = "weights = v3 2050 dispersed energy (all carriers) by PyPSA-Eur sector, all ASEAN countries in V3_DISPERSED_BY_UNSD_ROW.csv; used for 'other'"
    def shp(name, et, alt=False):
        if name == "MIX_DISPERSED":
            return shapes[f"MIX_DISPERSED_{et}"]
        if alt and name in shapes_alt:
            return shapes_alt[name]
        return shapes[name]
    # shape stats + 168 templates
    st = []
    for k, t in shapes.items():
        st.append(dict(shape=k, source=("FfE 59 curve %d" % FFE_SHAPES[k]) if k in FFE_SHAPES else ("NREL" if k.startswith("NREL") else ("mix" if k.startswith("MIX") else "flat")), **stats168(t)))
    for k, t in shapes_alt.items():
        st.append(dict(shape=k + "@utc", source="FfE 59 curve %d read as UTC" % FFE_SHAPES[k], **stats168(t)))
    S = pd.DataFrame(st).merge(pd.DataFrame(seas), on="shape", how="left").merge(NR, on="shape", how="left")
    S.to_csv(ev / "G5_SHAPE_STATS.csv", index=False, float_format="%.5f")
    W = pd.DataFrame({k: v for k, v in shapes.items()}); W.insert(0, "local_hour", np.tile(np.arange(24), 7)); W.insert(0, "local_weekday_mon0", np.repeat(np.arange(7), 24))
    for k, v in shapes_alt.items():
        W[k + "@utc"] = v
    W.to_csv(a.out / "WEEK_TEMPLATES_168.csv", index=False, float_format="%.8f")
    # variants -> curves
    variants = {
        "MAIN": dict(col="shape_main"), "S1_SOURCE": dict(col="shape_source"), "S2_OTHER_FLAT": dict(col="shape_other_flat"),
        "S3_OTHER_FFE13": dict(col="shape_other_ffe13"), "S4_FFE_CLOCK_UTC": dict(col="shape_main", alt=True), "S5_SAT_WORKDAY": dict(col="shape_main", sat=True),
        "S6_SHIFT_P1": dict(col="shape_main", shift=1.0), "S6_SHIFT_M1": dict(col="shape_main", shift=-1.0), "S7_HOLIDAYS": dict(col="shape_main", hol=True),
        "S8_UPPER": dict(col="shape_source_upper", hol=True),
    }
    M["shape_source_upper"] = np.where(M.subsector == "other", M.shape_other_ffe13, M.shape_source)
    curves, index, seen = {}, [], {}
    zones_hol = [(c, COUNTRY_TZ[c]) for c in COUNTRY_TZ] + [("ID", 7.0), ("ID", 8.0), ("ID", 9.0)]
    for vn, spec in variants.items():
        for _, m in M.iterrows():
            base = shp(m[spec["col"]], m.etype, spec.get("alt", False))
            if spec.get("sat"):
                base = sat_work(base)
            zl = [(c, o) for c, o in zones_hol] if spec.get("hol") else [("", o) for o in ZONES]
            for c, o in zl:
                hd = {d for d, _ in HOLIDAYS_2013[c]} if c else None
                y = to_model(base, o, spec.get("shift", 0.0), hd)
                key = hashlib.sha256(np.round(y, 12).tobytes()).hexdigest()[:16]
                if key not in seen:
                    seen[key] = f"c{len(seen):04d}"; curves[seen[key]] = y
                index.append(dict(variant=vn, subsector=m.subsector, etype=m.etype, zone=(f"{c}@" if c else "") + zone(o), shape=m[spec["col"]], curve_id=seen[key]))
    I = pd.DataFrame(index)
    I.to_csv(a.out / "PROFILE_INDEX.csv", index=False)
    P = pd.DataFrame(curves, index=pd.DatetimeIndex(U, name="snapshot_utc"))
    P = P[sorted(P.columns)]
    pq.write_table(pa.Table.from_pandas(P), a.out / "PROFILES_8760.parquet", compression="zstd")
    chk = dict(curves=int(P.shape[1]), rows=int(P.shape[0]), max_abs_mean_minus_1=float((P.mean() - 1).abs().max()), min_value=float(P.min().min()),
               max_value=float(P.max().max()), index_rows=len(I), variants=list(variants))
    R["profiles"] = chk
    M.to_csv(a.out / "PROFILE_MAPPING.csv", index=False)
    tz_nodes(a.repo, a.network, a.out, R)
    R["holidays_2013_design"] = {c: [d for d, _ in v] for c, v in HOLIDAYS_2013.items()}
    (ev / "G5_PROFILES.json").write_text(json.dumps(R, indent=1, default=str, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: R[k] for k in ("ffe_tests", "ffe_interpretation", "profiles", "timezones")}, indent=1, default=str)[:6000])


if __name__ == "__main__":
    main()
