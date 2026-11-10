# The red-team engine, layer 1

**Scope.** Every result here is a result about lockrun's complete procedure, measured by simulation under the stated nulls. This layer is pure local simulation: it never touches a deployment.

An automated adversarial search against lockrun's statistical rule. It looks for any researcher strategy that gets a false promotion under the null more than 5% of the time. Numpy only. It imports the rule from `tools/joint_bar/standalone/`, the copy the suite holds identical to the product, so a finding is a finding against the real rule.

    python -m tools.redteam.search --family all --rule-version 3 --planned-openings 20 --minutes 20 --seed 0

This writes `out/redteam/<date>/report.md` and `findings.json`, ignored by git, and `tests/redteam/test_finding_<date>_<n>.py` for each confirmed finding. The first run builds the bar tables under `out/redteam/bars/`: about 180 fitted dfs at 200k paths per statistic, and at 2M paths those the confirmation meets. That can add several minutes; later runs reuse them.

## What it attacks

Rule version 3 (each trial against its own b_k, `--planned-openings` N), version 2 (plain t) or version 1 (PSR statistic). Each holdout gets the product's procedure: its df fitted on its residuals, its own table, `jr.Holdout.joint` for versions 1 and 2's verdict at `min_t` 100, `T` 250, threshold 0.95, on the null worlds of `joint_assumptions.MARKETS` (the drift worlds excepted).

A strategy spends its openings in one of two ways:

- **At the end:** every opening is made, then each trial meets `c(n)` for all of them. This is the cell of the standalone tables.
- **One promote at a time:** after each opening the researcher promotes, and stops at the first PASS. On version 3 each trial meets its own b_k. On versions 1 and 2 the first FAIL now refuses every further promote, so this ends at one try.

The `side_*` families attack each channel of the audit, and `fail_bit_adaptive` the FAIL bit. On version 3 each channel returns nothing; the leaky controls of `controls.py` open one at a time, so the suite shows that each family exploits its channel when it is open.

## The validity constraint

The adversary must be predictable. Each step's weights may use only past returns, its own past exposures, returns and z, the window covariance of rows strictly before the step, the trial count and the public bar. `adversary.Past` exposes only those, and `check_predictable` proves it empirically: it replaces the market's future from several steps and requires every weight up to that step unchanged. A candidate that fails is marked `look-ahead` and can never be a finding.

## What it does not attack

- **Weights built on earlier openings' summaries, on versions 1 and 2.** A researcher there is shown each opening's rounded Sharpe, over the whole holdout, so a later opening's weights could depend on it. No version 3 family needs this: version 3 shows no summary. On versions 1 and 2 the channel exists and only the `leaky-v2` control is built to model it; that control has not been run on a budget.
- Anything outside the statistical rule (ledger, runners, deployment): `THREAT_MODEL.md` covers those.

## What counts as a finding

1. **Search.** A genetic algorithm in numpy (no CMA-ES: an eigendecomposition in the search would tie genomes to the BLAS) maximizes false promotions on search seeds, using 200k-path tables.
2. **Race.** A genome above 0.045 on the generations' few seeds meets more search seeds, each family's best first and each raced to the end, so a budget that ends leaves the weakest unraced. One still above 0.045 at 3200 is a candidate. With 100 seeds a generation, half of all honest genomes clear 0.045 by noise, so confirming them directly would be pure cost.
3. **Confirmation.** Every candidate runs on fresh seeds, disjoint from every search seed (`confirm.fresh_seed`), under the product's 2M-path tables. The run goes in rounds of 1,000 seeds and stops once decided, with 20000 seeds as the ceiling (see "Sequential confirmation" below). `--fixed-confirm` runs every candidate on all 20000 seeds, with no optional stopping.

| Status | Meaning |
|--|--|
| finding | exact one-sided 95% binomial lower bound above 0.05 |
| near miss | point estimate above 0.05, lower bound not above |
| cleared | point estimate at most 0.05 |
| look-ahead | failed `check_predictable`, not run |

