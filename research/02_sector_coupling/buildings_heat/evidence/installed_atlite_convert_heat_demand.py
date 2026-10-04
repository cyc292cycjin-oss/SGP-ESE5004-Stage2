def convert_heat_demand(ds, threshold, a, constant, hour_shift):
    # Temperature is in Kelvin; take daily average
    T = ds["temperature"]
    T = T.assign_coords(
        time=(T.coords["time"] + np.timedelta64(dt.timedelta(hours=hour_shift)))
    )

    T = T.resample(time="1D").mean(dim="time")
    threshold += 273.15
    heat_demand = a * (threshold - T)

    heat_demand = heat_demand.clip(min=0.0)

    return (constant + heat_demand).rename("heat_demand")
