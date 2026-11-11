# Rule version 3: the false-pass bound and its conditions

Status, 10 November 2026: rule version 3 is the default for new holdouts; its bar is the declared portfolio's (v3-close,
5 November 2026). Nothing of version 3 has run on a live host (WHAT_IS_VERIFIED.md).

**What this document claims.**
- **Proven:** the theorem below, under assumptions A1 and A2. No assumption is proven here.
- **A1 is measured, not proven.** In the 20 complete null worlds no cell is above alpha (2,077 below, 78 at alpha
  within their 95% interval), and it fails in the three skewed-crash worlds. No level of the size table is settled.
  Read with the correction of 10 November 2026 at the top of [SIZE_TABLE.md](SIZE_TABLE.md): a 'below' close to alpha
  is unsettled.
- **A2 is closed in code and tested.** It is not verified on a live host.
- **The crash-premium hurdle** is decided and measured on ten cells. It is not implemented and not proven.

Code: in lockrun's source (not public), `lockrun/declared.py` (the declaration, the deviation), `lockrun/calibration.py`
(`boot_bar`, the levels), `lockrun/data/host.py` (the bar at the opening) and `lockrun/service/app.py` (grading,
feedback, slots). The numpy-only copy, which is published, is `tools/joint_bar/standalone/joint_rule.py`
(`declared_active`, `graded_on`, `boot_seed`, `BootStream`, `boot_bar`). lockrun's suite holds it to the package's
number (`tests/test_declared_bar.py`).

**The hole it closes.** Under versions 1 and 2 a promote is graded at c(n), n the openings so far, and a FAIL ends
nothing. A researcher who stops each trial at the bar and promotes after each opening spends about 5%/k at opening k,
with no ceiling. Our red-team engine measured 0.1915 false promotions at 100 openings (lower bound 0.187), and 0.0683 at
just 2.

## The rule

At init, risk declares N, the planned openings. Opening k of the holdout, counted across all researchers, spends

    alpha_k = 0.045 / N  (k <= N),     alpha_k = 0.005 * 6 / (pi^2 (k - N)^2)  (k > N),     sum_k alpha_k <= 0.05.

