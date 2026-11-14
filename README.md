# OrmanGözcü

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24223204.svg)](https://doi.org/10.5281/zenodo.24223204)

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

366 cells that burned in 2016-2019, test seasons 2021-2024 (May to October): 267,912 cell-days, of which 20,283 (7.6%) had a detection the next day, about 28 fire cells a day.

| Model | Average precision | ROC AUC | Brier | ECE | Top-10% capture |
|---|---|---|---|---|---|
| Fire history only (climatology) | 0.301 | 0.811 | 0.062 | 0.022 | 38.3% |
| Fire today + history (persistence) | 0.366 | 0.834 | 0.057 | 0.016 | 41.4% |
| Logistic regression | 0.412 | 0.843 | 0.056 | 0.010 | 44.0% |
| Gradient boosting (5 seeds) | **0.430** ± 0.001 | 0.842 | 0.055 | 0.012 | 44.1% |

Top-10% capture: share of next-day fire cells among each day's 37 highest-risk cells.

**Threshold set on 2020 for 60% recall, applied unchanged to 2021-2024:**

| Model | Recall | Precision | False alarms a day | Missed fire cells a day |
|---|---|---|---|---|
| Climatology | 57.9% | 24.0% | 50.8 | 11.7 |
| Persistence | 58.6% | 28.7% | 40.4 | 11.5 |
| Logistic regression | 55.0% | 33.6% | 30.2 | 12.5 |
| Gradient boosting | 58.4% | 31.7% | 34.9 | 11.5 |

**What this shows**

- **H1 (supported):** gradient boosting beat the historical-frequency baseline in every test year (average precision 0.378 vs 0.249 in 2021, 0.344 vs 0.232 in 2022, 0.452 vs 0.353 in 2023, 0.497 vs 0.378 in 2024). Over persistence (fire today plus history) the gain was 5 to 7 points of average precision every year.
- **At the same recall, fewer false alarms:** with the 2020 threshold, gradient boosting caught about the same share of fire cells as climatology (58% against 58%) with 31% fewer false alarms (34.9 against 50.8 cells a day).
- **H2 (not supported):** leaving a region out of training cost little. Gradient-boosting average precision on the held-out region was 0.320 vs 0.326 (central), 0.504 vs 0.515 (east) and 0.356 vs 0.357 (west) when trained on all regions. The largest drop was logistic regression in the east, 0.460 vs 0.487.
- **H3 (supported, pooled):** a threshold set for 60% recall on 2020 gave 55.0% to 58.6% recall over 2021-2024.
- ROC AUC hardly separates the models (0.81-0.84); the differences sit at the top of the ranking, which is where a warning list is read.

All models were calibrated on 2020 with isotonic regression (ECE 0.010-0.022). Full tables, per-year results and the chart are in `results/`. Detections include agricultural burning, so these are vegetation-fire detections, not forest fires only; see `docs/LIMITATIONS.md`.

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
