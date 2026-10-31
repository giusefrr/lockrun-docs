"""One command per table of tools/joint_bar/README.md: python standalone/run.py <table> [--seeds N | --quick]

  --stat psr on bar, adversaries, power and assumptions: the rule before; the default is the plain t.

  bar          c(n), the holdout the checks use (500k paths, seed 20261027; --seeds does not apply)
  finding      optional stopping under the DSR (10000, 3000 and 2000 seeds per row in full mode)
  adversaries  every adversarial variant, before and under the joint bar (--rows narrows it)
  power        the honest power cost
  dropped      the rules tried and dropped
  sizing       what the rule does not measure: an edge in sizing, the warm-up (one seeded draw)
  cost         the calibration's time and memory on one core (--seeds does not apply)
  assumptions  dependence and adaptive exposure, under the joint bar as the product runs it, every holdout its
               own df fit and bar: (a) correlated trials, (b) the main table on GARCH markets, (c) adversaries
               with the estimator's state, (d) pauses within a budget; --parts picks some, --window and --warmup
               vary the estimator
  all          every table
  fixes        the candidate fixes, standalone only (not in all): the plain t alone and with each covariance
               candidate, at every window and warm-up, assumptions and main tables and honest power; --out DIR
               keeps each configuration, and a second run resumes; the bounds C1 and C2 too, and rows aimed at them;
               --only "name;name" keeps those configurations
  targeted     the bounds at 60/20 on the rows that decide them, into --out/targeted
  confirm      --leaders "name;name" on --seeds fresh seeds from --first-seed, every cell at the stop that
               fixes chose, from fixes' --out

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

import joint_assumptions as aj  # noqa: E402
import joint_rule as jr  # noqa: E402
import joint_tables as jt  # noqa: E402
import joint_world as jw  # noqa: E402
import readme_numbers as rn  # noqa: E402

FULL_SEEDS, QUICK_SEEDS = 2000, 200
NUM: dict = {}     # the README's numbers for the statistic this run is under
CALIBRATION_PATHS, QUICK_PATHS = 2_000_000, 100_000     # the product's; the quick mode's
QUICK_ASSUMPTION_SEEDS = 50
TABLES = ("bar", "finding", "adversaries", "power", "dropped", "sizing", "cost", "assumptions")
EXTRA_TABLES = ("fixes", "targeted", "confirm")     # not in `all`: candidates for the rule, hours in full mode
CONFIRM_SEEDS = 8000


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
        print("README: " + "  ".join(f"c({n}) {v:.3f}" for n, v in NUM["BAR"].items()))
        print("differs: " + str([n for n, v in res.items() if round(v, 3) != NUM["BAR"][n]]))


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
                b = NUM["ADVERSARIES"][name]
                bad = [differs(c[k], v) for k, v in zip(("before1", "before2", "joint1", "joint2"), b)]
                line += f" {b[0]} / {b[1]} | {b[2]} / {b[3]} | {'DIFFERS' if any(bad) else ''} |"
        else:
            line = f"| {name} | not run | at most {fmt(c['joint'])} (over every stop tried {fmt(c['any_stop'])}) |"
            if compare:
                b = NUM["AT_MOST"][name]
                line += f" not run | at most {b} | {'DIFFERS' if differs(c['joint'], b) else ''} |"
        print(line)


def print_power(res, compare):
    print("| True annualized Sharpe | " + " | ".join(f"{s:g}" for s in res) + " |")
    for key, name in (("before", "PASS before (DSR)"), ("joint", "PASS with the joint bar")):
        vals = [res[s][key] for s in res]
        print(f"| {name} | " + " | ".join(f"{v:.3f}" for v in vals) + " |")
        if compare:
            print(f"| README | " + " | ".join(f"{v:.3f}" for v in NUM["POWER"][key]) + " |"
                  + ("" if all(round(a, 3) == b for a, b in zip(vals, NUM["POWER"][key])) else " DIFFERS"))


PARTS = {"a": "(a) Correlated trials", "b": "(b) The main table on GARCH markets, each holdout its own bar",
         "c": "(c) Adversaries with the estimator's state", "d": "(d) Pauses within the budget, T_eff above min_t"}


def print_assumptions(res):
    """Each cell: the worst rate over its stops, the first trial's median T_eff there, the share refused."""
    for part, title in PARTS.items():
        rows = {k: v for k, v in res.items() if v["part"] == part}
        if not rows:
            continue
        ns = next(iter(rows.values()))["ns"]
        print(f"\n### {title}\n\n| Row | " + " | ".join(f"n = {n}" for n in ns) + " | |\n|--|" + "--|" * (len(ns) + 1))
        for name, v in rows.items():
            cells = [v["cells"][n] for n in v["ns"]]
            marks = ", ".join(sorted({f"n = {n}" for n in v["ns"] if aj.above_nominal(v["cells"][n]["rate"])}))
            line = " | ".join(f"{c['rate']:.4f} (T_eff {c['t_eff']:g}, {c['refused']:.0%} refused)" for c in cells)
            extra = f" n = {'/'.join(map(str, v['ns']))}:" if v["ns"] != ns else ""
            traded = f" traded {v['traded']:.0%} of steps;" if "traded" in v else ""
            print(f"| {name} |{extra} {line} |{traded} {'above nominal: ' + marks if marks else ''} |")


