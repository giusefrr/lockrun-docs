"""What rule version 3 costs: honest power next to version 2's on the standard cells, at N equal to the openings.

  python power_v3.py [--seeds 4000] [--jobs N]

One edge trial holding one asset among N openings (the others null), T = 250, true annualized Sharpe 0 to 4. Numpy only.
"""
import argparse
import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")

from multiprocessing import get_context  # noqa: E402

import joint_rule as jr  # noqa: E402
import joint_tables as jt  # noqa: E402
import joint_world as jw  # noqa: E402

CELLS = (1, 5, 20, 100)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seeds", type=int, default=4000)
    p.add_argument("--jobs", type=int, default=os.cpu_count())
    p.add_argument("--paths", type=int, default=2_000_000)
    p.add_argument("--declared", action="store_true", help="also version 3 with the declared portfolio's bar, N = 1, 20")
    a = p.parse_args()
    cells = (1, 20) if a.declared else CELLS
    normal = float(jr.NORMAL_DF)
    bars = {"normal": jr.calibrate(jw.T, jw.MIN_T, normal, jw.THRESHOLD, a.paths, jw.SEED),
            "spending": {n: jr.calibrate(jw.T, jw.MIN_T, normal, jw.THRESHOLD, a.paths, jw.SEED, "t",
                                         (n, a.paths // 10, 1e-8))["spending"] for n in cells}}

    def chunks(seeds):
        size = max(1, seeds // (4 * a.jobs))
        return [range(i, min(i + size, seeds)) for i in range(0, seeds, size)]
    with get_context("spawn").Pool(a.jobs, initializer=jt.set_bars, initargs=(bars,)) as pool:
        if a.declared:
            res = jt.power_declared(a.seeds, pool, chunks, cells)
            print(f"| N | Sharpe | version 2, c(N) | version 3, b_k | version 3, declared portfolio's bar | "
                  f"({a.seeds} seeds, {a.paths} paths)")
            print("|---|---|---|---|---|")
            for key, v in res.items():
                n, s = key.split()
                print(f"| {n[2:]} | {s[7:]} | {v['v2']:.3f} | {v['v3']:.3f} | {v['declared']:.3f} |")
            return
        res = jt.power_v3(a.seeds, pool, chunks)
    print(f"| N | Sharpe | version 2, c(N) | version 3, b_k | ({a.seeds} seeds, {a.paths} paths)")
    print("|---|---|---|---|")
    for key, v in res.items():
        n, s = key.split()
        print(f"| {n[2:]} | {s[7:]} | {v['v2']:.3f} | {v['v3']:.3f} |")


if __name__ == "__main__":
    main()
