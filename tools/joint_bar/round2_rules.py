"""Plan item 3, case 4: the proposed three-part rule, simulated (nothing implemented).

Each trial is (r, g): its returns and its gross exposure per period. The researcher has n trials;
N = n + 1 (the fresh verification reserved, as the service computes). PASS counts when ANY of the
researcher's trials passes (it can promote each).
  today      the real evaluate_promotion (families, detector, floor), on r
  R12        x = r/g on active periods (g > 0 and g >= 10% of the median of g over g > 0); T_eff = active
             periods; min_t on T_eff; V = max(sample var of the trials' Sharpes, v_null(T_eff cand));
             sr0 = EMax(V, N); PASS iff (sr - sr0) sqrt(T_eff - 1)/sqrt(den) >= 1.645 (PSR >= 0.95)
  R123       the same with the critical value c_seq (sup over k in [min_t, T], calibrated under the null)
"""
import os as _os, sys as _sys
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_sys.path[:0] = [_HERE, _os.path.join(_HERE, "..", "..", "tests")]
import sys
import numpy as np
from adversary_world import Ledger, MIN_T, T, running_tstat
from lockrun import stats

C_SEQ = 2.244
SEEDS = 2000

def market(seed, A=8, dup=False):
    R = np.random.default_rng([seed, 0]).normal(0, 0.01, (T, A))
    if dup:                                   # the last asset tracks the one before it (an ETF and its twin)
        R[:, -1] = R[:, -2] + np.random.default_rng([seed, 5]).normal(0, 1e-4, T)
    return R

def base_weights(seed, i, A, single):
    """Unit gross exposure every period: a random direction, or one random asset long or short."""
    rng = np.random.default_rng([seed, i, 1])
    if single:
        W = np.zeros((T, A)); W[np.arange(T), rng.integers(0, A - (1 if single == "dup" else 0) - (1 if single == "dup" else 0), T)] = rng.choice([-1, 1], T)
        return W
    W = rng.normal(size=(T, A))
    return W / np.abs(W).sum(1, keepdims=True)

def trial(seed, i, R, variant, c, k0):
    A = R.shape[1]
    single = {"diversify": True, "hedge": "dup"}.get(variant[0], False)
    W = base_weights(seed, i, A, single)
    r = (W * R).sum(1)
    if variant[0] == "honest-flat-days":     # 10% of days flat, at random, not a terminal run
        W[np.random.default_rng([seed, i, 9]).random(T) < 0.10] = 0.0
    elif variant[0] != "honest":
        hit = np.flatnonzero((np.arange(1, T + 1) >= k0) & (running_tstat(r) >= c))
        if hit.size:
            k = hit[0] + 1
            kind, par = variant
            if kind == "flat":
                W[k:] = 0.0
            elif kind == "resume":
                W[k:T - par] = 0.0
            elif kind == "tiny":
                W[k:] *= par
            elif kind == "diversify":              # same gross, spread over every asset: less risk per unit
                W[k:] = 1.0 / A
            elif kind == "hedge":                  # long one twin, short the other: gross 2, almost no risk
                W[k:] = 0.0; W[k:, -2], W[k:, -1] = 1.0, -1.0
    r = (W * R).sum(1)
    return r, np.abs(W).sum(1)

def today(trials):
    L = Ledger(); ids = [L.trial(r) for r, _ in trials]
    return any(L.passes(i) for i in ids)

def normalized(r, g):
    pos = g > 0
    if not pos.any():
        return None
    active = pos & (g >= 0.10 * np.median(g[pos]))
    x = r[active] / g[active]
    try:
        return stats.moments(x)
    except ValueError:
        return None

def new_rule(trials, crit):
    ms = [normalized(r, g) for r, g in trials]
    srs = [m.sr for m in ms if m is not None]
    N = len(trials) + 1
    for m in ms:
        if m is None or m.T < MIN_T:
            continue
        v_null = stats.null_sharpe_variance(m.T)
        V = max(stats.sharpe_variance(srs), v_null) if len(srs) >= 2 else v_null
        sr0 = stats.expected_max_sharpe(V, N)
        den = 1 - m.skew * m.sr + (m.kurt - 1) / 4 * m.sr ** 2
        if den > 0 and (m.sr - sr0) * np.sqrt(m.T - 1) / np.sqrt(den) >= crit:
            return True
    return False

GRID = [(c, k0) for c in (1.5, 2.0, 2.2, 2.5, 3.0) for k0 in (2, 3, 20, 100)]
VARIANTS = [
    (("honest", None), {}), (("honest-flat-days", None), {}),
    (("flat", None), {}),
    (("resume", 1), {}), (("resume", 2), {}), (("resume", 5), {}),
    (("tiny", 1e-6), {}), (("tiny", 0.01), {}), (("tiny", 0.05), {}),
    (("diversify", None), {"A": 8}), (("diversify", None), {"A": 100}),
    (("hedge", None), {"dup": True}),
]

def rates(variant, mkt, n, c, k0):
    hits = {"today": 0, "R12": 0, "R123": 0}
    for seed in range(SEEDS):
        R = market(seed, **mkt)
        ts = [trial(seed, i, R, variant, c, k0) for i in range(n)]
        hits["today"] += today(ts)
        hits["R12"] += new_rule(ts, 1.6448536)
        hits["R123"] += new_rule(ts, C_SEQ)
    return {k: v / SEEDS for k, v in hits.items()}

if __name__ == "__main__":
  for variant, mkt in VARIANTS:
    for n in (1, 2):
        grid = [(None, None)] if variant[0].startswith("honest") else GRID
        res = [(rates(variant, mkt, n, c, k0), c, k0) for c, k0 in grid]
        best = {rule: max(res, key=lambda x: x[0][rule]) for rule in ("today", "R12", "R123")}
        label = f"{variant[0]}{'' if variant[1] is None else ' ' + str(variant[1])}{' A=' + str(mkt['A']) if 'A' in mkt else ''}"
        print(f"{label:22s} n={n}  " + "  ".join(f"{rule} {b[0][rule]:.4f} (c={b[1]},k0={b[2]})" for rule, b in best.items()), flush=True)
