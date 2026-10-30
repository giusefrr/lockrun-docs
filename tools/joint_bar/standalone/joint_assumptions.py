"""The assumptions table: dependence and adaptive exposure rules, under the joint bar as the product runs it.

Every holdout gets the product's own procedure: its df fitted on its residuals (floor 4), its bar from 2M null
paths, seed 20261027 (lockrun/service/holdout_init.py). Calibration is deterministic in those, so one table per
distinct df is exactly one calibration per holdout. --quick uses fewer paths and says so.

  (a) n correlated trials, on an iid market and a one-factor GARCH market
  (b) every row of the main table, on an independent GARCH market and the one-factor one
  (c) adversaries with the estimator's state: the window's smallest eigenvalue, the direction it most
      underestimates, trading only when true risk exceeds estimated risk by a factor, on iid and GARCH markets
  (d) pauses within a budget, so that T_eff stays above min_t

Each row reports, per n, the worst PASS rate over its stops, the median T_eff of its first trial at that stop and
the share of runs refused for T_eff below min_t: a low rate with a large share is refusal, not detection.
"""
from __future__ import annotations

import os
import sys
from collections import Counter
from dataclasses import dataclass, field

import numpy as np

import joint_rule as jr
import joint_tables as jt
import joint_world as jw

NOMINAL = 0.05
BARS: dict = {}     # each worker's tables, by df
CORRELATED_NS = (1, 2, 3, 5, 10, 20)
RHOS = (0.5, 0.9)
FACTORS = (1.5, 2.0, 3.0)
# The stops of an adversary that knows the bar: the main grid, and the bar itself.
STOPS = [(None, None), *jw.GRID, ("c(n)", jw.MIN_T), ("c(n)+0.3", jw.MIN_T)]


def above_nominal(rate: float | None) -> str:
    return "above nominal" if rate is not None and rate > NOMINAL else ""


def set_bars(bars: dict) -> None:
    BARS.update(bars)


MARKETS = {     # name: (kind, assets, regime)
    "iid": ("iid", 8, None), "iid50": ("iid", 50, None), "equal30": ("equal", 30, None),
    "equal50": ("equal", 50, None), "equal58": ("equal", 58, None),
    "garch": ("garch", 8, None), "garch50": ("garch", 50, None), "garch100": ("garch", 100, None),
    "garch-regime": ("garch", 8, jw.REGIME),
    "factor": ("factor", 8, None), "factor50": ("factor", 50, None), "factor100": ("factor", 100, None),
    "factor-regime": ("factor", 8, jw.REGIME),
}
MARKET_NAMES = {"iid": "iid", "iid50": "iid, 50 assets", "equal30": "iid, 30 equal assets", "equal50": "iid, 50 equal assets",
                "equal58": "iid, 58 equal assets", "garch": "GARCH",
                "garch50": "GARCH, 50 assets", "factor": "one-factor GARCH", "factor50": "one-factor GARCH, 50 assets"}


def returns_of(name: str, seed: int) -> tuple:
    kind, A, regime = MARKETS[name]
    if kind == "iid":
        return jw.market(seed, A), None
    if kind == "equal":
        return jw.equal_market(seed, A), None
    make = jw.garch_market if kind == "garch" else jw.factor_market
    return make(seed, A, regime=regime)


@dataclass(frozen=True)
class AssumptionRow:
    part: str
    name: str
    market: str
    kind: str                     # main, stopping, correlated, eigen, under, timed, pause
    par: object = None
    ns: tuple = (1, 2)
    stops: tuple = tuple(STOPS)
    guard: bool = True            # stops only with more than min_t active steps


