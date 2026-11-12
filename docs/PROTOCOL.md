# Protocol (v0.1.0)

## Question
Given today's satellite fire detections and weather, which 0.5-degree cells in Türkiye will have at least one fire detection tomorrow?

## Data
- **Fires:** NASA FIRMS VIIRS S-NPP 375 m, standard processing (`VIIRS_SNPP_SP`), area query for the rectangle 25.5-45.0 E, 35.5-42.5 N (the FIRMS country API does not serve the standard-processing archive), kept only if inside the Türkiye border (Natural Earth 10 m Admin-0, public domain), 1 May to 31 October. Low-confidence detections and non-vegetation types (static land sources, offshore) are dropped.
- **Weather:** ERA5 daily values from the Open-Meteo historical archive (`models=era5`): maximum 2 m temperature, precipitation, maximum 10 m wind speed and FAO reference evapotranspiration. One point per 1-degree block (2 x 2 fire cells) to stay within the free API allowance.
- **Not used in v0.1:** ESA WorldCover land cover and EFFIS statistics. Both are listed in `docs/SOURCES.md` for the next version.

## Cells
0.5-degree cells with at least 3 fire days in the training seasons (2016-2019). The cell set is fixed from training years only, so it carries no information from later seasons.

## Label and features
Label: at least one kept detection in the cell on day t+1. Features use day t and earlier: fire today, log detections today, fire days in the last 7 days, the same for the 8 neighbouring cells, the cell's training-season fire-day rate for that month, maximum temperature, precipitation, wind, evapotranspiration, 7- and 30-day precipitation, days since 1 mm of rain (capped at 30), 7-day mean evapotranspiration, and day of year.

## Splits
Train 2016-2019, validation 2020, test 2021-2024 (whole seasons, no shuffling). Regional transfer: three longitude bands (west of 30°E, 30-36°E, east of 36°E); a model trained on two bands is tested on the third and compared with a model trained on all three.

## Models
Historical frequency (climatology), fire today (persistence, ties broken by history), logistic regression, histogram gradient boosting (5 seeds). Every model's scores are mapped to probabilities by isotonic regression fitted on 2020.

## Metrics
Average precision (main metric, because positives are rare), ROC AUC, Brier score, 10-bin ECE, and the share of next-day fire cells that fall in each day's top 10% of cells by risk. For RQ3, a threshold is chosen on 2020 for 60% recall and applied unchanged to 2021-2024; false alarms and missed fire cells per day are reported.

## Hypotheses
- H1: gradient boosting has higher average precision than historical frequency on the test seasons.
- H2: average precision on a held-out region falls when that region is excluded from training.
- H3: a threshold set on 2020 keeps recall within 10 points of 60% on 2021-2024.
