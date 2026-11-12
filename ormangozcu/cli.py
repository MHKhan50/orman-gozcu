import argparse
import json
from pathlib import Path

import pandas as pd

from . import firms, weather
from .dataset import TEST_YEARS, TRAIN_YEARS, VAL_YEARS, add_history, build, fire_prone_cells
from .experiment import run
from .grid import block_centre, weather_block

YEARS = TRAIN_YEARS + VAL_YEARS + TEST_YEARS


def main(argv=None):
    ap = argparse.ArgumentParser(prog="ormangozcu", description="OrmanGözcü: next-day fire risk benchmark")
    sub = ap.add_subparsers(dest="command", required=True)
    sub.add_parser("download-fires", help="FIRMS VIIRS detections (needs FIRMS_MAP_KEY)")
    sub.add_parser("download-weather", help="ERA5 daily weather for fire-prone cells (Open-Meteo)")
    sub.add_parser("build", help="build the prediction table")
    r = sub.add_parser("run", help="run the experiments")
    r.add_argument("--out", default="results")
    args = ap.parse_args(argv)

    if args.command == "download-fires":
        firms.download(YEARS)
        return
    counts = firms.daily_cell_counts()
    if not counts:
        raise SystemExit("No FIRMS data found; run `python -m ormangozcu.cli download-fires` first")
    cells = fire_prone_cells(counts)
    if args.command == "download-weather":
        blocks = sorted({weather_block(c) for c in cells})
        print("%d fire-prone cells in %d one-degree weather blocks" % (len(cells), len(blocks)))
        weather.download({b: block_centre(b) for b in blocks}, YEARS)
        return
    table = Path("data/processed/table.csv.gz")
    if args.command == "build":
        df = add_history(build(counts, weather.load(), cells, YEARS))
        table.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(table, index=False)
        missing = df[["tmax", "precip", "wind_max", "et0"]].isna().mean().round(4).to_dict()
        print("Built %d rows for %d cells; share of missing weather: %s" % (len(df), len(cells), missing))
        return
    df = pd.read_csv(table)
    info = {"fires": "NASA FIRMS %s, area %s, inside the Türkiye border, May-October" % (firms.SOURCE, firms.AREA),
            "weather": "ERA5 daily via Open-Meteo archive: " + ", ".join(weather.VARIABLES),
            "cell_degrees": 0.5, "weather_block_degrees": 1.0}
    print(run(df, args.out, info).to_string(index=False))
    print("Wrote %s/tables.md" % args.out)


if __name__ == "__main__":
    main()