def rows_of(parts: str) -> list:
    rows = []
    if "a" in parts:
        for m in ("iid", "factor"):
            for rho in RHOS:
                rows.append(AssumptionRow("a", f"{MARKET_NAMES[m]}, rho = {rho}: honest", m, "correlated", (rho, "honest"),
                                          CORRELATED_NS, ((None, None),)))
                rows.append(AssumptionRow("a", f"{MARKET_NAMES[m]}, rho = {rho}: flat once ahead", m, "correlated",
                                          (rho, "flat"), CORRELATED_NS))
    if "b" in parts:
        for prefix, label in (("garch", "GARCH"), ("factor", "One-factor GARCH")):
            for r in jt.ROWS:
                if r.tail:
                    continue
                m = f"{prefix}-regime" if r.kind == "regime" else prefix + ("100" if r.A == 100 else "")
                name = "Every trial stopping, n = 1 to 50" if r.kind == "stopping" else r.name
                stops = {"fixed": ((None, None),), "grid": tuple(jw.GRID), "regime": tuple(jw.GRID),
                         "nullspace": tuple(jt.NULLSPACE_GRID), "stopping": ((None, None), (2.0, jw.MIN_T), (2.5, jw.MIN_T),
                                                                            *STOPS[-2:])}[r.kind]
                rows.append(AssumptionRow("b", f"{label}: {name}", m, "stopping" if r.kind == "stopping" else "main",
                                          r, jt.STOP_NS if r.kind == "stopping" else (1, 2), stops, False))
    if "c" in parts:
        for m in ("iid", "equal30", "equal50", "equal58", "garch", "garch50", "factor"):
            rows.append(AssumptionRow("c", f"(1) Window's smallest eigenvalue, {MARKET_NAMES[m]}", m, "eigen"))
            rows.append(AssumptionRow("c", f"(1) Direction most underestimated, {MARKET_NAMES[m]}", m, "under"))
        for m in ("iid", "equal30", "equal50", "equal58"):
            for f in FACTORS:
                rows.append(AssumptionRow("c", f"(2) Trades above {f}x, floor otherwise, {MARKET_NAMES[m]}", m, "timed", f))
        for m in ("garch", "garch50", "factor"):
            for f in FACTORS:
                rows.append(AssumptionRow("c", f"(3) Trades above {f}x, floor otherwise, {MARKET_NAMES[m]}", m, "timed", f))
    if "d" in parts:
        for m in ("iid", "equal50", "garch", "factor"):
            for rule, label in (("losing", "after each losing step"), ("behind", "while behind"),
                                ("timed", "where the window overestimates")):
                rows.append(AssumptionRow("d", f"Pauses {label}, {MARKET_NAMES[m]}", m, "pause", rule))
    return rows


class Holdout:
    """One seed's market, what its rows share."""

    def __init__(self, name: str, seed: int, p: dict):
        self.name, self.seed, self.p = name, seed, p
        self.R, self.sigma = returns_of(name, seed)
        self.A = self.R.shape[1]
        self.cov = jr.window_covariances(self.R, p)
        self.jb = BARS[jw.holdout_df(self.R)]
        self._sigma = self._eigen = self._under = None
        self.worlds: dict = {}

    @property
    def Sigma(self) -> np.ndarray:
        if self._sigma is None:
            self._sigma = jw.true_covariances(MARKETS[self.name][0], self.R, self.sigma)
        return self._sigma

    def eigen(self) -> np.ndarray:
        if self._eigen is None:
            self._eigen = jw.smallest_eigen_direction(self.cov)
        return self._eigen

    def under(self) -> tuple:
        if self._under is None:
            self._under = jw.most_underestimated_direction(self.cov, self.Sigma)
        return self._under


def _world(h: Holdout, row: AssumptionRow) -> jw.SeedWorld:
    if row.kind == "main":
        base, key = None, ("main",)
    elif row.kind == "stopping":
        base, key = None, ("main",)
    elif row.kind == "correlated":
        rho = row.par[0]
        base, key = (lambda s, i, A: jw.correlated_weights(s, i, A, rho)), ("rho", rho)
    elif row.kind == "eigen":
        base, key = (lambda s, i, A: jw.eigen_weights(h.eigen(), s, i, h.cov, A)), ("eigen",)
    elif row.kind == "under":
        base, key = (lambda s, i, A: jw.eigen_weights(h.under()[0], s, i, h.cov, A)), ("under",)
    else:
        f = row.par
        base, key = (lambda s, i, A: jw.timed_weights(*h.under(), f, s, i, h.cov, A)), ("timed", f)
    key = (*key, row.guard)
    if key not in h.worlds:
        h.worlds[key] = jw.SeedWorld(h.seed, h.A, R=h.R, base=base, p=h.p, cov=h.cov,
                                     min_active=jw.MIN_T + 1 if row.guard else 0)
    return h.worlds[key]


def _trial_maker(h: Holdout, row: AssumptionRow, n: int, stop: tuple):
    label, k0 = stop
    c = jr.bar(h.jb, n) + (0.3 if label == "c(n)+0.3" else 0.0) if isinstance(label, str) else label
    if row.kind == "pause":
        cache = h.worlds.setdefault(("pause", row.par), {})

        def make(i):
            key = (i, c, k0)
            if key not in cache:
                Sigma = h.Sigma if row.par == "timed" else None
                W = jw.pausing_weights(row.par, h.seed, i, h.R, h.cov, Sigma, c, k0)
                cache[key] = jr.trial_of_weights(W, h.R, h.cov)
            return cache[key]
        return make
    w = _world(h, row)
    if row.kind == "main":
        v = row.par.variant
        return lambda i: w.trial(i, v, c, k0, "norm")
    if row.kind == "correlated" and row.par[1] == "honest":
        return lambda i: w.trial(i, ("honest", None), None, None, "norm")
    v = ("honest", None) if c is None else ("flat", None)
    return lambda i: w.trial(i, v, c, k0, "norm")


