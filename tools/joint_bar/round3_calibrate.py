import os as _os, sys as _sys
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_sys.path[:0] = [_HERE, _os.path.join(_HERE, "..", "..", "tests")]
import json, sys, numpy as np
from round3_joint_bar import calibrate, fit_df
# df fit on a normal holdout and on a Student-t(4) one (8 assets x 250 periods), to check the fit
for name, R in (("normal", np.random.default_rng(3).normal(0, 0.01, (250, 8))),
                ("t4", 0.01 * np.random.default_rng(3).standard_t(4, (250, 8))),
                ("t6", 0.01 * np.random.default_rng(3).standard_t(6, (250, 8)))):
    print(name, "df used / fitted:", fit_df(R), flush=True)
out = {}
for df in (200.0, 4.0):
    c = calibrate(250, 100, df, 2_000_000)
    out[str(df)] = c["table"]
    print(f"df={df}: {c['seconds']:.0f}s for {c['paths']} paths (chunk {c['chunk']})", flush=True)
    print("  " + "  ".join(f"N={n}:{v:.3f}" for n, v in c["table"].items()), flush=True)
json.dump(out, open(_os.path.join(_HERE, "joint_tables.json"), "w"))
