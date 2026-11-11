# Size table: the declared-portfolio bar (rule version 3)

**Correction, 10 November 2026.** The size table's cells stop early under a sequential rule, and the 95% intervals
printed here do not account for that. Within 2% of alpha they cover the true value about 88 to 93% of the time (up to
94.5% within 5%), and a cell exactly at alpha is read 'below' up to 5.7% of the time. A cell at 1.05 alpha is read
'below' less than 0.2% of the time. Until the table is recomputed with intervals that are valid under early stopping,
read a 'below' close to alpha as unsettled. 34 of this table's cells (garch and main, at 0.045 and 0.045/5) were
computed on 5 November, before a later change to the rule's active set, and no job records were kept for them, so they
cannot be checked against the current code. They are being recomputed from scratch with the rest of the table.

Status, 10 November 2026. This table measures assumption A1 of rule version 3's proof
([RULE_V3_PROOF.md](RULE_V3_PROOF.md)): under the holdout's null, each declared-portfolio bar passes at most at its
level. The proof's bound of 0.05 holds only where A1 does. The rule's numpy-only code is published
(`tools/joint_bar/standalone/joint_rule.py`); lockrun's own source is not.

This table holds the 20 of 27 null worlds whose every cell is complete; in them, no cell is above alpha.
- **4 worlds are still computing:** garch50, garch50-t6, factor50 and factor50-t6.
- **The 3 skewed-crash worlds fail A1 and are not in this table:** skew-jumps, skew-rare and garch-skew. Honest held
  portfolios pass above alpha there: up to 1.92 alpha at 0.045/20 in skew-rare, strategy `single`, on 400,000 null
  paths. Their numbers and the cause are in the proof.
- **The fix is decided and not implemented:** a crash-premium hurdle from a history before the holdout. Until it is
  implemented and measured, the size guarantee does not cover those worlds.

## What a cell is

A cell is one null world, one strategy and one level a. Its number is the false-pass rate over a: the probability that
a trial under the world's null (no edge, conditional mean zero), stopped at the first prefix of its holdout whose
t-statistic passes, passes the declared-portfolio bar at level a; 1.00 is a size of exactly a. Then its 95% interval,
and its verdict from the interval alone: **below** (the interval entirely under a), **boundary** (it contains a),
**above** (entirely over a).

- Plain Monte Carlo. Level a runs on up to ceil(2000 / a) null paths (about 2,000 passes expected at size a), stopped
  early by a sequential test (0.95 a against 1.05 a, 1% errors each) only when the cell's interval at 2.58 standard
  errors agrees with the decision; otherwise to that budget.
- Levels: 0.045, 0.045/2, 0.045/5, 0.045/10, 0.045/20. The deeper levels are measured separately and are not here.
- Strategies: honest declarations held or switched by a declared rule (`sticky`, `single`, `fresh`, `twin`,
  `inverse_vol`, `momentum`, `eigen_low`, `equal`, `switch_tail`, `sign_switch`, `lever_t`, `block_period`, and their
  `_rev` and `_long` forms); `dev:A>B`, a trial that declares A and trades B beyond the declared tolerance (held to the
  stricter of the declared bar and its own); `near:A>B`, A moved toward B as far as the tolerance allows.
- A level is settled only when every cell of every world is below. **No level is settled:** every world has boundary
  cells: 56 of the 78 are `dev:equal>switch_tail` (0.96 to 1.04, in 19 of the 20 worlds), a trial that leaves its
  declaration; the other 22 are honest declarations and two `near:` trials at 0.96 to 0.98. **No cell of these 20
  worlds is above alpha.**

Source: lockrun's `tools/redteam/boot_size.py` (lockrun's source, not public), the grading of the active-set fix of
6 November and the sequential stop in force since 7 November (levels stopped under the earlier stop that this one would
not have stopped were dropped and run again); measured on the operator's machine and on cloud batch droplets
(6 to 9 November), the batch at commit 3b8f481; this file rendered at 29e03c7 from the merged results:
482,670 simulation jobs across all 27 worlds, 383,111,159 null paths for these 20 (each cell's largest level
budget, summed). Cells: 2,155, of which 2,077 below, 78 boundary,
0 above.

## Summary

| world | strategies | below | boundary | above | highest cell | null paths |
|--|--|--|--|--|--|--|
| main | 22 | 107 | 3 | 0 | dev:equal>switch_tail at 0.045: boundary 1.02 [0.97, 1.06] | 19,555,558 |
| garch | 22 | 105 | 5 | 0 | dev:equal>switch_tail at 0.045/20: boundary 0.99 [0.95, 1.04] | 19,555,558 |
| t3 | 22 | 107 | 3 | 0 | dev:equal>switch_tail at 0.045: boundary 0.98 [0.94, 1.02] | 19,555,558 |
| garch-jumps | 22 | 108 | 2 | 0 | fresh at 0.045: boundary 0.98 [0.94, 1.02] | 19,555,558 |
| jumps | 22 | 108 | 2 | 0 | dev:equal>switch_tail at 0.045: boundary 0.99 [0.95, 1.03] | 19,555,558 |
| garch-regime | 22 | 105 | 5 | 0 | dev:equal>switch_tail at 0.045: boundary 1.00 [0.96, 1.05] | 19,555,558 |
| factor-regime | 22 | 108 | 2 | 0 | dev:equal>switch_tail at 0.045/2: boundary 0.99 [0.94, 1.03] | 19,555,558 |
| main-regime | 22 | 107 | 3 | 0 | dev:equal>switch_tail at 0.045/2: boundary 0.99 [0.95, 1.04] | 19,555,558 |
| t4 | 22 | 108 | 2 | 0 | dev:equal>switch_tail at 0.045: boundary 0.99 [0.95, 1.03] | 19,555,558 |
| t5 | 22 | 108 | 2 | 0 | dev:equal>switch_tail at 0.045: boundary 1.04 [1.00, 1.08] | 19,555,558 |
| garch-normal | 22 | 104 | 6 | 0 | dev:equal>switch_tail at 0.045: boundary 1.00 [0.95, 1.04] | 19,555,558 |
| garch-t6 | 22 | 106 | 4 | 0 | dev:equal>switch_tail at 0.045: boundary 1.00 [0.95, 1.04] | 19,555,558 |
| garch-t6-regime | 22 | 104 | 6 | 0 | dev:equal>switch_tail at 0.045: boundary 1.01 [0.96, 1.05] | 19,555,558 |
| factor-t6 | 22 | 103 | 7 | 0 | dev:equal>switch_tail at 0.045: boundary 1.02 [0.97, 1.06] | 19,555,558 |
| factor-t6-regime | 22 | 104 | 6 | 0 | dev:equal>switch_tail at 0.045: boundary 0.99 [0.95, 1.04] | 19,555,558 |
| garch-persistent | 22 | 107 | 3 | 0 | dev:equal>switch_tail at 0.045: boundary 1.03 [0.98, 1.07] | 19,555,558 |
| garch-99 | 22 | 104 | 6 | 0 | dev:equal>switch_tail at 0.045/2: boundary 0.99 [0.95, 1.03] | 19,555,558 |
| garch-99-t8 | 22 | 106 | 4 | 0 | dev:equal>switch_tail at 0.045/2: boundary 0.98 [0.94, 1.02] | 19,555,558 |
| factor | 22 | 105 | 5 | 0 | dev:equal>switch_tail at 0.045: boundary 1.01 [0.97, 1.05] | 19,555,558 |
| equal58 | 13 | 63 | 2 | 0 | near:equal>switch_tail at 0.045: boundary 0.98 [0.94, 1.02] | 11,555,557 |

## Every cell

### main

| strategy | 0.045 | 0.045/2 | 0.045/5 | 0.045/10 | 0.045/20 |
|--|--|--|--|--|--|
| sticky | below 0.93 [0.89, 0.97] | below 0.92 [0.85, 0.98] | below 0.92 [0.88, 0.96] | below 0.89 [0.80, 0.98] | below 0.92 [0.88, 0.96] |
| single | below 0.91 [0.87, 0.95] | below 0.92 [0.85, 0.99] | below 0.90 [0.86, 0.94] | below 0.79 [0.67, 0.91] | below 0.90 [0.86, 0.94] |
| fresh | below 0.92 [0.87, 0.96] | below 0.94 [0.88, 1.00] | below 0.93 [0.88, 0.97] | below 0.89 [0.80, 0.98] | below 0.93 [0.89, 0.97] |
| twin | below 0.93 [0.89, 0.97] | below 0.93 [0.87, 0.98] | below 0.92 [0.86, 0.98] | below 0.93 [0.88, 0.98] | below 0.90 [0.86, 0.95] |
| inverse_vol | below 0.91 [0.87, 0.95] | below 0.90 [0.85, 0.96] | below 0.90 [0.83, 0.96] | below 0.91 [0.84, 0.98] | below 0.93 [0.88, 0.97] |
| momentum | below 0.91 [0.87, 0.95] | below 0.89 [0.82, 0.96] | below 0.93 [0.89, 0.97] | below 0.92 [0.84, 0.99] | below 0.90 [0.86, 0.94] |
| eigen_low | below 0.89 [0.85, 0.93] | below 0.87 [0.80, 0.94] | below 0.89 [0.85, 0.94] | below 0.91 [0.85, 0.98] | below 0.90 [0.86, 0.94] |
| equal | boundary 0.96 [0.92, 1.01] | below 0.95 [0.91, 0.99] | below 0.94 [0.89, 0.98] | below 0.88 [0.79, 0.97] | below 0.88 [0.84, 0.93] |
| switch_tail_rev | below 0.42 [0.38, 0.47] | below 0.41 [0.34, 0.47] | below 0.36 [0.26, 0.46] | below 0.35 [0.21, 0.48] | below 0.36 [0.33, 0.39] |
| dev:equal>single | below 0.88 [0.84, 0.93] | below 0.90 [0.83, 0.97] | below 0.82 [0.74, 0.91] | below 0.86 [0.77, 0.94] | below 0.83 [0.79, 0.87] |
| dev:equal>twin | below 0.90 [0.83, 0.97] | below 0.86 [0.79, 0.93] | below 0.77 [0.67, 0.88] | below 0.75 [0.63, 0.86] | below 0.86 [0.82, 0.91] |
| near:equal>single | below 0.92 [0.87, 0.97] | below 0.90 [0.84, 0.96] | below 0.88 [0.81, 0.96] | below 0.76 [0.64, 0.88] | below 0.88 [0.84, 0.92] |
| switch_tail | below 0.39 [0.35, 0.44] | below 0.38 [0.31, 0.44] | below 0.40 [0.30, 0.51] | below 0.33 [0.20, 0.47] | below 0.34 [0.32, 0.37] |
| sign_switch | below 0.95 [0.91, 0.99] | below 0.93 [0.88, 0.98] | below 0.90 [0.83, 0.97] | below 0.93 [0.88, 0.98] | below 0.95 [0.90, 0.99] |
| sign_switch_rev | below 0.55 [0.50, 0.60] | below 0.49 [0.42, 0.57] | below 0.52 [0.40, 0.64] | below 0.46 [0.35, 0.57] | below 0.47 [0.44, 0.50] |
| lever_t | below 0.74 [0.68, 0.80] | below 0.79 [0.70, 0.88] | below 0.81 [0.70, 0.91] | below 0.84 [0.73, 0.95] | below 0.89 [0.85, 0.93] |
| lever_t_rev | below 0.52 [0.47, 0.57] | below 0.38 [0.31, 0.44] | below 0.25 [0.17, 0.33] | below 0.19 [0.09, 0.30] | below 0.10 [0.09, 0.12] |
| block_period | below 0.41 [0.36, 0.45] | below 0.35 [0.29, 0.41] | below 0.29 [0.20, 0.38] | below 0.29 [0.17, 0.42] | below 0.37 [0.34, 0.40] |
| block_period_long | below 0.48 [0.43, 0.53] | below 0.50 [0.43, 0.57] | below 0.51 [0.39, 0.62] | below 0.51 [0.39, 0.62] | below 0.45 [0.42, 0.48] |
| dev:equal>switch_tail | boundary 1.02 [0.97, 1.06] | boundary 1.01 [0.96, 1.05] | below 0.95 [0.90, 0.99] | below 0.92 [0.87, 0.97] | below 0.92 [0.88, 0.96] |
| dev:inverse_vol>lever_t_rev | below 0.84 [0.77, 0.90] | below 0.73 [0.65, 0.82] | below 0.79 [0.69, 0.89] | below 0.83 [0.73, 0.92] | below 0.74 [0.70, 0.78] |
| near:equal>switch_tail | below 0.94 [0.90, 0.99] | below 0.93 [0.87, 0.99] | below 0.88 [0.79, 0.97] | below 0.81 [0.71, 0.91] | below 0.91 [0.87, 0.95] |

### garch

