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

The rule assumes independent trials and iid returns, and its risk estimate is known to the researcher. These rows relax each, under the joint bar. Command: `python standalone/run.py assumptions`, with `--parts a,b,c`, `--window` and `--warmup`; no lockrun needed ([standalone/README.md](standalone/README.md)).

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

- The market: iid returns, and GARCH(1,1) in the assumptions table. A common volatility factor, fat-tailed
  cross-sections and unbalanced panels are not simulated.
- The adversaries: each watches the statistic it is graded on and stops at the first crossing; an
  adversary that trades on information about the risk estimate's error beyond the regime shift is not.
- The bar's assumptions: trials independent (the maximum over correlated trials has a lower quantile,
  so the bar is conservative for them), iid Student-t returns at the holdout's fitted tail.
