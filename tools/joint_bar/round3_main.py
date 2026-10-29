"""Round 3: every variant (proposed W=60, lambda=0), all-adversaries-stopping, honest power. 2000 seeds."""
import os as _os, sys as _sys
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_sys.path[:0] = [_HERE, _os.path.join(_HERE, "..", "..", "tests")]
import os, sys
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from round3_risk_sim import GRID, MIN_T, T, TABLES, covariances, market, new_rule, today, trial, base, running_t, normalized
from round3_joint_bar import bar

W, LAM, SEEDS = 60, 0.0, 2000
VARIANTS = [(("honest", None), 8), (("honest-flat-days", None), 8), (("flat", None), 8),
            (("resume", 1), 8), (("resume", 2), 8), (("resume", 5), 8),
            (("tiny", 1e-6), 8), (("tiny", 0.01), 8), (("tiny", 0.05), 8),
            (("diversify", None), 8), (("diversify", None), 100),
            (("hedge", None), 8), (("hedge-drift", None), 8), (("lowvar", None), 8)]

def table_work(seeds):
    out = {}
    for seed in seeds:
        for A in (8, 100):
            R = market(seed, A); S = covariances(R, W, LAM)
            for variant, a in VARIANTS:
                if a != A: continue
                grid = [(None, None)] if variant[0].startswith("honest") else GRID
                for c, k0 in grid:
                    for n in (1, 2):
                        raw = [trial(seed, i, R, S, variant, c, k0, "raw") for i in range(n)]
                        norm = [trial(seed, i, R, S, variant, c, k0, "norm") for i in range(n)]
                        k = (variant, A, n, c, k0)
                        t, w = out.get(k, (0, 0))
                        out[k] = (t + today(R, raw), w + new_rule(R, S, norm, TABLES["200.0"]))
    return out

def stop_work(args):
    seeds, tail, key = args
    out = {}
    for seed in seeds:
        R = market(seed, 8, tail=tail); S = covariances(R, W, LAM)
        for n in (1, 2, 5, 10, 50):
            cN = bar(TABLES[key], n + 1)
            for label, c in (("honest", None), ("stop 2.0", 2.0), ("stop 2.5", 2.5), ("stop c(N)", cN), ("stop c(N)+0.3", cN + 0.3)):
                v = ("honest", None) if c is None else ("flat", None)
                Ws = [trial(seed, i, R, S, v, c, MIN_T, "norm") for i in range(n)]
                out[(tail, n, label)] = out.get((tail, n, label), 0) + new_rule(R, S, Ws, TABLES[key])
    return out

def power_work(seeds):
    out = {}
    for seed in seeds:
        for SA in (0.0, 1.0, 2.0, 3.0, 4.0):
            R = market(seed, 8, drift=SA / np.sqrt(252)); S = covariances(R, W, LAM)
            Wt = np.zeros((T, 8)); Wt[:, 3] = 1.0
            t, w = out.get(SA, (0, 0))
            out[SA] = (t + today(R, [Wt]), w + new_rule(R, S, [Wt], TABLES["200.0"]))
    return out

def merge(parts):
    tot = {}
    for p in parts:
        for k, v in p.items():
            tot[k] = tuple(a + b for a, b in zip(tot[k], v)) if isinstance(v, tuple) and k in tot else (tot.get(k, 0) + v if not isinstance(v, tuple) else v)
    return tot

if __name__ == "__main__":
    chunks = [range(s, SEEDS, 10) for s in range(10)]
    with ProcessPoolExecutor(10) as ex:
        tot = merge(ex.map(table_work, chunks))
        print("variant | n | today (c,k0) | new rule (c,k0)", flush=True)
        for variant, A in VARIANTS:
            for n in (1, 2):
                ks = [k for k in tot if k[0] == variant and k[1] == A and k[2] == n]
                bt = max(ks, key=lambda k: tot[k][0]); bn = max(ks, key=lambda k: tot[k][1])
                name = f"{variant[0]}{'' if variant[1] is None else ' ' + str(variant[1])} A={A}"
                print(f"{name:24s} n={n} today {tot[bt][0]/SEEDS:.4f} ({bt[3]},{bt[4]})  new {tot[bn][1]/SEEDS:.4f} ({bn[3]},{bn[4]})", flush=True)
        for tail, key in ((None, "200.0"), (4, "4.2")):
            tot = merge(ex.map(stop_work, [(c, tail, key) for c in chunks]))
            print(f"\nall adversaries stopping, market tail {tail or 'normal'} (table df {key}):", flush=True)
            for n in (1, 2, 5, 10, 50):
                print(f"  n={n:>2} " + "  ".join(f"{lab} {tot[(tail, n, lab)]/SEEDS:.4f}" for lab in ("honest", "stop 2.0", "stop 2.5", "stop c(N)", "stop c(N)+0.3")), flush=True)
        tot = merge(ex.map(power_work, chunks))
        print("\nhonest power (one asset held all T, true annualized Sharpe S, daily, T=250, n=1):", flush=True)
        for SA in (0.0, 1.0, 2.0, 3.0, 4.0):
            print(f"  S={SA}: today {tot[SA][0]/SEEDS:.3f}  new {tot[SA][1]/SEEDS:.3f}", flush=True)
