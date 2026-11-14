# OrmanGözcü results

366 cells, test seasons 2021-2024, 267912 test cell-days, 20283 with a next-day detection.

## Test seasons, all regions

| Model | Average precision | ROC AUC | Brier | ECE | Top-10% capture |
|---|---|---|---|---|---|
| climatology | 0.301 ± 0.000 | 0.811 ± 0.000 | 0.062 ± 0.000 | 0.022 ± 0.000 | 0.383 ± 0.000 |
| gbm | 0.430 ± 0.001 | 0.842 ± 0.001 | 0.055 ± 0.000 | 0.012 ± 0.000 | 0.441 ± 0.001 |
| logistic | 0.412 ± 0.000 | 0.843 ± 0.000 | 0.056 ± 0.000 | 0.010 ± 0.000 | 0.440 ± 0.000 |
| persistence | 0.366 ± 0.000 | 0.834 ± 0.000 | 0.057 ± 0.000 | 0.016 ± 0.000 | 0.414 ± 0.000 |

## Threshold chosen on 2020 for 60% recall, applied to the test seasons

| Model | Recall | Precision | False alarms per day | Missed fire cells per day |
|---|---|---|---|---|
| climatology | 0.579 | 0.240 | 50.8 | 11.67 |
| gbm | 0.584 | 0.317 | 34.9 | 11.54 |
| logistic | 0.550 | 0.336 | 30.2 | 12.46 |
| persistence | 0.586 | 0.287 | 40.4 | 11.48 |

## Average precision by test year

| Model | Year | Average precision | Base rate |
|---|---|---|---|
| climatology | 2021 | 0.249 | 0.0664 |
| climatology | 2022 | 0.232 | 0.0479 |
| climatology | 2023 | 0.353 | 0.0846 |
| climatology | 2024 | 0.378 | 0.1040 |
| gbm | 2021 | 0.378 | 0.0664 |
| gbm | 2022 | 0.344 | 0.0479 |
| gbm | 2023 | 0.452 | 0.0846 |
| gbm | 2024 | 0.497 | 0.1040 |
| logistic | 2021 | 0.351 | 0.0664 |
| logistic | 2022 | 0.321 | 0.0479 |
| logistic | 2023 | 0.444 | 0.0846 |
| logistic | 2024 | 0.488 | 0.1040 |
| persistence | 2021 | 0.324 | 0.0664 |
| persistence | 2022 | 0.276 | 0.0479 |
| persistence | 2023 | 0.398 | 0.0846 |
| persistence | 2024 | 0.434 | 0.1040 |

## Regional transfer (test seasons, held-out region only)

| Region | Model | Setting | Average precision | ROC AUC | Brier |
|---|---|---|---|---|---|
| central | climatology | region held out | 0.220 | 0.779 | 0.0550 |
| central | climatology | trained on all regions | 0.219 | 0.779 | 0.0538 |
| central | gbm | region held out | 0.320 | 0.810 | 0.0483 |
| central | gbm | trained on all regions | 0.326 | 0.813 | 0.0479 |
| central | logistic | region held out | 0.316 | 0.817 | 0.0481 |
| central | logistic | trained on all regions | 0.313 | 0.816 | 0.0482 |
| east | climatology | region held out | 0.355 | 0.838 | 0.0701 |
| east | climatology | trained on all regions | 0.365 | 0.840 | 0.0707 |
| east | gbm | region held out | 0.504 | 0.869 | 0.0602 |
| east | gbm | trained on all regions | 0.515 | 0.873 | 0.0596 |
| east | logistic | region held out | 0.460 | 0.868 | 0.0634 |
| east | logistic | trained on all regions | 0.487 | 0.871 | 0.0618 |
| west | climatology | region held out | 0.251 | 0.774 | 0.0608 |
| west | climatology | trained on all regions | 0.247 | 0.774 | 0.0607 |
| west | gbm | region held out | 0.356 | 0.799 | 0.0561 |
| west | gbm | trained on all regions | 0.357 | 0.798 | 0.0561 |
| west | logistic | region held out | 0.361 | 0.804 | 0.0558 |
| west | logistic | trained on all regions | 0.361 | 0.806 | 0.0559 |

± is the standard deviation over gradient-boosting seeds; other models are deterministic.
