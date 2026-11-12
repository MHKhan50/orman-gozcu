"""Daily ERA5 weather per cell centre from the Open-Meteo historical archive (no key needed).

Open-Meteo serves ERA5 reanalysis; models=era5 asks for ERA5 itself rather than a blend.
Responses are cached per batch and year so the download can stop and resume.
"""
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

URL = "https://archive-api.open-meteo.com/v1/archive"
VARIABLES = ("temperature_2m_max", "precipitation_sum", "wind_speed_10m_max", "et0_fao_evapotranspiration")
BATCH = 20


def download(cells_with_centres, years, raw_dir="data/raw/weather", opener=urllib.request.urlopen, pause=2.0):
    raw = Path(raw_dir)
    raw.mkdir(parents=True, exist_ok=True)
    items = sorted(cells_with_centres.items())
    days = 214  # 1 April to 31 October
    print("About %d Open-Meteo call units in total (free tier: 10,000 a day, 5,000 an hour); "
          "if the allowance runs out, run the same command later and it resumes."
          % (len(items) * len(list(years)) * (days / 14)))
    fetched = 0
    for year in years:
        for b in range(0, len(items), BATCH):
            batch = items[b:b + BATCH]
            path = raw / ("%d_batch%03d.json" % (year, b // BATCH))
            if path.exists():
                continue
            query = urllib.parse.urlencode({
                "latitude": ",".join("%.3f" % c[1][0] for c in batch),
                "longitude": ",".join("%.3f" % c[1][1] for c in batch),
                "start_date": "%d-04-01" % year, "end_date": "%d-10-31" % year,
                "daily": ",".join(VARIABLES), "models": "era5", "timezone": "GMT"})
            for attempt in range(6):
                try:
                    with opener(URL + "?" + query, timeout=180) as resp:
                        data = json.loads(resp.read().decode("utf-8"))
                    break
                except Exception:  # 429 when the hourly or daily allowance is used up
                    if attempt == 5:
                        raise
                    time.sleep(60 * (attempt + 1))
            if isinstance(data, dict):
                data = [data]
            out = {cell: d["daily"] for (cell, _), d in zip(batch, data)}
            path.write_text(json.dumps(out), encoding="utf-8")
            fetched += 1
            time.sleep(pause)
    print("Weather: fetched %d new batches into %s" % (fetched, raw))


def load(raw_dir="data/raw/weather"):
    """{(date, cell): {variable: value}}"""
    table = {}
    for path in sorted(Path(raw_dir).glob("*.json")):
        for cell, daily in json.loads(path.read_text(encoding="utf-8")).items():
            for i, day in enumerate(daily["time"]):
                table[(day, cell)] = {v: daily[v][i] for v in VARIABLES}
    return table