| strategy | 0.045 | 0.045/2 | 0.045/5 | 0.045/10 | 0.045/20 |
|--|--|--|--|--|--|
| sticky | below 0.91 [0.87, 0.95] | below 0.88 [0.84, 0.92] | below 0.90 [0.86, 0.94] | below 0.90 [0.86, 0.95] | below 0.89 [0.85, 0.93] |
| single | below 0.93 [0.89, 0.98] | below 0.92 [0.88, 0.96] | below 0.91 [0.87, 0.95] | below 0.88 [0.84, 0.92] | below 0.85 [0.81, 0.89] |
| fresh | below 0.90 [0.86, 0.95] | below 0.93 [0.88, 0.97] | below 0.93 [0.88, 0.97] | below 0.90 [0.86, 0.94] | below 0.92 [0.88, 0.96] |
| twin | below 0.89 [0.85, 0.93] | below 0.91 [0.87, 0.95] | below 0.92 [0.88, 0.96] | below 0.91 [0.87, 0.95] | below 0.87 [0.83, 0.91] |
| inverse_vol | below 0.88 [0.84, 0.92] | below 0.87 [0.83, 0.91] | below 0.89 [0.85, 0.93] | below 0.90 [0.86, 0.94] | below 0.88 [0.84, 0.92] |
| momentum | below 0.94 [0.89, 0.98] | below 0.95 [0.90, 0.99] | below 0.89 [0.85, 0.93] | below 0.90 [0.85, 0.94] | below 0.89 [0.85, 0.93] |
| eigen_low | below 0.89 [0.85, 0.94] | below 0.89 [0.85, 0.93] | below 0.87 [0.83, 0.91] | below 0.87 [0.83, 0.91] | below 0.89 [0.85, 0.93] |
| equal | below 0.90 [0.86, 0.94] | below 0.89 [0.85, 0.93] | below 0.91 [0.87, 0.95] | below 0.91 [0.87, 0.95] | below 0.89 [0.85, 0.93] |
| switch_tail_rev | below 0.40 [0.37, 0.42] | below 0.37 [0.35, 0.40] | below 0.35 [0.32, 0.37] | below 0.34 [0.32, 0.37] | below 0.31 [0.29, 0.33] |
| dev:equal>single | below 0.84 [0.81, 0.88] | below 0.82 [0.78, 0.86] | below 0.80 [0.76, 0.84] | below 0.78 [0.74, 0.82] | below 0.77 [0.73, 0.81] |
| dev:equal>twin | below 0.87 [0.83, 0.91] | below 0.90 [0.86, 0.94] | below 0.88 [0.84, 0.92] | below 0.85 [0.81, 0.89] | below 0.87 [0.83, 0.91] |
| near:equal>single | below 0.93 [0.89, 0.97] | below 0.94 [0.90, 0.98] | below 0.92 [0.88, 0.96] | below 0.92 [0.88, 0.96] | below 0.91 [0.87, 0.95] |
| switch_tail | below 0.40 [0.35, 0.44] | below 0.36 [0.30, 0.42] | below 0.36 [0.26, 0.46] | below 0.36 [0.22, 0.50] | below 0.32 [0.30, 0.35] |
| sign_switch | below 0.93 [0.88, 0.98] | below 0.89 [0.83, 0.96] | below 0.86 [0.78, 0.95] | below 0.87 [0.77, 0.96] | below 0.90 [0.86, 0.94] |
| sign_switch_rev | below 0.50 [0.45, 0.55] | below 0.49 [0.42, 0.56] | below 0.46 [0.35, 0.57] | below 0.37 [0.27, 0.47] | below 0.42 [0.39, 0.45] |
| lever_t | below 0.68 [0.62, 0.74] | below 0.73 [0.64, 0.82] | below 0.78 [0.68, 0.88] | below 0.77 [0.65, 0.89] | below 0.83 [0.79, 0.87] |
| lever_t_rev | below 0.59 [0.54, 0.65] | below 0.42 [0.35, 0.48] | below 0.33 [0.23, 0.42] | below 0.21 [0.10, 0.31] | below 0.13 [0.12, 0.15] |
| block_period | below 0.43 [0.39, 0.48] | below 0.40 [0.33, 0.47] | below 0.35 [0.26, 0.45] | below 0.36 [0.22, 0.50] | below 0.32 [0.30, 0.35] |
| block_period_long | below 0.46 [0.41, 0.51] | below 0.38 [0.32, 0.44] | below 0.36 [0.26, 0.46] | below 0.33 [0.20, 0.47] | below 0.39 [0.36, 0.42] |
| dev:equal>switch_tail | boundary 0.99 [0.95, 1.03] | boundary 0.97 [0.93, 1.01] | boundary 0.98 [0.94, 1.02] | boundary 0.97 [0.92, 1.01] | boundary 0.99 [0.95, 1.04] |
| dev:inverse_vol>lever_t_rev | below 0.90 [0.83, 0.97] | below 0.84 [0.75, 0.94] | below 0.73 [0.63, 0.83] | below 0.68 [0.55, 0.82] | below 0.73 [0.70, 0.77] |
| near:equal>switch_tail | below 0.93 [0.88, 0.98] | below 0.93 [0.86, 1.00] | below 0.89 [0.80, 0.98] | below 0.84 [0.73, 0.95] | below 0.90 [0.86, 0.95] |

### t3

| strategy | 0.045 | 0.045/2 | 0.045/5 | 0.045/10 | 0.045/20 |
|--|--|--|--|--|--|
| sticky | below 0.91 [0.87, 0.95] | below 0.89 [0.85, 0.93] | below 0.87 [0.83, 0.91] | below 0.90 [0.85, 0.94] | below 0.86 [0.82, 0.90] |
| single | below 0.86 [0.82, 0.90] | below 0.86 [0.82, 0.90] | below 0.87 [0.83, 0.91] | below 0.87 [0.83, 0.91] | below 0.87 [0.83, 0.91] |
| fresh | below 0.92 [0.88, 0.96] | below 0.89 [0.85, 0.93] | below 0.89 [0.85, 0.93] | below 0.89 [0.85, 0.93] | below 0.86 [0.82, 0.90] |
| twin | below 0.94 [0.90, 0.98] | below 0.93 [0.88, 0.97] | below 0.93 [0.88, 0.97] | below 0.92 [0.88, 0.96] | below 0.93 [0.89, 0.97] |
| inverse_vol | below 0.87 [0.83, 0.91] | below 0.91 [0.87, 0.95] | below 0.87 [0.83, 0.91] | below 0.90 [0.85, 0.94] | below 0.89 [0.85, 0.93] |
| momentum | below 0.93 [0.88, 0.98] | below 0.84 [0.75, 0.93] | below 0.82 [0.72, 0.93] | below 0.82 [0.73, 0.92] | below 0.89 [0.85, 0.93] |
| eigen_low | below 0.91 [0.86, 0.96] | below 0.87 [0.80, 0.93] | below 0.87 [0.78, 0.96] | below 0.84 [0.74, 0.93] | below 0.86 [0.82, 0.90] |
| equal | below 0.90 [0.86, 0.95] | below 0.90 [0.83, 0.97] | below 0.90 [0.85, 0.96] | below 0.89 [0.82, 0.97] | below 0.81 [0.77, 0.85] |
| switch_tail_rev | below 0.38 [0.34, 0.43] | below 0.34 [0.28, 0.40] | below 0.33 [0.23, 0.42] | below 0.24 [0.12, 0.35] | below 0.26 [0.24, 0.29] |
| dev:equal>single | below 0.79 [0.73, 0.86] | below 0.77 [0.68, 0.86] | below 0.63 [0.50, 0.76] | below 0.67 [0.54, 0.81] | below 0.67 [0.63, 0.70] |
| dev:equal>twin | below 0.90 [0.86, 0.95] | below 0.93 [0.88, 0.97] | below 0.91 [0.84, 0.98] | below 0.88 [0.79, 0.97] | below 0.94 [0.90, 0.98] |
| near:equal>single | below 0.93 [0.89, 0.97] | below 0.95 [0.90, 0.99] | below 0.91 [0.86, 0.97] | below 0.90 [0.83, 0.96] | below 0.86 [0.82, 0.90] |
| switch_tail | below 0.37 [0.32, 0.41] | below 0.28 [0.23, 0.34] | below 0.31 [0.22, 0.40] | below 0.25 [0.13, 0.37] | below 0.27 [0.24, 0.29] |
| sign_switch | below 0.91 [0.87, 0.95] | below 0.92 [0.87, 0.97] | below 0.93 [0.88, 0.98] | below 0.91 [0.84, 0.97] | below 0.88 [0.84, 0.92] |
| sign_switch_rev | below 0.46 [0.41, 0.51] | below 0.43 [0.36, 0.50] | below 0.41 [0.31, 0.51] | below 0.33 [0.20, 0.47] | below 0.37 [0.34, 0.40] |
| lever_t | below 0.74 [0.67, 0.80] | below 0.77 [0.68, 0.86] | below 0.77 [0.67, 0.88] | below 0.68 [0.55, 0.82] | below 0.75 [0.72, 0.79] |
| lever_t_rev | below 0.58 [0.53, 0.64] | below 0.44 [0.38, 0.51] | below 0.32 [0.23, 0.41] | below 0.28 [0.16, 0.40] | below 0.14 [0.12, 0.16] |
| block_period | below 0.40 [0.35, 0.44] | below 0.38 [0.31, 0.44] | below 0.33 [0.24, 0.43] | below 0.26 [0.15, 0.38] | below 0.29 [0.26, 0.31] |
| block_period_long | below 0.47 [0.42, 0.52] | below 0.48 [0.40, 0.55] | below 0.51 [0.39, 0.62] | below 0.32 [0.23, 0.41] | below 0.33 [0.30, 0.35] |
| dev:equal>switch_tail | boundary 0.98 [0.94, 1.02] | below 0.89 [0.82, 0.96] | boundary 0.97 [0.93, 1.01] | boundary 0.98 [0.94, 1.02] | below 0.95 [0.90, 0.99] |
| dev:inverse_vol>lever_t_rev | below 0.87 [0.80, 0.93] | below 0.84 [0.78, 0.91] | below 0.72 [0.62, 0.82] | below 0.67 [0.54, 0.81] | below 0.68 [0.64, 0.72] |
| near:equal>switch_tail | below 0.93 [0.88, 0.98] | below 0.93 [0.89, 0.98] | below 0.91 [0.84, 0.97] | below 0.88 [0.79, 0.97] | below 0.85 [0.81, 0.89] |

### garch-jumps

| strategy | 0.045 | 0.045/2 | 0.045/5 | 0.045/10 | 0.045/20 |
|--|--|--|--|--|--|
| sticky | below 0.87 [0.81, 0.94] | below 0.86 [0.77, 0.96] | below 0.87 [0.79, 0.94] | below 0.82 [0.71, 0.92] | below 0.81 [0.77, 0.85] |
| single | below 0.91 [0.86, 0.96] | below 0.89 [0.83, 0.94] | below 0.86 [0.79, 0.94] | below 0.80 [0.69, 0.90] | below 0.80 [0.76, 0.84] |
| fresh | boundary 0.98 [0.94, 1.02] | below 0.94 [0.89, 0.98] | below 0.92 [0.86, 0.98] | below 0.88 [0.80, 0.97] | below 0.88 [0.84, 0.93] |
| twin | below 0.95 [0.90, 1.00] | below 0.94 [0.89, 0.99] | below 0.92 [0.85, 0.99] | below 0.92 [0.86, 0.99] | below 0.90 [0.86, 0.94] |
| inverse_vol | below 0.90 [0.83, 0.97] | below 0.87 [0.80, 0.94] | below 0.86 [0.78, 0.95] | below 0.81 [0.71, 0.92] | below 0.85 [0.81, 0.89] |
| momentum | below 0.91 [0.84, 0.98] | below 0.92 [0.85, 0.98] | below 0.85 [0.77, 0.94] | below 0.78 [0.66, 0.90] | below 0.80 [0.76, 0.84] |
| eigen_low | below 0.91 [0.85, 0.98] | below 0.90 [0.84, 0.97] | below 0.88 [0.80, 0.96] | below 0.90 [0.82, 0.99] | below 0.86 [0.82, 0.90] |
| equal | below 0.86 [0.79, 0.93] | below 0.85 [0.78, 0.92] | below 0.89 [0.80, 0.98] | below 0.88 [0.79, 0.96] | below 0.85 [0.81, 0.89] |
| switch_tail_rev | below 0.40 [0.36, 0.45] | below 0.38 [0.32, 0.45] | below 0.40 [0.30, 0.51] | below 0.36 [0.26, 0.46] | below 0.29 [0.27, 0.31] |
| dev:equal>single | below 0.76 [0.70, 0.83] | below 0.76 [0.67, 0.85] | below 0.70 [0.61, 0.80] | below 0.59 [0.46, 0.72] | below 0.65 [0.61, 0.68] |
| dev:equal>twin | below 0.91 [0.84, 0.98] | below 0.90 [0.85, 0.95] | below 0.91 [0.85, 0.98] | below 0.87 [0.78, 0.96] | below 0.91 [0.86, 0.95] |
| near:equal>single | below 0.90 [0.85, 0.95] | below 0.89 [0.83, 0.94] | below 0.92 [0.87, 0.98] | below 0.91 [0.85, 0.97] | below 0.88 [0.84, 0.92] |
| switch_tail | below 0.39 [0.34, 0.43] | below 0.34 [0.28, 0.40] | below 0.28 [0.19, 0.36] | below 0.32 [0.19, 0.45] | below 0.29 [0.27, 0.31] |
| sign_switch | below 0.89 [0.82, 0.96] | below 0.87 [0.80, 0.94] | below 0.86 [0.77, 0.95] | below 0.84 [0.75, 0.93] | below 0.90 [0.86, 0.94] |
| sign_switch_rev | below 0.49 [0.44, 0.54] | below 0.50 [0.43, 0.58] | below 0.47 [0.36, 0.58] | below 0.41 [0.31, 0.51] | below 0.38 [0.35, 0.40] |
| lever_t | below 0.62 [0.57, 0.68] | below 0.71 [0.62, 0.79] | below 0.71 [0.61, 0.81] | below 0.65 [0.52, 0.78] | below 0.73 [0.69, 0.77] |
| lever_t_rev | below 0.56 [0.50, 0.61] | below 0.41 [0.34, 0.47] | below 0.30 [0.21, 0.39] | below 0.21 [0.10, 0.31] | below 0.18 [0.16, 0.19] |
| block_period | below 0.40 [0.35, 0.44] | below 0.38 [0.32, 0.45] | below 0.33 [0.24, 0.43] | below 0.33 [0.20, 0.47] | below 0.28 [0.26, 0.30] |
| block_period_long | below 0.46 [0.41, 0.51] | below 0.43 [0.37, 0.50] | below 0.38 [0.28, 0.47] | below 0.31 [0.18, 0.43] | below 0.37 [0.34, 0.39] |
| dev:equal>switch_tail | boundary 0.96 [0.92, 1.00] | below 0.92 [0.86, 0.98] | below 0.83 [0.72, 0.93] | below 0.83 [0.72, 0.93] | below 0.90 [0.86, 0.94] |
| dev:inverse_vol>lever_t_rev | below 0.80 [0.74, 0.87] | below 0.78 [0.69, 0.87] | below 0.72 [0.62, 0.82] | below 0.69 [0.58, 0.81] | below 0.70 [0.66, 0.74] |
| near:equal>switch_tail | below 0.90 [0.83, 0.97] | below 0.89 [0.83, 0.96] | below 0.91 [0.84, 0.98] | below 0.93 [0.86, 1.00] | below 0.86 [0.82, 0.90] |

