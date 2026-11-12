# OrmanGözcü

*A next-day forest-fire risk benchmark for Türkiye*

In Turkish forests, lookouts watch for the first smoke from fire towers (*yangın gözetleme kulesi*). OrmanGözcü ("forest lookout") asks a related question with satellite data: given today's fire detections and weather, which areas are most likely to show a fire detection tomorrow, and how often would a warning be a false alarm or a miss?

## Research questions

1. Do weather and recent fire signals rank tomorrow's fire cells better than a historical-frequency baseline?
2. Does a model trained in one part of Türkiye stay reliable in another?
3. Does a threshold set on one season keep a stable balance of false alarms and missed fires in later seasons?

## Data

| Source | Use |
|---|---|
| NASA FIRMS, VIIRS S-NPP 375 m standard processing | daily fire detections, May to October |
| ERA5 reanalysis via the Open-Meteo archive | daily maximum temperature, precipitation, maximum wind, reference evapotranspiration |

Satellite hotspots are detections, not mapped fires. Train 2016-2019, validate 2020, test 2021-2024. Full design in `docs/PROTOCOL.md`; limits in `docs/LIMITATIONS.md`.

## Results

Not filled in yet. They come from the commands below and are written to `results/`.

## Run it

Python 3.9 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tests -v
```

A free FIRMS MAP_KEY is needed for the fire data (request it at https://firms.modaps.eosdis.nasa.gov/api/map_key/). Put it in the environment, never in code:

```bash
read -s FIRMS_MAP_KEY && export FIRMS_MAP_KEY
python -m ormangozcu.cli download-fires
python -m ormangozcu.cli download-weather
python -m ormangozcu.cli build
python -m ormangozcu.cli run
```

Both downloads cache every piece under `data/raw/` and resume if stopped. The weather download prints how many Open-Meteo call units it needs; the free tier allows 10,000 a day, so it may take more than one day. Run the same command again and it continues.

Outputs: `results/tables.md`, `metrics.csv`, `thresholds.csv`, `by_year.csv`, `transfer.csv`, `next_day_risk.png`, `run_metadata.json`.

## Layout

```
ormangozcu/   grid, firms, weather, dataset, models, metrics, experiment, cli
tests/        offline tests on a small made-up fixture
docs/         protocol, limitations, sources
```

## Licence and citation

Code: MIT. FIRMS and ERA5 data keep their own terms and are downloaded at run time, not stored here. See `CITATION.cff`.
