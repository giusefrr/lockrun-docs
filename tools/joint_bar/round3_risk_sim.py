"""Case 4, round 3 (simulated, nothing implemented): ex-ante risk normalization + T_eff + the joint bar.

  x_t = r_t / sqrt(w_t' S_t w_t), S_t from the rows strictly before t (a rolling window of W rows,
  at least WARMUP of them, else the period is inactive), shrunk toward its diagonal by lambda.
  Inactive: no weights, no estimate, or ex-ante risk below 10% of the strategy's median ex-ante risk
  (over its periods with weights and an estimate). T_eff = active periods; min_t on T_eff.
  PASS iff z = sr sqrt(T_eff - 1)/sqrt(den) >= c(N) * max(1, sqrt(V_sample / v_null(T_eff))),
  N = trials + 1 (the reserved verification), c(N) the joint bar for the holdout's tail.
"""
import os as _os, sys as _sys
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_sys.path[:0] = [_HERE, _os.path.join(_HERE, "..", "..", "tests")]
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
from adversary_world import Ledger, MIN_T, T  # noqa: E402
from round3_joint_bar import bar  # noqa: E402
from lockrun import stats  # noqa: E402

WARMUP = 20
TABLES = {k: {int(n): v for n, v in t.items()} for k, t in json.load(open(os.path.join(HERE, "joint_tables.json"))).items()}
GRID = [(c, k0) for c in (1.5, 2.0, 2.5, 3.0, 3.5) for k0 in (2, 3, 20, 100)]


def market(seed, A=8, tail=None, drift=None):
    rng = np.random.default_rng([seed, 0])
    vol = np.geomspace(0.001, 0.02, A)
    vol[-2] = vol[-1] = 0.01
    z = rng.standard_t(tail, (T, A)) / np.sqrt(tail / (tail - 2)) if tail else rng.normal(size=(T, A))
    R = z * vol
    R[:, -1] = R[:, -2] + np.random.default_rng([seed, 5]).normal(0, 1e-4, T)    # the twin
    if drift is not None:
        R[:, 3] += drift * vol[3]
    return R


def covariances(R, W, lam):
    """S[t] from rows [max(0, t - W), t), shrunk toward its diagonal; NaN where fewer than WARMUP rows."""
    Tn, A = R.shape
    P = np.concatenate([np.zeros((1, A, A)), np.cumsum(R[:, :, None] * R[:, None, :], 0)])
    m = np.concatenate([np.zeros((1, A)), np.cumsum(R, 0)])
    t = np.arange(Tn)
    a = np.maximum(0, t - W)
    n = (t - a).astype(float)
    S = np.full((Tn, A, A), np.nan)
    ok = n >= WARMUP
    mu = (m[t] - m[a])[ok] / n[ok, None]
    S[ok] = ((P[t] - P[a])[ok] - n[ok, None, None] * mu[:, :, None] * mu[:, None, :]) / (n[ok, None, None] - 1)
    d = np.einsum("tii->ti", S)
    S = (1 - lam) * S + lam * (d[:, :, None] * np.eye(A))
    return S


def running_t(x):
    k = np.arange(1, len(x) + 1)
    s, q = np.cumsum(x), np.cumsum(x * x)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(k >= 2, (s / k) / np.sqrt((q - s * s / k) / (k - 1) / k), np.nan)


def normalized(W, R, S):
    """(x on active periods, their period indices)."""
    r = (W * R).sum(1)
    with np.errstate(invalid="ignore"):
        risk = np.sqrt(np.maximum(np.einsum("ti,tij,tj->t", W, S, W), 0))
    live = (np.abs(W).sum(1) > 0) & np.isfinite(risk) & (risk > 0)
    if not live.any():
        return np.array([]), np.array([], int)
    active = live & (risk >= 0.10 * np.median(risk[live]))
    idx = np.flatnonzero(active)
    return r[idx] / risk[idx], idx


def stop_period(series_t, idx, c, k0):
    """The first period index p >= k0 - 1 at which the watched running t reaches c, or None."""
    hit = np.flatnonzero((idx >= k0 - 1) & (series_t >= c))
    return int(idx[hit[0]]) + 1 if hit.size else None


def base(seed, i, A):
    W = np.random.default_rng([seed, i, 1]).normal(size=(T, A))
    return W / np.abs(W).sum(1, keepdims=True)


def after_stop(W, k, variant, seed, i):
    kind, par = variant
    A = W.shape[1]
    if kind == "flat":
        W[k:] = 0.0
    elif kind == "resume":
        W[k:T - par] = 0.0
    elif kind == "tiny":
        W[k:] *= par
    elif kind == "diversify":
        W[k:] = 1.0 / A
    elif kind == "hedge":
        W[k:] = 0.0
        W[k:, -2], W[k:, -1] = 1.0, -1.0
    elif kind == "hedge-drift":                 # the ratio a slow random walk from 1
        beta = 1 + np.cumsum(np.random.default_rng([seed, i, 7]).normal(0, 0.002, T - k))
        W[k:] = 0.0
        W[k:, -2], W[k:, -1] = 1.0, -beta
    elif kind == "lowvar":                      # only the lowest-variance asset
        W[k:] = 0.0
        W[k:, 0] = 1.0
    return W


def trial(seed, i, R, S, variant, c, k0, watch):
    """(weights) of one trial whose stop is decided on `watch`: "raw" (today's statistic) or "norm"."""
    W = base(seed, i, R.shape[1])
    if variant[0] == "honest":
        return W
    if variant[0] == "honest-flat-days":
        W[np.random.default_rng([seed, i, 9]).random(T) < 0.10] = 0.0
        return W
    if watch == "raw":
        r = (W * R).sum(1)
        k = stop_period(running_t(r), np.arange(T), c, k0)
    else:
        x, idx = normalized(W, R, S)
        k = stop_period(running_t(x), idx, c, k0)
    return W if k is None else after_stop(W.copy(), k, variant, seed, i)


def today(R, Ws):
    L = Ledger()
    ids = [L.trial((W * R).sum(1)) for W in Ws]
    return any(L.passes(i) for i in ids)


def new_rule(R, S, Ws, table):
    ms = []
    for W in Ws:
        x, _ = normalized(W, R, S)
        try:
            ms.append(stats.moments(x) if len(x) >= 4 else None)
        except ValueError:
            ms.append(None)
    srs = [m.sr for m in ms if m is not None]
    c = bar(table, len(Ws) + 1)
    for m in ms:
        if m is None or m.T < MIN_T:
            continue
        scale = max(1.0, (stats.sharpe_variance(srs) / stats.null_sharpe_variance(m.T)) ** 0.5) if len(srs) >= 2 else 1.0
        den = 1 - m.skew * m.sr + (m.kurt - 1) / 4 * m.sr ** 2
        if den > 0 and m.sr * np.sqrt(m.T - 1) / np.sqrt(den) >= c * scale:
            return True
    return False
