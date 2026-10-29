import os as _os, sys as _sys
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_sys.path[:0] = [_HERE, _os.path.join(_HERE, "..", "..", "tests")]
import sys
import numpy as np
from round2_sequential_calibration import sup_z  # noqa  (prints its own calibration on import)
from lockrun import stats
T, M, A = 250, 100, 0.05
rng = np.random.default_rng(8)
sups = np.concatenate([sup_z(rng.normal(size=(50_000, T)))[0] for _ in range(6)])
fixed = np.concatenate([sup_z(rng.normal(size=(50_000, T)), m=T)[0] for _ in range(6)])
v = stats.null_sharpe_variance(T)
print("\nN (incl. reserved) | composed bar sr0*sqrt(T-1)+c_seq | exact sup bar, max of N | exact fixed-T bar, max of N | DSR today sr0*sqrt(T-1)+1.645")
for N in (2, 3, 6, 11, 51):
    sr0 = stats.expected_max_sharpe(v, N) * np.sqrt(T - 1)
    q = (1 - A) ** (1 / N)
    print(f"{N:>3} | {sr0 + 2.244:.3f} | {np.quantile(sups, q):.3f} | {np.quantile(fixed, q):.3f} | {sr0 + 1.645:.3f}")
