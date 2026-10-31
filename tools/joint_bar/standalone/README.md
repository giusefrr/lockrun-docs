# The joint bar, standalone: every number without lockrun's source

**Scope.** Every result here is a result about lockrun's complete procedure (its exposure rules, risk normalization and stopping criterion), measured by simulation under the stated nulls. No theoretical claim about the PSR or the DSR as results is made.

This directory reproduces the numbers of [the joint bar's README](../README.md) with numpy alone. It
does not import lockrun. `joint_rule.py` is the rule and the DSR's evaluation before it, `joint_world.py`
the null markets and the adversaries, `joint_tables.py` one function per table, `run.py` the commands.
Decisions are deterministic in the seeds, whichever BLAS numpy links: a table's count does not depend on the
worker count, the order or the library. An eigenvector's sign is fixed by a positive dot product with a seeded
reference (`joint_world.sign_reference`), and the null-space portfolio is a projection, so no library's choice of
sign or basis enters a strategy. Checked on one ARM Mac, Apple Accelerate against OpenBLAS: every cell of the full
table the same on 8000 fresh seeds and on the first 200, in rate, T_eff and refused. Other machines are checked by
the suite's exact pins, which CI runs on Linux. The counts are identical, not every bit: statistics differ by up to
1.2e-8 between those two libraries, so a t within that distance of a bar could decide differently; on those seeds none did.

lockrun's suite (`tests/test_joint_bar_standalone.py`, `tests/test_rule_variants_parity.py`) runs this copy and
the package on the same seeded inputs under both statistics, the plain t (rule version 2, the default here and in
the product) and `--stat psr` (version 1), and requires identical PASS decisions, statistics, weights and bars, so
the copy cannot drift from either version of the product's rule.

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
| `python run.py finding` | Flat once ahead, under lockrun's procedure before the joint bar | 2 s |
| `python run.py adversaries` | Every variant, before and under the joint bar | 252 s |
| `python run.py adversaries --rows flat,hedge,honest` | Only the rows whose names contain these | about 60 s |
| `python run.py power` | The honest power cost | 1 s |
| `python run.py dropped` | The rules tried and dropped | 54 s |
| `python run.py sizing` | The edge in sizing, the warm-up | under 1 s |
| `python run.py cost` | The calibration's time and memory, one core | 6 min |
| `python run.py assumptions` | Dependence and adaptive exposure rules | 21 min with its tables (11 min of them), 10 min with `--bar-cache` |
| `python run.py all` | Every table | about 32 min |
| `python run.py fixes --only A --out DIR` | The candidates' tables, here A's, each window | about 15 min per window |
| `python run.py targeted --out DIR` | C1 and C2 on the rows that decide them | 83 min |
| `python run.py confirm --out DIR --first-seed 2000 --seeds 8000 --leaders "..."` | Fresh seeds at the stops `fixes` chose | 27 min per configuration |

- `--seeds N`: seeds 0 to N-1 per cell. Full mode, the default, is 2000 (`finding`: 10000, 3000 and 2000 by
  row). `bar`, `sizing` and `cost` take no seeds.
- `--quick`: 200 seeds per cell (50 and 100k-path bars in `assumptions`), a smoke test whose rates are noisy, not the README's numbers. `python run.py all --quick --jobs 2` took 5 min 53 s on this laptop limited to 2 worker processes; it was not timed on a 2-core machine.
- `--stat psr`: on `bar`, `adversaries`, `power` and `assumptions`, rule version 1 (the PSR statistic) instead of
  version 2 (the plain t), the default of every command.
- `--jobs N`: worker processes (default: every core). `--compare`: the README's number beside each, a
  difference flagged. `--json FILE`: the results.

## The rule, version 2: the plain t, window 60, warm-up 20

The default of every command here. z is the plain t-statistic of the returns over their ex-ante risk, with no skew or kurtosis term, and the bar is the sup of that same t on null paths. `--stat psr` gives the rule before, whose statistic has the PSR's denominator. The plain t is lockrun's default as rule version 2 since 30 October 2026; a holdout initialised before keeps version 1, the PSR statistic, which `--stat psr` runs here.

**Above nominal, nominal 0.05: on the first 2000 seeds, at the worst stop per cell, 5 of 288 cells, worst 0.0550 ((3) Trades above 1.5x, floor otherwise, GARCH, n = 2), a figure that carries the selection over stops. That cell is 0.0440 on 8000 fresh seeds at the stop the first 2000 chose. On those fresh seeds no cell of the 288 is above nominal: the worst is 0.0498 ((3) Trades above 3.0x, floor otherwise, GARCH, n = 1), standard error 0.0024.**

| The finding | Version 1: PSR statistic | Version 2: plain t |
|--|--|--|
| Worst cell, 8000 fresh seeds at the stop the first 2000 chose | 0.0858 above nominal | 0.0498 |
| Its row | (2) Trades above 3.0x, floor otherwise, iid, 58 equal assets, n = 2 | (3) Trades above 3.0x, floor otherwise, GARCH, n = 1 |
| That same (2) row, n = 2 | 0.0858 above nominal | 0.0340 |

Worst hedge 0.0208. Worst pause within the budget 0.0372, T_eff at least 101. An honest multi-asset strategy has T_eff 207 and none is refused.

Seeds 2000 to 9999, each cell at the stop the first 2000 seeds chose, so these rates carry no selection over stops; a cell is not re-maximized over stops on the fresh seeds. "First 2000" is seeds 0 to 1999 at the worst stop, which carries that selection. Every holdout gets its df fit and a 2M-path bar, as the product's procedure does. Only 60/20 is confirmed on fresh seeds; the other windows are in the section below, at 2000 seeds.

Commands, version 2: `python run.py fixes --only A --out DIR` (about 15 minutes per window, 2000 seeds), then `python run.py confirm --out DIR --first-seed 2000 --seeds 8000 --leaders "A, window 60, warm-up 20"` (27 minutes).

| True annualized Sharpe | 0 | 1 | 2 | 3 | 4 |
|--|--|--|--|--|--|
| PASS, version 2 (plain t), 8000 fresh seeds | 0.0114 | 0.0890 | 0.3515 | 0.7239 | 0.9356 |
| PASS, version 2 (plain t), first 2000 | 0.0100 | 0.1000 | 0.3325 | 0.6895 | 0.9300 |
| PASS, version 1 (PSR statistic), first 2000 | 0.0100 | 0.0995 | 0.3370 | 0.6905 | 0.9315 |

### The full table on fresh seeds

| Row | Fresh, n = 1 / 2 | First 2000, worst stop | T_eff median | Refused | |
|--|--|--|--|--|--|
| Main: Honest, constant exposure | 0.0130 / 0.0121 | 0.0130 / 0.0105 | 230 / 230 | 0% / 0% |  |
| Main: Honest, 10% random flat days | 0.0136 / 0.0119 | 0.0135 / 0.0095 | 207 / 207 | 0% / 0% |  |
| Main: Flat once ahead | 0.0216 / 0.0156 | 0.0200 / 0.0165 | 230 / 230 | 2% / 0% |  |
| Main: Flat, trading again for the last 1 period | 0.0217 / 0.0160 | 0.0200 / 0.0165 | 230 / 230 | 2% / 0% |  |
| Main: Flat, trading again for the last 2 periods | 0.0217 / 0.0160 | 0.0195 / 0.0165 | 230 / 230 | 2% / 0% |  |
| Main: Flat, trading again for the last 5 periods | 0.0201 / 0.0160 | 0.0165 / 0.0155 | 230 / 230 | 2% / 0% |  |
| Main: Weights times 1e-6 once ahead | 0.0217 / 0.0156 | 0.0205 / 0.0150 | 230 / 230 | 0% / 0% |  |
| Main: Weights times 0.01 once ahead | 0.0217 / 0.0156 | 0.0205 / 0.0150 | 230 / 230 | 0% / 0% |  |
| Main: Weights times 0.05 once ahead | 0.0187 / 0.0141 | 0.0170 / 0.0135 | 230 / 230 | 0% / 0% |  |
| Main: Same gross over every asset, 8 assets | 0.0104 / 0.0112 | 0.0125 / 0.0120 | 230 / 230 | 0% / 0% |  |
| Main: Same gross over every asset, 100 assets | 0.0116 / 0.0095 | 0.0130 / 0.0110 | 230 / 230 | 0% / 0% |  |
| Main: Hedge of two twin assets | 0.0208 / 0.0154 | 0.0195 / 0.0155 | 230 / 230 | 0% / 0% |  |
| Main: Hedge with a drifting ratio | 0.0175 / 0.0144 | 0.0160 / 0.0135 | 230 / 230 | 0% / 0% |  |
| Main: Only the lowest-variance asset | 0.0135 / 0.0111 | 0.0150 / 0.0105 | 230 / 230 | 0% / 0% |  |
| Main: Pausing in the window covariance's null space (100 assets) | 0.0124 / 0.0101 | 0.0140 / 0.0120 | 153 / 153 | 2% / 1% |  |
| Main: An asset whose volatility the window lags (falls tenfold) | 0.0147 / 0.0141 | 0.0180 / 0.0160 | 230 / 230 | 0% / 0% |  |
| Main: Every trial stopping at c(n), n = 1 to 50, normal market | 0.0296 / 0.0311 / 0.0185 / 0.0214 / 0.0213 | 0.0285 / 0.0305 / 0.0270 / 0.0170 / 0.0270 | 230 / 230 / 230 / 230 / 230 | 3% / 1% / 1% / 0% / 0% |  |
| Main: Every trial stopping at c(n), n = 1 to 50, Student-t(4) market | 0.0272 / 0.0301 / 0.0198 / 0.0205 / 0.0185 | 0.0380 / 0.0390 / 0.0170 / 0.0195 / 0.0180 | 230 / 230 / 230 / 230 / 230 | 3% / 1% / 1% / 0% / 0% |  |

### (a) Correlated trials on fresh seeds

n = 1 / 2 / 3 / 5 / 10 / 20.

| Row | Fresh, n as above | First 2000, worst stop | T_eff median | Refused | |
|--|--|--|--|--|--|
| iid, rho = 0.5: honest | 0.0124 / 0.0096 / 0.0074 / 0.0080 / 0.0065 / 0.0059 | 0.0140 / 0.0115 / 0.0100 / 0.0080 / 0.0075 / 0.0065 | 230 / 230 / 230 / 230 / 230 / 230 | 0% / 0% / 0% / 0% / 0% / 0% |  |
| iid, rho = 0.5: flat once ahead | 0.0452 / 0.0408 / 0.0316 / 0.0338 / 0.0348 / 0.0306 | 0.0470 / 0.0430 / 0.0330 / 0.0330 / 0.0345 / 0.0320 | 230 / 230 / 230 / 230 / 230 / 230 | 0% / 0% / 0% / 0% / 0% / 0% |  |
| iid, rho = 0.9: honest | 0.0126 / 0.0077 / 0.0063 / 0.0051 / 0.0037 / 0.0024 | 0.0115 / 0.0075 / 0.0060 / 0.0050 / 0.0020 / 0.0010 | 230 / 230 / 230 / 230 / 230 / 230 | 0% / 0% / 0% / 0% / 0% / 0% |  |
| iid, rho = 0.9: flat once ahead | 0.0435 / 0.0333 / 0.0236 / 0.0201 / 0.0166 / 0.0116 | 0.0465 / 0.0320 / 0.0270 / 0.0260 / 0.0170 / 0.0130 | 230 / 230 / 230 / 230 / 230 / 230 | 0% / 0% / 0% / 0% / 0% / 0% |  |
| one-factor GARCH, rho = 0.5: honest | 0.0116 / 0.0097 / 0.0090 / 0.0100 / 0.0085 / 0.0063 | 0.0135 / 0.0110 / 0.0080 / 0.0050 / 0.0060 / 0.0040 | 230 / 230 / 230 / 230 / 230 / 230 | 0% / 0% / 0% / 0% / 0% / 0% |  |
| one-factor GARCH, rho = 0.5: flat once ahead | 0.0476 / 0.0446 / 0.0362 / 0.0380 / 0.0362 / 0.0329 | 0.0510 / 0.0435 / 0.0275 / 0.0215 / 0.0220 / 0.0210 | 230 / 230 / 230 / 230 / 230 / 230 | 0% / 0% / 0% / 0% / 0% / 0% | first 2000 at the worst stop above nominal: n = 1 |
| one-factor GARCH, rho = 0.9: honest | 0.0121 / 0.0090 / 0.0061 / 0.0051 / 0.0041 / 0.0025 | 0.0125 / 0.0105 / 0.0085 / 0.0065 / 0.0055 / 0.0030 | 230 / 230 / 230 / 230 / 230 / 230 | 0% / 0% / 0% / 0% / 0% / 0% |  |
| one-factor GARCH, rho = 0.9: flat once ahead | 0.0473 / 0.0380 / 0.0312 / 0.0244 / 0.0190 / 0.0147 | 0.0485 / 0.0325 / 0.0245 / 0.0175 / 0.0125 / 0.0100 | 230 / 230 / 230 / 230 / 230 / 230 | 0% / 0% / 0% / 0% / 0% / 0% |  |

### (b) The main table on GARCH markets on fresh seeds

| Row | Fresh, n = 1 / 2 | First 2000, worst stop | T_eff median | Refused | |
|--|--|--|--|--|--|
| GARCH: Honest, constant exposure | 0.0129 / 0.0124 | 0.0115 / 0.0095 | 230 / 230 | 0% / 0% |  |
| GARCH: Honest, 10% random flat days | 0.0139 / 0.0127 | 0.0100 / 0.0085 | 207 / 207 | 0% / 0% |  |
| GARCH: Flat once ahead | 0.0216 / 0.0155 | 0.0150 / 0.0120 | 230 / 230 | 1% / 0% |  |
| GARCH: Flat, trading again for the last 1 period | 0.0216 / 0.0187 | 0.0150 / 0.0145 | 230 / 230 | 1% / 1% |  |
| GARCH: Flat, trading again for the last 2 periods | 0.0216 / 0.0182 | 0.0145 / 0.0150 | 230 / 230 | 1% / 1% |  |
| GARCH: Flat, trading again for the last 5 periods | 0.0210 / 0.0158 | 0.0135 / 0.0150 | 230 / 230 | 1% / 1% |  |
| GARCH: Weights times 1e-6 once ahead | 0.0219 / 0.0139 | 0.0175 / 0.0140 | 230 / 230 | 0% / 0% |  |
| GARCH: Weights times 0.01 once ahead | 0.0219 / 0.0140 | 0.0175 / 0.0140 | 230 / 230 | 0% / 0% |  |
| GARCH: Weights times 0.05 once ahead | 0.0161 / 0.0168 | 0.0150 / 0.0140 | 230 / 230 | 0% / 0% |  |
| GARCH: Same gross over every asset, 8 assets | 0.0132 / 0.0115 | 0.0140 / 0.0140 | 230 / 230 | 0% / 0% |  |
| GARCH: Same gross over every asset, 100 assets | 0.0109 / 0.0089 | 0.0135 / 0.0130 | 230 / 230 | 0% / 0% |  |
| GARCH: Hedge of two twin assets | 0.0105 / 0.0145 | 0.0145 / 0.0125 | 230 / 230 | 0% / 0% |  |
| GARCH: Hedge with a drifting ratio | 0.0174 / 0.0136 | 0.0160 / 0.0100 | 230 / 230 | 0% / 0% |  |
| GARCH: Only the lowest-variance asset | 0.0135 / 0.0107 | 0.0155 / 0.0135 | 230 / 230 | 0% / 0% |  |
| GARCH: Pausing in the window covariance's null space (100 assets) | 0.0112 / 0.0104 | 0.0160 / 0.0110 | 153 / 153 | 2% / 1% |  |
| GARCH: An asset whose volatility the window lags (falls tenfold) | 0.0163 / 0.0118 | 0.0175 / 0.0190 | 230 / 230 | 0% / 0% |  |
| GARCH: Every trial stopping, n = 1 to 50 | 0.0318 / 0.0352 / 0.0214 / 0.0217 / 0.0215 | 0.0275 / 0.0320 / 0.0200 / 0.0210 / 0.0185 | 230 / 230 / 230 / 230 / 230 | 3% / 1% / 1% / 0% / 0% |  |
| One-factor GARCH: Honest, constant exposure | 0.0134 / 0.0120 | 0.0120 / 0.0125 | 230 / 230 | 0% / 0% |  |
| One-factor GARCH: Honest, 10% random flat days | 0.0140 / 0.0118 | 0.0125 / 0.0105 | 207 / 207 | 0% / 0% |  |
| One-factor GARCH: Flat once ahead | 0.0208 / 0.0176 | 0.0170 / 0.0160 | 230 / 230 | 2% / 0% |  |
| One-factor GARCH: Flat, trading again for the last 1 period | 0.0208 / 0.0132 | 0.0165 / 0.0165 | 230 / 230 | 2% / 2% |  |
| One-factor GARCH: Flat, trading again for the last 2 periods | 0.0204 / 0.0165 | 0.0155 / 0.0170 | 230 / 230 | 2% / 2% |  |
| One-factor GARCH: Flat, trading again for the last 5 periods | 0.0191 / 0.0139 | 0.0155 / 0.0155 | 230 / 230 | 1% / 1% |  |
| One-factor GARCH: Weights times 1e-6 once ahead | 0.0216 / 0.0169 | 0.0190 / 0.0165 | 230 / 230 | 0% / 0% |  |
| One-factor GARCH: Weights times 0.01 once ahead | 0.0215 / 0.0169 | 0.0185 / 0.0165 | 230 / 230 | 0% / 0% |  |
| One-factor GARCH: Weights times 0.05 once ahead | 0.0166 / 0.0136 | 0.0165 / 0.0140 | 230 / 230 | 0% / 0% |  |
| One-factor GARCH: Same gross over every asset, 8 assets | 0.0125 / 0.0120 | 0.0145 / 0.0120 | 230 / 230 | 0% / 0% |  |
| One-factor GARCH: Same gross over every asset, 100 assets | 0.0114 / 0.0089 | 0.0180 / 0.0145 | 230 / 230 | 0% / 0% |  |
| One-factor GARCH: Hedge of two twin assets | 0.0206 / 0.0158 | 0.0170 / 0.0170 | 230 / 230 | 0% / 0% |  |
| One-factor GARCH: Hedge with a drifting ratio | 0.0170 / 0.0143 | 0.0145 / 0.0150 | 230 / 230 | 0% / 0% |  |
| One-factor GARCH: Only the lowest-variance asset | 0.0114 / 0.0121 | 0.0170 / 0.0130 | 230 / 230 | 0% / 0% |  |
| One-factor GARCH: Pausing in the window covariance's null space (100 assets) | 0.0096 / 0.0094 | 0.0125 / 0.0125 | 153 / 153 | 2% / 1% |  |
| One-factor GARCH: An asset whose volatility the window lags (falls tenfold) | 0.0141 / 0.0123 | 0.0125 / 0.0115 | 230 / 230 | 0% / 0% |  |
| One-factor GARCH: Every trial stopping, n = 1 to 50 | 0.0290 / 0.0299 / 0.0210 / 0.0205 / 0.0185 | 0.0270 / 0.0280 / 0.0180 / 0.0170 / 0.0250 | 230 / 230 / 230 / 230 / 230 | 3% / 1% / 0% / 0% / 0% |  |

### (c) Adversaries with the estimator's state on fresh seeds

| Row | Fresh, n = 1 / 2 | First 2000, worst stop | T_eff median | Refused | |
|--|--|--|--|--|--|
| (1) Window's smallest eigenvalue, iid | 0.0396 / 0.0418 | 0.0450 / 0.0435 | 230 / 230 | 0% / 0% |  |
| (1) Direction most underestimated, iid | 0.0436 / 0.0442 | 0.0495 / 0.0435 | 230 / 230 | 0% / 0% |  |
| (1) Window's smallest eigenvalue, iid, 30 equal assets | 0.0253 / 0.0254 | 0.0240 / 0.0265 | 228 / 228 | 0% / 0% |  |
| (1) Direction most underestimated, iid, 30 equal assets | 0.0253 / 0.0254 | 0.0240 / 0.0265 | 228 / 228 | 0% / 0% |  |
| (1) Window's smallest eigenvalue, iid, 50 equal assets | 0.0414 / 0.0380 | 0.0440 / 0.0390 | 230 / 230 | 0% / 0% |  |
| (1) Direction most underestimated, iid, 50 equal assets | 0.0414 / 0.0380 | 0.0440 / 0.0390 | 230 / 230 | 0% / 0% |  |
| (1) Window's smallest eigenvalue, iid, 58 equal assets | 0.0444 / 0.0414 | 0.0450 / 0.0370 | 228 / 228 | 0% / 0% |  |
| (1) Direction most underestimated, iid, 58 equal assets | 0.0444 / 0.0414 | 0.0450 / 0.0370 | 228 / 228 | 0% / 0% |  |
| (1) Window's smallest eigenvalue, GARCH | 0.0462 / 0.0460 | 0.0415 / 0.0490 | 230 / 230 | 0% / 0% |  |
| (1) Direction most underestimated, GARCH | 0.0467 / 0.0450 | 0.0525 / 0.0530 | 230 / 230 | 0% / 0% | first 2000 at the worst stop above nominal: n = 1, n = 2 |
| (1) Window's smallest eigenvalue, GARCH, 50 assets | 0.0281 / 0.0244 | 0.0225 / 0.0200 | 230 / 230 | 0% / 0% |  |
| (1) Direction most underestimated, GARCH, 50 assets | 0.0362 / 0.0362 | 0.0375 / 0.0390 | 229 / 230 | 0% / 0% |  |
| (1) Window's smallest eigenvalue, one-factor GARCH | 0.0446 / 0.0457 | 0.0470 / 0.0505 | 230 / 230 | 0% / 0% | first 2000 at the worst stop above nominal: n = 2 |
| (1) Direction most underestimated, one-factor GARCH | 0.0479 / 0.0449 | 0.0490 / 0.0500 | 230 / 230 | 0% / 0% |  |
| (2) Trades above 1.5x, floor otherwise, iid | 0.0425 / 0.0404 | 0.0435 / 0.0415 | 230 / 230 | 0% / 0% | traded 39% of steps |
| (2) Trades above 2.0x, floor otherwise, iid | 0.0467 / 0.0444 | 0.0465 / 0.0450 | 230 / 230 | 0% / 0% | traded 3% of steps |
| (2) Trades above 3.0x, floor otherwise, iid | 0.0483 / 0.0486 | 0.0485 / 0.0450 | 230 / 230 | 0% / 0% | traded 0% of steps |
| (2) Trades above 1.5x, floor otherwise, iid, 30 equal assets | 0.0185 / 0.0139 | 0.0120 / 0.0130 | 230 / 230 | 0% / 0% | traded 100% of steps |
| (2) Trades above 2.0x, floor otherwise, iid, 30 equal assets | 0.0185 / 0.0139 | 0.0120 / 0.0130 | 230 / 230 | 0% / 0% | traded 100% of steps |
| (2) Trades above 3.0x, floor otherwise, iid, 30 equal assets | 0.0152 / 0.0120 | 0.0095 / 0.0125 | 230 / 230 | 0% / 0% | traded 71% of steps |
| (2) Trades above 1.5x, floor otherwise, iid, 50 equal assets | 0.0310 / 0.0293 | 0.0340 / 0.0290 | 230 / 230 | 0% / 0% | traded 99% of steps |
| (2) Trades above 2.0x, floor otherwise, iid, 50 equal assets | 0.0304 / 0.0290 | 0.0355 / 0.0305 | 230 / 230 | 0% / 0% | traded 98% of steps |
| (2) Trades above 3.0x, floor otherwise, iid, 50 equal assets | 0.0311 / 0.0293 | 0.0375 / 0.0325 | 230 / 230 | 0% / 0% | traded 95% of steps |
| (2) Trades above 1.5x, floor otherwise, iid, 58 equal assets | 0.0428 / 0.0346 | 0.0430 / 0.0380 | 230 / 230 | 0% / 0% | traded 98% of steps |
| (2) Trades above 2.0x, floor otherwise, iid, 58 equal assets | 0.0429 / 0.0345 | 0.0435 / 0.0380 | 230 / 230 | 0% / 0% | traded 96% of steps |
| (2) Trades above 3.0x, floor otherwise, iid, 58 equal assets | 0.0430 / 0.0340 | 0.0430 / 0.0370 | 230 / 230 | 0% / 0% | traded 93% of steps |
| (3) Trades above 1.5x, floor otherwise, GARCH | 0.0426 / 0.0440 | 0.0480 / 0.0550 | 230 / 230 | 0% / 0% | first 2000 at the worst stop above nominal: n = 2; traded 82% of steps |
| (3) Trades above 2.0x, floor otherwise, GARCH | 0.0429 / 0.0452 | 0.0490 / 0.0490 | 230 / 230 | 0% / 0% | traded 10% of steps |
| (3) Trades above 3.0x, floor otherwise, GARCH | 0.0498 / 0.0490 | 0.0485 / 0.0495 | 230 / 230 | 0% / 0% | traded 0% of steps |
| (3) Trades above 1.5x, floor otherwise, GARCH, 50 assets | 0.0285 / 0.0259 | 0.0295 / 0.0275 | 230 / 230 | 0% / 0% | traded 100% of steps |
| (3) Trades above 2.0x, floor otherwise, GARCH, 50 assets | 0.0285 / 0.0261 | 0.0290 / 0.0275 | 230 / 230 | 0% / 0% | traded 98% of steps |
| (3) Trades above 3.0x, floor otherwise, GARCH, 50 assets | 0.0286 / 0.0259 | 0.0295 / 0.0280 | 230 / 230 | 0% / 0% | traded 95% of steps |
| (3) Trades above 1.5x, floor otherwise, one-factor GARCH | 0.0451 / 0.0429 | 0.0405 / 0.0410 | 230 / 230 | 0% / 0% | traded 65% of steps |
| (3) Trades above 2.0x, floor otherwise, one-factor GARCH | 0.0419 / 0.0396 | 0.0410 / 0.0430 | 230 / 230 | 0% / 0% | traded 5% of steps |
| (3) Trades above 3.0x, floor otherwise, one-factor GARCH | 0.0481 / 0.0464 | 0.0400 / 0.0395 | 230 / 230 | 0% / 0% | traded 0% of steps |
| (1) Window's smallest eigenvalue, iid, 20 equal assets | 0.0331 / 0.0286 | 0.0380 / 0.0320 | 229 / 229 | 0% / 0% |  |
| (1) Direction most underestimated, iid, 20 equal assets | 0.0331 / 0.0286 | 0.0380 / 0.0320 | 229 / 229 | 0% / 0% |  |
| (2) Trades above 1.5x, floor otherwise, iid, 20 equal assets | 0.0190 / 0.0161 | 0.0220 / 0.0165 | 230 / 230 | 0% / 0% | traded 100% of steps |
| (2) Trades above 2.0x, floor otherwise, iid, 20 equal assets | 0.0175 / 0.0150 | 0.0210 / 0.0155 | 230 / 230 | 0% / 0% | traded 88% of steps |
| (2) Trades above 3.0x, floor otherwise, iid, 20 equal assets | 0.0096 / 0.0073 | 0.0085 / 0.0065 | 230 / 230 | 0% / 0% | traded 9% of steps |
| (1) Window's smallest eigenvalue, iid, 45 equal assets | 0.0372 / 0.0319 | 0.0265 / 0.0295 | 229 / 229 | 0% / 0% |  |
| (1) Direction most underestimated, iid, 45 equal assets | 0.0372 / 0.0319 | 0.0265 / 0.0295 | 229 / 229 | 0% / 0% |  |
| (2) Trades above 1.5x, floor otherwise, iid, 45 equal assets | 0.0245 / 0.0196 | 0.0175 / 0.0200 | 230 / 230 | 0% / 0% | traded 100% of steps |
| (2) Trades above 2.0x, floor otherwise, iid, 45 equal assets | 0.0245 / 0.0196 | 0.0180 / 0.0205 | 230 / 230 | 0% / 0% | traded 99% of steps |
| (2) Trades above 3.0x, floor otherwise, iid, 45 equal assets | 0.0240 / 0.0189 | 0.0180 / 0.0185 | 230 / 230 | 0% / 0% | traded 96% of steps |
| (1) Window's smallest eigenvalue, iid, 50 equal assets with twins | 0.0216 / 0.0210 | 0.0220 / 0.0200 | 230 / 230 | 0% / 0% |  |
| (1) Direction most underestimated, iid, 50 equal assets with twins | 0.0394 / 0.0366 | 0.0460 / 0.0365 | 229 / 229 | 0% / 0% |  |
| (2) Trades above 1.5x, floor otherwise, iid, 50 equal assets with twins | 0.0324 / 0.0300 | 0.0340 / 0.0295 | 230 / 230 | 0% / 0% | traded 99% of steps |
| (2) Trades above 2.0x, floor otherwise, iid, 50 equal assets with twins | 0.0320 / 0.0299 | 0.0360 / 0.0285 | 230 / 230 | 0% / 0% | traded 98% of steps |
| (2) Trades above 3.0x, floor otherwise, iid, 50 equal assets with twins | 0.0325 / 0.0294 | 0.0365 / 0.0285 | 230 / 230 | 0% / 0% | traded 95% of steps |

### (d) Pauses within the budget on fresh seeds

| Row | Fresh, n = 1 / 2 | First 2000, worst stop | T_eff median | Refused | |
|--|--|--|--|--|--|
| Pauses after each losing step, iid | 0.0361 / 0.0356 | 0.0375 / 0.0345 | 153 / 153 | 0% / 0% |  |
| Pauses while behind, iid | 0.0199 / 0.0196 | 0.0235 / 0.0240 | 101 / 101 | 0% / 0% |  |
| Pauses where the window overestimates, iid | 0.0274 / 0.0250 | 0.0220 / 0.0195 | 120 / 120 | 0% / 0% |  |
| Pauses after each losing step, iid, 50 equal assets | 0.0345 / 0.0333 | 0.0305 / 0.0275 | 153 / 153 | 0% / 0% |  |
| Pauses while behind, iid, 50 equal assets | 0.0216 / 0.0215 | 0.0225 / 0.0245 | 101 / 101 | 0% / 0% |  |
| Pauses where the window overestimates, iid, 50 equal assets | 0.0241 / 0.0221 | 0.0225 / 0.0265 | 120 / 121 | 0% / 0% |  |
| Pauses after each losing step, GARCH | 0.0372 / 0.0349 | 0.0330 / 0.0375 | 153 / 153 | 0% / 0% |  |
| Pauses while behind, GARCH | 0.0244 / 0.0236 | 0.0250 / 0.0250 | 101 / 101 | 0% / 0% |  |
| Pauses where the window overestimates, GARCH | 0.0295 / 0.0296 | 0.0285 / 0.0265 | 134 / 134 | 0% / 0% |  |
| Pauses after each losing step, one-factor GARCH | 0.0341 / 0.0354 | 0.0360 / 0.0355 | 153 / 153 | 0% / 0% |  |
| Pauses while behind, one-factor GARCH | 0.0246 / 0.0238 | 0.0140 / 0.0140 | 101 / 101 | 0% / 0% |  |
| Pauses where the window overestimates, one-factor GARCH | 0.0288 / 0.0283 | 0.0235 / 0.0220 | 132 / 132 | 0% / 0% |  |

## Tried and dropped: the B and C candidates

Candidates to the plain t alone (A), measured as the rule would run them, none of them in the rule. Reading a row: seeds 0 to 1999, the worst stop per cell, so a cell near 0.05 carries that selection.

| Candidate at 60/20 | Worst cell | Its row, n | Cells above nominal | Worst hedge | Worst pause (least T_eff) | Honest T_eff, refused | Cells fully refused |
|--|--|--|--|--|--|--|--|
| A | 0.0550 above nominal | (3) Trades above 1.5x, floor otherwise, GARCH, 2 | 5 of 288 | 0.0195 | 0.0375 (101) | 207, 0% | 0 |
| A + B1 | 0.0565 above nominal | (1) Direction most underestimated, GARCH, 2 | 18 of 288 | 0.0465 | 0.0380 (101) | 207, 0% | 0 |
| A + B2 | 0.0515 above nominal | one-factor GARCH, rho = 0.5: flat once ahead, 1 | 2 of 288 | 0.0180 | 0.0395 (100) | 203, 0% | 22 |
| A + B3 | 0.0545 above nominal | (1) Window's smallest eigenvalue, iid, 45 equal assets, 2 | 5 of 288 | 0.0000 | 0.0175 (0) | 0, 100% | 242 |

- **B1, shrinkage toward the diagonal at the estimator's intensity:** more cells above nominal than A, and the hedge close to nominal: shrinking gives a twin hedge some of its excess back.
- **B2, a window and warm-up of at least 3 times the held assets:** refusal. Universes that do not fit are refused outright, 22 cells in full, and the longer warm-up takes up the pause budget.
- **B3, a step whose smallest window eigenvalue is under 1% of the median is inactive:** refusal. Its low rates are not detection: every honest multi-asset strategy has T_eff 0 and is refused, and 242 cells are refused in full.

| Worst cell by window, warm-up (cells above nominal) | 60, 20 | 20, 20 | 120, 20 | 250, 20 | 60, 60 |
|--|--|--|--|--|--|
| A | 0.0550 (5) | 0.0615 (28) | 0.0520 (3) | 0.0500 (0) | 0.0505 (1) |
| A + B1 | 0.0565 (18) | 0.0580 (27) | 0.0615 (27) | 0.0635 (25) | 0.0500 (0) |
| A + B2 | 0.0515 (2) | 0.0545 (5) | 0.0525 (1) | 0.0510 (1) | 0.0505 (1) |
| A + B3 | 0.0545 (5) | 0.0000 (0) | 0.0335 (0) | 0.0335 (0) | 0.0440 (0) |
| Power at Sharpe 3, A | 0.6895 | 0.6815 | 0.6875 | 0.6900 | 0.6020 |

A at 60/60 reads lower, at a cost in power: T_eff falls to about 190 while the bar stays the one for T = 250. A at 20/20 has the most cells above nominal. A at 250/20 has none on these 2000 seeds, its worst exactly 0.05; only 60/20 has fresh seeds behind it.

The C candidates bound one normalized return. C1: a risk under f times the median of the strategy's risks above 0 is raised to it and stays active; no estimate or zero risk stays inactive. C2: each normalized return clipped to [-k, k], the bar calibrated on unit-variance null draws clipped at the same k before the sup. They were measured at 60/20 on 67 rows (`python run.py targeted --out DIR`, 83 minutes): the rows then above nominal under A and under the PSR statistic, the hedges, the pauses and two groups aimed at the bounds. The list predates the eigenvectors' fixed sign, so it does not hold 1 of A's 5 cells now above nominal at the worst stop ((3) Trades above 1.5x, floor otherwise, GARCH, n = 2). None closed the rows it does hold, so none went to the full table or the window sweep.

| Candidate, 67 rows | Worst cell | Its row, n | Cells above nominal | Worst hedge | Worst pause | Worst pause at tiny weights (least T_eff) |
|--|--|--|--|--|--|--|
| A | 0.0535 above nominal | (1) Direction most underestimated at constant estimated risk, GARCH, 2 | 7 of 138 | 0.0195 | 0.0375 | 0.0265 (116) |
| A + C1 f=0.25 | 0.0535 above nominal | (1) Direction most underestimated, GARCH, 1 | 7 of 138 | 0.0185 | 0.0375 | 0.0505 above nominal (230) |
| A + C1 f=0.5 | 0.0535 above nominal | (1) Direction most underestimated, GARCH, 2 | 6 of 138 | 0.0190 | 0.0345 | 0.0470 (230) |
| A + C2 k=3 | 0.0605 above nominal | (1) Window's smallest eigenvalue at constant estimated risk, iid, 50 equal assets, 1 | 30 of 138 | 0.0210 | 0.0365 | 0.0225 (116) |
| A + C2 k=4 | 0.0620 above nominal | (2) Trades above 2.0x, floor otherwise, iid, 50 equal assets, 1 | 39 of 138 | 0.0195 | 0.0375 | 0.0260 (116) |
| A + C2 k=5 | 0.0620 above nominal | (1) Window's smallest eigenvalue at constant estimated risk, GARCH, 50 assets, 1 | 42 of 138 | 0.0195 | 0.0375 | 0.0260 (116) |
| A + C1 f=0.5 + C2 k=4 | 0.0625 above nominal | (2) Trades above 2.0x, floor otherwise, iid, 50 equal assets, 1 | 38 of 138 | 0.0205 | 0.0330 | 0.0470 (230) |

- **C1, a free pause:** its worst cell is A's, 0.0535, and a strategy that scales to one estimated risk has no step under the floor. A pause at tiny weights is raised, not excluded, so it counts toward T_eff: T_eff 230 where it was 116 to 153, and the worst such row reaches 0.0505 at f = 0.25.
- **C2, a clip that removes a protection:** cells above nominal rise from 7 to 30 or more. The ex-ante sd of 1 fails where these adversaries aim: on 150 seeds of attack (2) at 3.0x on 58 equal assets the median absolute normalized return is 26, and 81% to 85% of the returns hit the clip. Unclipped, its huge outliers leave an effective sample of about 9; clipped at 5, about 200. That reading of why the rate rises is not tested on its own.

## The numbers full mode produced

On a 10-core Apple Silicon laptop, numpy 2.5.3, 30 October 2026. Seeds 0 to N-1, N as stated; a cell is
the worst over its stopping rule (c from 1.5 to 3.5, first stop at period 2, 3, 20 or 100).

    Version 2, plain t:       c(1) 2.277  c(2) 2.585  c(5) 2.949  c(10) 3.193  c(50) 3.713  c(100) 3.927  c(1000) 4.530
    Version 1, PSR statistic: c(1) 2.252  c(2) 2.552  c(5) 2.906  c(10) 3.146  c(50) 3.662  c(100) 3.854  c(1000) 4.418

| Strategy (null market, T = 250) | N | PASS under the DSR | Seeds | c, k0 |
|--|--|--|--|--|
| Honest: constant exposure, never stops | 1 | 0.0152 | 10000 | |
| Flat once its t-statistic reaches c (best c and first stop k0) | 1 | 0.2680 | 3000 | 2.0, 2 |
| Flat once its t-statistic reaches c (best c and first stop k0) | 2 | 0.0817 | 3000 | 2.5, 3 |
| The same, trading again for the last period | 1 | 0.1720 | 2000 | 2.0, 2 |
| The same, weights times 1e-6 instead of zero | 1 | 0.2710 | 2000 | 2.0, 2 |

2000 seeds per cell:

| Researcher strategy | DSR, before the joint bar (n = 1 / 2) | Joint bar, version 1: PSR statistic (n = 1 / 2) | Joint bar, version 2: plain t (n = 1 / 2) |
|--|--|--|--|
| Honest, constant exposure | 0.0115 / 0.0020 | 0.0135 / 0.0105 | 0.0130 / 0.0105 |
| Honest, 10% random flat days | 0.0140 / 0.0020 | 0.0140 / 0.0100 | 0.0135 / 0.0095 |
| Flat once ahead | 0.2570 / 0.0705 | 0.0205 / 0.0160 | 0.0200 / 0.0165 |
| Flat, trading again for the last 1 period | 0.1640 / 0.0890 | 0.0205 / 0.0160 | 0.0200 / 0.0165 |
| Flat, trading again for the last 2 periods | 0.1195 / 0.0740 | 0.0200 / 0.0155 | 0.0195 / 0.0165 |
| Flat, trading again for the last 5 periods | 0.0830 / 0.0480 | 0.0175 / 0.0145 | 0.0165 / 0.0155 |
| Weights times 1e-6 once ahead | 0.2570 / 0.0705 | 0.0210 / 0.0145 | 0.0205 / 0.0150 |
| Weights times 0.01 once ahead | 0.2000 / 0.0680 | 0.0210 / 0.0145 | 0.0205 / 0.0150 |
| Weights times 0.05 once ahead | 0.1115 / 0.0390 | 0.0175 / 0.0130 | 0.0170 / 0.0135 |
| Same gross over every asset, 8 assets | 0.0140 / 0.0035 | 0.0130 / 0.0115 | 0.0125 / 0.0120 |
| Same gross over every asset, 100 assets | 0.0165 / 0.0045 | 0.0130 / 0.0105 | 0.0130 / 0.0110 |
| Hedge of two twin assets | 0.1290 / 0.0440 | 0.0205 / 0.0150 | 0.0195 / 0.0155 |
| Hedge with a drifting ratio | 0.0835 / 0.0285 | 0.0165 / 0.0130 | 0.0160 / 0.0135 |
| Only the lowest-variance asset | 0.0350 / 0.0075 | 0.0150 / 0.0105 | 0.0145 / 0.0105 |
| Pausing in the window covariance's null space (100 assets) | not run | 0.0135 / 0.0115 | 0.0140 / 0.0120 |
| An asset whose volatility the window lags (falls tenfold) | not run | 0.0200 / 0.0175 | 0.0180 / 0.0150 |
| Every trial stopping at c(n), n = 1 to 50, normal market | not run | at most 0.0205 over every stopping rule tried (0.0200 at the c(n) stop) | at most 0.0295 |
| Every trial stopping at c(n), n = 1 to 50, Student-t(4) market | not run | at most 0.0280 | at most 0.0385 |

| True annualized Sharpe | 0 | 1 | 2 | 3 | 4 |
|--|--|--|--|--|--|
| PASS before (DSR) | 0.015 | 0.119 | 0.413 | 0.775 | 0.962 |
| PASS with the joint bar, version 1 (PSR statistic) | 0.010 | 0.099 | 0.337 | 0.690 | 0.931 |
| PASS with the joint bar, version 2 (plain t) | 0.010 | 0.099 | 0.331 | 0.688 | 0.930 |

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

## The rule before, version 1: the assumptions table under the PSR statistic

Everything from here is `--stat psr`, rule version 1, where the excess was found.

**Above nominal, nominal 0.05: an adversary that sets the whole gross in the direction the window most underestimates, with every step kept active, passes at up to 0.0900 (n = 2, 2000 seeds), 0.0858 on 8000 fresh seeds at the stop the first 2000 chose (22 of 70 of these cells above nominal there), and 0.0905 at a window of 120 or 250.** Dependence (at most 0.0345), GARCH markets replaying every row of the main table (at most 0.0210) and pauses within the budget (at most 0.0310) stay below nominal.

Why, in these runs of lockrun's procedure: version 1's excess came from the denominator of the statistic as this procedure computes it on its normalized returns, not from the bar or the risk estimate's mean. With a universe close to the window, the smallest eigenvalue is close to zero on some steps, so one step's normalized return is about 25 to 36 times the median, the largest of a run at the median run (factor 1.5 and 3.0). A positive one gives the series large skew, and sqrt(1 - skew sr + (kurt - 1)/4 sr^2) falls well below 1: on attack (2) with no stop, runs that pass have a median t-statistic of 1.60 to 2.07, under the bar of about 2.25, and a median of that term of 0.58 to 0.78 (0.93 to 0.97 over all runs). With no stop at factor 1.5, on 1500 seeds and a 100k-path bar, z passes at 0.034 (58 assets) and 0.041 (30 assets) while the t-statistic against the same bar passes at 0.011 and 0.004. A scale alone changes no normalized return, so the (2) rows exceed the (1) rows only because scaling keeps those steps above the 10% floor.

Command: `python standalone/run.py assumptions --stat psr` (version 1), with `--parts a,b,c,d`, `--rows`, `--window`, `--warmup` and `--first-seed`; no lockrun needed. Each holdout gets the product's own procedure: its df fitted on its residuals, its bar from 2M paths, seed 20261027 (174 distinct dfs in the table, each exactly the calibration that holdout would get). 2000 seeds, 0 to 1999, unless stated. A cell is the worst over its stops, so a cell near 0.05 carries that selection; the fresh seeds below do not. T_eff is the first trial's median at that stop; "refused" is the share of runs under min_t. Rows above nominal say so.

### Confirmed on fresh seeds

Seeds 2000 to 9999, 8000 of them, each row at the stop the first 2000 seeds chose, so these rates carry no selection (standard error about 0.003).

| Fresh seeds, at the stop the first 2000 chose: | n = 1 / 2 | |
|--|--|--|
| Fresh: (1) Window's smallest eigenvalue, iid | 0.0278 / 0.0301 |  |
| Fresh: (1) Direction most underestimated, iid | 0.0315 / 0.0318 |  |
| Fresh: (1) Window's smallest eigenvalue, iid, 30 equal assets | 0.0318 / 0.0351 |  |
| Fresh: (1) Direction most underestimated, iid, 30 equal assets | 0.0318 / 0.0351 |  |
| Fresh: (1) Window's smallest eigenvalue, iid, 50 equal assets | 0.0432 / 0.0428 |  |
| Fresh: (1) Direction most underestimated, iid, 50 equal assets | 0.0432 / 0.0428 |  |
| Fresh: (1) Window's smallest eigenvalue, iid, 58 equal assets | 0.0530 / 0.0550 | above nominal |
| Fresh: (1) Direction most underestimated, iid, 58 equal assets | 0.0530 / 0.0550 | above nominal |
| Fresh: (1) Window's smallest eigenvalue, GARCH | 0.0251 / 0.0220 |  |
| Fresh: (1) Direction most underestimated, GARCH | 0.0297 / 0.0255 |  |
| Fresh: (1) Window's smallest eigenvalue, GARCH, 50 assets | 0.0391 / 0.0479 |  |
| Fresh: (1) Direction most underestimated, GARCH, 50 assets | 0.0285 / 0.0271 |  |
| Fresh: (1) Window's smallest eigenvalue, one-factor GARCH | 0.0276 / 0.0240 |  |
| Fresh: (1) Direction most underestimated, one-factor GARCH | 0.0348 / 0.0299 |  |
| Fresh: (2) Trades above 1.5x, floor otherwise, iid | 0.0326 / 0.0343 |  |
| Fresh: (2) Trades above 2.0x, floor otherwise, iid | 0.0370 / 0.0357 |  |
| Fresh: (2) Trades above 3.0x, floor otherwise, iid | 0.0359 / 0.0357 |  |
| Fresh: (2) Trades above 1.5x, floor otherwise, iid, 30 equal assets | 0.0620 / 0.0770 | above nominal |
| Fresh: (2) Trades above 2.0x, floor otherwise, iid, 30 equal assets | 0.0620 / 0.0770 | above nominal |
| Fresh: (2) Trades above 3.0x, floor otherwise, iid, 30 equal assets | 0.0634 / 0.0784 | above nominal |
| Fresh: (2) Trades above 1.5x, floor otherwise, iid, 50 equal assets | 0.0531 / 0.0681 | above nominal |
| Fresh: (2) Trades above 2.0x, floor otherwise, iid, 50 equal assets | 0.0532 / 0.0671 | above nominal |
| Fresh: (2) Trades above 3.0x, floor otherwise, iid, 50 equal assets | 0.0521 / 0.0669 | above nominal |
| Fresh: (2) Trades above 1.5x, floor otherwise, iid, 58 equal assets | 0.0754 / 0.0854 | above nominal |
| Fresh: (2) Trades above 2.0x, floor otherwise, iid, 58 equal assets | 0.0751 / 0.0855 | above nominal |
| Fresh: (2) Trades above 3.0x, floor otherwise, iid, 58 equal assets | 0.0755 / 0.0858 | above nominal |
| Fresh: (3) Trades above 1.5x, floor otherwise, GARCH | 0.0281 / 0.0270 |  |
| Fresh: (3) Trades above 2.0x, floor otherwise, GARCH | 0.0307 / 0.0301 |  |
| Fresh: (3) Trades above 3.0x, floor otherwise, GARCH | 0.0340 / 0.0304 |  |
| Fresh: (3) Trades above 1.5x, floor otherwise, GARCH, 50 assets | 0.0386 / 0.0478 |  |
| Fresh: (3) Trades above 2.0x, floor otherwise, GARCH, 50 assets | 0.0385 / 0.0473 |  |
| Fresh: (3) Trades above 3.0x, floor otherwise, GARCH, 50 assets | 0.0380 / 0.0475 |  |
| Fresh: (3) Trades above 1.5x, floor otherwise, one-factor GARCH | 0.0333 / 0.0296 |  |
| Fresh: (3) Trades above 2.0x, floor otherwise, one-factor GARCH | 0.0324 / 0.0300 |  |
| Fresh: (3) Trades above 3.0x, floor otherwise, one-factor GARCH | 0.0369 / 0.0336 |  |

On equal assets attack (2) is above nominal at 30, 50 and 58 assets, and attack (1) at 58, at n = 1 and n = 2. At 50 assets on GARCH every cell is below nominal, at most 0.0479.

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
| GARCH: Pausing in the window covariance's null space (100 assets) | 0.0115 / 0.0085 | 153 / 154 | 2% / 1% |  |
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
| One-factor GARCH: Pausing in the window covariance's null space (100 assets) | 0.0135 / 0.0115 | 153 / 153 | 2% / 0% |  |
| One-factor GARCH: An asset whose volatility the window lags (falls tenfold) | 0.0130 / 0.0120 | 230 / 230 | 0% / 0% |  |

| Every trial stopping, each holdout its own bar | n = 1 | n = 2 | n = 5 | n = 10 | n = 50 |
|--|--|--|--|--|--|
| GARCH | 0.0210 | 0.0180 | 0.0125 | 0.0095 | 0.0065 |
| One-factor GARCH | 0.0205 | 0.0180 | 0.0165 | 0.0105 | 0.0145 |

### (c) Adversaries with the estimator's state

Rebalanced every step, a random sign each step, stops from the grid and at c(n) and c(n) + 0.3, only with more than min_t active steps. (1) The whole gross in the window's smallest non-null eigenvalue's direction, or in the direction minimizing w' S w / w' Sigma w, with Sigma the true covariance, known before the step. (2) That direction, at a fixed risk, only where true risk exceeds estimated risk by the factor; elsewhere random weights at 10% of that risk, so every step stays active. (3) The same on GARCH markets, timed on the conditional volatility. The twins make a hedge the smallest eigenvalue at 8 assets; the equal-asset markets have none, and there the window's error is largest.

| Row | n = 1 / 2 | T_eff median | Refused | |
|--|--|--|--|--|
| (1) Window's smallest eigenvalue, iid | 0.0370 / 0.0285 | 230 / 230 | 0% / 0% |  |
| (1) Direction most underestimated, iid | 0.0355 / 0.0310 | 230 / 230 | 0% / 0% |  |
| (1) Window's smallest eigenvalue, iid, 30 equal assets | 0.0335 / 0.0380 | 228 / 228 | 0% / 0% |  |
| (1) Direction most underestimated, iid, 30 equal assets | 0.0335 / 0.0380 | 228 / 228 | 0% / 0% |  |
| (1) Window's smallest eigenvalue, iid, 50 equal assets | 0.0465 / 0.0430 | 230 / 230 | 0% / 0% |  |
| (1) Direction most underestimated, iid, 50 equal assets | 0.0465 / 0.0430 | 230 / 230 | 0% / 0% |  |
| (1) Window's smallest eigenvalue, iid, 58 equal assets | 0.0580 / 0.0580 | 228 / 228 | 0% / 0% | above nominal |
| (1) Direction most underestimated, iid, 58 equal assets | 0.0580 / 0.0580 | 228 / 228 | 0% / 0% | above nominal |
| (1) Window's smallest eigenvalue, GARCH | 0.0260 / 0.0220 | 230 / 230 | 0% / 0% |  |
| (1) Direction most underestimated, GARCH | 0.0345 / 0.0340 | 230 / 230 | 0% / 0% |  |
| (1) Window's smallest eigenvalue, GARCH, 50 assets | 0.0405 / 0.0445 | 230 / 230 | 0% / 0% |  |
| (1) Direction most underestimated, GARCH, 50 assets | 0.0305 / 0.0375 | 229 / 229 | 0% / 0% |  |
| (1) Window's smallest eigenvalue, one-factor GARCH | 0.0315 / 0.0285 | 230 / 230 | 0% / 0% |  |
| (1) Direction most underestimated, one-factor GARCH | 0.0350 / 0.0325 | 230 / 230 | 0% / 0% |  |
| (2) Trades above 1.5x, floor otherwise, iid | 0.0340 / 0.0375 | 230 / 230 | 0% / 0% | traded 39% of steps |
| (2) Trades above 2.0x, floor otherwise, iid | 0.0370 / 0.0385 | 230 / 230 | 0% / 0% | traded 3% of steps |
| (2) Trades above 3.0x, floor otherwise, iid | 0.0380 / 0.0295 | 230 / 230 | 0% / 0% | traded 0% of steps |
| (2) Trades above 1.5x, floor otherwise, iid, 30 equal assets | 0.0565 / 0.0750 | 230 / 230 | 0% / 0% | above nominal; traded 100% of steps |
| (2) Trades above 2.0x, floor otherwise, iid, 30 equal assets | 0.0565 / 0.0750 | 230 / 230 | 0% / 0% | above nominal; traded 100% of steps |
| (2) Trades above 3.0x, floor otherwise, iid, 30 equal assets | 0.0575 / 0.0765 | 230 / 230 | 0% / 0% | above nominal; traded 71% of steps |
| (2) Trades above 1.5x, floor otherwise, iid, 50 equal assets | 0.0565 / 0.0640 | 230 / 230 | 0% / 0% | above nominal; traded 99% of steps |
| (2) Trades above 2.0x, floor otherwise, iid, 50 equal assets | 0.0580 / 0.0640 | 230 / 230 | 0% / 0% | above nominal; traded 98% of steps |
| (2) Trades above 3.0x, floor otherwise, iid, 50 equal assets | 0.0585 / 0.0675 | 230 / 230 | 0% / 0% | above nominal; traded 95% of steps |
| (2) Trades above 1.5x, floor otherwise, iid, 58 equal assets | 0.0800 / 0.0880 | 230 / 230 | 0% / 0% | above nominal; traded 98% of steps |
| (2) Trades above 2.0x, floor otherwise, iid, 58 equal assets | 0.0790 / 0.0875 | 230 / 230 | 0% / 0% | above nominal; traded 96% of steps |
| (2) Trades above 3.0x, floor otherwise, iid, 58 equal assets | 0.0795 / 0.0900 | 230 / 230 | 0% / 0% | above nominal; traded 93% of steps |
| (3) Trades above 1.5x, floor otherwise, GARCH | 0.0350 / 0.0350 | 230 / 230 | 0% / 0% | traded 82% of steps |
| (3) Trades above 2.0x, floor otherwise, GARCH | 0.0340 / 0.0370 | 230 / 230 | 0% / 0% | traded 10% of steps |
| (3) Trades above 3.0x, floor otherwise, GARCH | 0.0370 / 0.0300 | 230 / 230 | 0% / 0% | traded 0% of steps |
| (3) Trades above 1.5x, floor otherwise, GARCH, 50 assets | 0.0450 / 0.0565 | 230 / 230 | 0% / 0% | above nominal; traded 100% of steps |
| (3) Trades above 2.0x, floor otherwise, GARCH, 50 assets | 0.0455 / 0.0570 | 230 / 230 | 0% / 0% | above nominal; traded 98% of steps |
| (3) Trades above 3.0x, floor otherwise, GARCH, 50 assets | 0.0455 / 0.0550 | 230 / 230 | 0% / 0% | above nominal; traded 95% of steps |
| (3) Trades above 1.5x, floor otherwise, one-factor GARCH | 0.0305 / 0.0320 | 230 / 230 | 0% / 0% | traded 64% of steps |
| (3) Trades above 2.0x, floor otherwise, one-factor GARCH | 0.0330 / 0.0305 | 230 / 230 | 0% / 0% | traded 5% of steps |
| (3) Trades above 3.0x, floor otherwise, one-factor GARCH | 0.0315 / 0.0275 | 230 / 230 | 0% / 0% | traded 0% of steps |

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
| (1) Window's smallest eigenvalue, iid | 0.0355 / 0.0340 (230) | 0.0350 / 0.0310 (230) | 0.0320 / 0.0295 (230) | 0.0285 / 0.0240 (190) |
| (1) Direction most underestimated, iid | 0.0380 / 0.0405 (230) | 0.0310 / 0.0315 (230) | 0.0300 / 0.0290 (230) | 0.0295 / 0.0245 (190) |
| (1) Window's smallest eigenvalue, iid, 30 equal assets | 0.0355 / 0.0340 (230) | 0.0235 / 0.0305 (227) | 0.0210 / 0.0295 (226) | 0.0265 / 0.0295 (190) |
| (1) Direction most underestimated, iid, 30 equal assets | 0.0355 / 0.0340 (230) | 0.0235 / 0.0305 (227) | 0.0210 / 0.0295 (226) | 0.0265 / 0.0295 (190) |
| (1) Window's smallest eigenvalue, iid, 50 equal assets | 0.0300 / 0.0330 (230) | 0.0310 / 0.0295 (226) | 0.0285 / 0.0275 (224) | 0.0340 / 0.0320 (190) |
| (1) Direction most underestimated, iid, 50 equal assets | 0.0300 / 0.0330 (230) | 0.0310 / 0.0295 (226) | 0.0285 / 0.0275 (224) | 0.0340 / 0.0320 (190) |
| (1) Window's smallest eigenvalue, iid, 58 equal assets | 0.0345 / 0.0285 (230) | 0.0255 / 0.0315 (225) | 0.0215 / 0.0280 (224) | 0.0445 / 0.0415 (189) |
| (1) Direction most underestimated, iid, 58 equal assets | 0.0345 / 0.0285 (230) | 0.0255 / 0.0315 (225) | 0.0215 / 0.0280 (224) | 0.0445 / 0.0415 (189) |
| (1) Window's smallest eigenvalue, GARCH | 0.0245 / 0.0200 (230) | 0.0230 / 0.0205 (230) | 0.0245 / 0.0180 (230) | 0.0275 / 0.0155 (190) |
| (1) Direction most underestimated, GARCH | 0.0305 / 0.0285 (230) | 0.0310 / 0.0300 (230) | 0.0290 / 0.0280 (230) | 0.0240 / 0.0210 (190) |
| (1) Window's smallest eigenvalue, GARCH, 50 assets | 0.0280 / 0.0230 (230) | 0.0350 / 0.0510 (229) above nominal | 0.0360 / 0.0490 (229) | 0.0275 / 0.0195 (190) |
| (1) Direction most underestimated, GARCH, 50 assets | 0.0350 / 0.0195 (230) | 0.0205 / 0.0265 (224) | 0.0165 / 0.0220 (222) | 0.0270 / 0.0205 (190) |
| (1) Window's smallest eigenvalue, one-factor GARCH | 0.0300 / 0.0290 (230) | 0.0295 / 0.0275 (230) | 0.0275 / 0.0280 (230) | 0.0260 / 0.0215 (190) |
| (1) Direction most underestimated, one-factor GARCH | 0.0435 / 0.0370 (230) | 0.0320 / 0.0310 (230) | 0.0285 / 0.0300 (230) | 0.0350 / 0.0305 (190) |
| (2) Trades above 1.5x, floor otherwise, iid | 0.0380 / 0.0410 (230) | 0.0330 / 0.0360 (230) | 0.0330 / 0.0350 (230) | 0.0355 / 0.0310 (190) |
| (2) Trades above 2.0x, floor otherwise, iid | 0.0395 / 0.0425 (230) | 0.0395 / 0.0400 (230) | 0.0400 / 0.0395 (230) | 0.0260 / 0.0250 (190) |
| (2) Trades above 3.0x, floor otherwise, iid | 0.0450 / 0.0420 (230) | 0.0390 / 0.0330 (230) | 0.0395 / 0.0335 (230) | 0.0260 / 0.0250 (190) |
| (2) Trades above 1.5x, floor otherwise, iid, 30 equal assets | 0.0355 / 0.0340 (230) | 0.0590 / 0.0790 (230) above nominal | 0.0605 / 0.0765 (230) above nominal | 0.0265 / 0.0295 (190) |
| (2) Trades above 2.0x, floor otherwise, iid, 30 equal assets | 0.0355 / 0.0345 (230) | 0.0575 / 0.0790 (230) above nominal | 0.0570 / 0.0805 (230) above nominal | 0.0265 / 0.0295 (190) |
| (2) Trades above 3.0x, floor otherwise, iid, 30 equal assets | 0.0405 / 0.0405 (230) | 0.0645 / 0.0905 (230) above nominal | 0.0650 / 0.0905 (230) above nominal | 0.0345 / 0.0260 (190) |
| (2) Trades above 1.5x, floor otherwise, iid, 50 equal assets | 0.0415 / 0.0350 (230) | 0.0590 / 0.0825 (230) above nominal | 0.0625 / 0.0850 (230) above nominal | 0.0340 / 0.0320 (190) |
| (2) Trades above 2.0x, floor otherwise, iid, 50 equal assets | 0.0420 / 0.0420 (230) | 0.0610 / 0.0820 (230) above nominal | 0.0615 / 0.0855 (230) above nominal | 0.0340 / 0.0320 (190) |
| (2) Trades above 3.0x, floor otherwise, iid, 50 equal assets | 0.0405 / 0.0370 (230) | 0.0620 / 0.0865 (230) above nominal | 0.0615 / 0.0870 (230) above nominal | 0.0340 / 0.0320 (190) |
| (2) Trades above 1.5x, floor otherwise, iid, 58 equal assets | 0.0420 / 0.0335 (230) | 0.0625 / 0.0795 (230) above nominal | 0.0695 / 0.0845 (230) above nominal | 0.0550 / 0.0650 (190) above nominal |
| (2) Trades above 2.0x, floor otherwise, iid, 58 equal assets | 0.0445 / 0.0350 (230) | 0.0630 / 0.0815 (230) above nominal | 0.0695 / 0.0850 (230) above nominal | 0.0550 / 0.0650 (190) above nominal |
| (2) Trades above 3.0x, floor otherwise, iid, 58 equal assets | 0.0445 / 0.0350 (230) | 0.0645 / 0.0825 (230) above nominal | 0.0675 / 0.0845 (230) above nominal | 0.0550 / 0.0650 (190) above nominal |
| (3) Trades above 1.5x, floor otherwise, GARCH | 0.0310 / 0.0285 (230) | 0.0335 / 0.0330 (230) | 0.0340 / 0.0310 (230) | 0.0295 / 0.0225 (190) |
| (3) Trades above 2.0x, floor otherwise, GARCH | 0.0280 / 0.0265 (230) | 0.0325 / 0.0305 (230) | 0.0310 / 0.0320 (230) | 0.0310 / 0.0270 (190) |
| (3) Trades above 3.0x, floor otherwise, GARCH | 0.0255 / 0.0325 (230) | 0.0310 / 0.0330 (230) | 0.0315 / 0.0355 (230) | 0.0295 / 0.0255 (190) |
| (3) Trades above 1.5x, floor otherwise, GARCH, 50 assets | 0.0240 / 0.0190 (230) | 0.0585 / 0.0765 (230) above nominal | 0.0580 / 0.0745 (230) above nominal | 0.0270 / 0.0205 (190) |
| (3) Trades above 2.0x, floor otherwise, GARCH, 50 assets | 0.0320 / 0.0265 (230) | 0.0595 / 0.0750 (230) above nominal | 0.0585 / 0.0745 (230) above nominal | 0.0270 / 0.0205 (190) |
| (3) Trades above 3.0x, floor otherwise, GARCH, 50 assets | 0.0305 / 0.0260 (230) | 0.0595 / 0.0725 (230) above nominal | 0.0570 / 0.0770 (230) above nominal | 0.0270 / 0.0205 (190) |
| (3) Trades above 1.5x, floor otherwise, one-factor GARCH | 0.0435 / 0.0375 (230) | 0.0240 / 0.0265 (230) | 0.0245 / 0.0275 (230) | 0.0390 / 0.0305 (190) |
| (3) Trades above 2.0x, floor otherwise, one-factor GARCH | 0.0485 / 0.0425 (230) | 0.0315 / 0.0290 (230) | 0.0305 / 0.0295 (230) | 0.0375 / 0.0330 (190) |
| (3) Trades above 3.0x, floor otherwise, one-factor GARCH | 0.0435 / 0.0445 (230) | 0.0310 / 0.0255 (230) | 0.0290 / 0.0235 (230) | 0.0365 / 0.0280 (190) |
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

Every PSR-statistic rate and c(n) above equals that README's at the digits it prints. Its calibration cost (19 to 23 s,
200 to 240 s, 392 MiB) was another run on the same laptop: the times here are somewhat above it, the memory
4% above it.

## What the tables cover

The simulated worlds of the README: iid markets with one regime shift, GARCH and one-factor GARCH nulls, and adversaries that watch the statistic they are graded on, the assumptions table's knowing the risk estimator's state. Failed openings are supported by `Holdout` and pinned by the suite, though no table uses them.
