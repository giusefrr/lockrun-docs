# lockrun: public documents

lockrun counts every backtest run against a protected holdout, so a strategy's Deflated Sharpe Ratio uses the true number of trials.
A risk-owned service holds the encrypted holdout and a hash-chained ledger; each researcher seals code, which runs on locked runners, and every opening is recorded, signed by the runner that ran it.
The ledgers' heads are anchored hourly in a public append-only repository, and risk signs each verdict with a key kept off the service host.
Anyone can check a signed verdict offline, with risk's public key and clones of the two public repositories.
Status: a prototype, with one live deployment (October 2026).

- [THREAT_MODEL.md](THREAT_MODEL.md): what the code enforces, what root on each host can do, what a signed verdict proves and what it does not.
- [WHAT_IS_VERIFIED.md](WHAT_IS_VERIFIED.md): what ran on the live deployment, what only the test suite shows, what we cannot verify; its status section first.
- [RULE_V3_PROOF.md](RULE_V3_PROOF.md): rule version 3's theorem, the false-pass bound of 0.05 under its assumptions A1 and A2, and what is measured of each: where A1 holds, and the skewed-crash worlds where it fails.
- [SIZE_TABLE.md](SIZE_TABLE.md): rule version 3's false-pass rate over alpha, per null world, strategy and level, in the 20 null worlds measured to the end (of 27); what is open, in its header.
- [REDTEAM.md](REDTEAM.md): the red-team engine, the adversarial search that found version 2's hole, and what its runs on version 3 show and do not show.
- [tools/joint_bar/](tools/joint_bar/): the simulations behind the statistical rule (optional stopping passed the DSR at 0.27, nominal 0.05), every number and the command that prints it; [standalone/](tools/joint_bar/standalone/) reproduces them with numpy alone, without lockrun's source, and holds rule version 3's declared-portfolio bar (`joint_rule.py`).
- Live examples, this deployment's: the anchors repository, [giusefrr/lockrun-anchors-demo6-20261031-1522](https://github.com/giusefrr/lockrun-anchors-demo6-20261031-1522), and the signed verdicts, [giusefrr/lockrun-verdicts-demo6](https://github.com/giusefrr/lockrun-verdicts-demo6).

File names in code formatting (`lockrun/...`, `tests/...`, `do.sh`, `README.md`) refer to lockrun's
source tree, which is not in this repository. These copies are generated (`do.sh docs-publish`):
change the source, not them.