def row_cells(h: Holdout, row: AssumptionRow) -> dict:
    """{(n, stop): (passed, the first trial's T_eff)} of one row on one holdout."""
    out = {}
    for n in row.ns:
        for stop in row.stops:
            make = _trial_maker(h, row, n, stop)
            trials = [make(i) for i in range(n)]
            hd = jr.Holdout(trials)
            passed = any(hd.joint(i, h.jb, jw.MIN_T, jw.THRESHOLD).passed for i in range(n))
            out[(n, stop)] = (passed, trials[0].t_eff or 0)
    return out


def market_counts(job: tuple) -> dict:
    """{row name: {(n, stop): [passes, Counter of T_eff]}} for the rows of one market, over seeds."""
    name, rows, seeds, p = job
    out: dict = {r.name: {} for r in rows}
    traded: dict = {}
    for seed in seeds:
        h = Holdout(name, seed, p)
        for row in rows:
            for key, (passed, t_eff) in row_cells(h, row).items():
                cell = out[row.name].setdefault(key, [0, Counter()])
                cell[0] += bool(passed)
                cell[1][t_eff] += 1
            if row.kind == "timed":
                traded[row.name] = traded.get(row.name, 0.0) + float((h.under()[1] >= row.par).mean())
    return {"cells": out, "traded": traded}


def _median(c: Counter) -> float:
    return float(np.median(np.repeat(list(c), list(c.values()))))


def holdout_dfs(job: tuple) -> set:
    name, seeds = job
    return {jw.holdout_df(returns_of(name, s)[0]) for s in seeds}


def calibrate_df(job: tuple) -> tuple:
    """A table for this df: from cache_dir when it holds it (calibration is deterministic in its parameters)."""
    df, paths, cache_dir = job
    path = os.path.join(cache_dir, f"bar-{df!r}-{paths}.npz") if cache_dir else None
    if path and os.path.exists(path):
        with np.load(path) as f:
            return df, {"T": jw.T, "min_t": jw.MIN_T, "threshold": jw.THRESHOLD, "df": df, "paths": paths, "seed": jw.SEED,
                        "zs": f["zs"], "ps": f["ps"]}
    jb = jr.calibrate(jw.T, jw.MIN_T, df, jw.THRESHOLD, paths, jw.SEED)
    if path:
        os.makedirs(cache_dir, exist_ok=True)
        np.savez(path + ".tmp.npz", zs=jb["zs"], ps=jb["ps"])
        os.replace(path + ".tmp.npz", path)
    return df, jb


def prepare_bars(rows: list, seeds: int, paths: int, pool, chunks, cache_dir: str | None = None) -> dict:
    """Every holdout's fit, and a table per distinct df."""
    dfs: set = set()
    by_market: dict = {}
    for name in sorted({r.market for r in rows}):
        fits: set = set()
        for part in pool.imap_unordered(holdout_dfs, [(name, s) for s in chunks(seeds)]):
            fits |= part
        by_market[name] = (min(fits), max(fits))
        dfs |= fits
    bars = dict(pool.imap_unordered(calibrate_df, [(df, paths, cache_dir) for df in sorted(dfs)]))
    return {"bars": bars, "df_range": by_market}


def assumptions(rows: list, seeds: int, pool, chunks, p: dict) -> dict:
    """The table: per row, per n, the worst rate over its stops, its stop, T_eff median and refused share."""
    by_market: dict = {}
    for r in rows:
        by_market.setdefault(r.market, []).append(r)
    total: dict = {r.name: {} for r in rows}
    traded: dict = {}
    jobs = [(m, rs, s, p) for m, rs in by_market.items() for s in chunks(seeds)]
    for part in pool.imap_unordered(market_counts, jobs):
        for name, cells in part["cells"].items():
            for key, (h, c) in cells.items():
                cell = total[name].setdefault(key, [0, Counter()])
                cell[0] += h
                cell[1] += c
        for name, v in part["traded"].items():
            traded[name] = traded.get(name, 0.0) + v
    out = {}
    for r in rows:
        cells = {}
        for n in r.ns:
            (stop, (h, c)) = max(((k[1], v) for k, v in total[r.name].items() if k[0] == n), key=lambda x: x[1][0])
            refused = sum(v for t, v in c.items() if t < jw.MIN_T) / seeds
            cells[n] = {"rate": h / seeds, "stop": stop, "t_eff": _median(c), "refused": refused,
                        "by_stop": {str(k[1]): v[0] / seeds for k, v in total[r.name].items() if k[0] == n}}
        out[r.name] = {"part": r.part, "ns": list(r.ns), "cells": cells}
        if r.name in traded:
            out[r.name]["traded"] = traded[r.name] / seeds
    print(f"  ... {len(rows)} rows", file=sys.stderr, flush=True)
    return out
