# The joint bar, standalone: every number without lockrun's source

This directory reproduces the numbers of [the joint bar's README](../README.md) with numpy alone. It
does not import lockrun. `joint_rule.py` is the rule and the DSR's evaluation before it, `joint_world.py`
the null markets and the adversaries, `joint_tables.py` one function per table, `run.py` the commands.
Decisions are deterministic in the seeds: a table's count does not depend on the worker count or the order.

lockrun's suite (`tests/test_joint_bar_standalone.py`) runs this copy and the package on the same seeded
inputs and requires identical PASS decisions, statistics, weights and bars, so the copy cannot drift from
the product.

## Install

    python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

Python 3.10 or later. Checked at the minimum versions (numpy 1.26.0, scipy 1.11.4, Python 3.12: the `bar`,
`power` and `finding` tables and the flat, hedge, honest and every-trial-stopping rows) and at numpy 2.5.3:
the same numbers. scipy is pinned but the code does not import it today; numpy and the standard library
are all it runs on.

## Commands

From this directory's parent or from here; each prints its table with the README's row names:

| Command | What it prints | Full mode on this laptop |
|--|--|--|
| `python run.py bar` | c(n) (500k paths, seed 20261027) | 7 s |
| `python run.py finding` | Optional stopping under the DSR | 2 s |
| `python run.py adversaries` | Every variant, before and under the joint bar | 252 s |
| `python run.py adversaries --rows flat,hedge,honest` | Only the rows whose names contain these | about 60 s |
| `python run.py power` | The honest power cost | 1 s |
| `python run.py dropped` | The rules tried and dropped | 54 s |
| `python run.py sizing` | The edge in sizing, the warm-up | under 1 s |
| `python run.py cost` | The calibration's time and memory, one core | 6 min |
| `python run.py assumptions` | Dependence and adaptive exposure rules | 21 min with its tables (11 min of them), 10 min with `--bar-cache` |
| `python run.py all` | Every table | about 32 min |

- `--seeds N`: seeds 0 to N-1 per cell. Full mode, the default, is 2000 (`finding`: 10000, 3000 and 2000 by
  row). `bar`, `sizing` and `cost` take no seeds.
- `--quick`: 200 seeds per cell (50 and 100k-path bars in `assumptions`), a smoke test whose rates are noisy, not the README's numbers. `python run.py all --quick --jobs 2` took 5 min 53 s on this laptop limited to 2 worker processes; it was not timed on a 2-core machine.
- `--jobs N`: worker processes (default: every core). `--compare`: the README's number beside each, a
  difference flagged. `--json FILE`: the results.

## The numbers full mode produced

On a 10-core Apple Silicon laptop, numpy 2.5.3, 30 October 2026. Seeds 0 to N-1, N as stated; a cell is
the worst over its stopping rule (c from 1.5 to 3.5, first stop at period 2, 3, 20 or 100).

    c(1) 2.252  c(2) 2.552  c(5) 2.906  c(10) 3.146  c(50) 3.662  c(100) 3.854  c(1000) 4.418

| Strategy (null market, T = 250) | N | PASS under the DSR | Seeds | c, k0 |
|--|--|--|--|--|
| Honest: constant exposure, never stops | 1 | 0.0152 | 10000 | |
| Flat once its t-statistic reaches c (best c and first stop k0) | 1 | 0.2680 | 3000 | 2.0, 2 |
| Flat once its t-statistic reaches c (best c and first stop k0) | 2 | 0.0817 | 3000 | 2.5, 3 |
| The same, trading again for the last period | 1 | 0.1720 | 2000 | 2.0, 2 |
| The same, weights times 1e-6 instead of zero | 1 | 0.2710 | 2000 | 2.0, 2 |

2000 seeds per cell:

| Researcher strategy | Before (n = 1 / 2) | Joint bar (n = 1 / 2) |
|--|--|--|
| Honest, constant exposure | 0.0115 / 0.0020 | 0.0135 / 0.0105 |
| Honest, 10% random flat days | 0.0140 / 0.0020 | 0.0140 / 0.0100 |
| Flat once ahead | 0.2570 / 0.0705 | 0.0205 / 0.0160 |
| Flat, trading again for the last 1 period | 0.1640 / 0.0890 | 0.0205 / 0.0160 |
| Flat, trading again for the last 2 periods | 0.1195 / 0.0740 | 0.0200 / 0.0155 |
| Flat, trading again for the last 5 periods | 0.0830 / 0.0480 | 0.0175 / 0.0145 |
| Weights times 1e-6 once ahead | 0.2570 / 0.0705 | 0.0210 / 0.0145 |
| Weights times 0.01 once ahead | 0.2000 / 0.0680 | 0.0210 / 0.0145 |
| Weights times 0.05 once ahead | 0.1115 / 0.0390 | 0.0175 / 0.0130 |
| Same gross over every asset, 8 assets | 0.0140 / 0.0035 | 0.0130 / 0.0115 |
| Same gross over every asset, 100 assets | 0.0165 / 0.0045 | 0.0130 / 0.0105 |
| Hedge of two twin assets | 0.1290 / 0.0440 | 0.0205 / 0.0150 |
| Hedge with a drifting ratio | 0.0835 / 0.0285 | 0.0165 / 0.0130 |
| Only the lowest-variance asset | 0.0350 / 0.0075 | 0.0150 / 0.0105 |
| Pausing in the window covariance's null space (100 assets) | not run | 0.0125 / 0.0075 |
| An asset whose volatility the window lags (falls tenfold) | not run | 0.0200 / 0.0175 |
| Every trial stopping at c(n), n = 1 to 50, normal market | not run | at most 0.0205 over every stopping rule tried (0.0200 at the c(n) stop) |
| Every trial stopping at c(n), n = 1 to 50, Student-t(4) market | not run | at most 0.0280 |

| True annualized Sharpe | 0 | 1 | 2 | 3 | 4 |
|--|--|--|--|--|--|
| PASS before (DSR) | 0.015 | 0.119 | 0.413 | 0.775 | 0.962 |
| PASS with the joint bar | 0.010 | 0.099 | 0.337 | 0.690 | 0.931 |

Rules tried and dropped, 2000 seeds:

| Rule | n = 1 | n = 2 |
|--|--|--|
| Gross exposure with the fixed-T value: hedge | 0.2320 | 0.0810 |
| Gross exposure with the sequential value: hedge | 0.0915 | 0.0175 |
| Gross exposure with the fixed-T value: 100-asset spread | 0.0880 | 0.0280 |
| Gross exposure with the sequential value: 100-asset spread | 0.0285 | 0.0050 |

| Hedge, n = 1: shrinkage | 0 | 0.001 | 0.01 | 0.1 |
|--|--|--|--|--|
| Window 20 | 0.0080 | 0.0200 | 0.0610 | 0.1295 |
| Window 60 | 0.0070 | 0.0230 | 0.0655 | 0.1365 |
| Window 250 | 0.0090 | 0.0220 | 0.0635 | 0.1370 |

The composed bar over the exact quantile, in t-units: N = 2, 0.22; 3, 0.39; 6, 0.58; 11, 0.70; 51, 0.88.

The rule's t over the raw t on a sizing edge: 0.869 (seed 3, T = 20000). Largest T_eff at T = 250: 230.

The calibration on one core, 2M paths, in two runs: T = 250 normal 20 and 25 s, df = 4.2 27 and 37 s,
T = 2500 243 and 304 s; 408 MiB at most. Timings depend on the machine and what else runs on it.

## The assumptions table

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

## Calibration cost against the joint bar's README

Every rate and c(n) above equals that README's at the digits it prints. Its calibration cost (19 to 23 s,
200 to 240 s, 392 MiB) was another run on the same laptop: the times here are somewhat above it, the memory
4% above it.

## What the tables cover

The simulated worlds of the README: iid markets with one regime shift, GARCH and one-factor GARCH nulls, and adversaries that watch the statistic they are graded on, the assumptions table's knowing the risk estimator's state. Failed openings are supported by `Holdout` and pinned by the suite, though no table uses them.