**The declared portfolio.** The signed execute request names the trial portfolio: its starting weights and an exposure
rule (`hold`, or `inverse_vol` over the rule's window). Both are predictable: step t's weights read only periods before
t, and which assets have a row dated t. At the trial's opening, before any row reaches the strategy, the data host
computes:
1. that portfolio's normalized returns x_d over every step of the holdout;
2. the bar b_k: the (1 - a_k) quantile of the sup of the t-statistic over every stopping time in [min_t, T]. The
   quantile comes from a stationary block bootstrap of x_d (mean block T^(1/3)), each draw's sign randomized. a_k is
   the largest level at or below alpha_k among the levels the code lists (`SETTLED_LEVELS`); with none, there is no
   bar;
3. x_d's active steps A_d: those whose declared ex-ante risk is at least the floor (0.1) times the median declared risk
   over the whole holdout. They are fixed here, once, from the declaration, never from a trial.

The data host signs b_k and A_d. The opening record carries both, with the declaration's hash and the method, and
nothing recomputes them.

**Grading.** A promote grades the run's latest trial: PASS iff its t exceeds the bar. A trial within its declaration is
graded on A_d alone: its r_t / risk_t on the steps of A_d through its stop (exposure.graded_on).
- **Deviation.** Suppose the realized weights leave the declared ones by more than the rule's tolerance: L1 0.05 at any
  step up to the trial's last weight. Then the bar is the stricter of b_k and the bar of the trial's own realized
  series, under the same seed and level. The data host signs the deviation and that bar, and risk reads both in the
  promote record and the risk report.
- **Stopping**, meaning zero weights from some step on, is not a deviation.
- **No bar.** A trial with no declaration, or one off the holdout, has no bar and is a plain FAIL.

Before the first pass a researcher reads only FAIL. The first pass freezes the holdout; a reproduction makes it final.

## The theorem

Let the adversary be everyone who chooses trials, jointly, with private randomness w independent of the data. A *false
pass* is a first pass on a null trial: a trial with no edge, its declared series of conditional mean zero. S_k is trial
k's statistic and B_k its graded bar.

**Lemma (unique transcript).** Under A2, every transcript before the first pass is F, F, .... So trial k, its
declaration included, is p_k(w), a function of w alone, on every path that reaches k without a pass. *Proof:* induction
on k. Each answer was F, and timing, counts and refusals are constant across outcomes (A2). ∎

**Theorem.** If A1 and A2 hold, then P(false pass) <= sum_k alpha_k <= 0.05. This holds for any dependence between
trials, any stopping inside a trial and any adaptive use of the FAIL bit.

*Proof:* couple the adaptive run with the one that plays p_1(w), p_2(w), ... regardless of the answers. By the lemma the
two agree until the first pass. Fix w. Each trial is now fixed in advance, so by A1 P(S_k > B_k) <= alpha_k, and the
union bound needs no independence. Average over w. ∎

The theorem is exactly as strong as A1 and A2. Neither is proven: A1 is a property of the null distribution of the
holdout's returns, which no argument about the procedure alone can establish. Where A1 fails, the theorem says nothing,
and the measured size there is above alpha (below).

## A1, an assumption: under the world's null, each declared bar's marginal size is at most a_k

A1 is the statement, for the declared portfolio under the null:

    (A1, assumed, under the null)   P( sup over stopping times of t(x_d) > b_k(x_d, seed) ) <= a_k <= alpha_k.

**What the construction gives.** It reduces every trial to this one series; it does not prove the inequality.
- b_k is a function of x_d and the seed alone. x_d is fixed by the declaration (in p_k(w)) and the holdout; the
  strategy's output, its stopping time included, enters neither.
- A trial that follows its declaration and stops at tau is graded on the steps of A_d up to tau, where its weights,
  returns and risks are the declared ones. Its graded series is the first k(tau) values of x_d, and its t is one of
  the stopping times b_k takes the sup over.
- This is a property of the construction, not of the strategy: A_d is fixed before any row is read and no trial moves
  it.
- Before the fix, it held only by accident, when the active set was the trial's own: the floor was relative to the
  median risk of the trial's own steps up to tau. A declaration whose risk changes tenfold, a twin long-short then a
  single asset, made a stop before the change grade the tiny-risk stretch as active. That series is no prefix of x_d,
  and b_k never covered it. switch_tail on GARCH measured 1.10, 1.15 and 1.22 alpha at 0.045, 0.045/20 and 0.045/50;
  graded on A_d, 0.41, 0.32 and 0.28.

**When the inequality holds.** It holds when the bootstrap's null for x_d (signs flipped, blocks resampled) matches the
holdout's null for x_d: in particular, when a series of conditional mean zero is close enough to symmetric that a
sign flip does not move its sup-t quantile. It does not hold when the null is skewed so that the declared series
drifts upward between rare crashes. Neither condition is proven for any class of worlds; the size table measures
where A1 holds. On iid series the declared bar measures 1.007 [0.970, 1.044] alpha, and on GARCH 0.996
[0.959, 1.033] (`tools/redteam/boot_looks.py`). The bar of the old rule, one per look from each prefix the strategy
tried, measured 1.186 alpha on iid series.

**Where A1 is measured to hold: the size table** (SIZE_TABLE.md).
- Read with the correction of 10 November 2026 at the top of [SIZE_TABLE.md](SIZE_TABLE.md): a 'below' close to alpha
  is unsettled.
- **Scope.** The 20 complete null worlds: main, garch, t3, t4, t5, jumps, garch-jumps, garch-regime, main-regime,
  factor, factor-regime, factor-t6, factor-t6-regime, garch-normal, garch-t6, garch-t6-regime, garch-persistent,
  garch-99, garch-99-t8 and equal58. 22 strategies each (13 in equal58), at the levels 0.045, 0.045/2, 0.045/5,
  0.045/10 and 0.045/20.
- **Result.** 2,155 cells: 2,077 below alpha, 78 at the boundary (their 95% interval contains alpha), 0 above.
  - 56 of the 78 are `dev:equal>switch_tail` at 0.96 to 1.04 alpha, in 19 of the 20 worlds: a trial that leaves its
    declaration.
  - The other 22 are honest declarations and two `near:` trials at 0.96 to 0.98.
- **No level is settled.** A level is settled when every cell of every world is below. `SETTLED_LEVELS` in the code
  lists the seven levels 0.045/n (n = 1, 2, 5, 10, 20, 50, 100) provisionally; the size table has settled none of
  them. The deeper levels 0.045/50 and 0.045/100 are measured separately and are not in the published table.
- **Not yet measured.** Four 50-asset worlds (garch50, garch50-t6, factor50, factor50-t6) are still computing.

So, at the levels of the table: in these 20 worlds, for these strategies, no cell's size is measurably above alpha.
That is a measurement, not a theorem, and it is no statement about any other world.

**Where A1 fails: the skewed-crash worlds** (skew-jumps, skew-rare, garch-skew). These are null worlds with rare,
compensated crashes: a jump of -5 vol with probability 0.02 a step (skew-jumps, garch-skew), or of -12 vol with
probability 0.004 (skew-rare). Each is compensated by a drift that makes the conditional mean zero. Honest held
portfolios pass above alpha there. On 400,000 null paths per cell (`tools/redteam/hurdle_probe.py`, the rule's bar):

| World · strategy | 0.045 | 0.045/5 | 0.045/20 |
|--|--|--|--|
| skew-rare single | 1.12 [1.10, 1.13] | 1.47 [1.43, 1.51] | 1.92 [1.83, 2.01] |
| skew-rare sticky | 1.00 [0.98, 1.01] | 1.16 [1.12, 1.19] | 1.44 [1.36, 1.52] |
| skew-jumps single | 0.99 [0.98, 1.01] | 1.17 [1.13, 1.20] | 1.46 [1.38, 1.54] |
| skew-jumps sticky | 0.95 [0.94, 0.96] | 1.02 [0.98, 1.05] | 1.15 [1.08, 1.22] |
| garch-skew single | 1.05 [1.03, 1.06] | 1.31 [1.27, 1.34] | 1.73 [1.64, 1.81] |
| garch-skew sticky | 0.97 [0.96, 0.98] | 1.02 [0.99, 1.05] | 1.12 [1.06, 1.19] |

The size table's own partial cells for these worlds agree: skew-rare `single` at 0.045/20 is 1.86 [1.55, 2.18].
Read with the correction of 10 November 2026 at the top of [SIZE_TABLE.md](SIZE_TABLE.md): a 'below' close to alpha is
unsettled.

**The cause, measured.**
- Between crashes, the compensating drift gives the declared series a positive mean on every step. A holdout that
  happens to contain no crash looks like one with a true edge. A bar bootstrapped from the holdout's own returns
  cannot tell the two apart: the sign flip makes the null symmetric, and this null is not.
- The true 0.045/20 quantile of the sup-t is 3.63 in skew-rare `single` and 3.57 in skew-jumps `single`. The bar's
  median is 3.33 to 3.43 in every world.
- In skew-rare `single`, the 38% of paths with no step below -4 risk units give 55 to 64% of the false passes.
- Five bootstrap nulls were tested on the same paths (`tools/redteam/skew_probe.py`): the rule's sign flip, the
  sample mean subtracted, whole-block flips, and Mammen weights on x and on x minus its mean. None brings these cells
  under alpha.

**What follows.** The theorem's bound of 0.05 is not established for a holdout whose returns can carry a compensated
crash premium. The size guarantee does not cover such worlds today.

## The crash-premium hurdle: decided, not implemented, not proven

Decided on 10 November 2026: each trial is graded on its declared series less one delta >= 0, fixed at its opening.

    delta = max(delta_hat, delta_min)

- **delta_hat** is the net tail beyond ±4 risk units of a history of 10 T steps before the holdout: the assets'
  pre-holdout returns combined with the declared portfolio's holdout weights.
- **delta_min** is a floor that risk declares at init, default 0.

The history is risk's and is held by the data host. No strategy code runs on it.

**Measured on ten cells** (five worlds times `single` and `sticky`, at 0.045, 0.045/5 and 0.045/20), with the history
built by running the declared exposure rule over it. The decided form, the holdout's declared weights on the history's
returns, differs, and must be measured again:
- **Size.** Every cell is below alpha with the history's net tail as delta. The worst is 0.87 alpha (garch `sticky`
  at 0.045), and the highest upper bound is 0.89 (garch `single` at 0.045/20). In the skewed-crash worlds the
  largest is 0.79 (garch-skew `sticky` at 0.045/20).
- **Power.** On the cells measured for power (the garch and main worlds, Sharpe 1, 2 and 3) the cost is at most 1.1
  points of pass rate (garch `single`, Sharpe 2, 0.045: 45.5% to 44.4%). At Sharpe 3 and 0.045/20 on main `single`, it is 37.5%
  without the hurdle and 37.4% with it.

**What it does not give.**
- It is not implemented: the rule grades without it today.
- It is not proven: the theorem's A1 is not shown for a data-dependent hurdle.
- It needs the history to show the crashes. A crash rarer than one per history length is not detected, and delta_min
  is risk's floor for that.
- Before it is called a fix, the implementation must pass three tests:
  - a test that a hurdle can only lower passes (so the 20-world table stands as an upper bound);
  - a manipulation family, tame in the history and crash-exposed in the holdout;
  - the three skewed-crash worlds' table with the hurdle in force.

## The rest of A1's evidence

**Within the tolerance.** A trial that stays within 0.05 per step of its declaration but is not on it is graded at b_k
alone, on A_d. Its series differs from x_d by that bounded amount on the same steps, and the construction does not
cover it. Measured on GARCH, moving toward switch_tail or a single asset as far as the tolerance allows gives 0.88 to
0.93 alpha. In the size table's 20 worlds the `near:` cells are below or at the boundary.
Read with the correction of 10 November 2026 at the top of [SIZE_TABLE.md](SIZE_TABLE.md): a 'below' close to alpha is
unsettled.

**Deviation.** A deviating trial passes only if its t beats both b_k and its own bar, so its size is at most that of
either bar alone. That bounds nothing by itself: the own bar is the old rule's, which is over alpha under stopping. It
is measured on GARCH, declaring equal weights or inverse-vol and trading switch_tail, a single asset, lever_t_rev or the
twin: 0.76 to 0.91 alpha at 0.045 and 0.045/5. Every deviator scores below the same strategy declared honestly, so
deviating gains nothing, as measured. In the size table, `dev:equal>switch_tail` reaches 0.96 to 1.04: it is most of
the boundary cells.
Read with the correction of 10 November 2026 at the top of [SIZE_TABLE.md](SIZE_TABLE.md): a 'below' close to alpha is
unsettled.

**The seed.** seed = SHA256(the data host's signed opening statement of the trial || the holdout's secret).
- The secret is made by the data host at install and is in no answer and no backup before retirement.
- The retirement record publishes it, signed, so anyone can recompute every bar from the plaintext, the declaration
  and the opening.
- What makes it safe is the secret, not the hash. A researcher who knew the seed could choose, among declarations, the
  one whose bootstrap draws are kindest, or a deviator could stop where its own bar is lowest.
  - A known seed lowered a chosen stop's bar by 0.176 ± 0.005 in t; a derived one, by 0.014 ± 0.009, which is
    nothing (`tests/test_boot_seed.py`).
  - Every size result assumes the secret stays secret until the trial's weights are fixed.

## A2 to A6

**A2: nothing outcome-dependent reaches anyone who chooses trials, before the first pass.** Each channel is closed in
code and tested in `tests/test_rule_v3.py`; none is verified on a live host.
- Views show the execution state only.
- Every failure is one FAIL answer and one record.
- Slots are fixed (timeout + cleanup), releases come from the schedule, and promote answers fall on a fixed step.
- No FAIL verdict is published before retirement, and anchors are one line per event.
- The declared bar depends on the holdout's data, so it is outcome-dependent. It is in the opening record only, which
  no researcher reads, and a PASS shows it after the first pass. Its computation runs inside the slot, before "go",
  so it moves no release time.
- The non-interference test pins these together: worlds with identical actions give identical bytes and release times
  to every researcher.

**A3: to be verified live** (`deploy/ITEM7_CHECKLIST.md`): marks between jobs (#24), shared hardware state (#25), and
knocking a runner out (#26).

**A4:** the holdout has no public copy (THREAT_MODEL.md §5). **A5:** service mode only. **A6:** risk staff pass on
nothing, and the hosts and K_risk are uncompromised.

**Out of scope.** Holdouts under versions 1 and 2 keep their rule. Version 1 has its own finding, window_aim at 0.2990.