def print_mapping(res, compare):
    for name, v in res.items():
        print(f"{name}: " + ("  ".join(f"{k} {x:.4f}" for k, x in v.items()) if isinstance(v, dict) else f"{v}"))


def chunker(jobs):
    def chunks(seeds):
        size = max(1, min(25, seeds // (jobs * 4) or 1))
        return [range(s, min(s + size, seeds)) for s in range(0, seeds, size)]
    return chunks


def config_name(c: dict) -> str:
    return f"{aj.fix_name(c)}, window {c['window']}, warm-up {c['warmup']}"


def config_path(directory: str, name: str) -> str:
    return os.path.join(directory, name.replace(" ", "_").replace(",", "").replace(":", "") + ".json")


def confirm(a, chunks) -> dict:
    """--leaders on seeds --first-seed onward, each cell at the stop the first seeds chose, from --out's results:
    the choice's selection stays with the seeds that made it."""
    seeds = a.seeds or (QUICK_ASSUMPTION_SEEDS if a.quick else CONFIRM_SEEDS)
    paths = QUICK_PATHS if a.quick else CALIBRATION_PATHS
    shifted = lambda n: [range(r.start + a.first_seed, r.stop + a.first_seed) for r in chunks(n)]  # noqa: E731
    by_name = {config_name(c): c for c in aj.fix_configurations()}
    directory = os.path.join(a.out, f"confirm-{a.first_seed}-{seeds}")
    os.makedirs(directory, exist_ok=True)
    out = {}
    for leader in a.leaders.split(";"):
        c = by_name[leader.removesuffix(", aimed")]
        path = config_path(directory, leader)
        if os.path.exists(path):
            with open(path) as f:
                out[leader] = json.load(f)
            continue
        with open(config_path(a.out, leader)) as f:
            first = json.load(f)
        parts = aj.AIMED_PARTS if leader.endswith(", aimed") else aj.FIX_PARTS
        rows = [aj.with_chosen_stops(r, first[r.name]) for r in aj.rows_of(parts)]
        with Pool(a.jobs) as pool:
            prep = aj.prepare_bars(rows, seeds, paths, pool, shifted, a.bar_cache, aj.bar_stat(c))
        t0 = time.perf_counter()
        with Pool(a.jobs, initializer=aj.set_bars, initargs=(prep["bars"],)) as inner:
            res = json.loads(json.dumps(aj.assumptions(rows, seeds, inner, shifted, c), default=str))
        with open(path + ".tmp", "w") as f:
            json.dump(res, f, default=str)
        os.replace(path + ".tmp", path)
        print(f"  ... {leader}: {time.perf_counter() - t0:.0f} s", file=sys.stderr, flush=True)
        out[leader] = res
    return out


def targeted(a, chunks) -> dict:
    """One window, the rows that decide whether a bound closes the excess: each configuration saved as it ends."""
    seeds = a.seeds or (QUICK_ASSUMPTION_SEEDS if a.quick else FULL_SEEDS)
    paths = QUICK_PATHS if a.quick else CALIBRATION_PATHS
    rows = aj.targeted_rows()
    directory = os.path.join(a.out, "targeted")
    os.makedirs(directory, exist_ok=True)
    out = {}
    for c in aj.targeted_configurations():
        name = aj.fix_name(c)
        path = config_path(directory, name)
        if os.path.exists(path):
            with open(path) as f:
                out[name] = json.load(f)
            continue
        with Pool(a.jobs) as pool:
            prep = aj.prepare_bars(rows, seeds, paths, pool, chunks, a.bar_cache, aj.bar_stat(c))
        t0 = time.perf_counter()
        with Pool(a.jobs, initializer=aj.set_bars, initargs=(prep["bars"],)) as inner:
            out[name] = json.loads(json.dumps(aj.assumptions(rows, seeds, inner, chunks, c), default=str))
        with open(path + ".tmp", "w") as f:
            json.dump(out[name], f, default=str)
        os.replace(path + ".tmp", path)
        print(f"  ... {name}: {time.perf_counter() - t0:.0f} s", file=sys.stderr, flush=True)
    return out


def print_targeted(out: dict) -> None:
    """Per row, per configuration, its worst rate over n; the least T_eff beside a pause or attack that refuses."""
    names = list(out)
    print("| Row | " + " | ".join(names) + " |\n|--|" + "--|" * len(names))
    for row in next(iter(out.values())):
        cells = [max(out[n][row]["cells"].values(), key=lambda c: c["rate"]) for n in names]
        print(f"| {row} | " + " | ".join(f"{c['rate']:.4f}{'*' if c['rate'] > aj.NOMINAL else ''} ({c['t_eff']:g}, {c['refused']:.0%})" for c in cells) + " |")
    print("\n* above nominal. Each cell: the worst rate over n and stops (the first trial's median T_eff there, refused).")


def fixes(a, chunks) -> dict:
    """Each configuration in turn, saved as it ends."""
    seeds =a.seeds or (QUICK_ASSUMPTION_SEEDS if a.quick else FULL_SEEDS)
    paths = QUICK_PATHS if a.quick else CALIBRATION_PATHS
    rows = aj.rows_of(aj.FIX_PARTS)
    aimed = aj.rows_of(aj.AIMED_PARTS)
    baseline = aj.rows_of("p")
    out = {}
    all_configs = aj.fix_configurations()
    if a.only:
        wanted = a.only.split(";")
        all_configs = [c for c in all_configs if aj.fix_name(c) in wanted]
    with Pool(a.jobs) as pool:
        tables = {s: aj.prepare_bars(rows + aimed, seeds, paths, pool, chunks, a.bar_cache, s)
                  for s in sorted({aj.bar_stat(c) for c in all_configs})}
        psr = aj.prepare_bars(baseline, seeds, paths, pool, chunks, a.bar_cache, "psr")
    configs = [("current rule: power", {**jw.P, "stat": "psr", "cov": "sample"}, baseline, psr)]
    configs += [(config_name(c), c, rows, tables[aj.bar_stat(c)]) for c in all_configs]
    configs += [(f"{config_name(c)}, aimed", c, aimed, tables[aj.bar_stat(c)]) for c in all_configs if c["cov"] == "sample"]
    if a.out:
        os.makedirs(a.out, exist_ok=True)
    for name, rule, which, bars in configs:
        path = config_path(a.out, name) if a.out else None
        if path and os.path.exists(path):
            with open(path) as f:
                res = json.load(f)
        else:
            t0 = time.perf_counter()
            with Pool(a.jobs, initializer=aj.set_bars, initargs=(bars["bars"],)) as inner:
                res = json.loads(json.dumps(aj.assumptions(which, seeds, inner, chunks, rule), default=str))
            if path:
                with open(path + ".tmp", "w") as f:
                    json.dump(res, f, default=str)
                os.replace(path + ".tmp", path)
            print(f"  ... {name}: {time.perf_counter() - t0:.0f} s", file=sys.stderr, flush=True)
        out[name] = res
    return out


def print_fixes(out: dict) -> None:
    print("| Configuration | Worst cell | Its row, n | T_eff | Refused | Cells above nominal | Worst hedge | Worst pause (least T_eff) | Honest multi-asset T_eff, refused | Power at Sharpe 1 / 2 / 3 / 4 |")
    print("|--|--|--|--|--|--|--|--|--|--|")
    for name, rows in out.items():
        if name.startswith("current"):
            print(f"| {name} | | | | | | | | | " + " / ".join(f"{rows[f'Honest power, Sharpe {s}']['cells']['1']['rate']:.3f}" for s in (1, 2, 3, 4)) + " |")
            continue
        if name.endswith(", aimed"):
            continue
        s = aj.fix_summary(rows)
        w = s["worst"]
        power = " / ".join(f"{s['power'][str(k)]['rate']:.3f}" for k in (1, 2, 3, 4))
        print(f"| {name} | {w[0]:.4f} {'above nominal' if w[0] > aj.NOMINAL else ''} | {w[1]}, n = {w[2]} | {w[3]:g} | {w[4]:.0%} | {s['above']} "
              f"| {s['hedge'][0]:.4f} | {s['pause'][0]:.4f} ({s['pause_t_eff']:g}) | {s['honest_t_eff']:g}, {s['honest_refused']:.0%} | {power} |")
    print("\n### Rows aimed at the bounds: not in the full table\n\n| Configuration | Worst cell | Its row, n | T_eff | Refused | Cells above nominal |\n|--|--|--|--|--|--|")
    for name, rows in out.items():
        if name.endswith(", aimed"):
            cells = [(c["rate"], k, n, c["t_eff"], c["refused"]) for k, v in rows.items() for n, c in v["cells"].items()]
            w = max(cells, key=lambda x: x[0])
            print(f"| {name.removesuffix(', aimed')} | {w[0]:.4f} {'above nominal' if w[0] > aj.NOMINAL else ''} | {w[1]}, n = {w[2]} | {w[3]:g} | {w[4]:.0%} "
                  f"| {sum(1 for x in cells if x[0] > aj.NOMINAL)} |")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("table", choices=[*TABLES, *EXTRA_TABLES, "all"])
    p.add_argument("--seeds", type=int, help=f"seeds 0 .. N-1 per cell (full mode: {FULL_SEEDS}; finding: by row)")
    p.add_argument("--quick", action="store_true", help=f"{QUICK_SEEDS} seeds per cell: a smoke test, not the README's numbers")
    p.add_argument("--rows", help="adversaries: comma-separated parts of row names (flat,hedge,honest)")
    p.add_argument("--jobs", type=int, default=os.cpu_count(), help="worker processes (default: every core)")
    p.add_argument("--compare", action="store_true", help="print the README's number beside each, and flag a difference")
    p.add_argument("--json", help="also write the results here")
    p.add_argument("--window", type=int, help="assumptions: the covariance window (default 60)")
    p.add_argument("--warmup", type=int, help="assumptions: the warm-up (default 20)")
    p.add_argument("--parts", default="abcd", help="assumptions: which of a, b, c, d (default all)")
    p.add_argument("--first-seed", type=int, default=0, help="assumptions: start from this seed (fresh seeds confirm a cell)")
    p.add_argument("--stat", choices=("psr", "t"), help="bar, adversaries, power, assumptions: the statistic (default t, the plain t; psr, the rule before)")
    p.add_argument("--cov", choices=aj.COVS, default="sample", help="assumptions: the covariance estimate (default the product's)")
    p.add_argument("--out", help="fixes: the directory for each configuration's results")
    p.add_argument("--bar-cache", help="assumptions: keep each df's table in this directory")
    p.add_argument("--leaders", help="confirm: configurations by name, separated by ;")
    p.add_argument("--only", help="fixes: these configurations, by name without the window, separated by ;")
    a = p.parse_args()
    if a.table == "targeted" and not a.out:
        p.error("targeted needs --out")
    if a.table == "confirm" and not (a.leaders and a.out and a.first_seed):
        p.error("confirm needs --leaders, --out and --first-seed")
    if (a.first_seed or a.bar_cache or a.cov != "sample") and a.table not in ("assumptions", "fixes", "targeted", "confirm"):
        p.error("--first-seed, --bar-cache and --cov apply to the assumptions tables only")
    if a.stat and a.table not in ("bar", "adversaries", "power", "assumptions"):
        p.error("--stat applies to the bar, adversaries, power and assumptions tables")
    stat = a.stat or jr.DEFAULT_STAT
    NUM.update(rn.NUMBERS[stat])
    if (a.window or a.warmup) and a.table != "assumptions":
        p.error("--window and --warmup apply to the assumptions table only: the other tables are the rule as implemented")
    rule = {**jw.P, "window": a.window or jw.P["window"], "warmup": a.warmup or jw.P["warmup"]}
    rule.update(stat=stat, cov=a.cov)
    if not 2 <= rule["warmup"] <= rule["window"]:
        p.error("--window and --warmup must have 2 <= warmup <= window")
    seeds = a.seeds or (QUICK_SEEDS if a.quick else None)
    chunks = chunker(a.jobs)
    wanted = TABLES if a.table == "all" else (a.table,)
    needs_bars = {"adversaries", "power"} & set(wanted)
    t0 = time.perf_counter()
    if a.table == "fixes":
        res = fixes(a, chunks)
        print_fixes(res)
        if a.json:
            with open(a.json, "w") as f:
                json.dump(res, f, indent=1, default=str)
        print(f"\ntotal: {time.perf_counter() - t0:.0f} s, {a.jobs} workers", flush=True)
        return 0
    if a.table == "targeted":
        print_targeted(targeted(a, chunks))
        print(f"\ntotal: {time.perf_counter() - t0:.0f} s, {a.jobs} workers", flush=True)
        return 0
    if a.table == "confirm":
        res = confirm(a, chunks)
        print_fixes(res)
        print(f"\ntotal: {time.perf_counter() - t0:.0f} s, {a.jobs} workers", flush=True)
        return 0
    bars = {"stat": stat}
    if needs_bars:
        bars["normal"] = jw.joint_bar(stat)
        if "adversaries" in wanted and any(r.tail for r in jt.selected_rows(a.rows)):
            bars["t4"] = jw.t4_joint_bar(stat)
    results = {}
    with Pool(a.jobs, initializer=jt.set_bars, initargs=(bars,)) as pool:
        for table in wanted:
            t1 = time.perf_counter()
            print(f"\n## {table}" + (f" ({seeds} seeds, 0 to {seeds - 1})" if seeds else ""), flush=True)
            if table == "bar":
                res = jt.bar_table(stat)
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
            elif table == "assumptions":
                n_seeds = a.seeds or (QUICK_ASSUMPTION_SEEDS if a.quick else FULL_SEEDS)
                rows = aj.rows_of(a.parts)
                if a.rows:
                    rows = [r for r in rows if any(w.strip().lower() in r.name.lower() for w in a.rows.split(","))]
                paths = QUICK_PATHS if a.quick else CALIBRATION_PATHS
                shifted = lambda n: [range(r.start + a.first_seed, r.stop + a.first_seed) for r in chunks(n)]  # noqa: E731
                prep = aj.prepare_bars(rows, n_seeds, paths, pool, shifted, a.bar_cache, stat)
                print(f"stat {stat}, covariance {a.cov}; window {rule['window']}, warm-up {rule['warmup']}; GARCH innovations' df {jw.garch_df():g}; "
                      f"{len(prep['bars'])} distinct fitted dfs, a {paths}-path table each; nominal 0.05")
                with Pool(a.jobs, initializer=aj.set_bars, initargs=(prep["bars"],)) as inner:
                    res = aj.assumptions(rows, n_seeds, inner, shifted, rule)
                print_assumptions(res)
                print("\nfitted df per market: " + ", ".join(f"{k} {lo:g} to {hi:g}" for k, (lo, hi) in sorted(prep["df_range"].items())))
                res = {"rows": res, "df_range": prep["df_range"], "distinct_dfs": len(prep["bars"])}
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