### jumps

| strategy | 0.045 | 0.045/2 | 0.045/5 | 0.045/10 | 0.045/20 |
|--|--|--|--|--|--|
| sticky | below 0.93 [0.88, 0.98] | below 0.89 [0.83, 0.96] | below 0.91 [0.84, 0.99] | below 0.90 [0.82, 0.98] | below 0.83 [0.79, 0.87] |
| single | below 0.95 [0.91, 0.99] | below 0.90 [0.84, 0.96] | below 0.82 [0.73, 0.90] | below 0.76 [0.64, 0.88] | below 0.85 [0.81, 0.89] |
| fresh | below 0.93 [0.88, 0.98] | below 0.90 [0.83, 0.97] | below 0.92 [0.86, 0.98] | below 0.90 [0.83, 0.97] | below 0.89 [0.85, 0.93] |
| twin | below 0.87 [0.81, 0.94] | below 0.82 [0.72, 0.91] | below 0.82 [0.72, 0.93] | below 0.90 [0.82, 0.99] | below 0.91 [0.87, 0.95] |
| inverse_vol | below 0.94 [0.89, 0.99] | below 0.93 [0.86, 0.99] | below 0.90 [0.83, 0.97] | below 0.89 [0.80, 0.98] | below 0.87 [0.83, 0.91] |
| momentum | below 0.86 [0.79, 0.93] | below 0.84 [0.75, 0.94] | below 0.88 [0.80, 0.97] | below 0.90 [0.82, 0.99] | below 0.84 [0.80, 0.89] |
| eigen_low | below 0.92 [0.85, 0.99] | below 0.89 [0.82, 0.96] | below 0.91 [0.83, 0.99] | below 0.92 [0.85, 1.00] | below 0.88 [0.84, 0.92] |
| equal | below 0.88 [0.81, 0.95] | below 0.82 [0.73, 0.92] | below 0.83 [0.72, 0.93] | below 0.85 [0.76, 0.95] | below 0.83 [0.79, 0.87] |
| switch_tail_rev | below 0.40 [0.35, 0.44] | below 0.37 [0.31, 0.43] | below 0.32 [0.23, 0.41] | below 0.31 [0.18, 0.43] | below 0.27 [0.24, 0.29] |
| dev:equal>single | below 0.85 [0.79, 0.92] | below 0.76 [0.67, 0.85] | below 0.73 [0.63, 0.83] | below 0.72 [0.60, 0.83] | below 0.68 [0.64, 0.72] |
| dev:equal>twin | below 0.83 [0.77, 0.90] | below 0.85 [0.76, 0.94] | below 0.84 [0.73, 0.95] | below 0.82 [0.72, 0.93] | below 0.94 [0.89, 0.98] |
| near:equal>single | below 0.94 [0.89, 0.99] | below 0.91 [0.84, 0.98] | below 0.88 [0.80, 0.95] | below 0.83 [0.74, 0.93] | below 0.85 [0.81, 0.89] |
| switch_tail | below 0.40 [0.35, 0.44] | below 0.36 [0.30, 0.42] | below 0.33 [0.23, 0.42] | below 0.33 [0.20, 0.47] | below 0.28 [0.26, 0.31] |
| sign_switch | below 0.92 [0.87, 0.97] | below 0.92 [0.87, 0.97] | below 0.94 [0.89, 0.98] | below 0.92 [0.87, 0.98] | below 0.88 [0.84, 0.92] |
| sign_switch_rev | below 0.47 [0.42, 0.52] | below 0.43 [0.37, 0.50] | below 0.40 [0.30, 0.51] | below 0.43 [0.32, 0.54] | below 0.37 [0.34, 0.39] |
| lever_t | below 0.69 [0.63, 0.75] | below 0.74 [0.65, 0.83] | below 0.76 [0.66, 0.86] | below 0.64 [0.51, 0.77] | below 0.72 [0.69, 0.76] |
| lever_t_rev | below 0.50 [0.45, 0.55] | below 0.39 [0.33, 0.46] | below 0.28 [0.19, 0.36] | below 0.19 [0.09, 0.30] | below 0.15 [0.13, 0.17] |
| block_period | below 0.38 [0.33, 0.42] | below 0.36 [0.30, 0.42] | below 0.28 [0.20, 0.37] | below 0.33 [0.20, 0.47] | below 0.29 [0.27, 0.32] |
| block_period_long | below 0.49 [0.44, 0.55] | below 0.48 [0.41, 0.55] | below 0.44 [0.34, 0.55] | below 0.40 [0.30, 0.51] | below 0.36 [0.34, 0.39] |
| dev:equal>switch_tail | boundary 0.99 [0.95, 1.03] | boundary 0.98 [0.94, 1.02] | below 0.91 [0.84, 0.99] | below 0.84 [0.73, 0.94] | below 0.92 [0.88, 0.96] |
| dev:inverse_vol>lever_t_rev | below 0.82 [0.76, 0.89] | below 0.75 [0.66, 0.84] | below 0.76 [0.66, 0.86] | below 0.65 [0.52, 0.78] | below 0.72 [0.68, 0.76] |
| near:equal>switch_tail | below 0.92 [0.85, 0.99] | below 0.93 [0.86, 0.99] | below 0.86 [0.79, 0.94] | below 0.82 [0.72, 0.92] | below 0.81 [0.77, 0.85] |

### garch-regime

| strategy | 0.045 | 0.045/2 | 0.045/5 | 0.045/10 | 0.045/20 |
|--|--|--|--|--|--|
| sticky | below 0.90 [0.83, 0.96] | below 0.86 [0.77, 0.96] | below 0.82 [0.72, 0.93] | below 0.79 [0.67, 0.91] | below 0.83 [0.79, 0.87] |
| single | below 0.93 [0.86, 1.00] | below 0.92 [0.85, 0.99] | below 0.92 [0.84, 0.99] | below 0.91 [0.83, 0.99] | below 0.86 [0.82, 0.90] |
| twin | below 0.93 [0.86, 1.00] | below 0.92 [0.85, 0.99] | below 0.91 [0.83, 0.99] | below 0.78 [0.68, 0.88] | below 0.90 [0.86, 0.94] |
| inverse_vol | below 0.89 [0.83, 0.96] | below 0.91 [0.84, 0.98] | below 0.85 [0.76, 0.93] | below 0.83 [0.72, 0.93] | below 0.88 [0.84, 0.92] |
| momentum | below 0.96 [0.92, 1.00] | below 0.94 [0.89, 0.98] | below 0.91 [0.85, 0.97] | below 0.92 [0.87, 0.98] | below 0.91 [0.87, 0.95] |
| eigen_low | below 0.85 [0.79, 0.92] | below 0.79 [0.70, 0.89] | below 0.77 [0.67, 0.87] | below 0.80 [0.70, 0.90] | below 0.84 [0.80, 0.89] |
| equal | below 0.91 [0.84, 0.97] | below 0.91 [0.84, 0.98] | below 0.88 [0.79, 0.97] | below 0.84 [0.75, 0.94] | below 0.87 [0.82, 0.91] |
| switch_tail_rev | below 0.41 [0.37, 0.46] | below 0.35 [0.29, 0.41] | below 0.29 [0.20, 0.38] | below 0.18 [0.08, 0.28] | below 0.30 [0.28, 0.32] |
| dev:equal>single | below 0.83 [0.77, 0.90] | below 0.82 [0.73, 0.92] | below 0.79 [0.69, 0.89] | below 0.77 [0.65, 0.89] | below 0.77 [0.73, 0.81] |
| dev:equal>twin | below 0.90 [0.83, 0.97] | below 0.87 [0.80, 0.94] | below 0.89 [0.80, 0.98] | below 0.88 [0.80, 0.96] | below 0.93 [0.88, 0.97] |
| near:equal>single | below 0.95 [0.90, 0.99] | below 0.95 [0.91, 0.99] | below 0.88 [0.79, 0.97] | below 0.93 [0.88, 0.98] | below 0.90 [0.86, 0.94] |
| fresh | below 0.84 [0.77, 0.90] | below 0.93 [0.86, 1.00] | below 0.91 [0.83, 0.99] | below 0.86 [0.77, 0.96] | below 0.86 [0.82, 0.90] |
| switch_tail | below 0.43 [0.39, 0.48] | below 0.42 [0.36, 0.49] | below 0.42 [0.31, 0.52] | below 0.33 [0.24, 0.43] | below 0.32 [0.29, 0.34] |
| sign_switch | below 0.92 [0.87, 0.97] | below 0.93 [0.88, 0.98] | below 0.93 [0.88, 0.98] | below 0.91 [0.85, 0.97] | below 0.91 [0.87, 0.95] |
| sign_switch_rev | below 0.51 [0.46, 0.56] | below 0.49 [0.42, 0.57] | below 0.40 [0.29, 0.50] | below 0.41 [0.31, 0.51] | below 0.43 [0.40, 0.46] |
| lever_t | below 0.73 [0.67, 0.80] | below 0.79 [0.70, 0.89] | below 0.89 [0.80, 0.98] | below 0.89 [0.80, 0.98] | below 0.84 [0.80, 0.88] |
| lever_t_rev | below 0.59 [0.53, 0.64] | below 0.41 [0.34, 0.47] | below 0.30 [0.21, 0.39] | below 0.18 [0.08, 0.28] | below 0.13 [0.12, 0.15] |
| block_period | below 0.40 [0.36, 0.45] | below 0.33 [0.27, 0.39] | below 0.26 [0.17, 0.34] | below 0.31 [0.18, 0.43] | below 0.32 [0.30, 0.35] |
| block_period_long | below 0.50 [0.45, 0.56] | below 0.48 [0.41, 0.55] | below 0.47 [0.35, 0.58] | below 0.35 [0.26, 0.45] | below 0.40 [0.37, 0.43] |
| dev:equal>switch_tail | boundary 1.00 [0.96, 1.05] | boundary 0.97 [0.93, 1.01] | boundary 0.97 [0.92, 1.01] | boundary 0.97 [0.93, 1.01] | boundary 0.96 [0.92, 1.01] |
| dev:inverse_vol>lever_t_rev | below 0.83 [0.76, 0.89] | below 0.81 [0.72, 0.90] | below 0.67 [0.54, 0.81] | below 0.65 [0.51, 0.78] | below 0.72 [0.69, 0.76] |
| near:equal>switch_tail | below 0.93 [0.89, 0.97] | below 0.87 [0.77, 0.96] | below 0.86 [0.77, 0.94] | below 0.91 [0.85, 0.97] | below 0.88 [0.84, 0.92] |

### factor-regime

