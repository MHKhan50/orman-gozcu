"""Baselines and learned models; every model returns a probability per row."""
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .dataset import FEATURES

MODELS = ("climatology", "persistence", "logistic", "gbm")


class Calibrated:
    """Fit on train, map scores to probabilities with isotonic regression fitted on validation."""

    def __init__(self, name, seed=0):
        if name not in MODELS:
            raise ValueError("Unknown model %r" % name)
        self.name, self.seed, self.iso = name, seed, None

    def _raw(self, df):
        if self.name == "climatology":
            return df["hist_freq"].to_numpy(float)
        if self.name == "persistence":
            # fire today ranks first; history breaks ties among the rest
            return df["fire_today"].to_numpy(float) + 0.5 * df["hist_freq"].to_numpy(float)
        return self.model.predict_proba(df[FEATURES])[:, 1]

    def fit(self, train, val):
        if self.name == "logistic":
            self.model = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(),
                                       LogisticRegression(max_iter=2000, class_weight="balanced"))
            self.model.fit(train[FEATURES], train["label"])
        elif self.name == "gbm":
            self.model = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_leaf_nodes=31,
                                                        l2_regularization=1.0, random_state=self.seed)
            self.model.fit(train[FEATURES], train["label"])
        self.iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
        self.iso.fit(self._raw(val), val["label"].to_numpy(int))
        return self

    def predict(self, df):
        return self.iso.predict(self._raw(df))

    def raw(self, df):
        return self._raw(df)
