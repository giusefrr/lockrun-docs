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
ASSUMPTIONS = {
    "(a) Trials sharing a latent signal, rho = 0.5: honest": (
        0.0135,
        0.0115
    ),
    "(a) Trials sharing a latent signal, rho = 0.5: flat once ahead": (
        0.019,
        0.0145
    ),
    "(a) Trials sharing a latent signal, rho = 0.9: honest": (
        0.0125,
        0.0075
    ),
    "(a) Trials sharing a latent signal, rho = 0.9: flat once ahead": (
        0.02,
        0.014
    ),
    "(b) GARCH(1,1) null: Honest, constant exposure": (
        0.0085,
        0.009
    ),
    "(b) GARCH(1,1) null: Honest, 10% random flat days": (
        0.0075,
        0.0075
    ),
    "(b) GARCH(1,1) null: Flat once ahead": (
        0.014,
        0.012
    ),
    "(b) GARCH(1,1) null: Flat, trading again for the last 1 period": (
        0.0135,
        0.0125
    ),
    "(b) GARCH(1,1) null: Flat, trading again for the last 2 periods": (
        0.0125,
        0.0115
    ),
    "(b) GARCH(1,1) null: Flat, trading again for the last 5 periods": (
        0.01,
        0.0125
    ),
    "(b) GARCH(1,1) null: Weights times 1e-6 once ahead": (
        0.016,
        0.013
    ),
    "(b) GARCH(1,1) null: Weights times 0.01 once ahead": (
        0.016,
        0.013
    ),
    "(b) GARCH(1,1) null: Weights times 0.05 once ahead": (
        0.0135,
        0.0125
    ),
    "(b) GARCH(1,1) null: Same gross over every asset, 8 assets": (
        0.011,
        0.0135
    ),
    "(b) GARCH(1,1) null: Same gross over every asset, 100 assets": (
        0.01,
        0.009
    ),
    "(b) GARCH(1,1) null: Hedge of two twin assets": (
        0.0135,
        0.011
    ),
    "(b) GARCH(1,1) null: Hedge with a drifting ratio": (
        0.015,
        0.0115
    ),
    "(b) GARCH(1,1) null: Only the lowest-variance asset": (
        0.015,
        0.012
    ),
    "(b) GARCH(1,1) null: Pausing in the window covariance's null space (100 assets)": (
        0.0075,
        0.005
    ),
    "(b) GARCH(1,1) null: An asset whose volatility the window lags (falls tenfold)": (
        0.0175,
        0.016
    ),
    "(b) GARCH(1,1) null: Every trial stopping, n = 1 to 50": (
        0.0205,
        0.0205
    ),
    "(c) Knows the estimator, iid market: weights times true / estimated risk": (
        0.0205,
        0.016
    ),
    "(c) Knows the estimator, iid market: all weight where the window most underestimates": (
        0.014,
        0.0175
    ),
    "(c) Knows the estimator, iid market: the same, flat where it underestimates least": (
        0.004,
        0.004
    ),
    "(c) Knows the estimator, GARCH market: weights times true / estimated risk": (
        0.014,
        0.012
    ),
    "(c) Knows the estimator, GARCH market: all weight where the window most underestimates": (
        0.018,
        0.0115
    ),
    "(c) Knows the estimator, GARCH market: the same, flat where it underestimates least": (
        0.006,
        0.0065
    )
}
ASSUMPTIONS_WINDOWS = {
    "(c) Knows the estimator, iid market: weights times true / estimated risk": {
        "60/20": (
            0.0205,
            0.016
        ),
        "20/20": (
            0.0195,
            0.0165
        ),
        "120/20": (
            0.0185,
            0.017
        ),
        "250/20": (
            0.018,
            0.017
        ),
        "60/60": (
            0.0095,
            0.01
        )
    },
    "(c) Knows the estimator, iid market: all weight where the window most underestimates": {
        "60/20": (
            0.014,
            0.0175
        ),
        "20/20": (
            0.0185,
            0.0155
        ),
        "120/20": (
            0.018,
            0.016
        ),
        "250/20": (
            0.013,
            0.016
        ),
        "60/60": (
            0.0165,
            0.014
        )
    },
    "(c) Knows the estimator, iid market: the same, flat where it underestimates least": {
        "60/20": (
            0.004,
            0.004
        ),
        "20/20": (
            0.0095,
            0.0095
        ),
        "120/20": (
            0.0025,
            0.0025
        ),
        "250/20": (
            0.001,
            0.003
        ),
        "60/60": (
            0.006,
            0.0045
        )
    },
    "(c) Knows the estimator, GARCH market: weights times true / estimated risk": {
        "60/20": (
            0.014,
            0.012
        ),
        "20/20": (
            0.0145,
            0.014
        ),
        "120/20": (
            0.012,
            0.011
        ),
        "250/20": (
            0.0115,
            0.012
        ),
        "60/60": (
            0.0135,
            0.0095
        )
    },
    "(c) Knows the estimator, GARCH market: all weight where the window most underestimates": {
        "60/20": (
            0.018,
            0.0115
        ),
        "20/20": (
            0.0195,
            0.017
        ),
        "120/20": (
            0.022,
            0.0145
        ),
        "250/20": (
            0.022,
            0.0175
        ),
        "60/60": (
            0.019,
            0.0155
        )
    },
    "(c) Knows the estimator, GARCH market: the same, flat where it underestimates least": {
        "60/20": (
            0.006,
            0.0065
        ),
        "20/20": (
            0.0085,
            0.0085
        ),
        "120/20": (
            0.0105,
            0.0115
        ),
        "250/20": (
            0.008,
            0.008
        ),
        "60/60": (
            0.005,
            0.006
        )
    }
}
