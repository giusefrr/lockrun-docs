"""The joint bar c(n) through the implemented calibration (lockrun/calibration.py), for the holdout the
implementation checks use (tests/risk_world.py: T = 250, min_t = 100, threshold 0.95, normal tail,
500k paths, seed 20261027), under the default rule (version 2, the plain t; risk_world.joint_bar("psr") is
version 1's). A deployment calibrates with 2M paths and the holdout's fitted df."""
import os as _os, sys as _sys
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_sys.path[:0] = [_HERE, _os.path.join(_HERE, "..", "..", "tests")]
from risk_world import joint_bar
from lockrun import calibration

jb = joint_bar()
print("  ".join(f"c({n}) {calibration.bar(jb, n):.3f}" for n in (1, 2, 5, 10, 50, 100, 1000)))