At 20000 seeds the bound decides at a point estimate of about 0.0525; a confirmation that stops earlier has a finding only where est − 2.58 se is above 0.05. The report also gives each bound with Bonferroni over the candidates tested. The finding definition does not use it, but a marginal finding among many candidates should be read with it. The report states how many candidates the budget left unconfirmed or unraced.

## The surrogate search (measured; not shipped)

`--method surrogate` replaces the genetic algorithm's breeding with Bayesian optimization (`search.Surrogate`). It is not shipped: it failed its acceptance test (below), so nightly runs and the controls stay on `--method evolution`, the default.

**What it does.** Each family's first generation is the evolution's own, random or taken from the archive. After that, each generation keeps the elites: the best genomes by lcb, measured again on new seeds exactly as the evolution's are. The other genomes are chosen by expected improvement:

- **The model** (`search.GP`): a Gaussian process over the genome cube, fitted to everything measured so far, at most 400 genomes. It predicts each genome's false-promotion rate. Each measurement's noise is its own binomial variance. The kernel's length scale and signal variance are the grid point of largest marginal likelihood: a grid, not an optimizer, so the same data give the same fit. numpy only.
- **The incumbent:** the best predicted rate among the genomes already measured.
- **The candidates:** 3,800 Gaussian steps around the three best predicted genomes (a trust region) and 200 uniform genomes, drawn from the family's seeded generator.
- **The batch:** filled greedily. Each pick's neighbourhood is penalized for the next pick, so a generation is not one point many times.

The race and the confirmation on fresh seeds are unchanged. The same seed gives the same genomes. Acquisition values are rounded to 10 significant digits, with ties going to the lower index, so a BLAS that differs in the last bits rarely changes a pick; the caveat of Determinism below applies.

**Its measured power** (`python -m tools.redteam.power --units 400000 --seeds 10 --jobs 10 --fixed-confirm`; measured with fixed confirmation, then the default). The rule's own landscape is unknown, so the harness plants one (`tools/redteam/power.py`):

- **The landscape:** a 10-gene genome cube. The background rate is smooth and between 0.55 and 0.85 of alpha. The plant is a Gaussian basin of width 0.5 whose peak is k × alpha, for k = 1.5, 1.3 and 1.1.
- **Evaluation:** hits are drawn binomially from the true rate, seeded by genome and seeds, and each seed costs one unit.
- **The pipeline:** the search's own code. `search.evolve`, `search.race`, the 50/20/30 budget split, and `confirm.classify` on 20,000 fresh seeds.
- **The metrics:** found means the report holds a finding. The budget to first find is the units spent when the search first measured a genome with a true rate of at least 0.0525. At that rate the confirmation calls a finding about half the time.
- **Calibration:** the width and the evolution's budget were chosen on the evolution alone, on calibration landscapes (seeds 100–107). 400,000 units is the smallest budget at which it finds the 1.5× plant in at least 80% of runs. The surrogate's candidate settings were chosen on the same calibration landscapes. The table below is on the test landscapes, seeds 0–9, the same for every method.

| plant | method | budget | found | reached 0.0525 | mean budget to first find | mean best true rate |
|--|--|--|--|--|--|--|
| 1.5x | evolution | 400,000 | 100% | 100% | 20,660 | 1.382 alpha |
| 1.5x | surrogate | 400,000 | 100% | 100% | 41,440 | 1.445 alpha |
| 1.5x | surrogate | 200,000 | 100% | 100% | 41,440 | 1.336 alpha |
| 1.3x | evolution | 400,000 | 90% | 100% | 38,970 | 1.218 alpha |
| 1.3x | surrogate | 400,000 | 80% | 90% | 82,011 (113,810 counting a miss at its budget) | 1.203 alpha |
| 1.3x | surrogate | 200,000 | 70% | 70% | 62,429 (103,700) | 1.111 alpha |
| 1.1x | evolution | 400,000 | 10% | 30% | 166,333 (329,900) | 1.008 alpha |
| 1.1x | surrogate | 400,000 | 0% | 0% | - | 0.908 alpha |
| 1.1x | surrogate | 200,000 | 0% | 0% | - | 0.878 alpha |

