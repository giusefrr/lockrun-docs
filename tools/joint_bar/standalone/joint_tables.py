"""Every table of tools/joint_bar/README.md: one function per table, each a dict that run.py prints.

Each cell's count is a sum over seeds 0 .. N-1; a seed's PASS decisions do not depend on the others, the
worker count or the order, so a table is deterministic in its seeds.
"""
from __future__ import annotations

import math
import sys
import time
from dataclasses import dataclass

import numpy as np

import joint_rule as jr
import joint_world as jw

JB = {}     # each worker's bars, set by the pool's initializer


def set_bars(bars: dict) -> None:
    JB.update(bars)


# ---------------------------------------------------------------- the adversaries table

@dataclass(frozen=True)
class Row:
    name: str
    kind: str                 # grid (c and k0 from GRID), fixed (no stop), nullspace, regime, stopping
    variant: tuple = (None, None)
    A: int = 8
    tail: float | None = None


ROWS = [
    Row("Honest, constant exposure", "fixed", ("honest", None)),
    Row("Honest, 10% random flat days", "fixed", ("honest-flat-days", None)),
    Row("Flat once ahead", "grid", ("flat", None)),
    Row("Flat, trading again for the last 1 period", "grid", ("resume", 1)),
    Row("Flat, trading again for the last 2 periods", "grid", ("resume", 2)),
    Row("Flat, trading again for the last 5 periods", "grid", ("resume", 5)),
    Row("Weights times 1e-6 once ahead", "grid", ("tiny", 1e-6)),
    Row("Weights times 0.01 once ahead", "grid", ("tiny", 0.01)),
    Row("Weights times 0.05 once ahead", "grid", ("tiny", 0.05)),
    Row("Same gross over every asset, 8 assets", "grid", ("diversify", None)),
    Row("Same gross over every asset, 100 assets", "grid", ("diversify", None), A=100),
    Row("Hedge of two twin assets", "grid", ("hedge", None)),
    Row("Hedge with a drifting ratio", "grid", ("hedge-drift", None)),
    Row("Only the lowest-variance asset", "grid", ("lowvar", None)),
    Row("Pausing in the window covariance's null space (100 assets)", "nullspace", ("nullspace", None), A=100),
    Row("An asset whose volatility the window lags (falls tenfold)", "regime", ("regime", None)),
    Row("Every trial stopping at c(n), n = 1 to 50, normal market", "stopping"),
    Row("Every trial stopping at c(n), n = 1 to 50, Student-t(4) market", "stopping", tail=4),
]
STOP_NS = (1, 2, 5, 10, 50)
STOP_CS = (None, 2.0, 2.5, "c(n)", "c(n)+0.3")
NULLSPACE_GRID = [(c, k0) for c in (2.0, 2.5, 3.0) for k0 in (2, 100)]


def _passes(w: jw.SeedWorld, trials: list, jb: dict | None) -> bool:
    """Any of the researcher's trials PASSes (it can promote each): under the joint bar, or the DSR with
    the fresh verification reserved when jb is None."""
    h = jr.Holdout(trials)
    if jb is None:
        return any(h.before(i, jw.MIN_T, jw.THRESHOLD, reserved=1).passed for i in range(len(trials)))
    return any(h.joint(i, jb, jw.MIN_T, jw.THRESHOLD).passed for i in range(len(trials)))


