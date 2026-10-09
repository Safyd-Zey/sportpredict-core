"""Ordered logistic regression mapping an Elo difference to P(away), P(draw), P(home).

The approach follows Hvattum & Arntzen (2010), "Using ELO ratings for match
result prediction in association football", Int. J. of Forecasting 26(3).
Model:  P(Y <= j | x) = sigmoid(theta_j - beta * x),  j in {away, draw},
with x = elo_diff / 100 and theta_away < theta_draw.
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit

_EPS = 1e-12


class OrderedLogit:
    def __init__(self) -> None:
        self.beta_: float | None = None
        self.thresholds_: tuple[float, float] | None = None

    @staticmethod
    def _unpack(params: np.ndarray) -> tuple[float, float, float]:
        beta, theta1, log_gap = params
        return float(beta), float(theta1), float(theta1 + np.exp(log_gap))

    @staticmethod
    def _proba(beta: float, t1: float, t2: float, x: np.ndarray) -> np.ndarray:
        c1 = expit(t1 - beta * x)
        c2 = expit(t2 - beta * x)
        return np.column_stack([c1, c2 - c1, 1.0 - c2])

    def fit(self, x: np.ndarray, y: np.ndarray) -> OrderedLogit:
        x = np.asarray(x, dtype=float) / 100.0
        y = np.asarray(y, dtype=int)
        if x.shape[0] != y.shape[0]:
            raise ValueError("x and y must have the same length")
        if not np.isin(y, [0, 1, 2]).all():
            raise ValueError("y must be coded as 0 (away), 1 (draw), 2 (home)")

        def nll(params: np.ndarray) -> float:
            p = self._proba(*self._unpack(params), x)
            return -float(np.sum(np.log(p[np.arange(len(y)), y] + _EPS)))

        res = minimize(nll, x0=np.array([0.5, -0.5, 0.0]), method="BFGS")
        beta, t1, t2 = self._unpack(res.x)
        self.beta_, self.thresholds_ = beta, (t1, t2)
        return self

    def predict_proba(self, x: np.ndarray) -> np.ndarray:
        if self.beta_ is None or self.thresholds_ is None:
            raise RuntimeError("model is not fitted; call fit() first")
        x = np.asarray(x, dtype=float) / 100.0
        return self._proba(self.beta_, *self.thresholds_, x)