| strategy | 0.045 | 0.045/2 | 0.045/5 | 0.045/10 | 0.045/20 |
|--|--|--|--|--|--|
| sticky | below 0.93 [0.86, 1.00] | below 0.93 [0.86, 1.00] | below 0.88 [0.80, 0.95] | below 0.90 [0.82, 0.98] | below 0.82 [0.78, 0.86] |
| single | below 0.86 [0.79, 0.92] | below 0.79 [0.70, 0.88] | below 0.80 [0.70, 0.90] | below 0.86 [0.77, 0.96] | below 0.90 [0.85, 0.94] |
| fresh | below 0.91 [0.84, 0.98] | below 0.90 [0.83, 0.97] | below 0.93 [0.89, 0.98] | below 0.91 [0.84, 0.97] | below 0.92 [0.88, 0.97] |
| twin | below 0.91 [0.84, 0.98] | below 0.87 [0.77, 0.96] | below 0.95 [0.91, 0.99] | below 0.93 [0.89, 0.98] | below 0.92 [0.88, 0.96] |
| inverse_vol | below 0.87 [0.80, 0.94] | below 0.86 [0.77, 0.96] | below 0.80 [0.69, 0.90] | below 0.69 [0.58, 0.81] | below 0.87 [0.83, 0.91] |
| eigen_low | below 0.81 [0.75, 0.88] | below 0.79 [0.70, 0.88] | below 0.83 [0.73, 0.94] | below 0.88 [0.80, 0.96] | below 0.89 [0.85, 0.93] |
| equal | below 0.88 [0.81, 0.94] | below 0.92 [0.85, 0.99] | below 0.86 [0.77, 0.95] | below 0.91 [0.82, 0.99] | below 0.86 [0.82, 0.91] |
| switch_tail_rev | below 0.40 [0.36, 0.45] | below 0.34 [0.28, 0.40] | below 0.33 [0.23, 0.42] | below 0.31 [0.18, 0.43] | below 0.31 [0.29, 0.33] |
| dev:equal>single | below 0.88 [0.81, 0.95] | below 0.80 [0.71, 0.89] | below 0.76 [0.66, 0.86] | below 0.74 [0.62, 0.85] | below 0.77 [0.73, 0.81] |
| dev:equal>twin | below 0.92 [0.85, 0.98] | below 0.90 [0.85, 0.96] | below 0.91 [0.84, 0.98] | below 0.84 [0.75, 0.94] | below 0.88 [0.84, 0.92] |
| near:equal>single | below 0.87 [0.81, 0.94] | below 0.81 [0.72, 0.90] | below 0.84 [0.73, 0.94] | below 0.80 [0.70, 0.91] | below 0.88 [0.84, 0.92] |
| momentum | below 0.92 [0.87, 0.97] | below 0.88 [0.82, 0.95] | below 0.93 [0.87, 0.98] | below 0.91 [0.86, 0.97] | below 0.89 [0.85, 0.93] |
| switch_tail | below 0.41 [0.36, 0.46] | below 0.36 [0.30, 0.43] | below 0.31 [0.22, 0.40] | below 0.35 [0.26, 0.45] | below 0.30 [0.27, 0.32] |
| sign_switch | below 0.92 [0.85, 0.99] | below 0.93 [0.87, 0.98] | below 0.87 [0.78, 0.96] | below 0.90 [0.82, 0.98] | below 0.90 [0.86, 0.94] |
| sign_switch_rev | below 0.49 [0.44, 0.54] | below 0.45 [0.38, 0.52] | below 0.43 [0.32, 0.54] | below 0.45 [0.34, 0.56] | below 0.44 [0.41, 0.47] |
| lever_t | below 0.70 [0.64, 0.76] | below 0.74 [0.66, 0.83] | below 0.87 [0.78, 0.95] | below 0.86 [0.77, 0.96] | below 0.84 [0.80, 0.88] |
| lever_t_rev | below 0.56 [0.51, 0.61] | below 0.38 [0.31, 0.44] | below 0.27 [0.19, 0.36] | below 0.17 [0.07, 0.26] | below 0.13 [0.12, 0.15] |
| block_period | below 0.42 [0.37, 0.46] | below 0.39 [0.33, 0.46] | below 0.33 [0.23, 0.42] | below 0.29 [0.17, 0.42] | below 0.31 [0.29, 0.34] |
| block_period_long | below 0.50 [0.45, 0.55] | below 0.47 [0.40, 0.54] | below 0.49 [0.37, 0.60] | below 0.50 [0.38, 0.62] | below 0.41 [0.38, 0.43] |
| dev:equal>switch_tail | boundary 0.98 [0.94, 1.02] | boundary 0.99 [0.94, 1.03] | below 0.95 [0.91, 0.99] | below 0.92 [0.87, 0.98] | below 0.96 [0.91, 1.00] |
| dev:inverse_vol>lever_t_rev | below 0.86 [0.79, 0.93] | below 0.85 [0.76, 0.95] | below 0.78 [0.68, 0.88] | below 0.82 [0.72, 0.92] | below 0.78 [0.74, 0.82] |
| near:equal>switch_tail | below 0.90 [0.83, 0.97] | below 0.90 [0.83, 0.97] | below 0.83 [0.72, 0.93] | below 0.80 [0.69, 0.90] | below 0.86 [0.82, 0.90] |

### main-regime

| strategy | 0.045 | 0.045/2 | 0.045/5 | 0.045/10 | 0.045/20 |
|--|--|--|--|--|--|
| sticky | below 0.92 [0.85, 0.99] | below 0.91 [0.84, 0.98] | below 0.90 [0.83, 0.98] | below 0.87 [0.77, 0.97] | below 0.89 [0.85, 0.93] |
| single | below 0.94 [0.90, 0.98] | below 0.92 [0.86, 0.98] | below 0.93 [0.89, 0.98] | below 0.95 [0.91, 0.99] | below 0.92 [0.87, 0.96] |
| fresh | below 0.88 [0.81, 0.95] | below 0.90 [0.83, 0.97] | below 0.85 [0.77, 0.94] | below 0.87 [0.78, 0.96] | below 0.88 [0.84, 0.92] |
| twin | below 0.95 [0.91, 1.00] | below 0.92 [0.87, 0.97] | below 0.90 [0.83, 0.97] | below 0.89 [0.81, 0.96] | below 0.93 [0.89, 0.97] |
| inverse_vol | below 0.90 [0.83, 0.97] | below 0.87 [0.80, 0.94] | below 0.89 [0.80, 0.98] | below 0.84 [0.74, 0.93] | below 0.88 [0.84, 0.93] |
| momentum | below 0.90 [0.86, 0.95] | below 0.89 [0.82, 0.96] | below 0.92 [0.86, 0.97] | below 0.89 [0.81, 0.97] | below 0.88 [0.83, 0.92] |
| eigen_low | below 0.85 [0.78, 0.91] | below 0.82 [0.73, 0.92] | below 0.80 [0.70, 0.91] | below 0.82 [0.72, 0.93] | below 0.88 [0.83, 0.92] |
| equal | below 0.93 [0.88, 0.98] | below 0.89 [0.83, 0.96] | below 0.88 [0.80, 0.96] | below 0.86 [0.78, 0.95] | below 0.88 [0.84, 0.92] |
| switch_tail_rev | below 0.42 [0.38, 0.47] | below 0.38 [0.32, 0.45] | below 0.43 [0.32, 0.54] | below 0.33 [0.24, 0.43] | below 0.36 [0.34, 0.39] |
| dev:equal>single | below 0.84 [0.77, 0.91] | below 0.81 [0.71, 0.90] | below 0.68 [0.55, 0.81] | below 0.72 [0.60, 0.83] | below 0.81 [0.77, 0.85] |
| dev:equal>twin | below 0.84 [0.78, 0.91] | below 0.82 [0.72, 0.91] | below 0.82 [0.72, 0.93] | below 0.76 [0.64, 0.88] | below 0.82 [0.78, 0.86] |
| near:equal>single | below 0.92 [0.85, 0.99] | below 0.92 [0.86, 0.98] | below 0.91 [0.83, 0.98] | below 0.89 [0.80, 0.98] | below 0.85 [0.81, 0.89] |
| switch_tail | below 0.40 [0.35, 0.44] | below 0.33 [0.27, 0.39] | below 0.34 [0.25, 0.44] | below 0.32 [0.19, 0.45] | below 0.36 [0.33, 0.39] |
| sign_switch | below 0.88 [0.81, 0.95] | below 0.88 [0.81, 0.94] | below 0.82 [0.71, 0.92] | below 0.84 [0.73, 0.94] | below 0.93 [0.89, 0.97] |
| sign_switch_rev | below 0.53 [0.47, 0.58] | below 0.49 [0.42, 0.56] | below 0.47 [0.36, 0.58] | below 0.58 [0.45, 0.70] | below 0.47 [0.44, 0.50] |
| lever_t | below 0.72 [0.65, 0.78] | below 0.81 [0.72, 0.91] | below 0.87 [0.78, 0.96] | below 0.86 [0.77, 0.96] | below 0.89 [0.85, 0.93] |
| lever_t_rev | below 0.56 [0.51, 0.62] | below 0.35 [0.29, 0.41] | below 0.22 [0.14, 0.29] | below 0.12 [0.04, 0.21] | below 0.12 [0.10, 0.13] |
| block_period | below 0.42 [0.38, 0.47] | below 0.38 [0.31, 0.44] | below 0.33 [0.24, 0.43] | below 0.36 [0.22, 0.50] | below 0.35 [0.33, 0.38] |
| block_period_long | below 0.50 [0.45, 0.55] | below 0.46 [0.39, 0.53] | below 0.34 [0.25, 0.44] | below 0.25 [0.13, 0.37] | below 0.45 [0.42, 0.48] |
| dev:equal>switch_tail | boundary 0.96 [0.92, 1.00] | boundary 0.99 [0.95, 1.04] | boundary 0.97 [0.92, 1.01] | below 0.87 [0.78, 0.96] | below 0.91 [0.87, 0.95] |
| dev:inverse_vol>lever_t_rev | below 0.84 [0.77, 0.90] | below 0.79 [0.70, 0.88] | below 0.75 [0.65, 0.85] | below 0.77 [0.65, 0.89] | below 0.76 [0.72, 0.80] |
| near:equal>switch_tail | below 0.92 [0.87, 0.97] | below 0.93 [0.87, 0.99] | below 0.90 [0.83, 0.97] | below 0.85 [0.77, 0.94] | below 0.89 [0.85, 0.93] |

### t4

| strategy | 0.045 | 0.045/2 | 0.045/5 | 0.045/10 | 0.045/20 |
|--|--|--|--|--|--|
| sticky | below 0.87 [0.80, 0.93] | below 0.82 [0.73, 0.91] | below 0.84 [0.73, 0.94] | below 0.81 [0.70, 0.91] | below 0.85 [0.81, 0.89] |
| single | below 0.93 [0.88, 0.98] | below 0.92 [0.87, 0.97] | below 0.88 [0.81, 0.95] | below 0.92 [0.85, 0.98] | below 0.87 [0.83, 0.91] |
| fresh | below 0.93 [0.88, 0.98] | below 0.91 [0.85, 0.97] | below 0.88 [0.79, 0.97] | below 0.88 [0.79, 0.97] | below 0.93 [0.88, 0.97] |
| twin | below 0.93 [0.89, 0.97] | below 0.93 [0.88, 0.98] | below 0.91 [0.85, 0.96] | below 0.90 [0.84, 0.96] | below 0.88 [0.84, 0.92] |
| inverse_vol | below 0.93 [0.86, 1.00] | below 0.88 [0.81, 0.94] | below 0.87 [0.78, 0.95] | below 0.92 [0.84, 0.99] | below 0.88 [0.84, 0.92] |
| momentum | below 0.92 [0.87, 0.97] | below 0.87 [0.81, 0.94] | below 0.83 [0.73, 0.93] | below 0.87 [0.79, 0.95] | below 0.85 [0.81, 0.89] |
| eigen_low | below 0.87 [0.80, 0.93] | below 0.86 [0.76, 0.95] | below 0.87 [0.78, 0.96] | below 0.89 [0.80, 0.98] | below 0.85 [0.81, 0.89] |
| equal | below 0.92 [0.85, 0.99] | below 0.92 [0.85, 0.99] | below 0.85 [0.77, 0.94] | below 0.87 [0.77, 0.97] | below 0.86 [0.82, 0.90] |
| switch_tail_rev | below 0.39 [0.34, 0.43] | below 0.39 [0.32, 0.45] | below 0.35 [0.26, 0.45] | below 0.25 [0.13, 0.37] | below 0.32 [0.29, 0.34] |
| dev:equal>single | below 0.72 [0.66, 0.78] | below 0.72 [0.64, 0.81] | below 0.81 [0.70, 0.91] | below 0.83 [0.72, 0.93] | below 0.72 [0.69, 0.76] |
| dev:equal>twin | below 0.93 [0.86, 0.99] | below 0.92 [0.85, 0.99] | below 0.84 [0.75, 0.92] | below 0.88 [0.80, 0.97] | below 0.91 [0.86, 0.95] |
| near:equal>single | below 0.94 [0.90, 0.98] | below 0.93 [0.89, 0.98] | below 0.93 [0.88, 0.98] | below 0.92 [0.86, 0.98] | below 0.88 [0.84, 0.93] |
| switch_tail | below 0.40 [0.35, 0.44] | below 0.39 [0.33, 0.46] | below 0.26 [0.18, 0.35] | below 0.19 [0.09, 0.30] | below 0.29 [0.26, 0.31] |
| sign_switch | below 0.94 [0.89, 0.99] | below 0.93 [0.86, 0.99] | below 0.86 [0.77, 0.95] | below 0.92 [0.84, 1.00] | below 0.88 [0.84, 0.93] |
| sign_switch_rev | below 0.50 [0.45, 0.55] | below 0.47 [0.40, 0.54] | below 0.53 [0.41, 0.65] | below 0.47 [0.35, 0.58] | below 0.42 [0.39, 0.44] |
| lever_t | below 0.75 [0.69, 0.82] | below 0.83 [0.74, 0.92] | below 0.83 [0.73, 0.94] | below 0.81 [0.72, 0.90] | below 0.83 [0.79, 0.87] |
| lever_t_rev | below 0.56 [0.51, 0.62] | below 0.41 [0.34, 0.47] | below 0.28 [0.19, 0.36] | below 0.15 [0.06, 0.24] | below 0.12 [0.10, 0.13] |
| block_period | below 0.42 [0.38, 0.47] | below 0.37 [0.31, 0.43] | below 0.38 [0.28, 0.48] | below 0.28 [0.16, 0.40] | below 0.31 [0.29, 0.34] |
| block_period_long | below 0.47 [0.42, 0.52] | below 0.48 [0.41, 0.55] | below 0.49 [0.37, 0.60] | below 0.47 [0.35, 0.58] | below 0.37 [0.34, 0.40] |
| dev:equal>switch_tail | boundary 0.99 [0.95, 1.03] | boundary 0.98 [0.94, 1.03] | below 0.92 [0.87, 0.98] | below 0.90 [0.82, 0.98] | below 0.94 [0.90, 0.99] |
| dev:inverse_vol>lever_t_rev | below 0.83 [0.77, 0.90] | below 0.83 [0.73, 0.92] | below 0.72 [0.62, 0.82] | below 0.73 [0.61, 0.84] | below 0.73 [0.69, 0.77] |
| near:equal>switch_tail | below 0.94 [0.89, 0.99] | below 0.91 [0.85, 0.97] | below 0.89 [0.80, 0.98] | below 0.77 [0.67, 0.88] | below 0.86 [0.82, 0.90] |

### t5