def _row_seed(row: Row, seed: int, before: bool, garch_p: dict | None = None) -> dict:
    """{(column, n, c, k0): passed} of one row on one seed; garch_p: on the GARCH null, the bar at its fitted
    df, with that window and warm-up."""
    out = {}
    if row.kind == "stopping":
        if garch_p:
            jb, w = JB["garch"], jw.SeedWorld(seed, 8, R=jw.garch_market(seed, 8)[0], p=garch_p)
        else:
            jb, w = JB["t4" if row.tail else "normal"], jw.SeedWorld(seed, 8, tail=row.tail)
        for n in STOP_NS:
            for label in STOP_CS:
                c = jr.bar(jb, n) + (0.3 if label == "c(n)+0.3" else 0.0) if isinstance(label, str) else label
                v = ("honest", None) if c is None else ("flat", None)
                trials = [w.trial(i, v, c, jw.MIN_T, "norm") for i in range(n)]
                out[("joint", n, label, jw.MIN_T)] = _passes(w, trials, jb)
        return out
    market_kw = {"regime": jw.REGIME} if row.kind == "regime" else {}
    if garch_p:
        w = jw.SeedWorld(seed, row.A, R=jw.garch_market(seed, row.A, **market_kw)[0], p=garch_p)
    else:
        w = jw.SeedWorld(seed, row.A, **market_kw)
    bar_of = JB["garch"] if garch_p else JB.get("normal")
    grid = {"fixed": [(None, None)], "grid": jw.GRID, "regime": jw.GRID, "nullspace": NULLSPACE_GRID}[row.kind]
    for c, k0 in grid:
        for n in (1, 2):
            joint = [w.trial(i, row.variant, c, k0, "norm") for i in range(n)]
            out[("joint", n, c, k0)] = _passes(w, joint, bar_of)
            if before and row.kind in ("fixed", "grid"):
                raw = [w.trial(i, row.variant, c, k0, "raw") for i in range(n)]
                out[("before", n, c, k0)] = _passes(w, raw, None)
    return out


def row_counts(job: tuple) -> dict:
    row, seeds, before = job
    counts: dict = {}
    for seed in seeds:
        for k, v in _row_seed(row, seed, before).items():
            counts[k] = counts.get(k, 0) + bool(v)
    return counts


def worst(counts: dict, column: str, n: int | None = None) -> tuple:
    """(the largest count, its cell) of a column, over the stopping rule."""
    return max(((h, k) for k, h in counts.items() if k[0] == column and (n is None or k[1] == n)), key=lambda x: x[0])


def selected_rows(names: str | None) -> list[Row]:
    if not names:
        return ROWS
    wanted = [x.strip().lower() for x in names.split(",")]
    return [r for r in ROWS if any(w in r.name.lower() for w in wanted)]


def adversaries(seeds: int, pool, chunks, rows: str | None = None, before: bool = True) -> dict:
    out = {}
    for row in selected_rows(rows):
        total: dict = {}
        for part in pool.imap_unordered(row_counts, [(row, s, before) for s in chunks(seeds)]):
            for k, v in part.items():
                total[k] = total.get(k, 0) + v
        if row.kind == "stopping":
            h = max(v for k, v in total.items() if k[2] == "c(n)")     # the stop the row is named for
            top, cell = worst(total, "joint")
            out[row.name] = {"before": None, "joint": h / seeds, "any_stop": top / seeds, "worst_any_stop": cell[1:3]}
        else:
            cells = {}
            for col in ("before", "joint"):
                has = before and row.kind in ("fixed", "grid") or col == "joint"
                for n in (1, 2):
                    if has:
                        h, cell = worst(total, col, n)
                        cells[f"{col}{n}"] = h / seeds
                        cells[f"worst_{col}{n}"] = cell[2:]
                    else:
                        cells[f"{col}{n}"] = None
            out[row.name] = cells
        print(f"  ... {row.name}", file=sys.stderr, flush=True)
    return out


# ---------------------------------------------------------------- the assumptions

NOMINAL = 0.05
RHOS = (0.5, 0.9)
AWARE = (("scale", "weights times true / estimated risk"), ("select", "all weight where the window most underestimates"),
         ("pause", "the same, flat where it underestimates least"))


def above_nominal(rate: float | None) -> str:
    return "above nominal" if rate is not None and rate > NOMINAL else ""


