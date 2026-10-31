"""Inside the implementation (tests/risk_world.py: the real exposure, calibration and promote code),
under c(n), 2000 seeds per cell: the two adversaries on the risk estimate (null space, a volatility
regime the window lags), every trial stopping once ahead (n = 1, 2, 5, 10, 50; normal and Student-t(4)
markets, the bar at each one's fitted df), and the honest power table, under the default rule (version 2,
the plain t, since 2026-10-30). Run from anywhere:
    uv run python tools/joint_bar/implementation_check_rest.py"""
import os as _os, sys as _sys
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_sys.path[:0] = [_HERE, _os.path.join(_HERE, "..", "..", "tests")]
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from lockrun import calibration
from risk_world import (MIN_T, PATHS, REGIME, SEED, T, THRESHOLD, GRID, Ledger, adversary, custom_adversary,
                        joint_bar, market, nullspace_strategy, regime_strategy)

SEEDS = 2000


def t4_bar() -> dict:
    R = market(0, tail=4)
    used, fitted = calibration.fit_df(calibration.residuals({a: R[:, a] for a in range(R.shape[1])}))
    return calibration.calibrate(T, MIN_T, used, THRESHOLD, PATHS, SEED, df_fitted=fitted)


def work(job):
    kind = job[0]
    if kind == "nullspace":
        _, n, c, k0 = job
        adv = custom_adversary(nullspace_strategy, n, c, k0, A=100)
    elif kind == "regime":
        _, n, c, k0 = job
        adv = custom_adversary(regime_strategy, n, c, k0, regime=REGIME)
    elif kind == "stopping":
        _, tail, n, c = job
        jb = t4_bar() if tail else joint_bar()
        c = calibration.bar(jb, n) + (0.3 if c == "c(n)+0.3" else 0.0) if isinstance(c, str) else c
        variant = ("honest", None) if c is None else ("flat", None)
        adv = adversary(variant, n, c, MIN_T, jb=jb, tail=tail)
    else:                                                 # power: one asset held, true Sharpe S annualized
        _, s = job
        jb = joint_bar()

        def adv(seed):
            R = market(seed, drift=s / np.sqrt(252))
            W = np.zeros((T, 8))
            W[:, 3] = 1.0
            L = Ledger(jb)
            return L.passes(L.trial(W, R))
    return job, sum(adv(s) for s in range(SEEDS))


if __name__ == "__main__":
    jobs = [("nullspace", n, c, k0) for n in (1, 2) for c in (2.0, 2.5, 3.0) for k0 in (2, 100)]
    jobs += [("regime", n, c, k0) for n in (1, 2) for c, k0 in GRID]
    jobs += [("stopping", tail, n, c) for tail in (None, 4) for n in (1, 2, 5, 10, 50)
             for c in (None, 2.0, 2.5, "c(n)", "c(n)+0.3")]
    jobs += [("power", s) for s in (0.0, 1.0, 2.0, 3.0, 4.0)]
    with ProcessPoolExecutor(10) as ex:
        res = dict(ex.map(work, jobs))
    for kind in ("nullspace", "regime"):
        for n in (1, 2):
            h, job = max((h, j) for j, h in res.items() if j[0] == kind and j[1] == n)
            print(f"{kind} n={n}: worst {h}/{SEEDS} = {h / SEEDS:.4f} (c={job[2]}, k0={job[3]})", flush=True)
    for tail in (None, 4):
        for n in (1, 2, 5, 10, 50):
            cells = "  ".join(f"{c or 'honest'} {res[('stopping', tail, n, c)] / SEEDS:.4f}"
                              for c in (None, 2.0, 2.5, "c(n)", "c(n)+0.3"))
            print(f"every trial stopping, tail {tail or 'normal'}, n={n}: {cells}", flush=True)
    for s in (0.0, 1.0, 2.0, 3.0, 4.0):
        print(f"honest power S={s}: {res[('power', s)] / SEEDS:.3f}", flush=True)
