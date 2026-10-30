"""One command per table of tools/joint_bar/README.md: python standalone/run.py <table> [--seeds N | --quick]

  bar          c(n), the holdout the checks use (500k paths, seed 20261027; --seeds does not apply)
  finding      optional stopping under the DSR (10000, 3000 and 2000 seeds per row in full mode)
  adversaries  every adversarial variant, before and under the joint bar (--rows narrows it)
  power        the honest power cost
  dropped      the rules tried and dropped
  sizing       what the rule does not measure: an edge in sizing, the warm-up (one seeded draw)
  cost         the calibration's time and memory on one core (--seeds does not apply)
  all          every table

--compare prints the README's number beside each and flags a difference; meaningful only in full mode.
"""
import argparse
import json
import os
import sys
import time

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")     # one BLAS thread per worker, before numpy loads

from multiprocessing import Pool, get_context  # noqa: E402

import joint_tables as jt  # noqa: E402
import joint_world as jw  # noqa: E402
import readme_numbers as rn  # noqa: E402

FULL_SEEDS, QUICK_SEEDS = 2000, 200
TABLES = ("bar", "finding", "adversaries", "power", "dropped", "sizing", "cost")


def fmt(x) -> str:
    return "not run" if x is None else f"{x:.4f}"


def differs(a, b, digits=None) -> bool:
    """a, computed, against the README's b, at the digits the README prints."""
    if a is None or b is None:
        return a is not b
    d = digits if digits is not None else max(len(repr(float(b)).split(".")[1]), 3)
    return round(a, d) != round(b, d)


def print_bar(res, compare):
    print("  ".join(f"c({n}) {v:.3f}" for n, v in res.items()))
    if compare:
        print("README: " + "  ".join(f"c({n}) {v:.3f}" for n, v in rn.BAR.items()))
        print("differs: " + str([n for n, v in res.items() if round(v, 3) != rn.BAR[n]]))


def print_finding(res, compare):
    print("| Strategy (null market, T = 250) | N | PASS rate under the DSR | seeds | c | k0 |" + (" README |" if compare else ""))
    for r in res:
        extra = ""
        if compare:
            b = rn.FINDING[(r["name"], r["n"])]
            extra = f" {b} {'DIFFERS' if abs(r['rate'] - b) >= 0.5 * 10 ** -len(repr(b).split('.')[1]) else ''} |"
        print(f"| {r['name']} | {r['n']} | {r['rate']:.4f} | {r['seeds']} | {r['c']} | {r['k0']} |{extra}")


def print_adversaries(res, compare):
    print("| Researcher strategy | Before (n = 1 / 2) | Joint bar (n = 1 / 2) |" + (" README before | README joint | |" if compare else ""))
    for name, c in res.items():
        if "joint1" in c:
            line = f"| {name} | {fmt(c['before1'])} / {fmt(c['before2'])} | {fmt(c['joint1'])} / {fmt(c['joint2'])} |"
            if compare:
                b = rn.ADVERSARIES[name]
                bad = [differs(c[k], v) for k, v in zip(("before1", "before2", "joint1", "joint2"), b)]
                line += f" {b[0]} / {b[1]} | {b[2]} / {b[3]} | {'DIFFERS' if any(bad) else ''} |"
        else:
            line = f"| {name} | not run | at most {fmt(c['joint'])} (over every stop tried {fmt(c['any_stop'])}) |"
            if compare:
                b = rn.AT_MOST[name]
                line += f" not run | at most {b} | {'DIFFERS' if differs(c['joint'], b) else ''} |"
        print(line)


def print_power(res, compare):
    print("| True annualized Sharpe | " + " | ".join(f"{s:g}" for s in res) + " |")
    for key, name in (("before", "PASS before (DSR)"), ("joint", "PASS with the joint bar")):
        vals = [res[s][key] for s in res]
        print(f"| {name} | " + " | ".join(f"{v:.3f}" for v in vals) + " |")
        if compare:
            print(f"| README | " + " | ".join(f"{v:.3f}" for v in rn.POWER[key]) + " |"
                  + ("" if all(round(a, 3) == b for a, b in zip(vals, rn.POWER[key])) else " DIFFERS"))


def print_mapping(res, compare):
    for name, v in res.items():
        print(f"{name}: " + ("  ".join(f"{k} {x:.4f}" for k, x in v.items()) if isinstance(v, dict) else f"{v}"))


def chunker(jobs):
    def chunks(seeds):
        size = max(1, min(25, seeds // (jobs * 4) or 1))
        return [range(s, min(s + size, seeds)) for s in range(0, seeds, size)]
    return chunks


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("table", choices=[*TABLES, "all"])
    p.add_argument("--seeds", type=int, help=f"seeds 0 .. N-1 per cell (full mode: {FULL_SEEDS}; finding: by row)")
    p.add_argument("--quick", action="store_true", help=f"{QUICK_SEEDS} seeds per cell: a smoke test, not the README's numbers")
    p.add_argument("--rows", help="adversaries: comma-separated parts of row names (flat,hedge,honest)")
    p.add_argument("--jobs", type=int, default=os.cpu_count(), help="worker processes (default: every core)")
    p.add_argument("--compare", action="store_true", help="print the README's number beside each, and flag a difference")
    p.add_argument("--json", help="also write the results here")
    a = p.parse_args()
    seeds = a.seeds or (QUICK_SEEDS if a.quick else None)
    chunks = chunker(a.jobs)
    wanted = TABLES if a.table == "all" else (a.table,)
    needs_bars = {"adversaries", "power"} & set(wanted)
    t0 = time.perf_counter()
    bars = {}
    if needs_bars:
        bars["normal"] = jw.joint_bar()
        if "adversaries" in wanted and any(r.tail for r in jt.selected_rows(a.rows)):
            bars["t4"] = jw.t4_joint_bar()
    results = {}
    with Pool(a.jobs, initializer=jt.set_bars, initargs=(bars,)) as pool:
        for table in wanted:
            t1 = time.perf_counter()
            print(f"\n## {table}" + (f" ({seeds} seeds, 0 to {seeds - 1})" if seeds else ""), flush=True)
            if table == "bar":
                res = jt.bar_table()
                print_bar(res, a.compare)
            elif table == "finding":
                res = jt.finding(seeds, pool, chunks)
                print_finding(res, a.compare)
            elif table == "adversaries":
                res = jt.adversaries(seeds or FULL_SEEDS, pool, chunks, a.rows)
                print_adversaries(res, a.compare)
            elif table == "power":
                res = jt.power(seeds or FULL_SEEDS, pool, chunks)
                print_power(res, a.compare)
            elif table == "dropped":
                res = jt.dropped(seeds or FULL_SEEDS, pool, chunks)
                print_mapping(res, a.compare)
            elif table == "sizing":
                res = jt.sizing()
                print_mapping(res, a.compare)
            else:
                with get_context("spawn").Pool(1) as one:      # its own process: the peak memory is the calibration's
                    res = one.apply(jt.cost, (a.quick,))
                print_mapping(res, a.compare)
            results[table] = res
            print(f"({table}: {time.perf_counter() - t1:.0f} s)", flush=True)
    print(f"\ntotal: {time.perf_counter() - t0:.0f} s, {a.jobs} workers", flush=True)
    if a.json:
        with open(a.json, "w") as f:
            json.dump(results, f, indent=1, default=str)
    return 0


if __name__ == "__main__":
    sys.exit(main())
