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
 "iid, rho = 0.5: honest": {
  "1": 0.014,
  "2": 0.0125,
  "3": 0.01,
  "5": 0.0105,
  "10": 0.009,
  "20": 0.007
 },
 "iid, rho = 0.5: flat once ahead": {
  "1": 0.033,
  "2": 0.0295,
  "3": 0.021,
  "5": 0.026,
  "10": 0.023,
  "20": 0.023
 },
 "iid, rho = 0.9: honest": {
  "1": 0.0125,
  "2": 0.0075,
  "3": 0.007,
  "5": 0.0045,
  "10": 0.0025,
  "20": 0.001
 },
 "iid, rho = 0.9: flat once ahead": {
  "1": 0.034,
  "2": 0.026,
  "3": 0.022,
  "5": 0.018,
  "10": 0.0125,
  "20": 0.0085
 },
 "one-factor GARCH, rho = 0.5: honest": {
  "1": 0.012,
  "2": 0.01,
  "3": 0.0095,
  "5": 0.0045,
  "10": 0.005,
  "20": 0.0035
 },
 "one-factor GARCH, rho = 0.5: flat once ahead": {
  "1": 0.0345,
  "2": 0.0295,
  "3": 0.022,
  "5": 0.015,
  "10": 0.017,
  "20": 0.013
 },
 "one-factor GARCH, rho = 0.9: honest": {
  "1": 0.0125,
  "2": 0.009,
  "3": 0.009,
  "5": 0.0065,
  "10": 0.0045,
  "20": 0.0035
 },
 "one-factor GARCH, rho = 0.9: flat once ahead": {
  "1": 0.033,
  "2": 0.025,
  "3": 0.016,
  "5": 0.015,
  "10": 0.0115,
  "20": 0.0075
 },
 "GARCH: Honest, constant exposure": {
  "1": 0.0085,
  "2": 0.0095
 },
 "GARCH: Honest, 10% random flat days": {
  "1": 0.0075,
  "2": 0.0075
 },
 "GARCH: Flat once ahead": {
  "1": 0.014,
  "2": 0.0125
 },
 "GARCH: Flat, trading again for the last 1 period": {
  "1": 0.0135,
  "2": 0.013
 },
 "GARCH: Flat, trading again for the last 2 periods": {
  "1": 0.0125,
  "2": 0.012
 },
 "GARCH: Flat, trading again for the last 5 periods": {
  "1": 0.01,
  "2": 0.013
 },
 "GARCH: Weights times 1e-6 once ahead": {
  "1": 0.016,
  "2": 0.0135
 },
 "GARCH: Weights times 0.01 once ahead": {
  "1": 0.016,
  "2": 0.0135
 },
 "GARCH: Weights times 0.05 once ahead": {
  "1": 0.0135,
  "2": 0.012
 },
 "GARCH: Same gross over every asset, 8 assets": {
  "1": 0.011,
  "2": 0.0125
 },
 "GARCH: Same gross over every asset, 100 assets": {
  "1": 0.01,
  "2": 0.008
 },
 "GARCH: Hedge of two twin assets": {
  "1": 0.0135,
  "2": 0.0115
 },
 "GARCH: Hedge with a drifting ratio": {
  "1": 0.015,
  "2": 0.0105
 },
 "GARCH: Only the lowest-variance asset": {
  "1": 0.0145,
  "2": 0.0115
 },
 "GARCH: Pausing in the window covariance's null space (100 assets)": {
  "1": 0.0075,
  "2": 0.005
 },
 "GARCH: An asset whose volatility the window lags (falls tenfold)": {
  "1": 0.0165,
  "2": 0.0155
 },
 "GARCH: Every trial stopping, n = 1 to 50": {
  "1": 0.021,
  "2": 0.018,
  "5": 0.0125,
  "10": 0.0095,
  "50": 0.0065
 },
 "One-factor GARCH: Honest, constant exposure": {
  "1": 0.012,
  "2": 0.0115
 },
 "One-factor GARCH: Honest, 10% random flat days": {
  "1": 0.013,
  "2": 0.0095
 },
 "One-factor GARCH: Flat once ahead": {
  "1": 0.0165,
  "2": 0.015
 },
 "One-factor GARCH: Flat, trading again for the last 1 period": {
  "1": 0.016,
  "2": 0.015
 },
 "One-factor GARCH: Flat, trading again for the last 2 periods": {
  "1": 0.0155,
  "2": 0.015
 },
 "One-factor GARCH: Flat, trading again for the last 5 periods": {
  "1": 0.0145,
  "2": 0.0145
 },
 "One-factor GARCH: Weights times 1e-6 once ahead": {
  "1": 0.019,
  "2": 0.0165
 },
 "One-factor GARCH: Weights times 0.01 once ahead": {
  "1": 0.0185,
  "2": 0.0155
 },
 "One-factor GARCH: Weights times 0.05 once ahead": {
  "1": 0.0155,
  "2": 0.0135
 },
 "One-factor GARCH: Same gross over every asset, 8 assets": {
  "1": 0.0125,
  "2": 0.011
 },
 "One-factor GARCH: Same gross over every asset, 100 assets": {
  "1": 0.0175,
  "2": 0.0145
 },
 "One-factor GARCH: Hedge of two twin assets": {
  "1": 0.0165,
  "2": 0.016
 },
 "One-factor GARCH: Hedge with a drifting ratio": {
  "1": 0.014,
  "2": 0.014
 },
 "One-factor GARCH: Only the lowest-variance asset": {
  "1": 0.017,
  "2": 0.012
 },
 "One-factor GARCH: Pausing in the window covariance's null space (100 assets)": {
  "1": 0.0105,
  "2": 0.0085
 },
 "One-factor GARCH: An asset whose volatility the window lags (falls tenfold)": {
  "1": 0.013,
  "2": 0.012
 },
 "One-factor GARCH: Every trial stopping, n = 1 to 50": {
  "1": 0.0205,
  "2": 0.018,
  "5": 0.0165,
  "10": 0.0105,
  "50": 0.0145
 },
 "(1) Window's smallest eigenvalue, iid": {
  "1": 0.0425,
  "2": 0.029
 },
 "(1) Direction most underestimated, iid": {
  "1": 0.03,
  "2": 0.031
 },
 "(1) Window's smallest eigenvalue, iid, 30 equal assets": {
  "1": 0.0395,
  "2": 0.0405
 },
 "(1) Direction most underestimated, iid, 30 equal assets": {
  "1": 0.0395,
  "2": 0.0405
 },
 "(1) Window's smallest eigenvalue, iid, 50 equal assets": {
  "1": 0.041,
  "2": 0.0475
 },
 "(1) Direction most underestimated, iid, 50 equal assets": {
  "1": 0.041,
  "2": 0.0475
 },
 "(1) Window's smallest eigenvalue, iid, 58 equal assets": {
  "1": 0.05,
  "2": 0.0535
 },
 "(1) Direction most underestimated, iid, 58 equal assets": {
  "1": 0.05,
  "2": 0.0535
 },
 "(1) Window's smallest eigenvalue, GARCH": {
  "1": 0.028,
  "2": 0.02
 },
 "(1) Direction most underestimated, GARCH": {
  "1": 0.0295,
  "2": 0.0295
 },
 "(1) Window's smallest eigenvalue, GARCH, 50 assets": {
  "1": 0.0425,
  "2": 0.0505
 },
 "(1) Direction most underestimated, GARCH, 50 assets": {
  "1": 0.0365,
  "2": 0.0295
 },
 "(1) Window's smallest eigenvalue, one-factor GARCH": {
  "1": 0.0325,
  "2": 0.0275
 },
 "(1) Direction most underestimated, one-factor GARCH": {
  "1": 0.033,
  "2": 0.032
 },
 "(2) Trades above 1.5x, floor otherwise, iid": {
  "1": 0.02,
  "2": 0.0205
 },
 "(2) Trades above 2.0x, floor otherwise, iid": {
  "1": 0.0335,
  "2": 0.032
 },
 "(2) Trades above 3.0x, floor otherwise, iid": {
  "1": 0.038,
  "2": 0.031
 },
 "(2) Trades above 1.5x, floor otherwise, iid, 30 equal assets": {
  "1": 0.0605,
  "2": 0.083
 },
 "(2) Trades above 2.0x, floor otherwise, iid, 30 equal assets": {
  "1": 0.0605,
  "2": 0.083
 },
 "(2) Trades above 3.0x, floor otherwise, iid, 30 equal assets": {
  "1": 0.062,
  "2": 0.082
 },
 "(2) Trades above 1.5x, floor otherwise, iid, 50 equal assets": {
  "1": 0.0525,
  "2": 0.059
 },
 "(2) Trades above 2.0x, floor otherwise, iid, 50 equal assets": {
  "1": 0.0505,
  "2": 0.0575
 },
 "(2) Trades above 3.0x, floor otherwise, iid, 50 equal assets": {
  "1": 0.0525,
  "2": 0.059
 },
 "(2) Trades above 1.5x, floor otherwise, iid, 58 equal assets": {
  "1": 0.066,
  "2": 0.081
 },
 "(2) Trades above 2.0x, floor otherwise, iid, 58 equal assets": {
  "1": 0.0665,
  "2": 0.08
 },
 "(2) Trades above 3.0x, floor otherwise, iid, 58 equal assets": {
  "1": 0.0665,
  "2": 0.0795
 },
 "(3) Trades above 1.5x, floor otherwise, GARCH": {
  "1": 0.027,
  "2": 0.0285
 },
 "(3) Trades above 2.0x, floor otherwise, GARCH": {
  "1": 0.0375,
  "2": 0.0285
 },
 "(3) Trades above 3.0x, floor otherwise, GARCH": {
  "1": 0.0385,
  "2": 0.0295
 },
 "(3) Trades above 1.5x, floor otherwise, GARCH, 50 assets": {
  "1": 0.047,
  "2": 0.0495
 },
 "(3) Trades above 2.0x, floor otherwise, GARCH, 50 assets": {
  "1": 0.048,
  "2": 0.0495
 },
 "(3) Trades above 3.0x, floor otherwise, GARCH, 50 assets": {
  "1": 0.048,
  "2": 0.0515
 },
 "(3) Trades above 1.5x, floor otherwise, one-factor GARCH": {
  "1": 0.031,
  "2": 0.0295
 },
 "(3) Trades above 2.0x, floor otherwise, one-factor GARCH": {
  "1": 0.0405,
  "2": 0.034
 },
 "(3) Trades above 3.0x, floor otherwise, one-factor GARCH": {
  "1": 0.032,
  "2": 0.0255
 },
 "Pauses after each losing step, iid": {
  "1": 0.031,
  "2": 0.0255
 },
 "Pauses while behind, iid": {
  "1": 0.022,
  "2": 0.0205
 },
 "Pauses where the window overestimates, iid": {
  "1": 0.018,
  "2": 0.016
 },
 "Pauses after each losing step, iid, 50 equal assets": {
  "1": 0.023,
  "2": 0.017
 },
 "Pauses while behind, iid, 50 equal assets": {
  "1": 0.0195,
  "2": 0.0195
 },
 "Pauses where the window overestimates, iid, 50 equal assets": {
  "1": 0.0195,
  "2": 0.022
 },
 "Pauses after each losing step, GARCH": {
  "1": 0.026,
  "2": 0.025
 },
 "Pauses while behind, GARCH": {
  "1": 0.0215,
  "2": 0.02
 },
 "Pauses where the window overestimates, GARCH": {
  "1": 0.02,
  "2": 0.0165
 },
 "Pauses after each losing step, one-factor GARCH": {
  "1": 0.025,
  "2": 0.0235
 },
 "Pauses while behind, one-factor GARCH": {
  "1": 0.0135,
  "2": 0.0125
 },
 "Pauses where the window overestimates, one-factor GARCH": {
  "1": 0.019,
  "2": 0.02
 }
}
