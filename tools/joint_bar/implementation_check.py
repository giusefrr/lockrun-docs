"""Inside the implementation: every round-3 variant and the honest controls under c(n), 2000 seeds, under the
default rule (tests/risk_world.py: version 2, the plain t, since 2026-10-30)."""
import os as _os, sys as _sys
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_sys.path[:0] = [_HERE, _os.path.join(_HERE, "..", "..", "tests")]
import os, sys
from concurrent.futures import ProcessPoolExecutor
from risk_world import GRID, adversary, joint_bar

VARIANTS = [(("honest", None), 8), (("honest-flat-days", None), 8), (("flat", None), 8),
            (("resume", 1), 8), (("resume", 2), 8), (("resume", 5), 8),
            (("tiny", 1e-6), 8), (("tiny", 0.01), 8), (("tiny", 0.05), 8),
            (("diversify", None), 8), (("diversify", None), 100),
            (("hedge", None), 8), (("hedge-drift", None), 8), (("lowvar", None), 8)]
SEEDS = 2000

def work(args):
    variant, A, n, c, k0 = args
    adv = adversary(variant, n, c, k0, A)
    return args, sum(adv(s) for s in range(SEEDS))

if __name__ == "__main__":
    jobs = [(v, A, n, c, k0) for v, A in VARIANTS for n in (1, 2)
            for c, k0 in ([(None, None)] if v[0].startswith("honest") else GRID)]
    res = {}
    with ProcessPoolExecutor(10) as ex:
        for args, hits in ex.map(work, jobs):
            res[args] = hits
    for v, A in VARIANTS:
        for n in (1, 2):
            cells = [(h, a[3], a[4]) for a, h in res.items() if a[0] == v and a[1] == A and a[2] == n]
            h, c, k0 = max(cells)
            print(f"{v[0]}{'' if v[1] is None else ' ' + str(v[1])} A={A} n={n}: worst {h}/{SEEDS} = {h/SEEDS:.4f} (c={c}, k0={k0})", flush=True)