| strategy | 0.045 | 0.045/2 | 0.045/5 | 0.045/10 | 0.045/20 |
|--|--|--|--|--|--|
| sticky | below 0.92 [0.87, 0.97] | below 0.92 [0.85, 0.99] | below 0.88 [0.79, 0.97] | below 0.86 [0.77, 0.96] | below 0.90 [0.86, 0.95] |
| single | below 0.91 [0.84, 0.98] | below 0.88 [0.82, 0.95] | below 0.87 [0.78, 0.96] | below 0.90 [0.82, 0.98] | below 0.88 [0.84, 0.92] |
| fresh | below 0.91 [0.87, 0.95] | below 0.91 [0.85, 0.96] | below 0.89 [0.82, 0.96] | below 0.85 [0.76, 0.94] | below 0.90 [0.86, 0.95] |
| twin | below 0.91 [0.86, 0.96] | below 0.88 [0.81, 0.95] | below 0.79 [0.69, 0.89] | below 0.87 [0.78, 0.96] | below 0.88 [0.84, 0.92] |
| inverse_vol | below 0.91 [0.84, 0.97] | below 0.88 [0.81, 0.95] | below 0.84 [0.73, 0.95] | below 0.86 [0.77, 0.96] | below 0.90 [0.86, 0.94] |
| momentum | below 0.92 [0.87, 0.97] | below 0.89 [0.82, 0.95] | below 0.83 [0.73, 0.94] | below 0.82 [0.71, 0.92] | below 0.89 [0.85, 0.93] |
| eigen_low | below 0.89 [0.82, 0.95] | below 0.82 [0.73, 0.91] | below 0.77 [0.67, 0.87] | below 0.88 [0.80, 0.97] | below 0.84 [0.80, 0.88] |
| equal | below 0.92 [0.88, 0.96] | below 0.91 [0.86, 0.97] | below 0.90 [0.85, 0.96] | below 0.91 [0.84, 0.97] | below 0.88 [0.84, 0.92] |
| switch_tail_rev | below 0.44 [0.40, 0.49] | below 0.36 [0.30, 0.42] | below 0.29 [0.20, 0.38] | below 0.32 [0.19, 0.45] | below 0.33 [0.31, 0.36] |
| dev:equal>single | below 0.84 [0.77, 0.91] | below 0.79 [0.70, 0.88] | below 0.83 [0.74, 0.91] | below 0.77 [0.65, 0.89] | below 0.76 [0.72, 0.79] |
| dev:equal>twin | below 0.83 [0.77, 0.90] | below 0.82 [0.73, 0.92] | below 0.76 [0.66, 0.86] | below 0.86 [0.76, 0.95] | below 0.88 [0.84, 0.92] |
| near:equal>single | below 0.93 [0.88, 0.98] | below 0.93 [0.87, 0.98] | below 0.87 [0.78, 0.96] | below 0.90 [0.81, 0.98] | below 0.95 [0.91, 1.00] |
| switch_tail | below 0.44 [0.39, 0.49] | below 0.39 [0.33, 0.46] | below 0.42 [0.31, 0.52] | below 0.36 [0.26, 0.46] | below 0.34 [0.32, 0.37] |
| sign_switch | below 0.94 [0.89, 0.99] | below 0.90 [0.83, 0.97] | below 0.84 [0.73, 0.95] | below 0.82 [0.72, 0.93] | below 0.93 [0.89, 0.97] |
| sign_switch_rev | below 0.50 [0.45, 0.56] | below 0.46 [0.39, 0.53] | below 0.39 [0.29, 0.49] | below 0.48 [0.37, 0.59] | below 0.44 [0.41, 0.46] |
| lever_t | below 0.66 [0.61, 0.72] | below 0.69 [0.60, 0.77] | below 0.77 [0.67, 0.87] | below 0.86 [0.76, 0.95] | below 0.84 [0.80, 0.88] |
| lever_t_rev | below 0.52 [0.47, 0.57] | below 0.33 [0.27, 0.39] | below 0.21 [0.13, 0.28] | below 0.18 [0.08, 0.28] | below 0.12 [0.10, 0.13] |
| block_period | below 0.40 [0.36, 0.45] | below 0.36 [0.29, 0.42] | below 0.33 [0.23, 0.42] | below 0.25 [0.13, 0.37] | below 0.36 [0.34, 0.39] |
| block_period_long | below 0.51 [0.46, 0.56] | below 0.48 [0.41, 0.55] | below 0.42 [0.32, 0.53] | below 0.35 [0.21, 0.48] | below 0.39 [0.36, 0.41] |
| dev:equal>switch_tail | boundary 1.04 [1.00, 1.08] | boundary 1.00 [0.95, 1.04] | below 0.94 [0.90, 0.99] | below 0.95 [0.91, 1.00] | below 0.95 [0.91, 0.99] |
| dev:inverse_vol>lever_t_rev | below 0.84 [0.78, 0.91] | below 0.86 [0.76, 0.95] | below 0.81 [0.71, 0.91] | below 0.79 [0.69, 0.89] | below 0.71 [0.68, 0.75] |
| near:equal>switch_tail | below 0.90 [0.85, 0.94] | below 0.88 [0.82, 0.95] | below 0.87 [0.78, 0.96] | below 0.90 [0.82, 0.98] | below 0.89 [0.85, 0.93] |

### garch-normal

| strategy | 0.045 | 0.045/2 | 0.045/5 | 0.045/10 | 0.045/20 |
|--|--|--|--|--|--|
| sticky | below 0.91 [0.86, 0.96] | boundary 0.96 [0.92, 1.00] | below 0.94 [0.90, 0.98] | below 0.93 [0.88, 0.98] | below 0.93 [0.89, 0.98] |
| single | below 0.92 [0.88, 0.97] | below 0.91 [0.84, 0.98] | below 0.90 [0.82, 0.97] | below 0.89 [0.82, 0.97] | below 0.92 [0.88, 0.97] |
| fresh | below 0.91 [0.87, 0.96] | below 0.89 [0.82, 0.96] | boundary 0.96 [0.92, 1.00] | below 0.96 [0.91, 1.00] | boundary 0.96 [0.92, 1.00] |
| twin | below 0.89 [0.82, 0.96] | below 0.90 [0.83, 0.97] | below 0.88 [0.79, 0.97] | below 0.84 [0.73, 0.95] | below 0.90 [0.86, 0.94] |
| inverse_vol | below 0.94 [0.89, 0.99] | below 0.92 [0.87, 0.98] | below 0.92 [0.84, 1.00] | below 0.90 [0.83, 0.98] | below 0.91 [0.87, 0.96] |
| momentum | below 0.92 [0.88, 0.96] | below 0.91 [0.86, 0.97] | below 0.82 [0.72, 0.93] | below 0.82 [0.72, 0.93] | below 0.91 [0.87, 0.95] |
| eigen_low | below 0.90 [0.84, 0.97] | below 0.92 [0.85, 0.98] | below 0.92 [0.84, 1.00] | below 0.84 [0.75, 0.94] | below 0.89 [0.85, 0.93] |
| equal | below 0.93 [0.88, 0.98] | below 0.93 [0.88, 0.98] | below 0.91 [0.85, 0.97] | below 0.94 [0.90, 0.99] | below 0.89 [0.85, 0.93] |
| switch_tail_rev | below 0.45 [0.40, 0.50] | below 0.47 [0.40, 0.54] | below 0.47 [0.35, 0.58] | below 0.37 [0.27, 0.47] | below 0.33 [0.31, 0.36] |
| dev:equal>single | below 0.91 [0.84, 0.98] | below 0.87 [0.80, 0.94] | below 0.83 [0.73, 0.94] | below 0.83 [0.72, 0.93] | below 0.82 [0.78, 0.86] |
| dev:equal>twin | below 0.85 [0.79, 0.92] | below 0.90 [0.84, 0.97] | below 0.84 [0.75, 0.93] | below 0.81 [0.71, 0.91] | below 0.80 [0.76, 0.84] |
| near:equal>single | below 0.93 [0.89, 0.97] | boundary 0.97 [0.92, 1.01] | below 0.91 [0.85, 0.97] | below 0.90 [0.82, 0.97] | below 0.92 [0.88, 0.96] |
| switch_tail | below 0.43 [0.38, 0.48] | below 0.39 [0.32, 0.45] | below 0.35 [0.25, 0.44] | below 0.35 [0.25, 0.44] | below 0.33 [0.30, 0.35] |
| sign_switch | below 0.91 [0.86, 0.96] | below 0.92 [0.85, 0.99] | below 0.84 [0.76, 0.93] | below 0.86 [0.78, 0.94] | below 0.87 [0.83, 0.91] |
| sign_switch_rev | below 0.54 [0.49, 0.60] | below 0.56 [0.48, 0.63] | below 0.54 [0.42, 0.66] | below 0.49 [0.37, 0.60] | below 0.46 [0.44, 0.49] |
| lever_t | below 0.69 [0.63, 0.75] | below 0.71 [0.63, 0.80] | below 0.78 [0.68, 0.88] | below 0.78 [0.66, 0.90] | below 0.88 [0.84, 0.92] |
| lever_t_rev | below 0.53 [0.48, 0.58] | below 0.35 [0.29, 0.41] | below 0.20 [0.13, 0.27] | below 0.21 [0.10, 0.31] | below 0.12 [0.11, 0.14] |
| block_period | below 0.46 [0.41, 0.50] | below 0.41 [0.35, 0.48] | below 0.35 [0.26, 0.45] | below 0.35 [0.21, 0.48] | below 0.36 [0.33, 0.39] |
| block_period_long | below 0.58 [0.53, 0.64] | below 0.54 [0.47, 0.62] | below 0.51 [0.40, 0.63] | below 0.52 [0.40, 0.64] | below 0.44 [0.41, 0.47] |
| dev:equal>switch_tail | boundary 1.00 [0.95, 1.04] | boundary 0.98 [0.94, 1.02] | below 0.95 [0.90, 0.99] | below 0.89 [0.82, 0.96] | below 0.92 [0.88, 0.96] |
| dev:inverse_vol>lever_t_rev | below 0.84 [0.78, 0.91] | below 0.83 [0.74, 0.93] | below 0.84 [0.75, 0.92] | below 0.79 [0.70, 0.88] | below 0.76 [0.72, 0.80] |
| near:equal>switch_tail | below 0.95 [0.91, 0.99] | below 0.91 [0.86, 0.97] | below 0.90 [0.83, 0.97] | below 0.96 [0.91, 1.00] | below 0.94 [0.90, 0.99] |

### garch-t6

| strategy | 0.045 | 0.045/2 | 0.045/5 | 0.045/10 | 0.045/20 |
|--|--|--|--|--|--|
| sticky | below 0.94 [0.90, 0.98] | below 0.92 [0.87, 0.96] | below 0.92 [0.86, 0.98] | below 0.87 [0.78, 0.96] | below 0.90 [0.86, 0.95] |
| single | below 0.94 [0.90, 0.98] | below 0.87 [0.77, 0.96] | below 0.90 [0.84, 0.96] | below 0.92 [0.87, 0.98] | below 0.95 [0.91, 1.00] |
| fresh | below 0.92 [0.85, 0.99] | below 0.87 [0.78, 0.97] | below 0.91 [0.84, 0.99] | below 0.90 [0.82, 0.98] | below 0.91 [0.87, 0.96] |
| twin | boundary 0.97 [0.93, 1.01] | boundary 0.97 [0.93, 1.01] | below 0.92 [0.87, 0.98] | below 0.89 [0.81, 0.97] | below 0.89 [0.84, 0.93] |
| inverse_vol | below 0.91 [0.84, 0.98] | below 0.87 [0.80, 0.94] | below 0.92 [0.85, 0.99] | below 0.88 [0.80, 0.96] | below 0.88 [0.84, 0.92] |
| momentum | below 0.86 [0.80, 0.93] | below 0.94 [0.89, 0.98] | below 0.93 [0.88, 0.98] | below 0.92 [0.86, 0.97] | below 0.92 [0.88, 0.96] |
| eigen_low | below 0.93 [0.88, 0.98] | below 0.92 [0.87, 0.98] | below 0.89 [0.81, 0.97] | below 0.79 [0.69, 0.89] | below 0.90 [0.86, 0.95] |
| equal | below 0.85 [0.79, 0.92] | below 0.86 [0.77, 0.96] | below 0.92 [0.87, 0.97] | below 0.93 [0.88, 0.98] | below 0.89 [0.85, 0.93] |
| switch_tail_rev | below 0.41 [0.36, 0.45] | below 0.37 [0.30, 0.43] | below 0.39 [0.29, 0.49] | below 0.36 [0.22, 0.50] | below 0.31 [0.29, 0.34] |
| dev:equal>single | below 0.86 [0.79, 0.93] | below 0.81 [0.72, 0.91] | below 0.84 [0.75, 0.93] | below 0.82 [0.72, 0.93] | below 0.79 [0.75, 0.83] |
| dev:equal>twin | below 0.82 [0.75, 0.88] | below 0.85 [0.75, 0.94] | below 0.85 [0.78, 0.93] | below 0.83 [0.73, 0.94] | below 0.88 [0.84, 0.92] |
| near:equal>single | below 0.95 [0.91, 0.99] | below 0.92 [0.87, 0.97] | below 0.92 [0.86, 0.97] | below 0.95 [0.91, 1.00] | below 0.91 [0.87, 0.96] |
| switch_tail | below 0.42 [0.38, 0.47] | below 0.41 [0.35, 0.48] | below 0.31 [0.22, 0.40] | below 0.32 [0.19, 0.45] | below 0.32 [0.30, 0.35] |
| sign_switch | below 0.95 [0.91, 0.99] | below 0.93 [0.89, 0.98] | below 0.94 [0.89, 0.98] | below 0.93 [0.88, 0.98] | below 0.91 [0.87, 0.95] |
| sign_switch_rev | below 0.51 [0.46, 0.57] | below 0.49 [0.41, 0.56] | below 0.49 [0.38, 0.61] | below 0.55 [0.43, 0.67] | below 0.45 [0.42, 0.48] |
| lever_t | below 0.70 [0.64, 0.76] | below 0.75 [0.66, 0.84] | below 0.76 [0.66, 0.86] | below 0.90 [0.83, 0.97] | below 0.85 [0.81, 0.89] |
| lever_t_rev | below 0.59 [0.53, 0.64] | below 0.38 [0.32, 0.44] | below 0.32 [0.23, 0.41] | below 0.25 [0.13, 0.37] | below 0.12 [0.11, 0.14] |
| block_period | below 0.38 [0.34, 0.43] | below 0.34 [0.28, 0.40] | below 0.34 [0.25, 0.44] | below 0.33 [0.20, 0.47] | below 0.34 [0.31, 0.36] |
| block_period_long | below 0.51 [0.46, 0.56] | below 0.50 [0.43, 0.58] | below 0.44 [0.33, 0.55] | below 0.46 [0.35, 0.57] | below 0.42 [0.39, 0.44] |
| dev:equal>switch_tail | boundary 1.00 [0.95, 1.04] | boundary 0.96 [0.92, 1.00] | below 0.95 [0.91, 0.99] | below 0.92 [0.85, 0.98] | below 0.94 [0.90, 0.99] |
| dev:inverse_vol>lever_t_rev | below 0.82 [0.76, 0.89] | below 0.78 [0.69, 0.87] | below 0.75 [0.65, 0.85] | below 0.66 [0.53, 0.79] | below 0.75 [0.71, 0.79] |
| near:equal>switch_tail | below 0.89 [0.83, 0.96] | below 0.92 [0.86, 0.98] | below 0.88 [0.79, 0.97] | below 0.90 [0.83, 0.96] | below 0.93 [0.88, 0.97] |

