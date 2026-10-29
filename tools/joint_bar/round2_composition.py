import os as _os, sys as _sys
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_sys.path[:0] = [_HERE, _os.path.join(_HERE, "..", "..", "tests")]
import sys
import numpy as np
from statistics import NormalDist
from round2_rules import C_SEQ, market, trial, new_rule, today, SEEDS
from adversary_world import Ledger, T, MIN_T
from lockrun import stats
Nd = NormalDist()

print(f"composition, c_seq={C_SEQ}: every trial goes flat once z_k >= c from k0 = min_t (the best stop against R123)")
for n in (1, 2, 5, 10, 50):
    seeds = SEEDS if n <= 10 else 500
    for label, variant, c in (("honest", ("honest", None), None), ("stop@c_seq", ("flat", None), C_SEQ),
                              ("stop@2.0", ("flat", None), 2.0)):
        hit = sum(new_rule([trial(s, i, market(s), variant, c, MIN_T) for i in range(n)], C_SEQ) for s in range(seeds))
        print(f"  n={n:>2} {label:11s} R123 PASS {hit}/{seeds} = {hit/seeds:.4f}", flush=True)

print("\nthe bar for an honest constant-exposure strategy, n=1 (N=2 with the reservation), V at its floor:")
v = stats.null_sharpe_variance(T)
sr0 = stats.expected_max_sharpe(v, 2)
for name, crit in (("today", Nd.inv_cdf(0.95)), ("R123", C_SEQ)):
    need = sr0 + crit / np.sqrt(T - 1)
    print(f"  {name}: observed per-period Sharpe >= {need:.4f} (t = {need*np.sqrt(T):.2f}; annualized, daily: {need*np.sqrt(252):.2f})")

print("\npower: an honest constant-exposure strategy with true annualized Sharpe S (daily periods, T=250), n=1:")
for S in (0.0, 1.0, 2.0, 3.0, 4.0):
    s = S / np.sqrt(252)
    hits = {"today": 0, "R123": 0}
    for seed in range(SEEDS):
        r = 0.01 * (np.random.default_rng([seed, 11]).normal(size=T) + s)
        g = np.ones(T)
        hits["today"] += today([(r, g)])
        hits["R123"] += new_rule([(r, g)], C_SEQ)
    print(f"  S={S}: today {hits['today']/SEEDS:.3f}  R123 {hits['R123']/SEEDS:.3f}", flush=True)