The acceptance rule: on the 1.3x plant, the surrogate at half the budget must find the plant at least as often as the evolution at the full budget. It found it in 70% of runs against 90%: **not accepted**. At an equal budget it is also behind: 80% against 90%, about twice the budget to first find, and nothing at 1.1x where the evolution found 10%.

What we read from it:
- With 100 seeds a genome, a rate near 0.05 is measured to about ±0.02, so each measurement is mostly noise. The evolution's elites and tournament average that noise out about as well as the GP pools it.
- At half the budget, the confirmation's 30% share holds half as many 20,000-seed confirmations, whatever the search found.

**Adding it to nightly.py, were it to pass on a later design.** `nightly.py` runs the nightly pytest tier, so the surrogate would enter as tests:

1. A `method="surrogate"` parametrization of `test_positive_control_the_search_finds_a_planted_hole` and of the negative-control groups in `tests/test_redteam_engine.py` (`se.Config(..., method="surrogate")`), marked `nightly`.
2. A positive control on the harness: a 1.3x plant at the accepted budget, which must be found.

## Successive halving of the seeds (measured; not shipped)

`--halving 3` keeps the genetic algorithm and changes only how a generation's seeds are spent (`Evolution._halving_generation`). The total stays the same: population × generation_seeds.

- **The generation:** 3 × population genomes are bred, in three rounds of equal seed shares.
- **Round 1:** all 42 genomes on about 11 shared fresh seeds.
- **Round 2:** the best third by lcb, 14 genomes, on about 33.
- **Round 3:** the best 4 on about 100.
- **Everything counts:** every genome is measured and recorded, and the next generation is bred from the archive as before.

The idea: noise per genome is the bottleneck (about ±0.02 at 100 seeds), so spend seeds where the rate is still ahead. With the mode off (the default), the evolution's report is byte-identical (`REPORT_SHA`). The same seed gives the same run.

η = 3 and 3 rounds were chosen on the calibration landscapes (seeds 100–107), from four settings. On the 10 test landscapes, with fixed confirmation (`... --candidate halving --fixed-confirm`):

| plant | method | budget | found | reached 0.0525 | mean budget to first find | mean best true rate |
|--|--|--|--|--|--|--|
| 1.5x | evolution | 400,000 | 100% | 100% | 20,660 | 1.382 alpha |
| 1.5x | halving | 400,000 | 100% | 100% | 7,517 | 1.436 alpha |
| 1.5x | halving | 200,000 | 100% | 100% | 7,517 | 1.388 alpha |
| 1.3x | evolution | 400,000 | 90% | 100% | 38,970 | 1.218 alpha |
| 1.3x | halving | 400,000 | 90% | 100% | 28,789 | 1.210 alpha |
| 1.3x | halving | 200,000 | 80% | 100% | 28,789 | 1.181 alpha |
| 1.1x | evolution | 400,000 | 10% | 30% | 166,333 (329,900 counting a miss at its budget) | 1.008 alpha |
| 1.1x | halving | 400,000 | 10% | 20% | 84,932 (336,986) | 1.023 alpha |
| 1.1x | halving | 200,000 | 0% | 20% | 84,932 (176,986) | 1.015 alpha |

**Not accepted:** at half the budget it found the 1.3x plant in 8 of 10 runs, against the evolution's 9 of 10 at the full budget.

It does find holes faster. It reaches the 1.3x hole in every run at half the budget, at a mean of 28,789 units against 38,970, and the 1.5x hole about three times sooner. The miss is in the confirmation: at half the budget, the 30% confirmation share holds 3 confirmations of 20,000 seeds instead of 6. One run in ten is within the noise of ten landscapes, but the rule is the rule; it stays opt-in and out of nightly.