def _assumption_cells(spec: tuple, seed: int, p: dict) -> dict:
    """{(n, c, k0): passed} of one row of the table on one seed."""
    part, what, par = spec
    if part == "b":
        row = next(r for r in ROWS if r.name == what)
        if row.tail:
            return {}
        return {k[1:]: v for k, v in _row_seed(row, seed, False, p).items()}
    if part == "a":
        w = jw.SeedWorld(seed, 8, base=lambda s, i, A: jw.correlated_weights(s, i, A, par), p=p)
        jb = JB["normal"]
    else:
        if par == "garch":
            R, sigma = jw.garch_market(seed, 8)
            jb = JB["garch"]
        else:
            R, sigma = jw.market(seed, 8), np.broadcast_to(jw.market_vols(8), (jw.T, 8))
            jb = JB["normal"]
        cov = jr.window_covariances(R, p)
        w = jw.SeedWorld(seed, 8, R=R, p=p, base=lambda s, i, A: jw.risk_aware_weights(what, s, i, R, sigma, cov))
    honest = part == "a" and what == "honest"
    out = {}
    for c, k0 in ([(None, None)] if honest else [(None, None), *jw.GRID]):
        v = ("honest", None) if c is None else ("flat", None)
        for n in (1, 2):
            out[(n, c, k0)] = _passes(w, [w.trial(i, v, c, k0, "norm") for i in range(n)], jb)
    return out


def assumption_counts(job: tuple) -> dict:
    spec, seeds, p = job
    counts: dict = {}
    for seed in seeds:
        for k, v in _assumption_cells(spec, seed, p).items():
            counts[k] = counts.get(k, 0) + bool(v)
    return counts


def assumption_rows(parts: str) -> list:
    rows = []
    if "a" in parts:
        rows += [(f"(a) Trials sharing a latent signal, rho = {rho}: {label}", ("a", what, rho))
                 for rho in RHOS for what, label in (("honest", "honest"), ("flat", "flat once ahead"))]
    if "b" in parts:
        rows += [(f"(b) GARCH(1,1) null: {'Every trial stopping, n = 1 to 50' if r.kind == 'stopping' else r.name}",
                  ("b", r.name, None)) for r in ROWS if not r.tail]
    if "c" in parts:
        rows += [(f"(c) Knows the estimator, {mkt} market: {label}", ("c", what, m))
                 for m, mkt in (("iid", "iid"), ("garch", "GARCH")) for what, label in AWARE]
    return rows


def assumptions(seeds: int, pool, chunks, parts: str, p: dict) -> dict:
    out = {}
    for name, spec in assumption_rows(parts):
        total: dict = {}
        for part in pool.imap_unordered(assumption_counts, [(spec, s, p) for s in chunks(seeds)]):
            for k, v in part.items():
                total[k] = total.get(k, 0) + v
        cells = {}
        ns = sorted({k[0] for k in total})
        if spec[1] == "Every trial stopping at c(n), n = 1 to 50, normal market":
            h = max(v for k, v in total.items() if k[1] == "c(n)")
            top = max(total.items(), key=lambda x: x[1])
            cells = {"at_cn": h / seeds, "any_stop": top[1] / seeds, "worst": top[0]}
        else:
            for n in ns:
                c = max(((v, k) for k, v in total.items() if k[0] == n), key=lambda x: x[0])
                cells[f"n{n}"] = c[0] / seeds
                cells[f"worst{n}"] = c[1][1:]
        out[name] = cells
        print(f"  ... {name}", file=sys.stderr, flush=True)
    return out


# ---------------------------------------------------------------- the first table

def _finding_cell(job: tuple) -> dict:
    seeds, n, grid, mode, par = job
    out = {}
    for seed in seeds:
        R = jw.iid_market(seed)
        rs = [(jw.random_weights(seed, i) * R).sum(1) for i in range(n)]
        ts = [jw.running_t(r) for r in rs]
        decided: dict = {}
        for c, k0 in grid:
            ks = tuple(jw.first_crossing(t, c, k0) for t in ts)
            if ks not in decided:
                trials = [jr.trial_of_returns(jw.stopped_returns(r, k, mode, par)) for r, k in zip(rs, ks)]
                decided[ks] = jr.Holdout(trials).before(jw.best_run(trials), jw.MIN_T, jw.THRESHOLD, reserved=1).passed
            out[(c, k0)] = out.get((c, k0), 0) + decided[ks]
    return out


