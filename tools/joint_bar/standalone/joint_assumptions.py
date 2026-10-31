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
from dataclasses import dataclass, replace

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
    "equal50": ("equal", 50, None), "equal58": ("equal", 58, None), "equal20": ("equal", 20, None),
    "equal45": ("equal", 45, None), "twin50": ("twin", 50, None),
    "main": ("main", 8, None), "main100": ("main", 100, None), "main-regime": ("main", 8, jw.REGIME),
    "t4": ("t4", 8, None), **{f"drift{s}": ("drift", 8, s) for s in (0, 1, 2, 3, 4)},
    "garch": ("garch", 8, None), "garch50": ("garch", 50, None), "garch100": ("garch", 100, None),
    "garch-regime": ("garch", 8, jw.REGIME),
    "factor": ("factor", 8, None), "factor50": ("factor", 50, None), "factor100": ("factor", 100, None),
    "factor-regime": ("factor", 8, jw.REGIME),
}
MARKET_NAMES = {"iid": "iid", "iid50": "iid, 50 assets", "equal20": "iid, 20 equal assets", "equal30": "iid, 30 equal assets", "equal45": "iid, 45 equal assets",
                "twin50": "iid, 50 equal assets with twins", "equal50": "iid, 50 equal assets",
                "equal58": "iid, 58 equal assets", "garch": "GARCH",
                "garch50": "GARCH, 50 assets", "factor": "one-factor GARCH", "factor50": "one-factor GARCH, 50 assets"}


def returns_of(name: str, seed: int) -> tuple:
    kind, A, regime = MARKETS[name]
    if kind == "iid":
        return jw.market(seed, A), None
    if kind == "equal":
        return jw.equal_market(seed, A), None
    if kind == "twin":
        return jw.twin_equal_market(seed, A), None
    if kind == "main":
        return jw.market(seed, A, regime=regime), None
    if kind == "t4":
        return jw.market(seed, A, tail=4), None
    if kind == "drift":
        return jw.market(seed, A, drift=regime / np.sqrt(252)), None
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
    chosen: tuple = ()            # ((n, stop), ...): each n at this stop alone, the fresh seeds' confirmation

    def stops_of(self, n: int) -> tuple:
        return next(((s,) for m, s in self.chosen if m == n), self.stops)