## Sequential confirmation (the default since 2026-11-08)

The default confirmation (`Config.confirm_sequential`; `--fixed-confirm` opts out) runs each candidate's confirmation on its fresh seeds in rounds of 1,000 (`search.confirm_counts`), stopping as soon as it is decided (`search.sequential_stop`), with the 20,000 seeds as the ceiling. The rule is the size table's:

- **The test:** Wald's SPRT on the count, 0.95 against 1.05 × nominal, 1% error each.
- **A stop:** taken only when the stop interval at z = 2.58 agrees. "Finding" needs est − 2.58 se above 0.05; "not a finding" needs est + 2.58 se under 0.0475.
- **The verdict:** always `confirm.classify` on the seeds used. A confirmation run to its ceiling is the fixed one, since its rounds are a prefix of the same fresh seeds.

**Early stops against the full budget**, on 4,000 planted confirmations per rate, with each early stop's remaining draws continued to 20,000:

| true rate | early stops contradicting the full budget's verdict | findings | mean seeds |
|--|--|--|--|
| 0.8 x nominal | 0 | 0% | 6,054 |
| 1.0 x | 22 (0.55%) | 4.67% | 19,844 |
| 1.05 x | 46 (1.2%) | 49.1% | 18,076 |
| 1.2 x | 0 | 100% | 5,302 |
| 1.3 x | 0 | 100% | 3,544 |

At exactly nominal, all of the contradictions go one way: an early finding where all 20,000 seeds would say "not a finding". On those 4,000 seeds that is 4.67% findings sequentially against 4.12% at the full budget. So the red team over-reports there: a false alarm at a rate of 0.55%, never a missed hole. The contradictions near nominal are inherent: an early stop cannot know what its remaining seeds would say. A wider stop interval only thins them, to 7 at z 3.0, 3 at 3.29 and 2 at 3.5 at 1.0 x, for more seeds at the clear rates (8,916 at 0.8 x with z 3.5). `tests/test_redteam_power.py` pins none at 0.8 and 1.2, and at nominal pins them as rare, with no more findings than the full budget's.

**The acceptance table with sequential confirmation for both methods**, on the 10 test landscapes:

| plant | method | budget | found | confirmations | mean seeds per confirmation (before: 20,000) |
|--|--|--|--|--|--|
| 1.5x | evolution | 400,000 | 100% | 196 | 6,413 |
| 1.5x | halving | 200,000 | 100% | 83 | 8,060 |
| 1.3x | evolution | 400,000 | 100% | 98 | 13,112 |
| 1.3x | halving | 400,000 | 90% | 93 | 13,860 |
| 1.3x | halving | 200,000 | 80% | 42 | 15,476 |
| 1.1x | evolution | 400,000 | 20% | 73 | 15,260 |
| 1.1x | halving | 400,000 | 20% | 73 | 15,658 |
| 1.1x | halving | 200,000 | 0% | 33 | 16,030 |

Sequential confirmation lifts the evolution itself (1.3x from 90% to 100%, 1.1x from 10% to 20%) more than it lifts halving at half the budget (still 80%). **Halving is not accepted** and stays opt-in.

Sequential confirmation is the default, nightly included: it lifts the evolution's own power at an equal budget and spends about a third to three quarters of the seeds. `REPORT_SHA` stays the same, because its confirming run confirms on 400 seeds, under one round. `REPORT_SHA_SEQUENTIAL` pins a run whose finding stops at 1,000 seeds.

**The measured power curve, with the default (the evolution, sequential confirmation, 400,000 units, the 10 test landscapes): 1.5x 100%, 1.3x 100%, 1.1x 20%.** The 1.1x limit, plainly: a hole 10% over nominal (a false-promotion rate of 0.055) is found in 2 runs of 10 at this budget. A night that reports no finding has not shown there is no such hole. Holes at 1.3x and above are found every time on these landscapes.

