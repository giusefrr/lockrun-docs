"""The joint bar: c(N) = the (1 - alpha) quantile of max over N independent null trials of
sup_{k in [min_t, T]} z_k, z_k the PSR statistic vs 0 on the first k active periods, with iid
Student-t(df) returns, df fitted on the holdout's residuals (floor 4). Numpy only."""
from __future__ import annotations

import os as _os, sys as _sys
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_sys.path[:0] = [_HERE, _os.path.join(_HERE, "..", "..", "tests")]

import math
import time

import numpy as np

ALPHA = 0.05
N_GRID = (1, 2, 3, 5, 10, 20, 50, 100, 200, 500, 1000)


def fit_df(R: np.ndarray, floor: float = 4.0) -> tuple[float, float]:
    """(df used, df fitted): Student-t df by profile likelihood on every asset's standardized
    residuals, pooled (unit variance: scale sqrt((df-2)/df)); the grid's top (200) stands for normal."""
    z = (R - R.mean(0)) / R.std(0, ddof=1)
    z = z.ravel()
    best = None
    for df in np.concatenate([np.linspace(2.05, 10, 160), np.geomspace(10, 200, 60)]):
        s = math.sqrt((df - 2) / df)
        ll = (z.size * (math.lgamma((df + 1) / 2) - math.lgamma(df / 2) - 0.5 * math.log(df * math.pi) - math.log(s))
              - (df + 1) / 2 * np.log1p((z / s) ** 2 / df).sum())
        if best is None or ll > best[0]:
            best = (ll, df)
    return max(floor, best[1]), best[1]


def sup_z(x: np.ndarray, min_t: int) -> np.ndarray:
    """sup over k in [min_t, T] of z_k = sr_k sqrt(k-1)/sqrt(1 - skew sr + (kurt-1)/4 sr^2), per row."""
    k = np.arange(1, x.shape[1] + 1, dtype=float)[min_t - 1:]
    s1, s2, s3, s4 = (np.cumsum(x ** p, 1)[:, min_t - 1:] for p in (1, 2, 3, 4))
    mu = s1 / k
    m2 = s2 / k - mu ** 2
    m3 = s3 / k - 3 * mu * s2 / k + 2 * mu ** 3
    m4 = s4 / k - 4 * mu * s3 / k + 6 * mu ** 2 * s2 / k - 3 * mu ** 4
    sr = mu / np.sqrt(m2 * k / (k - 1))
    den = 1 - (m3 / m2 ** 1.5) * sr + ((m4 / m2 ** 2) - 1) / 4 * sr ** 2
    return (sr * np.sqrt(k - 1) / np.sqrt(den)).max(1)


def calibrate(T: int, min_t: int, df: float, paths: int, seed: int = 1, chunk_bytes: float = 2.5e8) -> dict:
    """The table {N: c(N)} over N_GRID, from `paths` null paths, in chunks of at most chunk_bytes
    of working memory (about 12 arrays of chunk x T float64)."""
    rng = np.random.default_rng(seed)
    chunk = max(1000, int(chunk_bytes / (12 * 8 * T)))
    sups, t0 = [], time.perf_counter()
    for start in range(0, paths, chunk):
        n = min(chunk, paths - start)
        x = rng.standard_t(df, size=(n, T)) if df < 200 else rng.normal(size=(n, T))
        sups.append(sup_z(x, min_t))
    sups = np.sort(np.concatenate(sups))
    table = {N: float(np.quantile(sups, (1 - ALPHA) ** (1 / N))) for N in N_GRID}
    return {"table": table, "seconds": time.perf_counter() - t0, "paths": paths, "chunk": chunk}


def bar(table: dict, N: int) -> float:
    """c(N), interpolated linearly in log N between the grid's points."""
    ns = sorted(table)
    if N <= ns[0]:
        return table[ns[0]]
    for a, b in zip(ns, ns[1:]):
        if N <= b:
            w = (math.log(N) - math.log(a)) / (math.log(b) - math.log(a))
            return table[a] + w * (table[b] - table[a])
    raise ValueError(f"N={N} is beyond the table ({ns[-1]})")