### garch-t6-regime

| strategy | 0.045 | 0.045/2 | 0.045/5 | 0.045/10 | 0.045/20 |
|--|--|--|--|--|--|
| sticky | below 0.90 [0.83, 0.97] | below 0.84 [0.75, 0.94] | below 0.87 [0.78, 0.96] | below 0.86 [0.77, 0.96] | below 0.87 [0.83, 0.91] |
| single | below 0.91 [0.86, 0.96] | below 0.88 [0.82, 0.95] | below 0.83 [0.75, 0.92] | below 0.88 [0.80, 0.97] | below 0.93 [0.89, 0.98] |
| fresh | below 0.93 [0.88, 0.98] | below 0.93 [0.88, 0.98] | below 0.92 [0.87, 0.98] | below 0.94 [0.89, 0.98] | below 0.91 [0.87, 0.95] |
| twin | below 0.92 [0.87, 0.97] | below 0.92 [0.87, 0.98] | boundary 0.96 [0.92, 1.00] | below 0.92 [0.86, 0.97] | below 0.90 [0.86, 0.95] |
| inverse_vol | below 0.88 [0.81, 0.95] | below 0.88 [0.81, 0.95] | below 0.91 [0.85, 0.96] | below 0.89 [0.81, 0.97] | below 0.89 [0.85, 0.93] |
| momentum | below 0.91 [0.84, 0.98] | below 0.93 [0.88, 0.98] | below 0.88 [0.79, 0.97] | below 0.87 [0.78, 0.96] | below 0.87 [0.82, 0.91] |
| eigen_low | below 0.93 [0.88, 0.98] | below 0.92 [0.87, 0.98] | below 0.90 [0.83, 0.97] | below 0.84 [0.74, 0.93] | below 0.85 [0.81, 0.90] |
| equal | below 0.86 [0.79, 0.92] | below 0.88 [0.81, 0.95] | below 0.87 [0.78, 0.96] | below 0.86 [0.77, 0.95] | below 0.86 [0.82, 0.90] |
| switch_tail_rev | below 0.45 [0.40, 0.49] | below 0.41 [0.35, 0.48] | below 0.33 [0.23, 0.42] | below 0.29 [0.17, 0.42] | below 0.35 [0.32, 0.37] |
| dev:equal>single | below 0.84 [0.77, 0.91] | below 0.85 [0.75, 0.94] | below 0.78 [0.68, 0.89] | below 0.75 [0.63, 0.86] | below 0.76 [0.72, 0.80] |
| dev:equal>twin | below 0.87 [0.80, 0.94] | below 0.86 [0.77, 0.96] | below 0.85 [0.77, 0.94] | below 0.86 [0.77, 0.96] | below 0.87 [0.83, 0.91] |
| near:equal>single | below 0.90 [0.84, 0.97] | below 0.88 [0.82, 0.95] | below 0.87 [0.78, 0.96] | below 0.86 [0.76, 0.95] | below 0.88 [0.84, 0.93] |
| switch_tail | below 0.43 [0.39, 0.48] | below 0.39 [0.32, 0.45] | below 0.34 [0.25, 0.44] | below 0.33 [0.20, 0.47] | below 0.30 [0.28, 0.33] |
| sign_switch | below 0.88 [0.83, 0.93] | below 0.86 [0.80, 0.93] | below 0.84 [0.73, 0.94] | below 0.93 [0.86, 1.00] | below 0.93 [0.88, 0.97] |
| sign_switch_rev | below 0.49 [0.44, 0.55] | below 0.47 [0.40, 0.54] | below 0.42 [0.32, 0.53] | below 0.36 [0.22, 0.50] | below 0.42 [0.39, 0.45] |
| lever_t | below 0.65 [0.59, 0.71] | below 0.71 [0.63, 0.80] | below 0.85 [0.76, 0.93] | below 0.91 [0.82, 0.99] | below 0.84 [0.80, 0.88] |
| lever_t_rev | below 0.51 [0.46, 0.56] | below 0.34 [0.28, 0.40] | below 0.17 [0.10, 0.23] | below 0.14 [0.05, 0.22] | below 0.13 [0.12, 0.15] |
| block_period | below 0.41 [0.36, 0.45] | below 0.36 [0.30, 0.42] | below 0.31 [0.22, 0.40] | below 0.26 [0.15, 0.38] | below 0.34 [0.32, 0.37] |
| block_period_long | below 0.57 [0.52, 0.63] | below 0.51 [0.43, 0.58] | below 0.40 [0.30, 0.51] | below 0.32 [0.19, 0.45] | below 0.41 [0.38, 0.44] |
| dev:equal>switch_tail | boundary 1.01 [0.96, 1.05] | boundary 0.96 [0.92, 1.01] | boundary 0.97 [0.93, 1.01] | boundary 0.99 [0.94, 1.03] | boundary 0.97 [0.92, 1.01] |
| dev:inverse_vol>lever_t_rev | below 0.85 [0.78, 0.92] | below 0.82 [0.73, 0.92] | below 0.82 [0.71, 0.92] | below 0.82 [0.71, 0.92] | below 0.75 [0.71, 0.79] |
| near:equal>switch_tail | below 0.93 [0.89, 0.97] | below 0.95 [0.90, 0.99] | below 0.96 [0.91, 1.00] | below 0.93 [0.88, 0.98] | below 0.92 [0.88, 0.96] |

### factor-t6

| strategy | 0.045 | 0.045/2 | 0.045/5 | 0.045/10 | 0.045/20 |
|--|--|--|--|--|--|
| sticky | below 0.87 [0.80, 0.94] | below 0.86 [0.77, 0.96] | below 0.80 [0.69, 0.90] | below 0.83 [0.74, 0.93] | below 0.88 [0.84, 0.92] |
| single | below 0.96 [0.92, 1.00] | boundary 0.96 [0.92, 1.01] | below 0.94 [0.90, 0.99] | below 0.91 [0.84, 0.98] | below 0.88 [0.84, 0.92] |
| fresh | below 0.91 [0.86, 0.96] | below 0.90 [0.84, 0.97] | below 0.93 [0.88, 0.98] | below 0.91 [0.84, 0.98] | below 0.88 [0.84, 0.92] |
| twin | below 0.90 [0.84, 0.97] | below 0.91 [0.84, 0.98] | below 0.90 [0.84, 0.97] | below 0.88 [0.80, 0.96] | below 0.90 [0.86, 0.94] |
| inverse_vol | below 0.94 [0.89, 0.98] | below 0.88 [0.82, 0.95] | below 0.89 [0.81, 0.97] | below 0.90 [0.84, 0.96] | below 0.89 [0.85, 0.93] |
| momentum | below 0.92 [0.87, 0.97] | below 0.90 [0.83, 0.97] | below 0.91 [0.84, 0.98] | below 0.85 [0.76, 0.95] | below 0.89 [0.85, 0.93] |
| eigen_low | below 0.91 [0.86, 0.96] | below 0.90 [0.83, 0.97] | below 0.86 [0.78, 0.93] | below 0.83 [0.72, 0.93] | below 0.86 [0.82, 0.90] |
| equal | boundary 0.96 [0.92, 1.00] | below 0.92 [0.86, 0.98] | below 0.91 [0.85, 0.96] | below 0.92 [0.87, 0.98] | below 0.94 [0.90, 0.98] |
| switch_tail_rev | below 0.40 [0.36, 0.45] | below 0.36 [0.29, 0.42] | below 0.33 [0.24, 0.43] | below 0.36 [0.22, 0.50] | below 0.34 [0.32, 0.37] |
| dev:equal>single | below 0.87 [0.80, 0.93] | below 0.86 [0.77, 0.96] | below 0.81 [0.73, 0.90] | below 0.82 [0.71, 0.92] | below 0.84 [0.80, 0.88] |
| dev:equal>twin | below 0.83 [0.77, 0.90] | below 0.82 [0.73, 0.91] | below 0.84 [0.76, 0.93] | below 0.74 [0.63, 0.86] | below 0.89 [0.85, 0.93] |
| near:equal>single | below 0.94 [0.90, 0.98] | below 0.90 [0.84, 0.97] | below 0.93 [0.88, 0.98] | below 0.90 [0.83, 0.97] | below 0.90 [0.86, 0.94] |
| switch_tail | below 0.47 [0.42, 0.52] | below 0.44 [0.38, 0.51] | below 0.37 [0.27, 0.47] | below 0.36 [0.22, 0.50] | below 0.36 [0.33, 0.39] |
| sign_switch | below 0.91 [0.86, 0.96] | below 0.90 [0.83, 0.97] | below 0.90 [0.82, 0.97] | below 0.94 [0.90, 0.99] | below 0.93 [0.89, 0.97] |
| sign_switch_rev | below 0.47 [0.42, 0.52] | below 0.48 [0.41, 0.55] | below 0.42 [0.32, 0.53] | below 0.47 [0.35, 0.58] | below 0.42 [0.39, 0.45] |
| lever_t | below 0.66 [0.60, 0.72] | below 0.71 [0.62, 0.80] | below 0.73 [0.63, 0.83] | below 0.74 [0.62, 0.85] | below 0.88 [0.84, 0.92] |
| lever_t_rev | below 0.57 [0.51, 0.62] | below 0.44 [0.37, 0.51] | below 0.34 [0.25, 0.44] | below 0.29 [0.17, 0.42] | below 0.12 [0.11, 0.14] |
| block_period | below 0.44 [0.39, 0.48] | below 0.47 [0.40, 0.54] | below 0.42 [0.32, 0.53] | below 0.36 [0.22, 0.50] | below 0.35 [0.33, 0.38] |
| block_period_long | below 0.50 [0.45, 0.55] | below 0.44 [0.37, 0.50] | below 0.44 [0.34, 0.55] | below 0.41 [0.31, 0.51] | below 0.44 [0.42, 0.47] |
| dev:equal>switch_tail | boundary 1.02 [0.97, 1.06] | boundary 1.01 [0.97, 1.06] | boundary 0.97 [0.93, 1.01] | boundary 0.99 [0.94, 1.03] | boundary 0.98 [0.94, 1.02] |
| dev:inverse_vol>lever_t_rev | below 0.85 [0.79, 0.92] | below 0.79 [0.70, 0.89] | below 0.77 [0.67, 0.87] | below 0.78 [0.66, 0.90] | below 0.76 [0.72, 0.80] |
| near:equal>switch_tail | below 0.89 [0.82, 0.96] | below 0.92 [0.86, 0.98] | below 0.90 [0.83, 0.97] | below 0.87 [0.78, 0.96] | below 0.89 [0.85, 0.93] |

### factor-t6-regime