## The findings archive (elitism across runs)

`--archive out/redteam/archive.json` keeps each (rule, family)'s best genomes across runs (`search.Archive`): every confirmed finding first, then the best by lcb, eight at most. A run seeds each family's first generation with them, then adds its own best at its end. Nothing of their past counts is carried: they are measured again on the night's own seeds, and a finding is confirmed again on its fresh seeds.

Measured on the harness: night 1 at 1,000,000 units, then night 2 with a new search seed and 100,000 units, on the same 10 test landscapes.

| plant | night 1 found | night 2 re-found within 100,000 units, from the archive | night 2 without the archive |
|--|--|--|--|
| 1.5x | 10/10 | 10/10 (at 90,700–92,600 units) | 7/10 |
| 1.3x | 10/10 | 8/10 | 4/10 |
| 1.1x | 6/10 | 2/6 | 0/10 |

**In nightly.** `nightly.py --archive out/redteam/archive.json`, as the workflow runs it, makes the negative controls' searches start from the previous nights' best genomes. The positive controls start from nothing, so they still measure the engine's power from scratch. The archive travels as an artifact:

1. `archive-in`, on GitHub's runner with `actions: read`, downloads the newest earlier night's `redteam-archive`, or makes an empty one on the first night.
2. It hands it to the run as `redteam-archive-in`.
3. The droplet uploads what it leaves as `redteam-archive`.

No token reaches the droplet, which `tests/test_ci_workflow.py` pins. Parallel family groups merge into the file under a lock. `test_positive_control_the_archive_finds_last_nights_hole_again_within_a_tenth`, in the nightly tier, holds the archive to its measured power: at least 9 of 10 re-finds at 1.5x and 7 of 10 at 1.3x. A failure there is lost power, not a finding.

**The power curve in every nightly report.** `nightly.py` runs the evolution on the harness's 10 test landscapes at 400,000 units, a few seconds, and writes the fraction of 1.5x, 1.3x and 1.1x plants found under the verdict, next to the findings. With the default confirmation it is 100%, 100%, 20%. A failure of the curve is reported, never the verdict.

A night 2 must hold one 20,000-seed confirmation after its evolution and race (and the race finishes the genome it began), so a tenth needs a large night 1. At 700,000 and 70,000, the race's overshoot pushed most confirmations just past 70,000 (2 of 10 within it at 1.5x); at 1,000,000 and 100,000 they fit. `tests/test_redteam_power.py` pins one case: 1.5x, night 1 on seed 3, night 2 on seed 1003, re-found before 100,000 units.

## The budget

`--minutes` buys a fixed budget of simulated work, not wall-clock time: a clock in the loop would make the report depend on the machine and its load. One unit is one 8-asset row, about 0.2 ms of one core (`search.budget_cost`). `search.UNITS_PER_MINUTE` converts minutes to units as measured on a 10-core laptop, so elsewhere the same `--minutes` gives the same report in a different time.

## Determinism

The same seed gives the same report, byte for byte, at any worker count. The report holds counts and genomes, nothing of the clock or the machine. Eigenvectors use the standalone's sign convention (`joint_world.sign_reference`). `tests/test_redteam_engine.py` pins a report's sha256, run on Accelerate locally and on OpenBLAS in CI. Statistics can differ between BLAS libraries in the last bits, so a value within about 1e-8 of a bar could in principle decide differently; the pin catches that if it happens on the pinned run.

## Reproducing a finding

`findings.json` records the family, genome, first seed, replication count and path count of each finding. Either run its generated test:

    python -m pytest -n 0 tests/redteam/test_finding_<date>_<n>.py

or call it directly:

    python -c "import json; from tools.redteam.search import reproduce; print(reproduce(json.load(open('out/redteam/<date>/findings.json'))['findings'][0]))"

The generated test asserts a rate of at most 0.05, so it fails while the hole exists. Generated tests are not committed.

## Adding a family

