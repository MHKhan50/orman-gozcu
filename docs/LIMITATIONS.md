# Limitations

- **Detections are not fires on the ground.** A VIIRS hotspot is a hot pixel seen during an overpass. Small, short or cloud-covered fires are missed; agricultural burning is counted as fire. Results describe detection risk, not burned area or fire perimeters.
- **Overpass timing.** S-NPP passes about twice a day, so a fire that starts and ends between overpasses is invisible.
- **Coarse weather.** One ERA5 point per 1-degree block; local wind and humidity in forest valleys are not resolved. Relative humidity, fuel moisture and land cover are not used in v0.1.
- **Cell set.** Only cells that burned in 2016-2019 are scored, so a fire in a cell with no earlier record cannot be predicted.
- **Regions** are simple longitude bands, not ecological or administrative regions.
- **2021** was an exceptional season in south-western Türkiye; it is part of the test set on purpose, and per-year results are reported.
- This is a research benchmark, not an operational warning system.
