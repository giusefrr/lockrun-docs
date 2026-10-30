# The joint bar: the simulations behind lockrun's statistical rule of 27 October 2026

lockrun counts every backtest run against a protected holdout, so a strategy's Deflated Sharpe Ratio
(DSR) is computed with the true number of trials N. These scripts show that a correct N is not
enough, and they measured the rule that replaced the DSR's verdict. They are for an external
reviewer, the DSR's authors among them, to rerun and to vary. The rule is stated in full in
[THREAT_MODEL.md §5a](../../THREAT_MODEL.md#5a-statistical-rule-the-joint-bar-27-october-2026); this
page gives the finding, the rule in short, every number and the one command that prints it.

## The finding: optional stopping passes the DSR at 0.27, nominal 0.05

A strategy that watches its own running t-statistic and goes flat (zero weights) once it is ahead
keeps the t-statistic of its first k periods, while the PSR counts all T periods: the zeros dilute
nothing. Under the DSR with N correct (every opening counted, and one more reserved for the fresh
verification), at a nominal false-positive rate of 0.05, on a null market (iid zero-mean returns):

| Strategy (null market, T = 250) | PASS rate under the DSR |
|--|--|
| Honest: constant exposure, never stops | 0.015 (N = 1) |
| Flat once its t-statistic reaches c (best c and first stop k0) | **0.268** (N = 1), 0.082 (N = 2) |
| The same, trading again for the last period | 0.17 (N = 1) |
| The same, weights times 1e-6 instead of zero | 0.27 (N = 1) |

The last two rows defeat a rule that only looks at a terminal run of zeros. Commands (on the code
before the rule, below): `round1_zero_tail_grid.py` prints rows 1 and 2 (3000 seeds per cell, 10000
for the honest rate), `round1_evasions.py` rows 3 and 4 (2000 seeds). The table further down
repeats these strategies with 2000 seeds and the stopping grid of the later rounds.

## The rule

1. **Risk normalization.** Each step's return is divided by the ex-ante risk of its weights,
   sqrt(w' S w), with S the sample covariance of the held assets over the 60 rows strictly before the
   step (at least 20; no shrinkage). A step with no weights, no estimate, zero risk or a risk under 10%
   of the strategy's median active risk is inactive. Going flat, or cutting the size to almost zero,
   no longer stretches the series.
2. **T_eff.** The statistic is the PSR statistic against 0 on the active steps' normalized returns,
   z = sr sqrt(T_eff - 1) / sqrt(1 - skew sr + (kurt - 1)/4 sr^2); T_eff, the number of active steps,
   is what the minimum track record min_t applies to.
3. **The joint bar c(N).** F is the null CDF of sup over k in [min_t, T] of z_k for one trial (the
   researcher may stop at any k), simulated with iid Student-t returns at the holdout's fitted df
   (floor 4). For n trials each free to stop, c(n) = F^-1(threshold^(1/n)), and a candidate passes iff
   z >= c(n). n is every opening counted in N except fresh verifications. Each of the DSR's five
   trial families keeps its trials, with z scaled by s = max(1, the sd of its other trials'
   t-statistics).

On the holdout the implementation checks use (T = 250, min_t = 100, threshold 0.95, normal tail):

    c(1) 2.252  c(2) 2.552  c(5) 2.906  c(10) 3.146  c(50) 3.662  c(100) 3.854  c(1000) 4.418

Command: `uv run python tools/joint_bar/bar_table.py`.

## The numbers: every adversarial variant, nominal 0.05

PASS rate under the null, 2000 seeds per cell. "Before" is the DSR with N correct; "joint bar" is
the rule as implemented (`lockrun/exposure.py`, `lockrun/calibration.py`, `evaluate_promotion`, run
through `tests/risk_world.py`). Each adversary cell is the worst over its stopping rule (c from 1.5
to 3.5, first stop at period 2, 3, 20 or 100).

| Researcher strategy | Before (n = 1 / 2) | Joint bar (n = 1 / 2) |
|--|--|--|
| Honest, constant exposure | 0.0115 / 0.0020 | 0.0135 / 0.0105 |
| Honest, 10% random flat days | 0.0140 / 0.0020 | 0.0140 / 0.0100 |
| Flat once ahead | 0.257 / 0.0705 | 0.0205 / 0.0160 |
| Flat, trading again for the last 1 period | 0.164 / 0.089 | 0.0205 / 0.0160 |
| Flat, trading again for the last 2 periods | 0.1195 / 0.074 | 0.0200 / 0.0155 |
| Flat, trading again for the last 5 periods | 0.083 / 0.048 | 0.0175 / 0.0145 |
| Weights times 1e-6 once ahead | 0.257 / 0.0705 | 0.0210 / 0.0145 |
| Weights times 0.01 once ahead | 0.200 / 0.068 | 0.0210 / 0.0145 |
| Weights times 0.05 once ahead | 0.1115 / 0.039 | 0.0175 / 0.0130 |
| Same gross over every asset, 8 assets | 0.014 / 0.0035 | 0.0130 / 0.0115 |
| Same gross over every asset, 100 assets | 0.0165 / 0.0045 | 0.0130 / 0.0105 |
| Hedge of two twin assets | 0.129 / 0.044 | 0.0205 / 0.0150 |
| Hedge with a drifting ratio | 0.0835 / 0.0285 | 0.0165 / 0.0130 |
| Only the lowest-variance asset | 0.035 / 0.0075 | 0.0150 / 0.0105 |
| Pausing in the window covariance's null space (100 assets) | not run | 0.0125 / 0.0075 |
| An asset whose volatility the window lags (falls tenfold) | not run | 0.0200 / 0.0175 |
| Every trial stopping at c(n), n = 1 to 50, normal market | not run | at most 0.0205 over every stopping rule tried (0.0200 at the c(n) stop) |
| Every trial stopping at c(n), n = 1 to 50, Student-t(4) market | not run | at most 0.0280 |

| Column | Command |
|--|--|
| Before | `uv run python tools/joint_bar/round3_main.py`, column "today", on the code before the rule (below) |
| Joint bar, rows 1 to 14 | `uv run python tools/joint_bar/implementation_check.py` |
| Joint bar, rows 15 to 18 | `uv run python tools/joint_bar/implementation_check_rest.py` |

Rules that were tried and dropped, with their numbers: normalizing by gross exposure missed the hedge
and the 100-asset spread at n = 1 (fixed-T value: hedge 0.232, 100 assets 0.088; sequential value: hedge
0.0915, 100 assets 0.0285), `round2_rules.py`; shrinking S toward its diagonal by
0.01 or more gave the hedge back its excess (0.06 to 0.14), `round3_sensitivity.py`; composing a
sequential critical value with the DSR's sr0 was valid but 0.2 to 0.9 t-units too high,
`round2_composition.py` and `round2_joint_quantiles.py`.

## The assumptions: dependence and adaptive exposure rules

**Above nominal, nominal 0.05: an adversary that sets the whole gross in the direction the window most underestimates, with every step kept active, passes at up to 0.0830 (n = 2, 2000 seeds), 0.0848 on 8000 fresh seeds at the stop the first 2000 chose, and 0.0925 at a window of 120 or 250.** Dependence (at most 0.0345), GARCH markets replaying every row of the main table (at most 0.0210) and pauses within the budget (at most 0.0310) stay below nominal.

Why: the excess comes from the PSR statistic's denominator, not from the bar or the risk estimate's mean. With a universe close to the window, the smallest eigenvalue is close to zero on some steps, so one step's normalized return can be 40 times the median. A positive one gives the series large skew, and sqrt(1 - skew sr + (kurt - 1)/4 sr^2) falls well below 1: runs that pass have a median t-statistic of 1.79 to 1.96, under the bar of about 2.25, and a median denominator term of 0.37 to 0.48 (0.87 to 0.95 over all runs). With no stop, on 1500 seeds, z passes at 0.037 (58 assets) and 0.047 (30 assets) while the t-statistic against the same bar passes at 0.011 and 0.005. A scale alone changes no normalized return, so the (2) rows exceed the (1) rows only because scaling keeps those steps above the 10% floor.

Command: `python standalone/run.py assumptions`, with `--parts a,b,c,d`, `--rows`, `--window`, `--warmup` and `--first-seed`; no lockrun needed. Each holdout gets the product's own procedure: its df fitted on its residuals, its bar from 2M paths, seed 20261027 (174 distinct dfs in the table, each exactly the calibration that holdout would get). 2000 seeds, 0 to 1999, unless stated. A cell is the worst over its stops, so a cell near 0.05 carries that selection; the fresh seeds below do not. T_eff is the first trial's median at that stop; "refused" is the share of runs under min_t. Rows above nominal say so.

### Confirmed on fresh seeds

Seeds 2000 to 9999, 8000 of them, each row at the stop the first 2000 seeds chose, so these rates carry no selection (standard error about 0.003).

| Fresh seeds, at the stop the first 2000 chose: | n = 1 / 2 | |
|--|--|--|
| Fresh: (1) Window's smallest eigenvalue, iid, 30 equal assets | 0.0382 / 0.0401 |  |
| Fresh: (1) Direction most underestimated, iid, 30 equal assets | 0.0382 / 0.0401 |  |
| Fresh: (1) Window's smallest eigenvalue, iid, 50 equal assets | 0.0425 / 0.0444 |  |
| Fresh: (1) Direction most underestimated, iid, 50 equal assets | 0.0424 / 0.0444 |  |
| Fresh: (1) Window's smallest eigenvalue, iid, 58 equal assets | 0.0503 / 0.0546 | above nominal |
| Fresh: (1) Direction most underestimated, iid, 58 equal assets | 0.0503 / 0.0545 | above nominal |
| Fresh: (2) Trades above 1.5x, floor otherwise, iid, 30 equal assets | 0.0619 / 0.0756 | above nominal |
| Fresh: (2) Trades above 2.0x, floor otherwise, iid, 30 equal assets | 0.0619 / 0.0756 | above nominal |
| Fresh: (2) Trades above 3.0x, floor otherwise, iid, 30 equal assets | 0.0636 / 0.0809 | above nominal |
| Fresh: (2) Trades above 1.5x, floor otherwise, iid, 50 equal assets | 0.0505 / 0.0601 | above nominal |
| Fresh: (2) Trades above 2.0x, floor otherwise, iid, 50 equal assets | 0.0504 / 0.0676 | above nominal |
| Fresh: (2) Trades above 3.0x, floor otherwise, iid, 50 equal assets | 0.0467 / 0.0686 | above nominal |
| Fresh: (2) Trades above 1.5x, floor otherwise, iid, 58 equal assets | 0.0704 / 0.0841 | above nominal |
| Fresh: (2) Trades above 2.0x, floor otherwise, iid, 58 equal assets | 0.0703 / 0.0843 | above nominal |
| Fresh: (2) Trades above 3.0x, floor otherwise, iid, 58 equal assets | 0.0706 / 0.0848 | above nominal |
| Fresh: (1) Window's smallest eigenvalue, GARCH, 50 assets | 0.0399 / 0.0510 | above nominal |
| Fresh: (1) Direction most underestimated, GARCH, 50 assets | 0.0299 / 0.0296 |  |
| Fresh: (3) Trades above 1.5x, floor otherwise, GARCH, 50 assets | 0.0426 / 0.0503 | above nominal |
| Fresh: (3) Trades above 2.0x, floor otherwise, GARCH, 50 assets | 0.0434 / 0.0499 |  |
| Fresh: (3) Trades above 3.0x, floor otherwise, GARCH, 50 assets | 0.0436 / 0.0499 |  |

At 50 assets on GARCH the cells are at nominal within the noise. On equal assets attack (2) is above it at 30, 50 and 58 assets at n = 2, and attack (1) at 58.

### (a) Correlated trials

Weights share one latent draw, correlation rho between returns (measured 0.498 and 0.899); stops from the grid and at c(n) and c(n) + 0.3, only with more than min_t active steps. The one-factor market carries half of each asset's variance on one GARCH(1,1) factor (alpha 0.1, beta 0.85, Student-t innovations at df 4.35), so assets are correlated and their volatility moves together. T_eff median is 230 in every cell, refused 0%.

| Row | n = 1 | n = 2 | n = 3 | n = 5 | n = 10 | n = 20 | |
|--|--|--|--|--|--|--|--|
| iid, rho = 0.5: honest | 0.0140 | 0.0125 | 0.0100 | 0.0105 | 0.0090 | 0.0070 |  |
| iid, rho = 0.5: flat once ahead | 0.0330 | 0.0295 | 0.0210 | 0.0260 | 0.0230 | 0.0230 |  |
| iid, rho = 0.9: honest | 0.0125 | 0.0075 | 0.0070 | 0.0045 | 0.0025 | 0.0010 |  |
| iid, rho = 0.9: flat once ahead | 0.0340 | 0.0260 | 0.0220 | 0.0180 | 0.0125 | 0.0085 |  |
| one-factor GARCH, rho = 0.5: honest | 0.0120 | 0.0100 | 0.0095 | 0.0045 | 0.0050 | 0.0035 |  |
| one-factor GARCH, rho = 0.5: flat once ahead | 0.0345 | 0.0295 | 0.0220 | 0.0150 | 0.0170 | 0.0130 |  |
| one-factor GARCH, rho = 0.9: honest | 0.0125 | 0.0090 | 0.0090 | 0.0065 | 0.0045 | 0.0035 |  |
| one-factor GARCH, rho = 0.9: flat once ahead | 0.0330 | 0.0250 | 0.0160 | 0.0150 | 0.0115 | 0.0075 |  |

### (b) The main table on GARCH markets, each holdout its own bar

The main table's stops, on independent GARCH(1,1) assets and on the one-factor market. Fitted df: 4 to 6.95 (GARCH, 8 assets), 4 to 21.4 (one-factor).

| Row | n = 1 / 2 | T_eff median | Refused | |
|--|--|--|--|--|
| GARCH: Honest, constant exposure | 0.0085 / 0.0095 | 230 / 230 | 0% / 0% |  |
| GARCH: Honest, 10% random flat days | 0.0075 / 0.0075 | 207 / 207 | 0% / 0% |  |
| GARCH: Flat once ahead | 0.0140 / 0.0125 | 230 / 230 | 2% / 1% |  |
| GARCH: Flat, trading again for the last 1 period | 0.0135 / 0.0130 | 230 / 230 | 2% / 1% |  |
| GARCH: Flat, trading again for the last 2 periods | 0.0125 / 0.0120 | 230 / 230 | 2% / 1% |  |
| GARCH: Flat, trading again for the last 5 periods | 0.0100 / 0.0130 | 230 / 230 | 2% / 0% |  |
| GARCH: Weights times 1e-6 once ahead | 0.0160 / 0.0135 | 230 / 230 | 0% / 0% |  |
| GARCH: Weights times 0.01 once ahead | 0.0160 / 0.0135 | 230 / 230 | 0% / 0% |  |
| GARCH: Weights times 0.05 once ahead | 0.0135 / 0.0120 | 230 / 230 | 0% / 0% |  |
| GARCH: Same gross over every asset, 8 assets | 0.0110 / 0.0125 | 230 / 230 | 0% / 0% |  |
| GARCH: Same gross over every asset, 100 assets | 0.0100 / 0.0080 | 230 / 230 | 0% / 0% |  |
| GARCH: Hedge of two twin assets | 0.0135 / 0.0115 | 230 / 230 | 0% / 0% |  |
| GARCH: Hedge with a drifting ratio | 0.0150 / 0.0105 | 230 / 230 | 0% / 0% |  |
| GARCH: Only the lowest-variance asset | 0.0145 / 0.0115 | 230 / 230 | 0% / 0% |  |
| GARCH: Pausing in the window covariance's null space (100 assets) | 0.0075 / 0.0050 | 153 / 153 | 1% / 1% |  |
| GARCH: An asset whose volatility the window lags (falls tenfold) | 0.0165 / 0.0155 | 230 / 230 | 0% / 0% |  |
| One-factor GARCH: Honest, constant exposure | 0.0120 / 0.0115 | 230 / 230 | 0% / 0% |  |
| One-factor GARCH: Honest, 10% random flat days | 0.0130 / 0.0095 | 207 / 207 | 0% / 0% |  |
| One-factor GARCH: Flat once ahead | 0.0165 / 0.0150 | 230 / 230 | 1% / 0% |  |
| One-factor GARCH: Flat, trading again for the last 1 period | 0.0160 / 0.0150 | 230 / 230 | 1% / 1% |  |
| One-factor GARCH: Flat, trading again for the last 2 periods | 0.0155 / 0.0150 | 230 / 230 | 1% / 0% |  |
| One-factor GARCH: Flat, trading again for the last 5 periods | 0.0145 / 0.0145 | 230 / 230 | 1% / 0% |  |
| One-factor GARCH: Weights times 1e-6 once ahead | 0.0190 / 0.0165 | 230 / 230 | 0% / 0% |  |
| One-factor GARCH: Weights times 0.01 once ahead | 0.0185 / 0.0155 | 230 / 230 | 0% / 0% |  |
| One-factor GARCH: Weights times 0.05 once ahead | 0.0155 / 0.0135 | 230 / 230 | 0% / 0% |  |
| One-factor GARCH: Same gross over every asset, 8 assets | 0.0125 / 0.0110 | 230 / 230 | 0% / 0% |  |
| One-factor GARCH: Same gross over every asset, 100 assets | 0.0175 / 0.0145 | 230 / 230 | 0% / 0% |  |
| One-factor GARCH: Hedge of two twin assets | 0.0165 / 0.0160 | 230 / 230 | 0% / 0% |  |
| One-factor GARCH: Hedge with a drifting ratio | 0.0140 / 0.0140 | 230 / 230 | 0% / 0% |  |
| One-factor GARCH: Only the lowest-variance asset | 0.0170 / 0.0120 | 230 / 230 | 0% / 0% |  |
| One-factor GARCH: Pausing in the window covariance's null space (100 assets) | 0.0105 / 0.0085 | 153 / 153 | 2% / 0% |  |
| One-factor GARCH: An asset whose volatility the window lags (falls tenfold) | 0.0130 / 0.0120 | 230 / 230 | 0% / 0% |  |

| Every trial stopping, each holdout its own bar | n = 1 | n = 2 | n = 5 | n = 10 | n = 50 |
|--|--|--|--|--|--|
| GARCH | 0.0210 | 0.0180 | 0.0125 | 0.0095 | 0.0065 |
| One-factor GARCH | 0.0205 | 0.0180 | 0.0165 | 0.0105 | 0.0145 |

### (c) Adversaries with the estimator's state

Rebalanced every step, a random sign each step, stops from the grid and at c(n) and c(n) + 0.3, only with more than min_t active steps. (1) The whole gross in the window's smallest non-null eigenvalue's direction, or in the direction minimizing w' S w / w' Sigma w, with Sigma the true covariance, known before the step. (2) That direction, at a fixed risk, only where true risk exceeds estimated risk by the factor; elsewhere random weights at 10% of that risk, so every step stays active. (3) The same on GARCH markets, timed on the conditional volatility. The twins make a hedge the smallest eigenvalue at 8 assets; the equal-asset markets have none, and there the window's error is largest.

| Row | n = 1 / 2 | T_eff median | Refused | |
|--|--|--|--|--|
| (1) Window's smallest eigenvalue, iid | 0.0425 / 0.0290 | 230 / 230 | 0% / 0% |  |
| (1) Direction most underestimated, iid | 0.0300 / 0.0310 | 230 / 230 | 0% / 0% |  |
| (1) Window's smallest eigenvalue, iid, 30 equal assets | 0.0395 / 0.0405 | 228 / 228 | 0% / 0% |  |
| (1) Direction most underestimated, iid, 30 equal assets | 0.0395 / 0.0405 | 228 / 228 | 0% / 0% |  |
| (1) Window's smallest eigenvalue, iid, 50 equal assets | 0.0410 / 0.0475 | 230 / 230 | 0% / 0% |  |
| (1) Direction most underestimated, iid, 50 equal assets | 0.0410 / 0.0475 | 230 / 230 | 0% / 0% |  |
| (1) Window's smallest eigenvalue, iid, 58 equal assets | 0.0500 / 0.0535 | 228 / 228 | 0% / 0% | above nominal |
| (1) Direction most underestimated, iid, 58 equal assets | 0.0500 / 0.0535 | 228 / 228 | 0% / 0% | above nominal |
| (1) Window's smallest eigenvalue, GARCH | 0.0280 / 0.0200 | 230 / 230 | 0% / 0% |  |
| (1) Direction most underestimated, GARCH | 0.0295 / 0.0295 | 230 / 230 | 0% / 0% |  |
| (1) Window's smallest eigenvalue, GARCH, 50 assets | 0.0425 / 0.0505 | 230 / 230 | 0% / 0% | above nominal |
| (1) Direction most underestimated, GARCH, 50 assets | 0.0365 / 0.0295 | 229 / 229 | 0% / 0% |  |
| (1) Window's smallest eigenvalue, one-factor GARCH | 0.0325 / 0.0275 | 230 / 230 | 0% / 0% |  |
| (1) Direction most underestimated, one-factor GARCH | 0.0330 / 0.0320 | 230 / 230 | 0% / 0% |  |
| (2) Trades above 1.5x, floor otherwise, iid | 0.0200 / 0.0205 | 230 / 230 | 0% / 0% | ; traded 39% of steps |
| (2) Trades above 2.0x, floor otherwise, iid | 0.0335 / 0.0320 | 230 / 230 | 0% / 0% | ; traded 3% of steps |
| (2) Trades above 3.0x, floor otherwise, iid | 0.0380 / 0.0310 | 230 / 230 | 0% / 0% | ; traded 0% of steps |
| (2) Trades above 1.5x, floor otherwise, iid, 30 equal assets | 0.0605 / 0.0830 | 230 / 230 | 0% / 0% | above nominal; traded 100% of steps |
| (2) Trades above 2.0x, floor otherwise, iid, 30 equal assets | 0.0605 / 0.0830 | 230 / 230 | 0% / 0% | above nominal; traded 100% of steps |
| (2) Trades above 3.0x, floor otherwise, iid, 30 equal assets | 0.0620 / 0.0820 | 230 / 230 | 0% / 0% | above nominal; traded 71% of steps |
| (2) Trades above 1.5x, floor otherwise, iid, 50 equal assets | 0.0525 / 0.0590 | 230 / 230 | 0% / 0% | above nominal; traded 99% of steps |
| (2) Trades above 2.0x, floor otherwise, iid, 50 equal assets | 0.0505 / 0.0575 | 230 / 230 | 0% / 0% | above nominal; traded 98% of steps |
| (2) Trades above 3.0x, floor otherwise, iid, 50 equal assets | 0.0525 / 0.0590 | 230 / 230 | 0% / 0% | above nominal; traded 95% of steps |
| (2) Trades above 1.5x, floor otherwise, iid, 58 equal assets | 0.0660 / 0.0810 | 230 / 230 | 0% / 0% | above nominal; traded 98% of steps |
| (2) Trades above 2.0x, floor otherwise, iid, 58 equal assets | 0.0665 / 0.0800 | 230 / 230 | 0% / 0% | above nominal; traded 96% of steps |
| (2) Trades above 3.0x, floor otherwise, iid, 58 equal assets | 0.0665 / 0.0795 | 230 / 230 | 0% / 0% | above nominal; traded 93% of steps |
| (3) Trades above 1.5x, floor otherwise, GARCH | 0.0270 / 0.0285 | 230 / 230 | 0% / 0% | ; traded 82% of steps |
| (3) Trades above 2.0x, floor otherwise, GARCH | 0.0375 / 0.0285 | 230 / 230 | 0% / 0% | ; traded 10% of steps |
| (3) Trades above 3.0x, floor otherwise, GARCH | 0.0385 / 0.0295 | 230 / 230 | 0% / 0% | ; traded 0% of steps |
| (3) Trades above 1.5x, floor otherwise, GARCH, 50 assets | 0.0470 / 0.0495 | 230 / 230 | 0% / 0% | ; traded 100% of steps |
| (3) Trades above 2.0x, floor otherwise, GARCH, 50 assets | 0.0480 / 0.0495 | 230 / 230 | 0% / 0% | ; traded 98% of steps |
| (3) Trades above 3.0x, floor otherwise, GARCH, 50 assets | 0.0480 / 0.0515 | 230 / 230 | 0% / 0% | above nominal; traded 95% of steps |
| (3) Trades above 1.5x, floor otherwise, one-factor GARCH | 0.0310 / 0.0295 | 230 / 230 | 0% / 0% | ; traded 64% of steps |
| (3) Trades above 2.0x, floor otherwise, one-factor GARCH | 0.0405 / 0.0340 | 230 / 230 | 0% / 0% | ; traded 5% of steps |
| (3) Trades above 3.0x, floor otherwise, one-factor GARCH | 0.0320 / 0.0255 | 230 / 230 | 0% / 0% | ; traded 0% of steps |

### (d) Pauses within the budget

At most T - min_t - 1 inactive steps, warm-up included, and a stop only with more than min_t active steps: nothing here is refused, so a low rate is the rule's, not a refusal.

| Row | n = 1 / 2 | T_eff median | Refused | |
|--|--|--|--|--|
| Pauses after each losing step, iid | 0.0310 / 0.0255 | 153 / 153 | 0% / 0% |  |
| Pauses while behind, iid | 0.0220 / 0.0205 | 101 / 101 | 0% / 0% |  |
| Pauses where the window overestimates, iid | 0.0180 / 0.0160 | 120 / 120 | 0% / 0% |  |
| Pauses after each losing step, iid, 50 equal assets | 0.0230 / 0.0170 | 153 / 153 | 0% / 0% |  |
| Pauses while behind, iid, 50 equal assets | 0.0195 / 0.0195 | 101 / 101 | 0% / 0% |  |
| Pauses where the window overestimates, iid, 50 equal assets | 0.0195 / 0.0220 | 121 / 121 | 0% / 0% |  |
| Pauses after each losing step, GARCH | 0.0260 / 0.0250 | 153 / 153 | 0% / 0% |  |
| Pauses while behind, GARCH | 0.0215 / 0.0200 | 101 / 101 | 0% / 0% |  |
| Pauses where the window overestimates, GARCH | 0.0200 / 0.0165 | 135 / 136 | 0% / 0% |  |
| Pauses after each losing step, one-factor GARCH | 0.0250 / 0.0235 | 153 / 154 | 0% / 0% |  |
| Pauses while behind, one-factor GARCH | 0.0135 / 0.0125 | 101 / 101 | 0% / 0% |  |
| Pauses where the window overestimates, one-factor GARCH | 0.0190 / 0.0200 | 132 / 133 | 0% / 0% |  |

### (c) and (d) at other windows and warm-ups

| Row, n = 1 / 2 (T_eff median at n = 1) | Window, warm-up 20, 20 | Window, warm-up 120, 20 | Window, warm-up 250, 20 | Window, warm-up 60, 60 |
|--|--|--|--|--|
| (1) Window's smallest eigenvalue, iid | 0.0370 / 0.0345 (230) | 0.0375 / 0.0320 (230) | 0.0400 / 0.0365 (230) | 0.0275 / 0.0220 (190) |
| (1) Direction most underestimated, iid | 0.0375 / 0.0325 (230) | 0.0295 / 0.0295 (230) | 0.0290 / 0.0265 (230) | 0.0300 / 0.0315 (190) |
| (1) Window's smallest eigenvalue, iid, 30 equal assets | 0.0395 / 0.0355 (230) | 0.0275 / 0.0350 (227) | 0.0270 / 0.0365 (226) | 0.0320 / 0.0365 (190) |
| (1) Direction most underestimated, iid, 30 equal assets | 0.0395 / 0.0355 (230) | 0.0275 / 0.0350 (227) | 0.0270 / 0.0365 (226) | 0.0320 / 0.0365 (190) |
| (1) Window's smallest eigenvalue, iid, 50 equal assets | 0.0395 / 0.0285 (230) | 0.0300 / 0.0350 (225) | 0.0280 / 0.0340 (224) | 0.0350 / 0.0345 (190) |
| (1) Direction most underestimated, iid, 50 equal assets | 0.0330 / 0.0310 (230) | 0.0300 / 0.0355 (225) | 0.0280 / 0.0335 (224) | 0.0350 / 0.0345 (190) |
| (1) Window's smallest eigenvalue, iid, 58 equal assets | 0.0340 / 0.0345 (230) | 0.0320 / 0.0420 (225) | 0.0285 / 0.0375 (224) | 0.0455 / 0.0510 (189) above nominal |
| (1) Direction most underestimated, iid, 58 equal assets | 0.0340 / 0.0345 (230) | 0.0320 / 0.0420 (225) | 0.0285 / 0.0375 (224) | 0.0455 / 0.0510 (189) above nominal |
| (1) Window's smallest eigenvalue, GARCH | 0.0420 / 0.0340 (230) | 0.0290 / 0.0215 (230) | 0.0270 / 0.0195 (230) | 0.0220 / 0.0170 (190) |
| (1) Direction most underestimated, GARCH | 0.0280 / 0.0325 (230) | 0.0270 / 0.0220 (230) | 0.0260 / 0.0250 (230) | 0.0320 / 0.0245 (190) |
| (1) Window's smallest eigenvalue, GARCH, 50 assets | 0.0310 / 0.0225 (230) | 0.0435 / 0.0520 (229) above nominal | 0.0405 / 0.0495 (229) | 0.0240 / 0.0240 (190) |
| (1) Direction most underestimated, GARCH, 50 assets | 0.0270 / 0.0220 (230) | 0.0285 / 0.0305 (224) | 0.0265 / 0.0315 (222) | 0.0230 / 0.0220 (190) |
| (1) Window's smallest eigenvalue, one-factor GARCH | 0.0395 / 0.0355 (230) | 0.0385 / 0.0280 (230) | 0.0345 / 0.0260 (230) | 0.0215 / 0.0180 (190) |
| (1) Direction most underestimated, one-factor GARCH | 0.0400 / 0.0320 (230) | 0.0330 / 0.0310 (230) | 0.0305 / 0.0320 (230) | 0.0300 / 0.0285 (190) |
| (2) Trades above 1.5x, floor otherwise, iid | 0.0365 / 0.0330 (230) | 0.0220 / 0.0220 (230) | 0.0220 / 0.0220 (230) | 0.0325 / 0.0315 (190) |
| (2) Trades above 2.0x, floor otherwise, iid | 0.0370 / 0.0400 (230) | 0.0305 / 0.0300 (230) | 0.0320 / 0.0290 (230) | 0.0260 / 0.0250 (190) |
| (2) Trades above 3.0x, floor otherwise, iid | 0.0450 / 0.0520 (230) above nominal | 0.0385 / 0.0345 (230) | 0.0390 / 0.0355 (230) | 0.0260 / 0.0250 (190) |
| (2) Trades above 1.5x, floor otherwise, iid, 30 equal assets | 0.0395 / 0.0355 (230) | 0.0600 / 0.0750 (230) above nominal | 0.0600 / 0.0815 (230) above nominal | 0.0320 / 0.0365 (190) |
| (2) Trades above 2.0x, floor otherwise, iid, 30 equal assets | 0.0390 / 0.0350 (230) | 0.0555 / 0.0795 (230) above nominal | 0.0550 / 0.0815 (230) above nominal | 0.0320 / 0.0365 (190) |
| (2) Trades above 3.0x, floor otherwise, iid, 30 equal assets | 0.0475 / 0.0500 (230) | 0.0680 / 0.0925 (230) above nominal | 0.0680 / 0.0925 (230) above nominal | 0.0395 / 0.0400 (190) |
| (2) Trades above 1.5x, floor otherwise, iid, 50 equal assets | 0.0365 / 0.0360 (230) | 0.0620 / 0.0715 (230) above nominal | 0.0585 / 0.0695 (230) above nominal | 0.0350 / 0.0345 (190) |
| (2) Trades above 2.0x, floor otherwise, iid, 50 equal assets | 0.0410 / 0.0410 (230) | 0.0630 / 0.0710 (230) above nominal | 0.0625 / 0.0705 (230) above nominal | 0.0350 / 0.0345 (190) |
| (2) Trades above 3.0x, floor otherwise, iid, 50 equal assets | 0.0405 / 0.0370 (230) | 0.0575 / 0.0705 (230) above nominal | 0.0570 / 0.0700 (230) above nominal | 0.0350 / 0.0345 (190) |
| (2) Trades above 1.5x, floor otherwise, iid, 58 equal assets | 0.0465 / 0.0375 (230) | 0.0580 / 0.0805 (230) above nominal | 0.0620 / 0.0850 (230) above nominal | 0.0590 / 0.0700 (190) above nominal |
| (2) Trades above 2.0x, floor otherwise, iid, 58 equal assets | 0.0445 / 0.0350 (230) | 0.0600 / 0.0815 (230) above nominal | 0.0615 / 0.0835 (230) above nominal | 0.0590 / 0.0700 (190) above nominal |
| (2) Trades above 3.0x, floor otherwise, iid, 58 equal assets | 0.0445 / 0.0350 (230) | 0.0625 / 0.0825 (230) above nominal | 0.0600 / 0.0865 (230) above nominal | 0.0590 / 0.0700 (190) above nominal |
| (3) Trades above 1.5x, floor otherwise, GARCH | 0.0280 / 0.0325 (230) | 0.0270 / 0.0275 (230) | 0.0250 / 0.0210 (230) | 0.0290 / 0.0275 (190) |
| (3) Trades above 2.0x, floor otherwise, GARCH | 0.0305 / 0.0290 (230) | 0.0355 / 0.0290 (230) | 0.0355 / 0.0315 (230) | 0.0300 / 0.0230 (190) |
| (3) Trades above 3.0x, floor otherwise, GARCH | 0.0295 / 0.0400 (230) | 0.0315 / 0.0325 (230) | 0.0315 / 0.0355 (230) | 0.0295 / 0.0255 (190) |
| (3) Trades above 1.5x, floor otherwise, GARCH, 50 assets | 0.0340 / 0.0325 (230) | 0.0600 / 0.0710 (230) above nominal | 0.0610 / 0.0655 (230) above nominal | 0.0230 / 0.0220 (190) |
| (3) Trades above 2.0x, floor otherwise, GARCH, 50 assets | 0.0310 / 0.0250 (230) | 0.0615 / 0.0700 (230) above nominal | 0.0635 / 0.0675 (230) above nominal | 0.0230 / 0.0220 (190) |
| (3) Trades above 3.0x, floor otherwise, GARCH, 50 assets | 0.0305 / 0.0260 (230) | 0.0620 / 0.0675 (230) above nominal | 0.0620 / 0.0650 (230) above nominal | 0.0230 / 0.0220 (190) |
| (3) Trades above 1.5x, floor otherwise, one-factor GARCH | 0.0400 / 0.0320 (230) | 0.0295 / 0.0345 (230) | 0.0310 / 0.0320 (230) | 0.0395 / 0.0295 (190) |
| (3) Trades above 2.0x, floor otherwise, one-factor GARCH | 0.0375 / 0.0290 (230) | 0.0390 / 0.0315 (230) | 0.0380 / 0.0310 (230) | 0.0370 / 0.0310 (190) |
| (3) Trades above 3.0x, floor otherwise, one-factor GARCH | 0.0450 / 0.0415 (230) | 0.0320 / 0.0245 (230) | 0.0295 / 0.0220 (230) | 0.0365 / 0.0280 (190) |
| Pauses after each losing step, iid | 0.0265 / 0.0225 (153) | 0.0285 / 0.0230 (153) | 0.0300 / 0.0265 (153) | 0.0235 / 0.0235 (127) |
| Pauses while behind, iid | 0.0185 / 0.0205 (101) | 0.0210 / 0.0190 (101) | 0.0210 / 0.0205 (101) | 0.0160 / 0.0155 (101) |
| Pauses where the window overestimates, iid | 0.0250 / 0.0170 (124) | 0.0180 / 0.0180 (118) | 0.0175 / 0.0150 (117) | 0.0125 / 0.0150 (101) |
| Pauses after each losing step, iid, 50 equal assets | 0.0235 / 0.0245 (153) | 0.0225 / 0.0185 (153) | 0.0245 / 0.0195 (153) | 0.0180 / 0.0170 (127) |
| Pauses while behind, iid, 50 equal assets | 0.0215 / 0.0185 (101) | 0.0200 / 0.0190 (101) | 0.0200 / 0.0200 (101) | 0.0205 / 0.0170 (101) |
| Pauses where the window overestimates, iid, 50 equal assets | 0.0235 / 0.0190 (124) | 0.0180 / 0.0140 (119) | 0.0195 / 0.0095 (119) | 0.0165 / 0.0140 (101) |
| Pauses after each losing step, GARCH | 0.0250 / 0.0270 (153) | 0.0260 / 0.0245 (153) | 0.0245 / 0.0245 (153) | 0.0165 / 0.0135 (127) |
| Pauses while behind, GARCH | 0.0215 / 0.0180 (101) | 0.0205 / 0.0210 (101) | 0.0185 / 0.0215 (101) | 0.0175 / 0.0155 (101) |
| Pauses where the window overestimates, GARCH | 0.0185 / 0.0205 (151) | 0.0235 / 0.0135 (123) | 0.0190 / 0.0150 (117) | 0.0190 / 0.0130 (111) |
| Pauses after each losing step, one-factor GARCH | 0.0265 / 0.0250 (153) | 0.0280 / 0.0230 (153) | 0.0265 / 0.0230 (153) | 0.0255 / 0.0215 (127) |
| Pauses while behind, one-factor GARCH | 0.0125 / 0.0115 (101) | 0.0150 / 0.0120 (101) | 0.0140 / 0.0115 (101) | 0.0135 / 0.0160 (101) |
| Pauses where the window overestimates, one-factor GARCH | 0.0250 / 0.0255 (140) | 0.0105 / 0.0130 (124) | 0.0130 / 0.0155 (120) | 0.0200 / 0.0165 (108) |

## The honest power cost

One honest trial holding one asset, daily periods, T = 250, n = 1:

| True annualized Sharpe | 0 | 1 | 2 | 3 | 4 |
|--|--|--|--|--|--|
| PASS before (DSR) | 0.015 | 0.119 | 0.413 | 0.775 | 0.962 |
| PASS with the joint bar | 0.010 | 0.099 | 0.337 | 0.690 | 0.931 |

Commands: the "before" row is the last block of `round3_main.py` (column "today") on the code before
the rule; the joint-bar row is the last block of `implementation_check_rest.py`, and
`tests/test_joint_bar_controls.py` pins it. Two further costs are not in the table. The 20-row
warm-up leaves T_eff at most T - 20. Returns over their ex-ante risk weigh every active step alike,
so an edge that lies only in sizing (a larger position when the per-period Sharpe is known to be
higher) is not measured: about 13% of the t-statistic (ratio 0.869; theoretical 0.83) in the documented case.

The calibration's own cost (`round3_cost.py`, one core): 19 to 23 s for T = 250 and 200 to 240 s for
T = 2500, 2M paths, 392 MiB at most.

## Running the scripts

**Without lockrun's source:** [standalone/README.md](standalone/README.md) reproduces these tables with
numpy alone, one command per table. The scripts below are the originals.

The scripts import lockrun's package and its test worlds (`tests/adversary_world.py`,
`tests/risk_world.py`). They need lockrun's source tree, which is not public at this writing; the
copies in the public documents repository are for reading. With the source, run each from the
repository's root with the project's environment (uv):

    uv run python tools/joint_bar/<script>.py

Every script is deterministic (seeded). The multi-process scripts use 10 worker processes (written
for a 10-core laptop).

**The "before" numbers need the code before the rule.** From the rule's first commit on,
`evaluate_promotion` computes the joint bar, so the round 1 to 3 scripts' "today" column is the DSR
only on fe072c0, the last commit before it. In a worktree of that commit, with these scripts copied
in, the scripts import that commit's lockrun and test worlds:

    git worktree add ../lockrun-before-the-joint-bar fe072c0
    cd ../lockrun-before-the-joint-bar && git checkout main -- tools/joint_bar
    uv run python tools/joint_bar/round3_calibrate.py     # joint_tables.json: normal and df = 4 tables
    uv run python tools/joint_bar/round3_cost.py          # adds the df = 4.2 table round3_main reads
    uv run python tools/joint_bar/round3_main.py
    uv run python tools/joint_bar/round1_zero_tail_grid.py
    uv run python tools/joint_bar/round1_evasions.py

## Every script

| Script | Code | What it prints |
|--|--|--|
| `round1_zero_tail_grid.py` | before | Flat once ahead under the DSR: the best three (c, k0) per N = 1, 2, 3, 5, then the honest rate. |
| `round1_evasions.py` | before | Trading again for the last 1, 2, 5 periods, and weights times 1e-6 to 0.05, under the DSR. |
| `round2_sequential_calibration.py` | either | The critical value of sup over k of the PSR statistic under the null (T = 250, min_t = 100; normal and Student-t(5)), against approximations. |
| `round2_rules.py` | before | Every variant under the DSR, gross-exposure normalization with T_eff, and the sequential value. |
| `round2_composition.py` | before | Every trial stopping, n = 1 to 50, the sequential value composed with the DSR's sr0, and its power. |
| `round2_joint_quantiles.py` | either | The composed bar against the exact quantile of the maximum over N trials. |
| `round3_joint_bar.py` | either | The joint bar as first simulated: the df fit and the table c(N). |
| `round3_calibrate.py` | either | Writes `joint_tables.json` (c(N), normal and df = 4 tails, 2M paths, one core). Run it before the round-3 scripts. |
| `round3_risk_sim.py` | before | The module the next two use: risk normalization with T_eff and the joint bar, simulated. |
| `round3_sensitivity.py` | either | The covariance window (20, 60, 250 rows) against shrinkage (0 to 0.1) on the variants that attack the risk estimate. |
| `round3_main.py` | before | Every variant ("today" and the simulated rule), every trial stopping, honest power. |
| `round3_cost.py` | either | The calibration's time and memory on one core; adds the df = 4.2 table to `joint_tables.json`. |
| `bar_table.py` | current | c(n) through the implemented calibration. |
| `implementation_check.py` | current | Rows 1 to 14 under the implemented rule. |
| `implementation_check_rest.py` | current | Rows 15 to 18 and the honest power row under the implemented rule. |

"before" runs on fe072c0 for its DSR column; "current" on the code with the rule; "either" does not
call lockrun's verdict. The test suite pins the implemented cells with fewer seeds
(`tests/test_adversary_zero_tail.py`, `test_adversary_risk_cuts.py`, `test_adversary_risk_estimate.py`,
`test_joint_bar_controls.py`).

## What a reviewer may want to vary

- The market: iid returns, GARCH(1,1) and one-factor GARCH in the assumptions table. Unbalanced panels are
  not simulated.
- The adversaries: each watches the statistic it is graded on and stops at the first crossing; the
  assumptions table's also know the risk estimator's state.
- The bar's assumptions: trials independent (the maximum over correlated trials has a lower quantile,
  so the bar is conservative for them), iid Student-t returns at the holdout's fitted tail.
