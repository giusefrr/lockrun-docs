"""The numbers tools/joint_bar/README.md states, for run.py --compare."""
BAR = {1: 2.252, 2: 2.552, 5: 2.906, 10: 3.146, 50: 3.662, 100: 3.854, 1000: 4.418}
FINDING = {("Honest: constant exposure, never stops", 1): 0.015,
           ("Flat once its t-statistic reaches c (best c and first stop k0)", 1): 0.268,
           ("Flat once its t-statistic reaches c (best c and first stop k0)", 2): 0.082,
           ("The same, trading again for the last period", 1): 0.17,
           ("The same, weights times 1e-6 instead of zero", 1): 0.27}
ADVERSARIES = {   # before n = 1, n = 2; joint bar n = 1, n = 2
    "Honest, constant exposure": (0.0115, 0.0020, 0.0135, 0.0105),
    "Honest, 10% random flat days": (0.0140, 0.0020, 0.0140, 0.0100),
    "Flat once ahead": (0.257, 0.0705, 0.0205, 0.0160),
    "Flat, trading again for the last 1 period": (0.164, 0.089, 0.0205, 0.0160),
    "Flat, trading again for the last 2 periods": (0.1195, 0.074, 0.0200, 0.0155),
    "Flat, trading again for the last 5 periods": (0.083, 0.048, 0.0175, 0.0145),
    "Weights times 1e-6 once ahead": (0.257, 0.0705, 0.0210, 0.0145),
    "Weights times 0.01 once ahead": (0.200, 0.068, 0.0210, 0.0145),
    "Weights times 0.05 once ahead": (0.1115, 0.039, 0.0175, 0.0130),
    "Same gross over every asset, 8 assets": (0.014, 0.0035, 0.0130, 0.0115),
    "Same gross over every asset, 100 assets": (0.0165, 0.0045, 0.0130, 0.0105),
    "Hedge of two twin assets": (0.129, 0.044, 0.0205, 0.0150),
    "Hedge with a drifting ratio": (0.0835, 0.0285, 0.0165, 0.0130),
    "Only the lowest-variance asset": (0.035, 0.0075, 0.0150, 0.0105),
    "Pausing in the window covariance's null space (100 assets)": (None, None, 0.0125, 0.0075),
    "An asset whose volatility the window lags (falls tenfold)": (None, None, 0.0200, 0.0175),
}
AT_MOST = {"Every trial stopping at c(n), n = 1 to 50, normal market": 0.0200,
           "Every trial stopping at c(n), n = 1 to 50, Student-t(4) market": 0.0280}
POWER = {"before": (0.015, 0.119, 0.413, 0.775, 0.962), "joint": (0.010, 0.099, 0.337, 0.690, 0.931)}
