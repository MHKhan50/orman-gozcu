"""Small made-up fire and weather records for tests only. Not real data."""
import datetime as dt
import random

from ormangozcu.grid import centre, weather_block


def synthetic(cells=("r10_c5", "r10_c6", "r8_c20", "r8_c21", "r6_c30", "r6_c31"),
              years=range(2016, 2025), seed=7):
    rng = random.Random(seed)
    counts, weather = {}, {}
    for y in years:
        d = dt.date(y, 4, 1)
        while d <= dt.date(y, 10, 31):
            for c in cells:
                hot = 20 + 12 * rng.random()
                rain = 0.0 if rng.random() < 0.8 else 8 * rng.random()
                weather[(d.isoformat(), weather_block(c))] = {"temperature_2m_max": hot, "precipitation_sum": rain,
                                               "wind_speed_10m_max": 10 + 20 * rng.random(),
                                               "et0_fao_evapotranspiration": hot / 5}
                prev = counts.get(((d - dt.timedelta(days=1)).isoformat(), c), 0)
                p = 0.03 + 0.25 * (hot > 28) * (rain == 0) + 0.4 * (prev > 0)
                if rng.random() < p:
                    counts[(d.isoformat(), c)] = rng.randint(1, 5)
            d += dt.timedelta(days=1)
    return counts, weather, list(cells)


def firms_csv(rows):
    head = "country_id,latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_ti5,frp,daynight,type\n"
    return head + "".join("TUR,%.3f,%.3f,330,0.4,0.4,%s,1100,N,VIIRS,%s,2,290,5,D,%s\n" % r for r in rows)


def point_in(cell):
    return centre(cell)