| strategy | 0.045 | 0.045/2 | 0.045/5 | 0.045/10 | 0.045/20 |
|--|--|--|--|--|--|
| sticky | below 0.88 [0.81, 0.94] | below 0.84 [0.75, 0.94] | below 0.89 [0.82, 0.97] | below 0.90 [0.82, 0.97] | below 0.86 [0.82, 0.90] |
| single | below 0.94 [0.90, 0.98] | below 0.94 [0.90, 0.98] | below 0.90 [0.82, 0.97] | below 0.88 [0.80, 0.97] | below 0.90 [0.86, 0.94] |
| fresh | below 0.85 [0.79, 0.92] | below 0.81 [0.72, 0.90] | below 0.90 [0.83, 0.97] | below 0.88 [0.80, 0.95] | below 0.92 [0.88, 0.96] |
| twin | boundary 0.97 [0.93, 1.01] | below 0.93 [0.88, 0.98] | below 0.91 [0.85, 0.97] | below 0.88 [0.80, 0.96] | below 0.91 [0.87, 0.95] |
| inverse_vol | below 0.93 [0.88, 0.97] | below 0.86 [0.81, 0.92] | below 0.88 [0.80, 0.96] | below 0.84 [0.75, 0.94] | below 0.87 [0.83, 0.91] |
| momentum | below 0.90 [0.83, 0.97] | below 0.86 [0.77, 0.96] | below 0.86 [0.77, 0.95] | below 0.89 [0.81, 0.97] | below 0.90 [0.86, 0.94] |
| eigen_low | below 0.91 [0.84, 0.98] | below 0.88 [0.82, 0.95] | below 0.84 [0.73, 0.95] | below 0.76 [0.66, 0.86] | below 0.85 [0.81, 0.89] |
| equal | below 0.89 [0.84, 0.94] | below 0.90 [0.83, 0.97] | below 0.88 [0.82, 0.95] | below 0.84 [0.75, 0.92] | below 0.82 [0.78, 0.86] |
| switch_tail_rev | below 0.44 [0.39, 0.48] | below 0.42 [0.36, 0.49] | below 0.38 [0.28, 0.47] | below 0.35 [0.21, 0.48] | below 0.33 [0.30, 0.35] |
| dev:equal>single | below 0.87 [0.80, 0.93] | below 0.84 [0.75, 0.94] | below 0.83 [0.73, 0.93] | below 0.83 [0.72, 0.93] | below 0.80 [0.76, 0.84] |
| dev:equal>twin | below 0.85 [0.79, 0.92] | below 0.86 [0.76, 0.95] | below 0.86 [0.78, 0.93] | below 0.84 [0.73, 0.94] | below 0.83 [0.79, 0.87] |
| near:equal>single | below 0.94 [0.89, 0.99] | below 0.90 [0.83, 0.97] | below 0.83 [0.73, 0.94] | below 0.83 [0.72, 0.93] | below 0.83 [0.79, 0.87] |
| switch_tail | below 0.44 [0.39, 0.48] | below 0.42 [0.35, 0.48] | below 0.35 [0.25, 0.44] | below 0.33 [0.20, 0.47] | below 0.34 [0.32, 0.37] |
| sign_switch | below 0.95 [0.90, 0.99] | below 0.94 [0.89, 0.98] | below 0.91 [0.84, 0.98] | below 0.93 [0.89, 0.98] | below 0.91 [0.87, 0.95] |
| sign_switch_rev | below 0.49 [0.44, 0.54] | below 0.51 [0.43, 0.58] | below 0.45 [0.34, 0.56] | below 0.47 [0.35, 0.58] | below 0.44 [0.41, 0.47] |
| lever_t | below 0.76 [0.69, 0.82] | below 0.84 [0.74, 0.93] | below 0.82 [0.72, 0.92] | below 0.77 [0.67, 0.87] | below 0.85 [0.81, 0.89] |
| lever_t_rev | below 0.56 [0.51, 0.61] | below 0.37 [0.31, 0.43] | below 0.22 [0.14, 0.29] | below 0.18 [0.08, 0.28] | below 0.13 [0.11, 0.14] |
| block_period | below 0.42 [0.37, 0.46] | below 0.40 [0.33, 0.47] | below 0.40 [0.29, 0.50] | below 0.41 [0.31, 0.51] | below 0.32 [0.30, 0.35] |
| block_period_long | below 0.53 [0.47, 0.58] | below 0.53 [0.45, 0.60] | below 0.53 [0.41, 0.65] | below 0.42 [0.32, 0.53] | below 0.44 [0.41, 0.46] |
| dev:equal>switch_tail | boundary 0.99 [0.95, 1.04] | boundary 0.99 [0.95, 1.03] | boundary 0.99 [0.95, 1.03] | boundary 0.97 [0.93, 1.02] | boundary 0.99 [0.94, 1.03] |
| dev:inverse_vol>lever_t_rev | below 0.82 [0.76, 0.89] | below 0.84 [0.75, 0.93] | below 0.77 [0.67, 0.87] | below 0.74 [0.62, 0.85] | below 0.77 [0.73, 0.81] |
| near:equal>switch_tail | below 0.90 [0.86, 0.95] | below 0.87 [0.77, 0.96] | below 0.82 [0.74, 0.91] | below 0.75 [0.63, 0.87] | below 0.86 [0.82, 0.90] |

### garch-persistent

| strategy | 0.045 | 0.045/2 | 0.045/5 | 0.045/10 | 0.045/20 |
|--|--|--|--|--|--|
| sticky | below 0.88 [0.81, 0.94] | below 0.84 [0.75, 0.94] | below 0.88 [0.79, 0.96] | below 0.80 [0.69, 0.90] | below 0.87 [0.83, 0.91] |
| single | below 0.92 [0.85, 0.98] | below 0.93 [0.86, 1.00] | below 0.88 [0.79, 0.97] | below 0.85 [0.76, 0.95] | below 0.93 [0.88, 0.97] |
| fresh | below 0.88 [0.82, 0.95] | below 0.92 [0.86, 0.98] | below 0.90 [0.82, 0.97] | below 0.94 [0.90, 0.98] | below 0.93 [0.89, 0.97] |
| twin | below 0.88 [0.82, 0.95] | below 0.92 [0.86, 0.97] | below 0.85 [0.77, 0.94] | below 0.88 [0.80, 0.95] | below 0.88 [0.84, 0.93] |
| inverse_vol | below 0.92 [0.88, 0.97] | below 0.91 [0.85, 0.97] | below 0.88 [0.80, 0.95] | below 0.88 [0.79, 0.97] | below 0.89 [0.85, 0.93] |
| momentum | below 0.92 [0.87, 0.97] | below 0.94 [0.90, 0.99] | below 0.88 [0.79, 0.97] | below 0.91 [0.84, 0.97] | below 0.91 [0.87, 0.96] |
| eigen_low | below 0.90 [0.85, 0.95] | below 0.86 [0.80, 0.93] | below 0.84 [0.73, 0.95] | below 0.91 [0.85, 0.98] | below 0.88 [0.84, 0.92] |
| equal | below 0.94 [0.90, 0.98] | below 0.91 [0.87, 0.96] | below 0.88 [0.79, 0.97] | below 0.90 [0.84, 0.97] | below 0.89 [0.85, 0.93] |
| switch_tail_rev | below 0.43 [0.39, 0.48] | below 0.42 [0.35, 0.48] | below 0.34 [0.25, 0.44] | below 0.29 [0.17, 0.42] | below 0.34 [0.31, 0.36] |
| dev:equal>single | below 0.87 [0.80, 0.94] | below 0.86 [0.79, 0.93] | below 0.84 [0.76, 0.91] | below 0.83 [0.73, 0.94] | below 0.78 [0.74, 0.82] |
| dev:equal>twin | below 0.86 [0.79, 0.93] | below 0.84 [0.78, 0.91] | below 0.76 [0.66, 0.86] | below 0.78 [0.66, 0.90] | below 0.84 [0.80, 0.88] |
| near:equal>single | below 0.93 [0.89, 0.97] | below 0.94 [0.90, 0.98] | below 0.92 [0.86, 0.98] | below 0.92 [0.86, 0.98] | below 0.94 [0.90, 0.99] |
| switch_tail | below 0.39 [0.35, 0.44] | below 0.35 [0.29, 0.41] | below 0.33 [0.23, 0.42] | below 0.32 [0.19, 0.45] | below 0.36 [0.33, 0.39] |
| sign_switch | below 0.90 [0.83, 0.97] | below 0.87 [0.77, 0.96] | below 0.84 [0.73, 0.95] | boundary 0.96 [0.92, 1.00] | below 0.95 [0.91, 0.99] |
| sign_switch_rev | below 0.47 [0.42, 0.51] | below 0.41 [0.34, 0.47] | below 0.43 [0.32, 0.54] | below 0.38 [0.28, 0.47] | below 0.44 [0.41, 0.47] |
| lever_t | below 0.66 [0.60, 0.72] | below 0.72 [0.63, 0.80] | below 0.80 [0.69, 0.90] | below 0.86 [0.77, 0.96] | below 0.82 [0.78, 0.86] |
| lever_t_rev | below 0.56 [0.50, 0.61] | below 0.36 [0.30, 0.42] | below 0.23 [0.15, 0.31] | below 0.17 [0.07, 0.26] | below 0.13 [0.11, 0.14] |
| block_period | below 0.44 [0.39, 0.49] | below 0.43 [0.37, 0.50] | below 0.38 [0.28, 0.47] | below 0.40 [0.30, 0.51] | below 0.34 [0.32, 0.37] |
| block_period_long | below 0.46 [0.41, 0.51] | below 0.46 [0.39, 0.53] | below 0.44 [0.33, 0.55] | below 0.44 [0.33, 0.55] | below 0.41 [0.38, 0.44] |
| dev:equal>switch_tail | boundary 1.03 [0.98, 1.07] | boundary 0.97 [0.92, 1.01] | below 0.93 [0.88, 0.98] | below 0.92 [0.86, 0.98] | below 0.93 [0.88, 0.97] |
| dev:inverse_vol>lever_t_rev | below 0.81 [0.75, 0.88] | below 0.77 [0.68, 0.86] | below 0.73 [0.63, 0.82] | below 0.78 [0.66, 0.90] | below 0.76 [0.72, 0.80] |
| near:equal>switch_tail | below 0.91 [0.84, 0.98] | below 0.94 [0.90, 0.99] | below 0.90 [0.82, 0.97] | below 0.83 [0.72, 0.93] | below 0.89 [0.85, 0.93] |

### garch-99

| strategy | 0.045 | 0.045/2 | 0.045/5 | 0.045/10 | 0.045/20 |
|--|--|--|--|--|--|
| sticky | below 0.93 [0.88, 0.98] | below 0.92 [0.87, 0.98] | below 0.85 [0.77, 0.94] | below 0.84 [0.74, 0.93] | below 0.90 [0.86, 0.94] |
| single | below 0.94 [0.90, 0.98] | below 0.94 [0.90, 0.98] | below 0.92 [0.86, 0.98] | below 0.90 [0.83, 0.97] | below 0.91 [0.87, 0.95] |
| twin | below 0.91 [0.84, 0.98] | below 0.86 [0.77, 0.96] | below 0.95 [0.91, 0.99] | below 0.93 [0.88, 0.97] | below 0.90 [0.86, 0.94] |
| inverse_vol | below 0.88 [0.81, 0.95] | below 0.83 [0.74, 0.93] | below 0.75 [0.65, 0.85] | below 0.86 [0.77, 0.96] | below 0.88 [0.84, 0.92] |
| momentum | below 0.90 [0.85, 0.95] | below 0.92 [0.86, 0.98] | below 0.88 [0.81, 0.96] | below 0.81 [0.70, 0.91] | below 0.88 [0.84, 0.92] |
| eigen_low | below 0.91 [0.86, 0.96] | below 0.91 [0.84, 0.98] | below 0.89 [0.83, 0.96] | below 0.86 [0.77, 0.95] | below 0.86 [0.82, 0.90] |
| equal | below 0.96 [0.92, 1.00] | below 0.96 [0.91, 1.00] | below 0.94 [0.90, 0.99] | below 0.93 [0.89, 0.98] | below 0.93 [0.89, 0.98] |
| switch_tail_rev | below 0.42 [0.37, 0.47] | below 0.41 [0.34, 0.47] | below 0.40 [0.29, 0.50] | below 0.33 [0.20, 0.47] | below 0.34 [0.32, 0.37] |
| dev:equal>single | below 0.83 [0.77, 0.90] | below 0.90 [0.84, 0.97] | below 0.87 [0.79, 0.94] | below 0.88 [0.81, 0.96] | below 0.84 [0.80, 0.88] |
| dev:equal>twin | below 0.82 [0.75, 0.88] | below 0.85 [0.76, 0.95] | below 0.84 [0.73, 0.95] | below 0.85 [0.75, 0.95] | below 0.82 [0.78, 0.86] |
| near:equal>single | below 0.95 [0.91, 0.99] | below 0.92 [0.87, 0.98] | below 0.89 [0.83, 0.95] | below 0.92 [0.86, 0.98] | below 0.91 [0.86, 0.95] |
| fresh | below 0.95 [0.91, 0.99] | below 0.93 [0.88, 0.98] | boundary 0.97 [0.93, 1.01] | boundary 0.98 [0.94, 1.02] | boundary 0.97 [0.93, 1.01] |
| switch_tail | below 0.43 [0.39, 0.48] | below 0.40 [0.33, 0.47] | below 0.33 [0.24, 0.43] | below 0.44 [0.33, 0.55] | below 0.34 [0.32, 0.37] |
| sign_switch | below 0.90 [0.83, 0.97] | below 0.91 [0.86, 0.97] | below 0.90 [0.83, 0.97] | below 0.89 [0.81, 0.96] | below 0.94 [0.90, 0.98] |
| sign_switch_rev | below 0.50 [0.45, 0.56] | below 0.44 [0.37, 0.50] | below 0.33 [0.24, 0.43] | below 0.26 [0.15, 0.38] | below 0.46 [0.43, 0.49] |
| lever_t | below 0.70 [0.64, 0.76] | below 0.76 [0.67, 0.85] | below 0.81 [0.73, 0.90] | below 0.78 [0.66, 0.90] | below 0.87 [0.83, 0.91] |
| lever_t_rev | below 0.59 [0.54, 0.65] | below 0.36 [0.29, 0.42] | below 0.26 [0.17, 0.34] | below 0.18 [0.08, 0.28] | below 0.11 [0.10, 0.13] |
| block_period | below 0.41 [0.36, 0.46] | below 0.38 [0.31, 0.44] | below 0.35 [0.26, 0.45] | below 0.35 [0.21, 0.48] | below 0.38 [0.35, 0.41] |
| block_period_long | below 0.51 [0.46, 0.56] | below 0.42 [0.36, 0.49] | below 0.35 [0.26, 0.45] | below 0.32 [0.19, 0.45] | below 0.44 [0.41, 0.47] |
| dev:equal>switch_tail | boundary 0.97 [0.93, 1.01] | boundary 0.99 [0.95, 1.03] | boundary 0.97 [0.92, 1.01] | below 0.91 [0.85, 0.98] | below 0.93 [0.88, 0.97] |
| dev:inverse_vol>lever_t_rev | below 0.88 [0.81, 0.94] | below 0.80 [0.71, 0.89] | below 0.78 [0.68, 0.89] | below 0.74 [0.62, 0.85] | below 0.78 [0.74, 0.81] |
| near:equal>switch_tail | below 0.90 [0.83, 0.97] | below 0.93 [0.88, 0.98] | below 0.86 [0.78, 0.93] | below 0.82 [0.73, 0.91] | below 0.93 [0.89, 0.97] |