FINDING = [   # the README's row, n, grid, what happens once ahead, seeds in full mode
    ("Honest: constant exposure, never stops", 1, [(1e9, 2)], "flat", None, 10000),
    ("Flat once its t-statistic reaches c (best c and first stop k0)", 1, jw.FINDING_GRID, "flat", None, 3000),
    ("Flat once its t-statistic reaches c (best c and first stop k0)", 2, jw.FINDING_GRID, "flat", None, 3000),
    ("The same, trading again for the last period", 1, jw.EVASION_GRID, "resume", 1, 2000),
    ("The same, weights times 1e-6 instead of zero", 1, jw.EVASION_GRID, "tiny", 1e-6, 2000),
]


def finding(seeds: int | None, pool, chunks) -> list:
    out = []
    for name, n, grid, mode, par, full in FINDING:
        s = seeds or full
        total: dict = {}
        for part in pool.imap_unordered(_finding_cell, [(c, n, grid, mode, par) for c in chunks(s)]):
            for k, v in part.items():
                total[k] = total.get(k, 0) + v
        (c, k0), h = max(total.items(), key=lambda x: x[1])
        out.append({"name": name, "n": n, "rate": h / s, "seeds": s, "c": c, "k0": k0})
    return out


# ---------------------------------------------------------------- honest power

def _power_cell(job: tuple) -> dict:
    seeds, s = job
    b = j = 0
    for seed in seeds:
        R = jw.market(seed, drift=s / np.sqrt(252))
        W = np.zeros((jw.T, 8))
        W[:, 3] = 1.0
        t = jr.trial_of_weights(W, R, jr.window_covariances(R))
        h = jr.Holdout([t])
        b += h.before(0, jw.MIN_T, jw.THRESHOLD, reserved=1).passed
        j += h.joint(0, JB["normal"], jw.MIN_T, jw.THRESHOLD).passed
    return {s: (b, j)}


def power(seeds: int, pool, chunks) -> dict:
    out = {}
    for s in (0.0, 1.0, 2.0, 3.0, 4.0):
        b = j = 0
        for part in pool.imap_unordered(_power_cell, [(c, s) for c in chunks(seeds)]):
            b += part[s][0]
            j += part[s][1]
        out[s] = {"before": b / seeds, "joint": j / seeds}
    return out


# ---------------------------------------------------------------- rules tried and dropped

def _round2_trial(seed: int, i: int, R: np.ndarray, kind: str, c: float, k0: int) -> tuple:
    """Round 2's strategy: one random asset, long or short, every period (gross 1), stopping on its raw t."""
    A = R.shape[1]
    rng = np.random.default_rng([seed, i, 1])
    W = np.zeros((jw.T, A))
    W[np.arange(jw.T), rng.integers(0, A - (2 if kind == "hedge" else 0), jw.T)] = rng.choice([-1, 1], jw.T)
    k = jw.first_crossing(jw.running_t((W * R).sum(1)), c, k0)
    if k is not None:
        if kind == "diversify":
            W[k:] = 1.0 / A
        else:
            W[k:] = 0.0
            W[k:, -2], W[k:, -1] = 1.0, -1.0
    return (W * R).sum(1), np.abs(W).sum(1)


CRIT_FIXED, CRIT_SEQUENTIAL = 1.6448536, 2.244


def _gross_rule(trials: list, crit: float) -> bool:
    """Normalizing by gross exposure on the steps with g >= 10% of its median, with the DSR's sr0 at N = n + 1
    and crit: the critical value of a fixed T, or the sequential one (sup over k, round 2's calibration)."""
    ms = []
    for r, g in trials:
        pos = g > 0
        active = pos & (g >= 0.10 * np.median(g[pos]))
        try:
            ms.append(jr.moments(r[active] / g[active]))
        except ValueError:
            ms.append(None)
    srs = [m.sr for m in ms if m is not None]
    for m in ms:
        if m is None or m.T < jw.MIN_T:
            continue
        v_null = jr.null_sharpe_variance(m.T)
        sr0 = jr.expected_max_sharpe(max(jr.sharpe_variance(srs), v_null) if len(srs) >= 2 else v_null, len(trials) + 1)
        den = 1 - m.skew * m.sr + (m.kurt - 1) / 4 * m.sr ** 2
        if den > 0 and (m.sr - sr0) * np.sqrt(m.T - 1) / np.sqrt(den) >= crit:
            return True
    return False


