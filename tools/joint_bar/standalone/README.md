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
| `python run.py assumptions` | Dependence and adaptive exposure rules | 104 s |
| `python run.py all` | Every table | about 12 min |

- `--seeds N`: seeds 0 to N-1 per cell. Full mode, the default, is 2000 (`finding`: 10000, 3000 and 2000 by
  row). `bar`, `sizing` and `cost` take no seeds.
- `--quick`: 200 seeds per cell, a smoke test whose rates are noisy, not the README's numbers.
  `python run.py all --quick --jobs 2` took 107 s on this laptop limited to 2 worker processes; it was not
  timed on a 2-core machine.
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

`python run.py assumptions`, 104 s in full mode on this laptop, seeds 0 to 1999. `--parts a,b,c` picks some; `--window` and `--warmup` vary the estimator, for this table only.

| Assumption, under the joint bar, 2000 seeds | n = 1 / 2 |
|--|--|
| (a) Trials sharing a latent signal, rho = 0.5: honest | 0.0135 / 0.0115 |
| (a) Trials sharing a latent signal, rho = 0.5: flat once ahead | 0.0190 / 0.0145 |
| (a) Trials sharing a latent signal, rho = 0.9: honest | 0.0125 / 0.0075 |
| (a) Trials sharing a latent signal, rho = 0.9: flat once ahead | 0.0200 / 0.0140 |
| (b) GARCH(1,1) null: Honest, constant exposure | 0.0085 / 0.0090 |
| (b) GARCH(1,1) null: Honest, 10% random flat days | 0.0075 / 0.0075 |
| (b) GARCH(1,1) null: Flat once ahead | 0.0140 / 0.0120 |
| (b) GARCH(1,1) null: Flat, trading again for the last 1 period | 0.0135 / 0.0125 |
| (b) GARCH(1,1) null: Flat, trading again for the last 2 periods | 0.0125 / 0.0115 |
| (b) GARCH(1,1) null: Flat, trading again for the last 5 periods | 0.0100 / 0.0125 |
| (b) GARCH(1,1) null: Weights times 1e-6 once ahead | 0.0160 / 0.0130 |
| (b) GARCH(1,1) null: Weights times 0.01 once ahead | 0.0160 / 0.0130 |
| (b) GARCH(1,1) null: Weights times 0.05 once ahead | 0.0135 / 0.0125 |
| (b) GARCH(1,1) null: Same gross over every asset, 8 assets | 0.0110 / 0.0135 |
| (b) GARCH(1,1) null: Same gross over every asset, 100 assets | 0.0100 / 0.0090 |
| (b) GARCH(1,1) null: Hedge of two twin assets | 0.0135 / 0.0110 |
| (b) GARCH(1,1) null: Hedge with a drifting ratio | 0.0150 / 0.0115 |
| (b) GARCH(1,1) null: Only the lowest-variance asset | 0.0150 / 0.0120 |
| (b) GARCH(1,1) null: Pausing in the window covariance's null space (100 assets) | 0.0075 / 0.0050 |
| (b) GARCH(1,1) null: An asset whose volatility the window lags (falls tenfold) | 0.0175 / 0.0160 |
| (b) GARCH(1,1) null: Every trial stopping, n = 1 to 50 | at most 0.0205 over every stop tried (0.0205 at the c(n) stop) |
| (c) Knows the estimator, iid market: weights times true / estimated risk | 0.0205 / 0.0160 |
| (c) Knows the estimator, iid market: all weight where the window most underestimates | 0.0140 / 0.0175 |
| (c) Knows the estimator, iid market: the same, flat where it underestimates least | 0.0040 / 0.0040 |
| (c) Knows the estimator, GARCH market: weights times true / estimated risk | 0.0140 / 0.0120 |
| (c) Knows the estimator, GARCH market: all weight where the window most underestimates | 0.0180 / 0.0115 |
| (c) Knows the estimator, GARCH market: the same, flat where it underestimates least | 0.0060 / 0.0065 |