def with_chosen_stops(row: AssumptionRow, measured: dict) -> AssumptionRow:
    """The row at the stop each of its n's worst rate had on the first seeds (their results, as saved)."""
    return replace(row, chosen=tuple((int(n), tuple(c["stop"])) for n, c in measured["cells"].items()))


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
    if "e" in parts:                       # aimed at the candidate fixes: B1, B2, B3
        for m in ("equal20", "equal45", "twin50"):
            rows.append(AssumptionRow("c", f"(1) Window's smallest eigenvalue, {MARKET_NAMES[m]}", m, "eigen"))
            rows.append(AssumptionRow("c", f"(1) Direction most underestimated, {MARKET_NAMES[m]}", m, "under"))
            for f in FACTORS:
                rows.append(AssumptionRow("c", f"(2) Trades above {f}x, floor otherwise, {MARKET_NAMES[m]}", m, "timed", f))
    if "f" in parts:                       # aimed at the bounds on one normalized return: C1, C2
        for m in ("iid", "equal20", "equal30", "equal45", "equal50", "equal58", "twin50", "garch", "garch50", "factor"):
            rows.append(AssumptionRow("f", f"(1) Window's smallest eigenvalue at constant estimated risk, {MARKET_NAMES[m]}", m, "eigen-const"))
            rows.append(AssumptionRow("f", f"(1) Direction most underestimated at constant estimated risk, {MARKET_NAMES[m]}", m, "under-const"))
        for m in ("iid", "equal50", "garch", "factor"):
            for rule, label in (("losing", "after each losing step"), ("behind", "while behind"),
                                ("timed", "where the window overestimates")):
                rows.append(AssumptionRow("f", f"Pauses at tiny weights {label}, {MARKET_NAMES[m]}", m, "pause-tiny", rule))
    if "m" in parts:
        for r in jt.ROWS:
            m = "t4" if r.tail else "main-regime" if r.kind == "regime" else "main" + ("100" if r.A == 100 else "")
            stops = {"fixed": ((None, None),), "grid": tuple(jw.GRID), "regime": tuple(jw.GRID),
                     "nullspace": tuple(jt.NULLSPACE_GRID), "stopping": ((None, None), (2.0, jw.MIN_T), (2.5, jw.MIN_T),
                                                                        *STOPS[-2:])}[r.kind]
            rows.append(AssumptionRow("m", f"Main: {r.name}", m, "stopping" if r.kind == "stopping" else "main", r,
                                      jt.STOP_NS if r.kind == "stopping" else (1, 2), stops, False))
    if "p" in parts:
        for s in (0, 1, 2, 3, 4):
            rows.append(AssumptionRow("p", f"Honest power, Sharpe {s}", f"drift{s}", "power", None, (1,), ((None, None),), False))
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
        self.cov = jr.estimator(self.R, p)
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
    if row.kind == "power":
        def one_asset(s, i, A):
            W = np.zeros((jw.T, A))
            W[:, 3] = 1.0
            return W
        base, key = one_asset, ("power",)
    elif row.kind == "main":
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
    elif row.kind == "eigen-const":
        base, key = (lambda s, i, A: jw.constant_risk(jw.eigen_weights(h.eigen(), s, i, h.cov, A), h.cov)), ("eigen-const",)
    elif row.kind == "under-const":
        base, key = (lambda s, i, A: jw.constant_risk(jw.eigen_weights(h.under()[0], s, i, h.cov, A), h.cov)), ("under-const",)
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
    if row.kind in ("pause", "pause-tiny"):
        cache = h.worlds.setdefault((row.kind, row.par), {})
        tiny = 1e-6 if row.kind == "pause-tiny" else None

        def make(i):
            key = (i, c, k0)
            if key not in cache:
                Sigma = h.Sigma if row.par == "timed" else None
                W = jw.pausing_weights(row.par, h.seed, i, h.R, h.cov, Sigma, c, k0, tiny=tiny)
                cache[key] = jr.trial_of_weights(W, h.R, h.cov)
            return cache[key]
        return make
    w = _world(h, row)
    if row.kind == "power":
        return lambda i: w.trial(i, ("honest", None), None, None, "norm")
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
        for stop in row.stops_of(n):
            make = _trial_maker(h, row, n, stop)
            trials = [make(i) for i in range(n)]
            hd = jr.Holdout(trials)
            passed = any(hd.joint(i, h.jb, jw.MIN_T, jw.THRESHOLD, h.p.get("stat", jr.DEFAULT_STAT)).passed for i in range(n))
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
    df, paths, cache_dir, stat = job
    path = os.path.join(cache_dir, f"bar-{stat + '-' if stat != 'psr' else ''}{df!r}-{paths}.npz") if cache_dir else None
    if path and os.path.exists(path):
        with np.load(path) as f:
            return df, {"T": jw.T, "min_t": jw.MIN_T, "threshold": jw.THRESHOLD, "df": df, "paths": paths, "seed": jw.SEED,
                        "zs": f["zs"], "ps": f["ps"]}
    jb = jr.calibrate(jw.T, jw.MIN_T, df, jw.THRESHOLD, paths, jw.SEED, stat)
    if path:
        os.makedirs(cache_dir, exist_ok=True)
        np.savez(path + ".tmp.npz", zs=jb["zs"], ps=jb["ps"])
        os.replace(path + ".tmp.npz", path)
    return df, jb


def prepare_bars(rows: list, seeds: int, paths: int, pool, chunks, cache_dir: str | None = None, stat: str = jr.DEFAULT_STAT) -> dict:
    """Every holdout's fit, and a table per distinct df."""
    dfs: set = set()
    by_market: dict = {}
    for name in sorted({r.market for r in rows}):
        fits: set = set()
        for part in pool.imap_unordered(holdout_dfs, [(name, s) for s in chunks(seeds)]):
            fits |= part
        by_market[name] = (min(fits), max(fits))
        dfs |= fits
    bars = dict(pool.imap_unordered(calibrate_df, [(df, paths, cache_dir, stat) for df in sorted(dfs)]))
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


# ---------------------------------------------------------------- the candidate fixes, standalone only