### garch-99-t8

| strategy | 0.045 | 0.045/2 | 0.045/5 | 0.045/10 | 0.045/20 |
|--|--|--|--|--|--|
| sticky | below 0.89 [0.83, 0.96] | below 0.90 [0.83, 0.97] | boundary 0.97 [0.93, 1.02] | below 0.94 [0.89, 0.98] | below 0.91 [0.87, 0.96] |
| single | below 0.95 [0.91, 0.99] | below 0.89 [0.82, 0.96] | below 0.91 [0.84, 0.98] | below 0.91 [0.84, 0.97] | below 0.90 [0.86, 0.94] |
| twin | below 0.93 [0.88, 0.98] | below 0.87 [0.77, 0.96] | below 0.76 [0.66, 0.86] | below 0.86 [0.77, 0.96] | below 0.88 [0.84, 0.92] |
| inverse_vol | below 0.93 [0.88, 0.98] | below 0.89 [0.82, 0.96] | below 0.86 [0.77, 0.95] | below 0.86 [0.77, 0.96] | below 0.88 [0.84, 0.93] |
| momentum | below 0.95 [0.91, 0.99] | below 0.92 [0.88, 0.97] | below 0.92 [0.87, 0.97] | below 0.92 [0.85, 0.98] | below 0.92 [0.88, 0.97] |
| eigen_low | below 0.92 [0.87, 0.97] | below 0.85 [0.79, 0.92] | below 0.80 [0.69, 0.90] | below 0.89 [0.81, 0.96] | below 0.88 [0.84, 0.92] |
| equal | below 0.93 [0.88, 0.97] | below 0.87 [0.78, 0.97] | below 0.91 [0.85, 0.96] | below 0.90 [0.82, 0.97] | below 0.85 [0.81, 0.89] |
| switch_tail_rev | below 0.41 [0.36, 0.46] | below 0.35 [0.29, 0.41] | below 0.33 [0.23, 0.42] | below 0.31 [0.18, 0.43] | below 0.37 [0.34, 0.39] |
| dev:equal>single | below 0.82 [0.75, 0.88] | below 0.76 [0.67, 0.85] | below 0.75 [0.65, 0.85] | below 0.70 [0.59, 0.82] | below 0.80 [0.76, 0.84] |
| dev:equal>twin | below 0.87 [0.80, 0.93] | below 0.81 [0.72, 0.91] | below 0.83 [0.73, 0.93] | below 0.81 [0.70, 0.91] | below 0.86 [0.82, 0.90] |
| near:equal>single | below 0.93 [0.88, 0.98] | below 0.92 [0.87, 0.97] | below 0.91 [0.84, 0.98] | below 0.91 [0.86, 0.97] | below 0.87 [0.83, 0.92] |
| fresh | below 0.93 [0.89, 0.97] | below 0.85 [0.76, 0.95] | below 0.95 [0.91, 1.00] | below 0.95 [0.91, 0.99] | below 0.95 [0.91, 0.99] |
| switch_tail | below 0.46 [0.41, 0.51] | below 0.42 [0.36, 0.49] | below 0.41 [0.31, 0.51] | below 0.37 [0.27, 0.47] | below 0.33 [0.30, 0.35] |
| sign_switch | below 0.92 [0.87, 0.96] | below 0.91 [0.85, 0.97] | below 0.94 [0.89, 0.98] | below 0.94 [0.90, 0.98] | below 0.96 [0.91, 1.00] |
| sign_switch_rev | below 0.50 [0.45, 0.55] | below 0.51 [0.44, 0.58] | below 0.47 [0.35, 0.58] | below 0.47 [0.36, 0.58] | below 0.48 [0.45, 0.52] |
| lever_t | below 0.76 [0.69, 0.82] | below 0.82 [0.72, 0.91] | below 0.83 [0.72, 0.93] | below 0.87 [0.78, 0.95] | below 0.88 [0.84, 0.92] |
| lever_t_rev | below 0.61 [0.56, 0.67] | below 0.42 [0.35, 0.48] | below 0.22 [0.14, 0.29] | below 0.15 [0.06, 0.24] | below 0.13 [0.11, 0.14] |
| block_period | below 0.40 [0.35, 0.44] | below 0.39 [0.32, 0.45] | below 0.37 [0.27, 0.47] | below 0.28 [0.16, 0.40] | below 0.34 [0.32, 0.37] |
| block_period_long | below 0.49 [0.44, 0.54] | below 0.48 [0.41, 0.55] | below 0.42 [0.32, 0.53] | below 0.33 [0.20, 0.47] | below 0.41 [0.38, 0.44] |
| dev:equal>switch_tail | boundary 0.97 [0.93, 1.01] | boundary 0.98 [0.94, 1.02] | boundary 0.96 [0.92, 1.00] | below 0.94 [0.89, 0.99] | below 0.93 [0.89, 0.98] |
| dev:inverse_vol>lever_t_rev | below 0.78 [0.72, 0.85] | below 0.74 [0.66, 0.83] | below 0.82 [0.71, 0.92] | below 0.78 [0.66, 0.90] | below 0.79 [0.75, 0.83] |
| near:equal>switch_tail | below 0.93 [0.88, 0.98] | below 0.92 [0.88, 0.97] | below 0.90 [0.83, 0.96] | below 0.90 [0.83, 0.97] | below 0.89 [0.85, 0.94] |

### factor

| strategy | 0.045 | 0.045/2 | 0.045/5 | 0.045/10 | 0.045/20 |
|--|--|--|--|--|--|
| sticky | boundary 0.98 [0.93, 1.02] | below 0.94 [0.90, 0.99] | below 0.90 [0.84, 0.96] | below 0.87 [0.77, 0.97] | below 0.87 [0.83, 0.91] |
| single | below 0.88 [0.81, 0.95] | below 0.92 [0.86, 0.97] | below 0.89 [0.82, 0.95] | below 0.88 [0.79, 0.96] | below 0.86 [0.82, 0.90] |
| fresh | below 0.92 [0.87, 0.97] | below 0.93 [0.88, 0.98] | below 0.92 [0.86, 0.97] | below 0.90 [0.83, 0.97] | below 0.93 [0.88, 0.97] |
| twin | below 0.89 [0.82, 0.95] | below 0.87 [0.77, 0.96] | below 0.85 [0.76, 0.94] | below 0.88 [0.80, 0.95] | below 0.91 [0.87, 0.95] |
| inverse_vol | below 0.94 [0.90, 0.98] | below 0.92 [0.86, 0.97] | below 0.90 [0.82, 0.97] | below 0.83 [0.73, 0.94] | below 0.82 [0.79, 0.86] |
| eigen_low | below 0.91 [0.86, 0.95] | below 0.87 [0.77, 0.96] | below 0.83 [0.74, 0.91] | below 0.89 [0.81, 0.97] | below 0.87 [0.83, 0.91] |
| equal | below 0.89 [0.83, 0.96] | below 0.92 [0.86, 0.98] | below 0.91 [0.85, 0.98] | below 0.89 [0.81, 0.97] | below 0.86 [0.82, 0.90] |
| switch_tail_rev | below 0.39 [0.34, 0.43] | below 0.37 [0.31, 0.43] | below 0.33 [0.23, 0.42] | below 0.25 [0.13, 0.37] | below 0.31 [0.28, 0.33] |
| dev:equal>single | below 0.87 [0.80, 0.94] | below 0.79 [0.70, 0.88] | below 0.88 [0.79, 0.96] | below 0.84 [0.75, 0.94] | below 0.80 [0.76, 0.84] |
| dev:equal>twin | below 0.88 [0.81, 0.95] | below 0.84 [0.77, 0.90] | below 0.87 [0.79, 0.95] | below 0.91 [0.84, 0.98] | below 0.92 [0.88, 0.96] |
| near:equal>single | below 0.91 [0.86, 0.96] | below 0.91 [0.84, 0.98] | below 0.86 [0.78, 0.95] | below 0.89 [0.81, 0.96] | below 0.89 [0.85, 0.93] |
| momentum | below 0.89 [0.82, 0.95] | below 0.87 [0.80, 0.94] | below 0.83 [0.75, 0.92] | below 0.76 [0.65, 0.88] | below 0.88 [0.84, 0.92] |
| switch_tail | below 0.40 [0.36, 0.45] | below 0.37 [0.31, 0.43] | below 0.30 [0.21, 0.39] | below 0.32 [0.19, 0.45] | below 0.33 [0.30, 0.35] |
| sign_switch | boundary 0.97 [0.92, 1.01] | boundary 0.98 [0.93, 1.02] | below 0.93 [0.88, 0.98] | below 0.92 [0.86, 0.98] | below 0.90 [0.86, 0.94] |
| sign_switch_rev | below 0.51 [0.46, 0.56] | below 0.46 [0.39, 0.53] | below 0.43 [0.32, 0.54] | below 0.35 [0.21, 0.48] | below 0.43 [0.40, 0.46] |
| lever_t | below 0.72 [0.66, 0.78] | below 0.80 [0.71, 0.89] | below 0.82 [0.72, 0.92] | below 0.86 [0.77, 0.96] | below 0.81 [0.77, 0.85] |
| lever_t_rev | below 0.57 [0.51, 0.62] | below 0.40 [0.34, 0.47] | below 0.28 [0.19, 0.36] | below 0.21 [0.10, 0.31] | below 0.13 [0.11, 0.14] |
| block_period | below 0.42 [0.37, 0.46] | below 0.38 [0.32, 0.44] | below 0.33 [0.24, 0.43] | below 0.32 [0.19, 0.45] | below 0.32 [0.30, 0.35] |
| block_period_long | below 0.51 [0.46, 0.56] | below 0.51 [0.43, 0.58] | below 0.46 [0.35, 0.57] | below 0.44 [0.33, 0.55] | below 0.42 [0.40, 0.45] |
| dev:equal>switch_tail | boundary 1.01 [0.97, 1.05] | boundary 0.99 [0.95, 1.03] | below 0.95 [0.91, 0.99] | below 0.88 [0.79, 0.97] | below 0.93 [0.89, 0.97] |
| dev:inverse_vol>lever_t_rev | below 0.91 [0.84, 0.97] | below 0.84 [0.75, 0.93] | below 0.80 [0.70, 0.91] | below 0.81 [0.70, 0.91] | below 0.76 [0.73, 0.80] |
| near:equal>switch_tail | below 0.93 [0.89, 0.97] | below 0.91 [0.84, 0.98] | below 0.85 [0.77, 0.94] | below 0.87 [0.78, 0.96] | below 0.89 [0.85, 0.93] |

### equal58

| strategy | 0.045 | 0.045/2 | 0.045/5 | 0.045/10 | 0.045/20 |
|--|--|--|--|--|--|
| sticky | below 0.93 [0.89, 0.98] | below 0.90 [0.83, 0.97] | below 0.85 [0.74, 0.95] | below 0.78 [0.66, 0.90] | below 0.91 [0.87, 0.95] |
| single | below 0.93 [0.88, 0.98] | below 0.95 [0.91, 0.99] | below 0.92 [0.85, 0.98] | below 0.91 [0.84, 0.97] | below 0.91 [0.87, 0.95] |
| fresh | below 0.95 [0.90, 0.99] | boundary 0.96 [0.92, 1.00] | below 0.93 [0.87, 0.98] | below 0.93 [0.88, 0.98] | below 0.94 [0.89, 0.98] |
| inverse_vol | below 0.88 [0.81, 0.96] | below 0.86 [0.76, 0.95] | below 0.76 [0.64, 0.88] | below 0.94 [0.89, 0.98] | below 0.92 [0.88, 0.96] |
| momentum | below 0.91 [0.84, 0.98] | below 0.88 [0.80, 0.96] | below 0.84 [0.73, 0.95] | below 0.90 [0.84, 0.97] | below 0.89 [0.85, 0.93] |
| equal | below 0.94 [0.89, 0.98] | below 0.93 [0.87, 0.98] | below 0.87 [0.77, 0.96] | below 0.86 [0.76, 0.96] | below 0.91 [0.87, 0.95] |
| dev:equal>single | below 0.87 [0.78, 0.96] | below 0.82 [0.72, 0.92] | below 0.79 [0.67, 0.90] | below 0.86 [0.76, 0.96] | below 0.82 [0.78, 0.86] |
| dev:equal>twin | below 0.82 [0.72, 0.93] | below 0.87 [0.77, 0.96] | below 0.82 [0.71, 0.93] | below 0.85 [0.75, 0.96] | below 0.81 [0.77, 0.85] |
| near:equal>single | below 0.89 [0.82, 0.96] | below 0.91 [0.85, 0.98] | below 0.86 [0.76, 0.95] | below 0.83 [0.72, 0.93] | below 0.92 [0.87, 0.96] |
| eigen_low | below 0.78 [0.67, 0.90] | below 0.73 [0.61, 0.86] | below 0.63 [0.50, 0.77] | below 0.69 [0.56, 0.83] | below 0.67 [0.63, 0.70] |
| dev:equal>switch_tail | below 0.76 [0.65, 0.88] | below 0.74 [0.62, 0.87] | below 0.83 [0.72, 0.94] | below 0.88 [0.80, 0.97] | below 0.82 [0.78, 0.86] |
| dev:inverse_vol>lever_t_rev | below 0.88 [0.79, 0.97] | below 0.86 [0.77, 0.96] | below 0.90 [0.83, 0.97] | below 0.87 [0.78, 0.97] | below 0.79 [0.75, 0.82] |
| near:equal>switch_tail | boundary 0.98 [0.94, 1.02] | below 0.94 [0.90, 0.99] | below 0.94 [0.89, 0.98] | below 0.88 [0.80, 0.97] | below 0.90 [0.86, 0.94] |