| (d) The (c) rows, n = 1 / 2 | Window 60, warm-up 20 | Window 20, warm-up 20 | Window 120, warm-up 20 | Window 250, warm-up 20 | Window 60, warm-up 60 |
|--|--|--|--|--|--|
| Knows the estimator, iid market: weights times true / estimated risk | 0.0205 / 0.0160 | 0.0195 / 0.0165 | 0.0185 / 0.0170 | 0.0180 / 0.0170 | 0.0095 / 0.0100 |
| Knows the estimator, iid market: all weight where the window most underestimates | 0.0140 / 0.0175 | 0.0185 / 0.0155 | 0.0180 / 0.0160 | 0.0130 / 0.0160 | 0.0165 / 0.0140 |
| Knows the estimator, iid market: the same, flat where it underestimates least | 0.0040 / 0.0040 | 0.0095 / 0.0095 | 0.0025 / 0.0025 | 0.0010 / 0.0030 | 0.0060 / 0.0045 |
| Knows the estimator, GARCH market: weights times true / estimated risk | 0.0140 / 0.0120 | 0.0145 / 0.0140 | 0.0120 / 0.0110 | 0.0115 / 0.0120 | 0.0135 / 0.0095 |
| Knows the estimator, GARCH market: all weight where the window most underestimates | 0.0180 / 0.0115 | 0.0195 / 0.0170 | 0.0220 / 0.0145 | 0.0220 / 0.0175 | 0.0190 / 0.0155 |
| Knows the estimator, GARCH market: the same, flat where it underestimates least | 0.0060 / 0.0065 | 0.0085 / 0.0085 | 0.0105 / 0.0115 | 0.0080 / 0.0080 | 0.0050 / 0.0060 |

Every rate as measured, nominal 0.05: none is above nominal; the highest is 0.0205 in the table and 0.0220 in the window sweep. A cell is the worst over its stopping rule (the grid above and, in (c), no stop), so the rates carry that selection. These bound the adversaries built here, not every adversary.

How each was built:

- **(a)** The trials' weights share one latent draw, with correlation rho (measured between their returns: 0.498 and 0.899). n = 1 changes nothing but the draws, so only n = 2 tests dependence; n >= 3, where the bar's scale would act on correlated trials, is not run.
- **(b)** Each asset an independent GARCH(1,1), alpha 0.1, beta 0.85, no common volatility factor; the twins as in the main table. Innovations at df 4.35, the rule's fit on the Student-t(4) market. The bar is one calibration at df 4.5, the rule's fit on seed 0's holdout. A deployment fits each holdout: over 100 holdouts the fit ranged from 4.00 to 6.30 (median 4.12), c(1) from 2.366 to 2.302. Holdouts fitted above 4.5 would have a slightly lower bar than the one used; that is not simulated.
- **(c)** The adversary knows each asset's true conditional volatility before each period. A scale alone cannot do what the row asks: r / sqrt(w' S w) does not move with the size of w, so true / estimated risk acts only through the 10% floor (a test pins it). The two further rows change the portfolio instead: all weight on the asset with the largest true / estimated risk, and the same, flat on steps below the median of the ratios so far. That last row's low rate is mostly refusal, not detection: on the GARCH market T_eff has median 116 (45 to 193, 300 seeds), a third of its runs are under min_t with no stop, and 8 of the 9 runs stopped at c = 2.5 from period 100 are. It is a weak form of this attack; a pause on fewer steps is not run.
- **(d)** The same (c) rows at other windows and warm-ups, `--window` and `--warmup`. The bar does not depend on them. They apply to this table only, and the implemented rule stays at 60 and 20.

## Calibration cost against the joint bar's README

Every rate and c(n) above equals that README's at the digits it prints. Its calibration cost (19 to 23 s,
200 to 240 s, 392 MiB) was another run on the same laptop: the times here are somewhat above it, the memory
4% above it.

## Limits

Only the simulated worlds of the README: iid markets with one regime shift, the GARCH null, adversaries that watch the
statistic they are graded on. Failed openings are supported by `Holdout` and pinned by the suite, though no
table uses them.
