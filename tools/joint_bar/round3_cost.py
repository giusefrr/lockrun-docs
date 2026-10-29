import os as _os, sys as _sys
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_sys.path[:0] = [_HERE, _os.path.join(_HERE, "..", "..", "tests")]
import json, resource, sys, time
import numpy as np
from round3_joint_bar import calibrate, fit_df
t = json.load(open(_os.path.join(_HERE, "joint_tables.json")))
c = calibrate(250, 100, 4.2, 2_000_000)
t["4.2"] = c["table"]; json.dump(t, open(_os.path.join(_HERE, "joint_tables.json"), "w"))
print(f"T=250 df=4.2: {c['seconds']:.1f}s, 2M paths; N=2 {c['table'][2]:.3f} N=1000 {c['table'][1000]:.3f}", flush=True)
t0 = time.perf_counter(); fit_df(0.01 * np.random.default_rng(1).standard_t(4, (2500, 100)))
print(f"df fit, 2500 x 100 residuals: {time.perf_counter() - t0:.1f}s", flush=True)
for T, mt, paths in ((2500, 100, 2_000_000), (2500, 1000, 2_000_000)):
    c = calibrate(T, mt, 200.0, paths)
    print(f"T={T} min_t={mt}: {c['seconds']:.0f}s for {paths} paths (chunk {c['chunk']}); N=2 {c['table'][2]:.3f} N=1000 {c['table'][1000]:.3f}", flush=True)
print(f"peak RSS {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2**20:.0f} MiB", flush=True)