GROSS_GRID = [(c, k0) for c in (1.5, 2.0, 2.2, 2.5, 3.0) for k0 in (2, 3, 20, 100)]


def _gross_cell(job: tuple) -> dict:
    seeds, kind, A = job
    out = {}
    for seed in seeds:
        R = np.random.default_rng([seed, 0]).normal(0, 0.01, (jw.T, A))
        if kind == "hedge":
            R[:, -1] = R[:, -2] + np.random.default_rng([seed, 5]).normal(0, 1e-4, jw.T)
        for c, k0 in GROSS_GRID:
            for n in (1, 2):
                trials = [_round2_trial(seed, i, R, kind, c, k0) for i in range(n)]
                for crit in (CRIT_FIXED, CRIT_SEQUENTIAL):
                    out[(n, crit, c, k0)] = out.get((n, crit, c, k0), 0) + _gross_rule(trials, crit)
    return out


SHRINK_WINDOWS, SHRINK_LAMBDAS = (20, 60, 250), (0.0, 0.001, 0.01, 0.1)


def _shrunk_cov(R: np.ndarray, window: int, lam: float) -> tuple:
    S, ok = jr.window_covariances(R, {"window": window, "warmup": 20})
    d = np.einsum("tii->ti", S)
    return (1 - lam) * S + lam * (d[:, :, None] * np.eye(R.shape[1])), ok


def _shrink_cell(job: tuple) -> dict:
    """The hedge, n = 1, under the rule as first simulated: a shrunk S, no null-space test, the bar c(2)."""
    seeds, c2 = job
    out = {}
    for seed in seeds:
        R = jw.market(seed, 8)
        for window in SHRINK_WINDOWS:
            for lam in SHRINK_LAMBDAS:
                S, ok = _shrunk_cov(R, window, lam)
                full = np.full((jw.T, 8, 8), np.nan)
                full[ok] = S
                base = jw.base_weights(seed, 0, 8)
                t, idx = _shrunk_normalized(base, R, full)
                for c, k0 in jw.GRID:
                    hit = np.flatnonzero((idx >= k0 - 1) & (t >= c))
                    W = base if not hit.size else jw.after_stop(base.copy(), int(idx[hit[0]]) + 1, ("hedge", None), seed, 0)
                    x, _ = _shrunk_x(W, R, full)
                    out[(window, lam, c, k0)] = out.get((window, lam, c, k0), 0) + _z_above(x, c2)
    return out


def _shrunk_x(W: np.ndarray, R: np.ndarray, S: np.ndarray) -> tuple:
    r = (W * R).sum(1)
    with np.errstate(invalid="ignore"):
        risk = np.sqrt(np.maximum(np.einsum("ti,tij,tj->t", W, S, W), 0))
    live = (np.abs(W).sum(1) > 0) & np.isfinite(risk) & (risk > 0)
    if not live.any():
        return np.array([]), np.array([], int)
    idx = np.flatnonzero(live & (risk >= 0.10 * np.median(risk[live])))
    return r[idx] / risk[idx], idx


def _shrunk_normalized(W: np.ndarray, R: np.ndarray, S: np.ndarray) -> tuple:
    x, idx = _shrunk_x(W, R, S)
    return jw.running_t(x), idx


def _z_above(x: np.ndarray, c: float) -> bool:
    try:
        m = jr.moments(x) if len(x) >= 4 else None
    except ValueError:
        m = None
    if m is None or m.T < jw.MIN_T:
        return False
    den = 1 - m.skew * m.sr + (m.kurt - 1) / 4 * m.sr ** 2
    return bool(den > 0 and m.sr * np.sqrt(m.T - 1) / np.sqrt(den) >= c)