WINDOWS = ((60, 20), (20, 20), (120, 20), (250, 20), (60, 60))
COVS = ("sample", "lw", "minwin", "eigfloor")
FIX_NAMES = {"sample": "A", "lw": "A + B1", "minwin": "A + B2", "eigfloor": "A + B3"}
FIX_PARTS = "abcdemp"
AIMED_PARTS = "f"              # not in the full table: what each bound on one normalized return invites
RISK_FLOORS = (0.25, 0.5)
WINSORS = (3, 4, 5)


def fix_name(c: dict) -> str:
    bounds = ([f"C1 f={c['risk_floor']:g}"] if c.get("risk_floor") else []) + ([f"C2 k={c['winsor']:g}"] if c.get("winsor") else [])
    return " + ".join(["A", *bounds]) if bounds else FIX_NAMES[c["cov"]]


def bar_stat(c: dict) -> str:
    """Whose table the configuration's bar is: a floor changes no null return, a winsorization does."""
    return f"w{c['winsor']:g}" if c.get("winsor") else c["stat"]


def fix_configurations() -> list:
    """The covariance candidates first, so that a run saved before the bounds resumes; every window of each."""
    base = {"stat": "t", "cov": "sample", "floor": jw.P["floor"]}
    return [{**base, "cov": c, "window": w, "warmup": m} for w, m in WINDOWS for c in COVS] + \
        [{**base, "risk_floor": f, "window": w, "warmup": m} for w, m in WINDOWS for f in RISK_FLOORS] + \
        [{**base, "winsor": k, "window": w, "warmup": m} for w, m in WINDOWS for k in WINSORS] + \
        [{**base, "risk_floor": 0.5, "winsor": 4, "window": w, "warmup": m} for w, m in WINDOWS]


def targeted_configurations() -> list:
    return [c for c in fix_configurations() if c["cov"] == "sample" and (c["window"], c["warmup"]) == WINDOWS[0]]


# Above nominal under A at 60/20, 2000 seeds; the rest of the pass are the rows above nominal under the current rule,
# the hedges and the pauses.
ABOVE_UNDER_A = ("(1) Window's smallest eigenvalue, iid", "(1) Window's smallest eigenvalue, one-factor GARCH",
                 "one-factor GARCH, rho = 0.5: flat once ahead", "(1) Direction most underestimated, GARCH",
                 "(3) Trades above 3.0x, floor otherwise, GARCH")


def targeted_rows() -> list:
    def wanted(r):
        attack = ((r.name.startswith("(2) Trades") and r.name.endswith(("iid, 30 equal assets", "iid, 50 equal assets", "iid, 58 equal assets")))
                  or (r.name.startswith("(3) Trades") and r.name.endswith("GARCH, 50 assets")))
        return attack or "Hedge" in r.name or r.part in ("d", "f") or r.name in ABOVE_UNDER_A
    return [r for r in rows_of(FIX_PARTS + AIMED_PARTS) if wanted(r)]


def fix_summary(rows: dict) -> dict:
    """What the choice reads: the worst cell over the table, the hedges, the pauses, honest refusals, power."""
    def cells(pred):
        return [(c["rate"], k, n, c["t_eff"], c["refused"]) for k, v in rows.items() if pred(k, v)
                for n, c in v["cells"].items()]
    top = max(cells(lambda k, v: v["part"] != "p"), key=lambda x: x[0])
    hedge = max(cells(lambda k, v: "Hedge" in k), key=lambda x: x[0])
    pause = max(cells(lambda k, v: v["part"] == "d"), key=lambda x: x[0])
    honest = cells(lambda k, v: "onest," in k and v["part"] == "m")
    power = {k[-1]: rows[k]["cells"]["1"] for k in rows if k.startswith("Honest power")}
    return {"worst": top, "hedge": hedge, "pause": pause, "above": sum(1 for v in rows.values() if v["part"] != "p"
                                                                       for c in v["cells"].values() if c["rate"] > NOMINAL),
            "honest_refused": max(x[4] for x in honest), "honest_t_eff": min(x[3] for x in honest),
            "pause_t_eff": min(c[3] for c in cells(lambda k, v: v["part"] == "d")),
            "power": {s: {"rate": c["rate"], "refused": c["refused"]} for s, c in power.items()}}
