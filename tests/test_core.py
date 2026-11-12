import io
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from fixtures import firms_csv, point_in, synthetic
from ormangozcu import firms, weather
from ormangozcu.dataset import FEATURES, add_history, build, fire_prone_cells, split
from ormangozcu.experiment import run
from ormangozcu.grid import cell_of, centre, neighbours, region
from ormangozcu.metrics import ece, threshold_for_recall, top_share_capture
from ormangozcu.models import Calibrated


class Grid(unittest.TestCase):
    def test_round_trip(self):
        c = cell_of(37.26, 28.40)
        lat, lon = centre(c)
        self.assertEqual(cell_of(lat, lon), c)
        self.assertTrue(abs(lat - 37.26) <= 0.25 and abs(lon - 28.40) <= 0.25)

    def test_neighbours_and_regions(self):
        self.assertEqual(len(neighbours("r5_c5")), 8)
        self.assertEqual(region(cell_of(38.4, 27.1)), "west")     # Izmir
        self.assertEqual(region(cell_of(36.9, 30.7)), "central")  # Antalya
        self.assertEqual(region(cell_of(37.9, 40.2)), "east")     # Diyarbakir


class Firms(unittest.TestCase):
    def test_chunks_cover_season_once(self):
        days = sum(n for _, n in firms.season_chunks(2021))
        self.assertEqual(days, 184)
        self.assertTrue(all(n <= 5 for _, n in firms.season_chunks(2021)))

    def test_filters(self):
        inside = {"latitude": "39.93", "longitude": "32.86"}  # Ankara
        self.assertFalse(firms.keep(dict(inside, confidence="l", type="0")))
        self.assertFalse(firms.keep(dict(inside, confidence="h", type="2")))
        self.assertTrue(firms.keep(dict(inside, confidence="n", type="0")))
        # inside the query rectangle but outside Türkiye (northern Iraq, the Aegean sea, Cyprus)
        for lat, lon in [("35.627", "44.006"), ("37.8", "26.3"), ("35.2", "33.3")]:
            self.assertFalse(firms.keep({"latitude": lat, "longitude": lon, "confidence": "n", "type": "0"}))

    def test_download_caches_and_counts(self):
        calls = []
        lat, lon = point_in("r8_c20")

        class Resp(io.BytesIO):
            def __enter__(self): return self
            def __exit__(self, *a): return False

        def opener(url, timeout=0):
            calls.append(url)
            return Resp(firms_csv([(lat, lon, "2021-05-01", "n", "0"), (lat, lon, "2021-05-01", "l", "0")]).encode())

        with tempfile.TemporaryDirectory() as tmp:
            firms.download([2021], tmp, key="x", pause=0, opener=opener)
            n = len(calls)
            firms.download([2021], tmp, key="x", pause=0, opener=opener)
            self.assertEqual(len(calls), n)  # second run used the cache
            counts = firms.daily_cell_counts(tmp)
        self.assertEqual(counts[("2021-05-01", "r8_c20")], n)
        self.assertTrue(all("/api/area/csv/x/VIIRS_SNPP_SP/25.5,35.5,45,42.5/" in u for u in calls))  # one kept row per cached chunk

    def test_bad_request_stops_without_retry(self):
        import urllib.error
        calls = []

        def opener(url, timeout=0):
            calls.append(url)
            raise urllib.error.HTTPError(url, 400, "Bad Request", {}, io.BytesIO(b"Invalid API call."))

        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(RuntimeError) as ctx:
                firms.download([2021], tmp, key="secretkey", pause=0, opener=opener)
        self.assertEqual(len(calls), 1)
        self.assertNotIn("secretkey", str(ctx.exception))

    def test_missing_key(self):
        import os
        old = os.environ.pop("FIRMS_MAP_KEY", None)
        try:
            with self.assertRaises(RuntimeError):
                firms.download([2021], tempfile.mkdtemp())
        finally:
            if old:
                os.environ["FIRMS_MAP_KEY"] = old