def _composed_excess() -> dict:
    """The sequential value composed with the DSR's sr0, over the exact quantile of the maximum over N
    trials of sup z_k: both in t-units, N counting the reservation."""
    rng = np.random.default_rng(8)
    sups = np.concatenate([jr.sup_z(rng.normal(size=(50_000, jw.T)), jw.MIN_T) for _ in range(6)])
    v = jr.null_sharpe_variance(jw.T)
    return {N: float(jr.expected_max_sharpe(v, N) * np.sqrt(jw.T - 1) + 2.244 - np.quantile(sups, 0.95 ** (1 / N)))
            for N in (2, 3, 6, 11, 51)}


def dropped(seeds: int, pool, chunks) -> dict:
    out = {}
    for label, kind, A in (("hedge", "hedge", 8), ("100-asset spread", "diversify", 100)):
        total: dict = {}
        for part in pool.imap_unordered(_gross_cell, [(c, kind, A) for c in chunks(seeds)]):
            for k, v in part.items():
                total[k] = total.get(k, 0) + v
        out[f"gross, {label}"] = {f"n={n} {name}": max(h for k, h in total.items() if k[:2] == (n, crit)) / seeds
                                  for n in (1, 2)
                                  for name, crit in (("fixed-T value", CRIT_FIXED), ("sequential value", CRIT_SEQUENTIAL))}
    # The simulated rule's bar: its first calibration (2M paths, seed 1), c at N = n + 1 = 2.
    rng = np.random.default_rng(1)
    chunk = int(2.5e8 / (12 * 8 * jw.T))
    sups = [jr.sup_z(rng.normal(size=(min(chunk, 2_000_000 - s), jw.T)), jw.MIN_T) for s in range(0, 2_000_000, chunk)]
    c2 = float(np.quantile(np.concatenate(sups), 0.95 ** 0.5))
    total = {}
    for part in pool.imap_unordered(_shrink_cell, [(c, c2) for c in chunks(seeds)]):
        for k, v in part.items():
            total[k] = total.get(k, 0) + v
    out["shrinkage, hedge"] = {f"W={w} lambda={lam}": max(h for k, h in total.items() if k[:2] == (w, lam)) / seeds
                               for w in SHRINK_WINDOWS for lam in SHRINK_LAMBDAS}
    out["composed bar's excess, t-units"] = {f"N={k}": v for k, v in _composed_excess().items()}
    return out


# ---------------------------------------------------------------- the rest

def bar_table() -> dict:
    jb = jw.joint_bar()
    return {n: jr.bar(jb, n) for n in (1, 2, 5, 10, 50, 100, 1000)}


def sizing() -> dict:
    """An edge in sizing is not measured (the rule's t over the raw t), and the warm-up's cost (T_eff)."""
    rng = np.random.default_rng(3)
    n = 20000
    sr = np.where(rng.random(n) < 0.5, 0.05, 0.25)
    R = (0.01 * (sr + rng.normal(size=n)))[:, None]
    W = (sr / 0.25)[:, None]
    t = jr.trial_of_weights(W, R, jr.window_covariances(R))
    honest = jr.trial_of_weights(jw.base_weights(0, 0, 8), jw.market(0), jr.window_covariances(jw.market(0)))
    ratio = t.tstat / (t.m.sr * math.sqrt(n))
    return {"rule's t over the raw t": ratio, "raw t over the rule's t": 1 / ratio, "largest T_eff at T = 250": honest.t_eff}


def cost(quick: bool) -> dict:
    """The calibration on one core: seconds per table and the process's peak memory."""
    import resource   # POSIX only
    out = {}
    runs = [(250, 200.0, 200_000), (250, 4.2, 200_000)] if quick else \
        [(250, 200.0, 2_000_000), (250, 4.2, 2_000_000), (2500, 200.0, 2_000_000)]
    for T, df, paths in runs:
        t0 = time.perf_counter()
        jr.calibrate(T, 100, df, 0.95, paths, 1)
        out[f"T={T} df={df} paths={paths}"] = round(time.perf_counter() - t0, 1)
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    out["peak MiB"] = round(rss / 2**20 if sys.platform == "darwin" else rss / 2**10)
    return out


