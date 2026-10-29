"""Sensitivity of the window W and the diagonal shrinkage lambda, on the variants that attack the
risk estimate (n=1, normal market, adversary's best (c, k0)); 2000 seeds."""
import os as _os, sys as _sys
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_sys.path[:0] = [_HERE, _os.path.join(_HERE, "..", "..", "tests")]
import os, sys
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from round3_risk_sim import GRID, TABLES, covariances, market, new_rule, trial

CONFIGS = [(W, lam) for W in (20, 60, 250) for lam in (0.0, 0.001, 0.01, 0.1)]
VARIANTS = [(("hedge", None), 8), (("hedge-drift", None), 8), (("lowvar", None), 8), (("tiny", 1e-6), 8),
            (("diversify", None), 100), (("honest", None), 8)]

def work(seeds):
    counts = {}
    for seed in seeds:
        for A in (8, 100):
            R = market(seed, A)
            for W, lam in CONFIGS:
                S = covariances(R, W, lam)
                for variant, a in VARIANTS:
                    if a != A:
                        continue
                    grid = [(None, None)] if variant[0] == "honest" else GRID
                    for c, k0 in grid:
                        Ws = [trial(seed, 0, R, S, variant, c, k0, "norm")]
                        key = (variant, W, lam, c, k0)
                        counts[key] = counts.get(key, 0) + new_rule(R, S, Ws, TABLES["200.0"])
    return counts

if __name__ == "__main__":
    total = {}
    with ProcessPoolExecutor(10) as ex:
        for part in ex.map(work, [range(s, 2000, 10) for s in range(10)]):
            for k, v in part.items():
                total[k] = total.get(k, 0) + v
    for variant, A in VARIANTS:
        row = []
        for W, lam in CONFIGS:
            best = max((v, k[3], k[4]) for k, v in total.items() if k[0] == variant and k[1] == W and k[2] == lam)
            row.append(f"W{W}/l{lam}:{best[0]/2000:.4f}")
        print(f"{variant[0]}{'' if variant[1] is None else ' '+str(variant[1])} A={A}: " + " ".join(row), flush=True)