class Weather(unittest.TestCase):
    def test_download_and_load(self):
        class Resp(io.BytesIO):
            def __enter__(self): return self
            def __exit__(self, *a): return False

        def opener(url, timeout=0):
            daily = {"time": ["2021-05-01"], **{v: [1.0] for v in weather.VARIABLES}}
            return Resp(json.dumps([{"daily": daily}, {"daily": daily}]).encode())

        with tempfile.TemporaryDirectory() as tmp:
            weather.download({"r1_c1": (36, 30), "r1_c2": (36, 30.5)}, [2021], tmp, opener=opener, pause=0)
            table = weather.load(tmp)
        self.assertEqual(table[("2021-05-01", "r1_c2")]["precipitation_sum"], 1.0)


class Dataset(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        counts, wx, cells = synthetic()
        cls.counts = counts
        cls.df = add_history(build(counts, wx, cells, range(2016, 2025)))

    def test_label_is_next_day(self):
        d = self.df[self.df["cell"] == "r10_c5"].sort_values("date")
        self.assertTrue((d["label"].to_numpy()[:-1] == d["fire"].to_numpy()[1:])[d["year"].to_numpy()[:-1] == d["year"].to_numpy()[1:]].all())

    def test_season_and_features(self):
        self.assertEqual(self.df["date"].str[5:].min(), "05-01")
        self.assertEqual(self.df["date"].str[5:].max(), "10-30")
        self.assertFalse(self.df[FEATURES].isna().any().any())

    def test_fire_prone_uses_training_years_only(self):
        counts = {("2023-07-01", "r1_c1"): 1, ("2023-07-02", "r1_c1"): 1, ("2023-07-03", "r1_c1"): 1}
        self.assertEqual(fire_prone_cells(counts), [])

    def test_history_from_training_years_only(self):
        df = self.df.copy()
        train = df[df["year"] <= 2019]
        expected = train[(train["cell"] == "r8_c20") & (train["month"] == 7)]["fire"].mean()
        got = df[(df["cell"] == "r8_c20") & (df["month"] == 7) & (df["year"] == 2023)]["hist_freq"].iloc[0]
        self.assertAlmostEqual(expected, got)


class Metrics(unittest.TestCase):
    def test_ece_perfect(self):
        self.assertAlmostEqual(ece(np.array([0, 1]), np.array([0.0, 1.0])), 0.0)

    def test_top_capture(self):
        df = pd.DataFrame({"date": ["d"] * 10, "label": [1] + [0] * 9})
        p = np.linspace(1, 0, 10)
        self.assertEqual(top_share_capture(df, p, 0.1), 1.0)

    def test_threshold_for_recall(self):
        y = np.array([1, 1, 0, 1, 0])
        p = np.array([0.9, 0.8, 0.7, 0.2, 0.1])
        self.assertEqual(threshold_for_recall(y, p, 0.6), 0.8)


class Pipeline(unittest.TestCase):
    def test_models_and_run(self):
        counts, wx, cells = synthetic()
        df = add_history(build(counts, wx, cells, range(2016, 2025)))
        train, val, test = split(df)
        p = Calibrated("gbm", 0).fit(train, val).predict(test)
        self.assertTrue(((p >= 0) & (p <= 1)).all())
        with self.assertRaises(ValueError):
            Calibrated("nope")
        with tempfile.TemporaryDirectory() as tmp:
            summary = run(df, tmp, {"source": "synthetic test fixture"})
            for f in ("metrics.csv", "thresholds.csv", "by_year.csv", "transfer.csv", "tables.md",
                      "run_metadata.json", "next_day_risk.png"):
                self.assertTrue((Path(tmp) / f).exists(), f)
        self.assertEqual(set(summary["model"]), {"climatology", "persistence", "logistic", "gbm"})


if __name__ == "__main__":
    unittest.main()