Add one file to `tools/redteam/families/`; it is found by listing the directory. It exports `DESCRIPTION`, `SPACE` and `build`:

    """Why this attack might work."""
    from ..adversary import compose as build, space

    DESCRIPTION = "De-risking in a drawdown of normalized PnL."
    SPACE = space(("world", "openings", "dd_limit", "dd_scale"), {"direction": "sticky"})

`SPACE` names the genes it searches, from `adversary.GENES` or a `Gene` of its own, and the values it fixes. For behaviour the composite cannot express, subclass `adversary.Policy` and return a `Strategy` from `build`:

    class Mine(Policy):
        def weights(self, past):      # past: an adversary.Past; returns (past.m, past.A)
            ...

Use only the public fields of `Past`. `tests/test_redteam_engine.py` runs every family through `check_predictable`, and confirmation does so again.

## Positive and negative controls

`controls.py` plants three broken rules: no multiplicity correction, optional stopping ignored, and exposure normalization ignored. The suite requires a confirmed finding against each on a small budget. The negative control requires no finding against version 3 on pinned seeds, on every family with none left out. On a small budget that is a test of the machinery, not evidence of safety.

## Known result

**The hole, 2 November 2026.** This engine found it, on our own rule: under version 2, spending openings one promote at a time gave each opening its own chance at a bar set for that moment's n. 0.1915 false promotions at 100 openings on GARCH (lower bound 0.187), 0.0683 at 2 on the plain market. Rule version 3 closes it by rule change: `docs/RULE_V3_PROOF.md`. The three findings are permanent regressions in `tests/test_redteam_v3.py` and `tests/redteam_findings.json`.

| Run | Result |
|--|--|
| Version 3, all 37 families, N = 20, seed 0 | 0 findings, 0 near misses, nothing reached confirmation; best on search seeds `run_stop` 34/800 = 0.0425; sequential families only 1 to 4 generations |
| Version 3, sequential and fail-bit families, N = 100, seed 1 | 0 findings, nothing reached confirmation; best `opening_spend` 13/300 = 0.0433; 9 to 17 generations |
| Version 3, single-trial families, N = 1, seed 2 | 0 findings, nothing reached confirmation; best `leverage_burst` 7/300 = 0.0233 |
| The findings of 2 November on version 3, 20000 seeds | `bar_crossing`, garch, 100 openings: 0.0495 and 0.0490 at N = 100, 0.0513 and 0.0482 at N = 20. `z_crossing`, t4, 81 openings: 0.0138 at N = 81, 0.0240 at N = 20 |
| The 0.0513, on 100000 further seeds | 5050/100000 = 0.0505, lower bound 0.0494: not a finding |
| Version 1, all families, seed 0 | Finding: `window_aim`, 58 equal assets, 100 openings, all spent before the promote: 0.2990, lower bound 0.2937. On version 3 the same strategy: 0.0002 at N = 100, 0.0008 at N = 20 |

**What these results do not show.** On GARCH the bars run a little under their stated size: the attack at N = 100 has a union bound of 0.045 and measured 0.0495 (lower bound 0.047). The Student-t null of the calibration is a model, and this is the error in it. The same attack at N = 20 sits at about 0.05, 0.0505 on 100000 seeds, with no margin. That is not a finding, and it is not a guarantee either: the attacks were tuned against version 2, the search on version 3 did not rediscover anything as strong, so its clean reports are weaker evidence than they read, and a stronger attack on GARCH could cross 0.05.

The 20-minute budgets are units, not time: the N = 100 run spent 15.6M of its 30M units, about 8 minutes, because nothing reached the race or confirmation.

## What the refusal does not close

After the first FAIL on a version 1 or 2 holdout every further promote is refused, which stops promoting after each opening. Those holdouts still show summaries, so a researcher can read first and promote only a trial that clears the bar, and no FAIL is ever written. `rule.RealRule` models the first researcher, not this one. Version 1's `window_aim` finding also spends its openings before any promote, so the refusal does not touch it.
