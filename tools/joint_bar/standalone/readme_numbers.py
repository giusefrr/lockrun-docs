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
    "Pausing in the window covariance's null space (100 assets)": (None, None, 0.0135, 0.0115),
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
  "1": 0.0115,
  "2": 0.0085
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
  "1": 0.0135,
  "2": 0.0115
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
  "1": 0.037,
  "2": 0.0285
 },
 "(1) Direction most underestimated, iid": {
  "1": 0.0355,
  "2": 0.031
 },
 "(1) Window's smallest eigenvalue, iid, 30 equal assets": {
  "1": 0.0335,
  "2": 0.038
 },
 "(1) Direction most underestimated, iid, 30 equal assets": {
  "1": 0.0335,
  "2": 0.038
 },
 "(1) Window's smallest eigenvalue, iid, 50 equal assets": {
  "1": 0.0465,
  "2": 0.043
 },
 "(1) Direction most underestimated, iid, 50 equal assets": {
  "1": 0.0465,
  "2": 0.043
 },
 "(1) Window's smallest eigenvalue, iid, 58 equal assets": {
  "1": 0.058,
  "2": 0.058
 },
 "(1) Direction most underestimated, iid, 58 equal assets": {
  "1": 0.058,
  "2": 0.058
 },
 "(1) Window's smallest eigenvalue, GARCH": {
  "1": 0.026,
  "2": 0.022
 },
 "(1) Direction most underestimated, GARCH": {
  "1": 0.0345,
  "2": 0.034
 },
 "(1) Window's smallest eigenvalue, GARCH, 50 assets": {
  "1": 0.0405,
  "2": 0.0445
 },
 "(1) Direction most underestimated, GARCH, 50 assets": {
  "1": 0.0305,
  "2": 0.0375
 },
 "(1) Window's smallest eigenvalue, one-factor GARCH": {
  "1": 0.0315,
  "2": 0.0285
 },
 "(1) Direction most underestimated, one-factor GARCH": {
  "1": 0.035,
  "2": 0.0325
 },
 "(2) Trades above 1.5x, floor otherwise, iid": {
  "1": 0.034,
  "2": 0.0375
 },
 "(2) Trades above 2.0x, floor otherwise, iid": {
  "1": 0.037,
  "2": 0.0385
 },
 "(2) Trades above 3.0x, floor otherwise, iid": {
  "1": 0.038,
  "2": 0.0295
 },
 "(2) Trades above 1.5x, floor otherwise, iid, 30 equal assets": {
  "1": 0.0565,
  "2": 0.075
 },
 "(2) Trades above 2.0x, floor otherwise, iid, 30 equal assets": {
  "1": 0.0565,
  "2": 0.075
 },
 "(2) Trades above 3.0x, floor otherwise, iid, 30 equal assets": {
  "1": 0.0575,
  "2": 0.0765
 },
 "(2) Trades above 1.5x, floor otherwise, iid, 50 equal assets": {
  "1": 0.0565,
  "2": 0.064
 },
 "(2) Trades above 2.0x, floor otherwise, iid, 50 equal assets": {
  "1": 0.058,
  "2": 0.064
 },
 "(2) Trades above 3.0x, floor otherwise, iid, 50 equal assets": {
  "1": 0.0585,
  "2": 0.0675
 },
 "(2) Trades above 1.5x, floor otherwise, iid, 58 equal assets": {
  "1": 0.08,
  "2": 0.088
 },
 "(2) Trades above 2.0x, floor otherwise, iid, 58 equal assets": {
  "1": 0.079,
  "2": 0.0875
 },
 "(2) Trades above 3.0x, floor otherwise, iid, 58 equal assets": {
  "1": 0.0795,
  "2": 0.09
 },
 "(3) Trades above 1.5x, floor otherwise, GARCH": {
  "1": 0.035,
  "2": 0.035
 },
 "(3) Trades above 2.0x, floor otherwise, GARCH": {
  "1": 0.034,
  "2": 0.037
 },
 "(3) Trades above 3.0x, floor otherwise, GARCH": {
  "1": 0.037,
  "2": 0.03
 },
 "(3) Trades above 1.5x, floor otherwise, GARCH, 50 assets": {
  "1": 0.045,
  "2": 0.0565
 },
 "(3) Trades above 2.0x, floor otherwise, GARCH, 50 assets": {
  "1": 0.0455,
  "2": 0.057
 },
 "(3) Trades above 3.0x, floor otherwise, GARCH, 50 assets": {
  "1": 0.0455,
  "2": 0.055
 },
 "(3) Trades above 1.5x, floor otherwise, one-factor GARCH": {
  "1": 0.0305,
  "2": 0.032
 },
 "(3) Trades above 2.0x, floor otherwise, one-factor GARCH": {
  "1": 0.033,
  "2": 0.0305
 },
 "(3) Trades above 3.0x, floor otherwise, one-factor GARCH": {
  "1": 0.0315,
  "2": 0.0275
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


NUMBERS = {"psr": {"BAR": BAR, "ADVERSARIES": ADVERSARIES, "AT_MOST": AT_MOST, "POWER": POWER}, "t": {}}


CONFIRMED = {'iid, rho = 0.5: honest': {1: 0.012375, 2: 0.009625, 3: 0.007375, 5: 0.008, 10: 0.0065, 20: 0.005875},
 'iid, rho = 0.5: flat once ahead': {1: 0.04525, 2: 0.04075, 3: 0.031625, 5: 0.03375, 10: 0.03475, 20: 0.030625},
 'iid, rho = 0.9: honest': {1: 0.012625, 2: 0.00775, 3: 0.00625, 5: 0.005125, 10: 0.00375, 20: 0.002375},
 'iid, rho = 0.9: flat once ahead': {1: 0.0435, 2: 0.03325, 3: 0.023625, 5: 0.020125, 10: 0.016625, 20: 0.011625},
 'one-factor GARCH, rho = 0.5: honest': {1: 0.011625, 2: 0.00975, 3: 0.009, 5: 0.01, 10: 0.0085, 20: 0.00625},
 'one-factor GARCH, rho = 0.5: flat once ahead': {1: 0.047625,
                                                  2: 0.044625,
                                                  3: 0.03625,
                                                  5: 0.038,
                                                  10: 0.03625,
                                                  20: 0.032875},
 'one-factor GARCH, rho = 0.9: honest': {1: 0.012125, 2: 0.009, 3: 0.006125, 5: 0.005125, 10: 0.004125, 20: 0.0025},
 'one-factor GARCH, rho = 0.9: flat once ahead': {1: 0.04725,
                                                  2: 0.038,
                                                  3: 0.03125,
                                                  5: 0.024375,
                                                  10: 0.019,
                                                  20: 0.01475},
 'GARCH: Honest, constant exposure': {1: 0.012875, 2: 0.012375},
 'GARCH: Honest, 10% random flat days': {1: 0.013875, 2: 0.01275},
 'GARCH: Flat once ahead': {1: 0.021625, 2: 0.0155},
 'GARCH: Flat, trading again for the last 1 period': {1: 0.021625, 2: 0.01875},
 'GARCH: Flat, trading again for the last 2 periods': {1: 0.021625, 2: 0.01825},
 'GARCH: Flat, trading again for the last 5 periods': {1: 0.021, 2: 0.01575},
 'GARCH: Weights times 1e-6 once ahead': {1: 0.021875, 2: 0.013875},
 'GARCH: Weights times 0.01 once ahead': {1: 0.021875, 2: 0.014},
 'GARCH: Weights times 0.05 once ahead': {1: 0.016125, 2: 0.01675},
 'GARCH: Same gross over every asset, 8 assets': {1: 0.01325, 2: 0.0115},
 'GARCH: Same gross over every asset, 100 assets': {1: 0.010875, 2: 0.008875},
 'GARCH: Hedge of two twin assets': {1: 0.0105, 2: 0.0145},
 'GARCH: Hedge with a drifting ratio': {1: 0.017375, 2: 0.013625},
 'GARCH: Only the lowest-variance asset': {1: 0.0135, 2: 0.01075},
 "GARCH: Pausing in the window covariance's null space (100 assets)": {1: 0.01125, 2: 0.010375},
 'GARCH: An asset whose volatility the window lags (falls tenfold)': {1: 0.01625, 2: 0.01175},
 'GARCH: Every trial stopping, n = 1 to 50': {1: 0.03175, 2: 0.03525, 5: 0.021375, 10: 0.02175, 50: 0.0215},
 'One-factor GARCH: Honest, constant exposure': {1: 0.013375, 2: 0.012},
 'One-factor GARCH: Honest, 10% random flat days': {1: 0.014, 2: 0.01175},
 'One-factor GARCH: Flat once ahead': {1: 0.02075, 2: 0.017625},
 'One-factor GARCH: Flat, trading again for the last 1 period': {1: 0.02075, 2: 0.01325},
 'One-factor GARCH: Flat, trading again for the last 2 periods': {1: 0.020375, 2: 0.0165},
 'One-factor GARCH: Flat, trading again for the last 5 periods': {1: 0.019125, 2: 0.013875},
 'One-factor GARCH: Weights times 1e-6 once ahead': {1: 0.021625, 2: 0.016875},
 'One-factor GARCH: Weights times 0.01 once ahead': {1: 0.0215, 2: 0.016875},
 'One-factor GARCH: Weights times 0.05 once ahead': {1: 0.016625, 2: 0.013625},
 'One-factor GARCH: Same gross over every asset, 8 assets': {1: 0.0125, 2: 0.012},
 'One-factor GARCH: Same gross over every asset, 100 assets': {1: 0.011375, 2: 0.008875},
 'One-factor GARCH: Hedge of two twin assets': {1: 0.020625, 2: 0.01575},
 'One-factor GARCH: Hedge with a drifting ratio': {1: 0.017, 2: 0.01425},
 'One-factor GARCH: Only the lowest-variance asset': {1: 0.011375, 2: 0.012125},
 "One-factor GARCH: Pausing in the window covariance's null space (100 assets)": {1: 0.009625, 2: 0.009375},
 'One-factor GARCH: An asset whose volatility the window lags (falls tenfold)': {1: 0.014125, 2: 0.01225},
 'One-factor GARCH: Every trial stopping, n = 1 to 50': {1: 0.029, 2: 0.029875, 5: 0.021, 10: 0.0205, 50: 0.0185},
 "(1) Window's smallest eigenvalue, iid": {1: 0.039625, 2: 0.04175},
 '(1) Direction most underestimated, iid': {1: 0.043625, 2: 0.04425},
 "(1) Window's smallest eigenvalue, iid, 30 equal assets": {1: 0.02525, 2: 0.025375},
 '(1) Direction most underestimated, iid, 30 equal assets': {1: 0.02525, 2: 0.025375},
 "(1) Window's smallest eigenvalue, iid, 50 equal assets": {1: 0.041375, 2: 0.038},
 '(1) Direction most underestimated, iid, 50 equal assets': {1: 0.041375, 2: 0.038},
 "(1) Window's smallest eigenvalue, iid, 58 equal assets": {1: 0.044375, 2: 0.041375},
 '(1) Direction most underestimated, iid, 58 equal assets': {1: 0.044375, 2: 0.041375},
 "(1) Window's smallest eigenvalue, GARCH": {1: 0.04625, 2: 0.046},
 '(1) Direction most underestimated, GARCH': {1: 0.04675, 2: 0.045},
 "(1) Window's smallest eigenvalue, GARCH, 50 assets": {1: 0.028125, 2: 0.024375},
 '(1) Direction most underestimated, GARCH, 50 assets': {1: 0.03625, 2: 0.03625},
 "(1) Window's smallest eigenvalue, one-factor GARCH": {1: 0.044625, 2: 0.04575},
 '(1) Direction most underestimated, one-factor GARCH': {1: 0.047875, 2: 0.044875},
 '(2) Trades above 1.5x, floor otherwise, iid': {1: 0.0425, 2: 0.040375},
 '(2) Trades above 2.0x, floor otherwise, iid': {1: 0.04675, 2: 0.044375},
 '(2) Trades above 3.0x, floor otherwise, iid': {1: 0.04825, 2: 0.048625},
 '(2) Trades above 1.5x, floor otherwise, iid, 30 equal assets': {1: 0.0185, 2: 0.013875},
 '(2) Trades above 2.0x, floor otherwise, iid, 30 equal assets': {1: 0.0185, 2: 0.013875},
 '(2) Trades above 3.0x, floor otherwise, iid, 30 equal assets': {1: 0.01525, 2: 0.012},
 '(2) Trades above 1.5x, floor otherwise, iid, 50 equal assets': {1: 0.031, 2: 0.02925},
 '(2) Trades above 2.0x, floor otherwise, iid, 50 equal assets': {1: 0.030375, 2: 0.029},
 '(2) Trades above 3.0x, floor otherwise, iid, 50 equal assets': {1: 0.031125, 2: 0.02925},
 '(2) Trades above 1.5x, floor otherwise, iid, 58 equal assets': {1: 0.04275, 2: 0.034625},
 '(2) Trades above 2.0x, floor otherwise, iid, 58 equal assets': {1: 0.042875, 2: 0.0345},
 '(2) Trades above 3.0x, floor otherwise, iid, 58 equal assets': {1: 0.043, 2: 0.034},
 '(3) Trades above 1.5x, floor otherwise, GARCH': {1: 0.042625, 2: 0.044},
 '(3) Trades above 2.0x, floor otherwise, GARCH': {1: 0.042875, 2: 0.04525},
 '(3) Trades above 3.0x, floor otherwise, GARCH': {1: 0.04975, 2: 0.049},
 '(3) Trades above 1.5x, floor otherwise, GARCH, 50 assets': {1: 0.0285, 2: 0.025875},
 '(3) Trades above 2.0x, floor otherwise, GARCH, 50 assets': {1: 0.0285, 2: 0.026125},
 '(3) Trades above 3.0x, floor otherwise, GARCH, 50 assets': {1: 0.028625, 2: 0.025875},
 '(3) Trades above 1.5x, floor otherwise, one-factor GARCH': {1: 0.045125, 2: 0.042875},
 '(3) Trades above 2.0x, floor otherwise, one-factor GARCH': {1: 0.041875, 2: 0.039625},
 '(3) Trades above 3.0x, floor otherwise, one-factor GARCH': {1: 0.048125, 2: 0.046375},
 "(1) Window's smallest eigenvalue, iid, 20 equal assets": {1: 0.033125, 2: 0.028625},
 '(1) Direction most underestimated, iid, 20 equal assets': {1: 0.033125, 2: 0.028625},
 '(2) Trades above 1.5x, floor otherwise, iid, 20 equal assets': {1: 0.019, 2: 0.016125},
 '(2) Trades above 2.0x, floor otherwise, iid, 20 equal assets': {1: 0.0175, 2: 0.015},
 '(2) Trades above 3.0x, floor otherwise, iid, 20 equal assets': {1: 0.009625, 2: 0.00725},
 "(1) Window's smallest eigenvalue, iid, 45 equal assets": {1: 0.03725, 2: 0.031875},
 '(1) Direction most underestimated, iid, 45 equal assets': {1: 0.03725, 2: 0.031875},
 '(2) Trades above 1.5x, floor otherwise, iid, 45 equal assets': {1: 0.0245, 2: 0.019625},
 '(2) Trades above 2.0x, floor otherwise, iid, 45 equal assets': {1: 0.0245, 2: 0.019625},
 '(2) Trades above 3.0x, floor otherwise, iid, 45 equal assets': {1: 0.024, 2: 0.018875},
 "(1) Window's smallest eigenvalue, iid, 50 equal assets with twins": {1: 0.021625, 2: 0.021},
 '(1) Direction most underestimated, iid, 50 equal assets with twins': {1: 0.039375, 2: 0.036625},
 '(2) Trades above 1.5x, floor otherwise, iid, 50 equal assets with twins': {1: 0.032375, 2: 0.03},
 '(2) Trades above 2.0x, floor otherwise, iid, 50 equal assets with twins': {1: 0.032, 2: 0.029875},
 '(2) Trades above 3.0x, floor otherwise, iid, 50 equal assets with twins': {1: 0.0325, 2: 0.029375},
 'Main: Honest, constant exposure': {1: 0.013, 2: 0.012125},
 'Main: Honest, 10% random flat days': {1: 0.013625, 2: 0.011875},
 'Main: Flat once ahead': {1: 0.021625, 2: 0.015625},
 'Main: Flat, trading again for the last 1 period': {1: 0.02175, 2: 0.016},
 'Main: Flat, trading again for the last 2 periods': {1: 0.02175, 2: 0.016},
 'Main: Flat, trading again for the last 5 periods': {1: 0.020125, 2: 0.016},
 'Main: Weights times 1e-6 once ahead': {1: 0.02175, 2: 0.015625},
 'Main: Weights times 0.01 once ahead': {1: 0.02175, 2: 0.015625},
 'Main: Weights times 0.05 once ahead': {1: 0.01875, 2: 0.014125},
 'Main: Same gross over every asset, 8 assets': {1: 0.010375, 2: 0.01125},
 'Main: Same gross over every asset, 100 assets': {1: 0.011625, 2: 0.0095},
 'Main: Hedge of two twin assets': {1: 0.02075, 2: 0.015375},
 'Main: Hedge with a drifting ratio': {1: 0.0175, 2: 0.014375},
 'Main: Only the lowest-variance asset': {1: 0.0135, 2: 0.011125},
 "Main: Pausing in the window covariance's null space (100 assets)": {1: 0.012375, 2: 0.010125},
 'Main: An asset whose volatility the window lags (falls tenfold)': {1: 0.01475, 2: 0.014125},
 'Main: Every trial stopping at c(n), n = 1 to 50, normal market': {1: 0.029625,
                                                                    2: 0.031125,
                                                                    5: 0.0185,
                                                                    10: 0.021375,
                                                                    50: 0.02125},
 'Main: Every trial stopping at c(n), n = 1 to 50, Student-t(4) market': {1: 0.02725,
                                                                          2: 0.030125,
                                                                          5: 0.01975,
                                                                          10: 0.0205,
                                                                          50: 0.0185},
 'Honest power, Sharpe 0': {1: 0.011375},
 'Honest power, Sharpe 1': {1: 0.089},
 'Honest power, Sharpe 2': {1: 0.3515},
 'Honest power, Sharpe 3': {1: 0.723875},
 'Honest power, Sharpe 4': {1: 0.935625},
 'Pauses after each losing step, iid': {1: 0.036125, 2: 0.035625},
 'Pauses while behind, iid': {1: 0.019875, 2: 0.019625},
 'Pauses where the window overestimates, iid': {1: 0.027375, 2: 0.025},
 'Pauses after each losing step, iid, 50 equal assets': {1: 0.0345, 2: 0.03325},
 'Pauses while behind, iid, 50 equal assets': {1: 0.021625, 2: 0.0215},
 'Pauses where the window overestimates, iid, 50 equal assets': {1: 0.024125, 2: 0.022125},
 'Pauses after each losing step, GARCH': {1: 0.03725, 2: 0.034875},
 'Pauses while behind, GARCH': {1: 0.024375, 2: 0.023625},
 'Pauses where the window overestimates, GARCH': {1: 0.0295, 2: 0.029625},
 'Pauses after each losing step, one-factor GARCH': {1: 0.034125, 2: 0.035375},
 'Pauses while behind, one-factor GARCH': {1: 0.024625, 2: 0.02375},
 'Pauses where the window overestimates, one-factor GARCH': {1: 0.02875, 2: 0.02825}}
BAR_T = {1: 2.277, 2: 2.585, 5: 2.949, 10: 3.193, 50: 3.713, 100: 3.927, 1000: 4.53}
ADVERSARIES_T = {'Honest, constant exposure': (0.0115, 0.002, 0.013, 0.0105),
 'Honest, 10% random flat days': (0.014, 0.002, 0.0135, 0.0095),
 'Flat once ahead': (0.257, 0.0705, 0.02, 0.0165),
 'Flat, trading again for the last 1 period': (0.164, 0.089, 0.02, 0.0165),
 'Flat, trading again for the last 2 periods': (0.1195, 0.074, 0.0195, 0.0165),
 'Flat, trading again for the last 5 periods': (0.083, 0.048, 0.0165, 0.0155),
 'Weights times 1e-6 once ahead': (0.257, 0.0705, 0.0205, 0.015),
 'Weights times 0.01 once ahead': (0.2, 0.068, 0.0205, 0.015),
 'Weights times 0.05 once ahead': (0.1115, 0.039, 0.017, 0.0135),
 'Same gross over every asset, 8 assets': (0.014, 0.0035, 0.0125, 0.012),
 'Same gross over every asset, 100 assets': (0.0165, 0.0045, 0.013, 0.011),
 'Hedge of two twin assets': (0.129, 0.044, 0.0195, 0.0155),
 'Hedge with a drifting ratio': (0.0835, 0.0285, 0.016, 0.0135),
 'Only the lowest-variance asset': (0.035, 0.0075, 0.0145, 0.0105),
 "Pausing in the window covariance's null space (100 assets)": (None, None, 0.014, 0.012),
 'An asset whose volatility the window lags (falls tenfold)': (None, None, 0.018, 0.015)}
AT_MOST_T = {'Every trial stopping at c(n), n = 1 to 50, normal market': 0.0295, 'Every trial stopping at c(n), n = 1 to 50, Student-t(4) market': 0.0385}
POWER_T = {'before': (0.015, 0.119, 0.413, 0.775, 0.962), 'joint': (0.01, 0.099, 0.331, 0.688, 0.93)}
NUMBERS["t"] = {"BAR": BAR_T, "ADVERSARIES": ADVERSARIES_T, "AT_MOST": AT_MOST_T, "POWER": POWER_T}
DROPPED = {'A, 60/20': 0.055,
 'A + B1, 60/20': 0.0565,
 'A + B2, 60/20': 0.0515,
 'A + B3, 60/20': 0.0545,
 'A, 20/20': 0.0615,
 'A + B1, 20/20': 0.058,
 'A + B2, 20/20': 0.0545,
 'A + B3, 20/20': 0.0,
 'A, 120/20': 0.052,
 'A + B1, 120/20': 0.0615,
 'A + B2, 120/20': 0.0525,
 'A + B3, 120/20': 0.0335,
 'A, 250/20': 0.05,
 'A + B1, 250/20': 0.0635,
 'A + B2, 250/20': 0.051,
 'A + B3, 250/20': 0.0335,
 'A, 60/60': 0.0505,
 'A + B1, 60/60': 0.05,
 'A + B2, 60/60': 0.0505,
 'A + B3, 60/60': 0.044,
 'A, targeted': 0.0535,
 'A + C1 f=0.25, targeted': 0.0535,
 'A + C1 f=0.5, targeted': 0.0535,
 'A + C2 k=3, targeted': 0.0605,
 'A + C2 k=4, targeted': 0.062,
 'A + C2 k=5, targeted': 0.062,
 'A + C1 f=0.5 + C2 k=4, targeted': 0.0625}
CHOSEN_STOPS = {'(1) Direction most underestimated, GARCH': {'1': ['c(n)', 100], '2': ['c(n)', 100]},
 '(3) Trades above 3.0x, floor otherwise, GARCH': {'1': ['c(n)', 100], '2': ['c(n)', 100]},
 '(2) Trades above 3.0x, floor otherwise, iid, 58 equal assets': {'1': ['c(n)', 100], '2': ['c(n)', 100]},
 'Main: Hedge of two twin assets': {'1': [2.5, 100], '2': [3.0, 100]},
 'Main: Flat once ahead': {'1': [2.5, 100], '2': [3.0, 100]},
 'Pauses after each losing step, iid': {'1': ['c(n)', 100], '2': ['c(n)', 100]},
 '(3) Trades above 1.5x, floor otherwise, GARCH': {'1': ['c(n)', 100], '2': ['c(n)', 100]},
 'Honest power, Sharpe 3': {'1': [None, None]}}
FRESH_PINS = {'(1) Direction most underestimated, GARCH': {1: 11, 2: 8},
 '(3) Trades above 3.0x, floor otherwise, GARCH': {1: 12, 2: 14},
 '(2) Trades above 3.0x, floor otherwise, iid, 58 equal assets': {1: 12, 2: 6},
 'Main: Hedge of two twin assets': {1: 6, 2: 1},
 'Main: Flat once ahead': {1: 7, 2: 1},
 'Pauses after each losing step, iid': {1: 12, 2: 10},
 '(3) Trades above 1.5x, floor otherwise, GARCH': {1: 12, 2: 9},
 'Honest power, Sharpe 3': {1: 218}}
