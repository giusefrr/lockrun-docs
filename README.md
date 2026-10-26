# lockrun: public documents

lockrun counts every backtest run against a protected holdout, so a strategy's Deflated Sharpe Ratio uses the true number of trials.
A risk-owned service holds the encrypted holdout and a hash-chained ledger; each researcher seals code, which runs on locked runners, and every opening is recorded, signed by the runner that ran it.
The ledgers' heads are anchored hourly in a public append-only repository, and risk signs each verdict with a key kept off the service host.
Anyone can check a signed verdict offline, with risk's public key and clones of the two public repositories.
Status: a prototype, with one live deployment (October 2026).

- [THREAT_MODEL.md](THREAT_MODEL.md): what the code enforces, what root on each host can do, what a signed verdict proves and what it does not.
- [WHAT_IS_VERIFIED.md](WHAT_IS_VERIFIED.md): what ran on the live deployment, what only the test suite shows, what we cannot verify.
- Live examples: the anchors repository, https://github.com/giusefrr/lockrun-anchors-demo3, and the signed verdicts, https://github.com/giusefrr/lockrun-verdicts-demo3.

File names in code formatting (`lockrun/...`, `tests/...`, `do.sh`, `README.md`) refer to lockrun's
source tree, which is not in this repository. These copies are generated (`do.sh docs-publish`):
change the source, not them.
