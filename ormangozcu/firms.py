"""NASA FIRMS VIIRS S-NPP 375 m standard-processing detections for Türkiye.

Needs a free FIRMS MAP_KEY in the environment variable FIRMS_MAP_KEY. Raw responses
are cached per 5-day chunk under data/raw/firms, so an interrupted download resumes.
"""
import csv
import datetime as dt
import io
import os
import time
import urllib.request
from pathlib import Path

from .grid import cell_of

API = "https://firms.modaps.eosdis.nasa.gov/api/country/csv/{key}/{source}/TUR/{days}/{date}"
SOURCE = "VIIRS_SNPP_SP"
CHUNK_DAYS = 5


def season_chunks(year, start=(5, 1), end=(10, 31)):
    d, last = dt.date(year, *start), dt.date(year, *end)
    while d <= last:
        n = min(CHUNK_DAYS, (last - d).days + 1)
        yield d, n
        d += dt.timedelta(days=n)


def download(years, raw_dir="data/raw/firms", key=None, pause=0.5, opener=urllib.request.urlopen):
    key = key or os.environ.get("FIRMS_MAP_KEY")
    if not key:
        raise RuntimeError("Set FIRMS_MAP_KEY to your FIRMS MAP_KEY (do not paste it into code or chat)")
    raw = Path(raw_dir)
    raw.mkdir(parents=True, exist_ok=True)
    fetched = 0
    for year in years:
        for start, n in season_chunks(year):
            path = raw / ("%s_%s_%d.csv" % (SOURCE, start.isoformat(), n))
            if path.exists():
                continue
            url = API.format(key=key, source=SOURCE, days=n, date=start.isoformat())
            for attempt in range(5):
                try:
                    with opener(url, timeout=120) as resp:
                        text = resp.read().decode("utf-8")
                    break
                except Exception:  # network hiccup or rate limit: back off and retry
                    if attempt == 4:
                        raise
                    time.sleep(30 * (attempt + 1))
            if not text.startswith("country_id") and not text.startswith("latitude"):
                raise RuntimeError("Unexpected FIRMS reply for %s: %s" % (start, text[:200]))
            path.write_text(text, encoding="utf-8")
            fetched += 1
            time.sleep(pause)
    print("FIRMS: fetched %d new chunks into %s" % (fetched, raw))


def keep(row):
    """Vegetation-fire detections only: drop low confidence and non-vegetation types."""
    if str(row.get("confidence", "")).strip().lower() in ("l", "low"):
        return False
    t = str(row.get("type", "0")).strip()
    return t in ("", "0")


def daily_cell_counts(raw_dir="data/raw/firms"):
    """{(date, cell): detections} from all cached chunks."""
    counts = {}
    for path in sorted(Path(raw_dir).glob("*.csv")):
        for row in csv.DictReader(io.StringIO(path.read_text(encoding="utf-8"))):
            if not keep(row):
                continue
            key = (row["acq_date"], cell_of(float(row["latitude"]), float(row["longitude"])))
            counts[key] = counts.get(key, 0) + 1
    return counts
