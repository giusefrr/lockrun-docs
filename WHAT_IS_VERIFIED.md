# What is verified

For a risk team or an external reviewer. Three lists: what ran on a live deployment, what only the
test suite shows, and what we cannot verify. Status as of 25 October 2026: runner signatures
(THREAT_MODEL.md, claim 9) ran live on a deployment built from zero that night (below); the rest is as
of 18 October.

## 1. Verified on a live deployment

**Runner signatures, from zero (25 October 2026, 00:12–02:31 UTC).** `demo-from-zero --researcher tester
--holdout demo-1 --anchors-repo giusefrr/lockrun-anchors-demo2 --verdicts-repo giusefrr/lockrun-verdicts-demo2
--ops` on an empty account: nyc2, `s-1vcpu-2gb-amd`, Ubuntu 24.04 (kernel 6.8.0-142), gVisor `runsc`
release-20261019.0, runner image `sha256:3de8f4bc…`. 58 steps, the last the cutoff
(`require-signatures`); then the checks below.

- **Six runners, every gate:** `lockrun-p3-runner-tester`, `-tester2`, `-tester3` and `lockrun-p3-verify-1`
  (the rebuilt one), `-verify-2`, `-verify-3` each passed every `runner-check` gate, K1 (the key is the
  signer user's alone, 0600 in 0700, one sudo rule) and K2 (the agent reports its key) included.
  `check-service` passed with no failure.
- **Signed executions:** two of tester's executions, one before the cutoff and one after, each with
  every record signed by the runner that ran it; both fresh verifications matched, signed by their
  verify runners' own keys.
- **Two signed verdicts:**
  - `demo-1` #10 (run `012ca8e812ec`) and #20 (run `702ca16e4d48`), both PASS. sign-verdicts signed
    each only after the runner checks and the replay of the signed streams against the real holdout.
  - `verify-verdict` checked each from fresh public clones.
- **Two `recycle-all` runs from the ops droplet,** before and after the cutoff:
  - tester → tester2 → tester3 and verify-1 → verify-2 → verify-3, each new runner certified with K_ops;
  - every retirement carries the runner's own final statement (last counters 4, 4, 2, 2);
  - `verify @runners` passed after each swap.
- **After everything:**
  - `verify @runners` with risk's and ops' public keys: 9 records, every binding rule, counters
    complete for 6 keys;
  - `verify demo-1`: 20 records, every execution record carrying its runner's statements;
  - the risk report: N 4, both verdicts signed, anchors OK.
- **Not exercised live:** journal recovery ran before each execution and at each retirement and found
  nothing to recover; the crash it is for has run only in the suite.
- **What the run found,** each a test-first fix, then the run resumed by hand:
  - **The cloud firewall reached a new droplet after it booted** (step 15, `check-service` A2): the
    service's first-boot probe, at 10–19 s of uptime, still reached a public resolver on 443 and 853. The first
    boot now waits for it and records when it took effect (`525dbfa`); on the six droplets checked after
    the fix, it took effect 14.4–23.5 s after boot. The service droplet was rebuilt.
  - **runner-check left its own store** (step 35, H1, verify-1): D4's container is killed at its memory
    cap on purpose, and Podman's cleanup died with it; the removal's error went to `/dev/null`. It is now
    shown, and the removal gets up to three rounds (`ccdfa7a`); every runner since passed H1 in the first.
    verify-1, not yet registered, was rebuilt.
  - **anchors-deposit misread a deposit that worked** (step 43): it read the unit's last three journal
    lines, which systemd's own had filled. It now reads the unit's result and that run's own journal
    (`cbaa7a6`).
- **Timings:**

  | Step | Time |
  |---|---|
  | 1–12: risk-key to the builder destroyed | 4 min 12 s |
  | the service: create, `provision-service`, `check-service` | 113 s, 434 s, 32 s |
  | 16–24: issuers, GitHub keys and repositories, `anchors-install` | 42 s |
  | the primary runner: create, provision, lock, check, register | 60, 342, 11, 170, 7 s |
  | the verify runner (rebuilt): create, provision, lock, check, register | 51, 344, 13, 174, 10 s |
  | token, holdout, execute, promote, verify-fresh, promote | 8, 9, 17, 3, 17, 3 s |
  | deposit, `anchors-verify`, `sign-verdicts`, `verify-verdict` | 7, 4, 6, 1 s |
  | the ops droplet: create, `provision-ops`, issuers, key, `ops-sync`, authorize, firewalls | 53, 121, 5, 0, 81, 4, 22 s |
  | `demo-ops-auth` (the operator's token), `recycle-all`, `require-signatures` | 226 s, 1370 s, 4 s |
  | after the cutoff: `check-service`, `check-runner` (tester2, verify-2) | 33 s, 176 s each |
  | after the cutoff: execute, promote, verify-fresh, promote, deposit, sign, verify-verdict | 18, 4, 15, 4, 6, 6, 0 s |
  | after the cutoff: `recycle-all` (tester2 631 s, verify-2 655 s), `verify @runners`, `verify demo-1`, risk-report | 1306, 4, 5, 20 s |

  2 h 19 min in all, with the three fixes and two rebuilds.
- **A known cost, to reduce:** a signed execution took 10.8 s and 11.5 s from the seal record to the
  outcome record, on the service's clock, against 8.2 s unsigned on 16 October (17–18 s is
  `demo-execute`'s wall time, the client's requests and polling included).
  - Measured on tester3, the signing itself accounts for about 0.75 s: four signatures, each a sudo,
    a Python start and openssl spawns (the signer's `pub` takes 0.10 s), and three hellos that each
    ask the signer for its key (0.23 s against 0.17 s without).
  - The rest is not attributed: that run had another gVisor release (20261005.0) and other droplets.
  - Locally, on a development runner, signing adds 0.07 s per session; reading the signed end
    (0.06 s) costs about what the unsigned close did (0.04 s).

The rest of this section is the deployment of 14–16 October 2026.

DigitalOcean nyc2, droplets `s-1vcpu-2gb-amd`, Ubuntu 24.04 (kernel 6.8.0-142), Podman 4.9.3, gVisor
`runsc` release-20261005.0. 14–16 October 2026. Runner image `sha256:853b792a…` (14 October), then
`sha256:ce7695aa…` (15 October: one layer, every file 0:0, no `/etc/hosts` or `resolv.conf`).

**One command, from zero (16 October).** The deployment of 14–16 October was torn down
(`./do.sh destroy`) and its local state moved aside (`reset-local`). Then
`./do.sh demo-from-zero --researcher tester --holdout demo-1 --anchors-repo giusefrr/lockrun-anchors-demo
--verdicts-repo giusefrr/lockrun-verdicts-demo --ops --yes` rebuilt everything from an empty account
(a VPC, firewalls, tags and droplets, with only the admin SSH key in place).

- **Steps 1–41 passed** in 32 min 25 s (16:43:21–17:15:46, laptop time). The run then stopped at
  step 42, `anchors-deposit`, on a bug: the first deposit, at step 20, ran before any chain existed
  (anchors before chains). It staged an empty `anchors.jsonl` and committed nothing, and every
  later deposit refused `the clone has changes other than anchors.jsonl: A  anchors.jsonl`.
  - The fix, `1290c3c`, is test first: an empty file is never staged, and a file left staged that
    way is accepted.
  - It was deployed by re-running step 20, `anchors-install`, which then deposited 3 anchors.
  - Steps 42–55 were then run by hand, in the demo's order.
- **Per-step times.** demo-from-zero prints a step's time only when the step fails, so the times
  for steps 1–41 come from the timestamps of their step logs and artefacts in `out/`. Steps 42–55
  were timed directly.

  | Steps | Time |
  |---|---|
  | 1–8: allowlist, wheel, preflight, VPC, tags, firewalls, check, builder droplet | 1 min 24 s |
  | 9–12: build the image, fetch it, destroy the builder, create the service | 4 min 54 s (image on the laptop 1 min 33 s after the build began) |
  | 13 `provision-service` | 5 min 39 s |
  | 14 `check-service` | 28 s |
  | 15–20: GitHub host keys, strategy deploy key, repo allowlist, anchors repository and key, `anchors-install` | 27 s |
  | 21–23: `risk-key`, verdicts repository and key | 8 s |
  | 24 `create-droplet lockrun-p3-runner-tester` | about 61 s |
  | 25–26 `provision-runner` and `retag-locked` | 5 min 7 s |
  | 27 `lock-runner` | 11 s |
  | 28–30: `check-runner`, `register-runner` (bound to tester), `create-droplet lockrun-p3-verify-1` | 3 min 53 s |
  | 31–32 `provision-runner` and `retag-locked` | 5 min 19 s |
  | 33 `lock-runner` | 12 s |
  | 34–35 `check-runner` and `register-runner` (verify) | 2 min 58 s |
  | 36–41: token, holdout `demo-1`, honest execution, promote (pending), `verify-fresh` (match), promote | 44 s |
  | 42 `anchors-deposit`, first attempt | 3 s, failed (above) |
  | 20 `anchors-install` again, with the fix | 7 s |
  | 42 `anchors-deposit` | 7 s |
  | 43 `anchors-verify demo-1 2h` | 5 s |
  | 44 `sign-verdicts` | 5 s |
  | 45 `verify-verdict` | 1 s |
  | 46 `create-droplet lockrun-p3-ops` | 40 s |
  | 47 `provision-ops` | 60 s |
  | 48 `demo-ops-key` | 1 s |
  | 49 `ops-sync` | 17 s |
  | 50 `ops-authorize` | 5 s |
  | 51 `update-service-fw` | 7 s |
  | 52 `update-admin-ip` | 9 s |
  | 53 `check-firewalls` | 4 s |
  | 54 `demo-ops-auth` | 928 s, almost all of it waiting for the operator's `doctl auth init` on the ops droplet |
  | 55 `demo-ops-recycle` | 1179 s |

- **What the run produced:**
  - **The verdict:** `tester`'s honest strategy on `demo-1` gave PASS, N 2, DSR 1.0, record 10.
  - **Anchors:** the anchors repository verified at a 2 h cadence.
  - **The signed verdict:** signed on the laptop and verified offline from fresh public clones. It
    is the first live verdict that states its code version (`code_sha256 db067935…`).
- **The recycle (step 55):** `recycle-all` from the ops droplet, run once by hand, took 1167 s.
  - tester was rebuilt as tester2 in 563 s, and verify-1 as verify-2 in 585 s.
  - Each new runner was provisioned in 318 s, locked, and passed `check-runner` (168–169 s).
  - The primary's `runner_replace` and the verify runner's registration were recorded, and
    `@runners` was verified after each swap. The old droplets were destroyed.
  - `ops-pull` then pinned both new runners on the laptop.
- **End to end:** 76 min, from 16:43 to 18:00, including the fix and the wait at step 54.

The lists below are for the 14–16 October deployment unless they say otherwise.

- **Runner gates** (`runner-check.sh`): 28 of 28 (B0–B7, A1, C1–C2, D1–D4, E1–E6, F1–F4, G1–G2,
  H1) on `lockrun-p3-runner-tester2` and `lockrun-p3-verify-2` (first image), and on
  `lockrun-p3-runner-tester3`, `lockrun-p3-verify-3` and `lockrun-p3-verify-4` (rebuilt image).
- **Service gates** (`service-check.sh` through `check-service`): every gate, 88 to 92 as holdouts
  were added, after provisioning and after the service updates.
- **Launch profile:** one launch exactly as the agent launches a job, inspected live and checked by
  the agent's launch check; every field matched. Fixture `tests/data/podman-4.9.3-live-launch.json`
  (tester3, rebuilt image), shown in THREAT_MODEL.md, "Launch profile as observed". Its profile hash
  `7eb5b959…` equals what gate E6 printed on tester3.
- **End-to-end execution:** seal over the read-only deploy key, double execution on the bound runner
  under gVisor, returns recorded, rounded summary returned; the same config gave the same returns
  hash on both images.
- **Memory-cap kill and cleanup:** a strategy allocating 1536 MiB under a 1024 MiB cap; the kernel's
  memory-cgroup OOM killer killed `gvisor_sentry` in the job's own scope; recorded `no_returns`
  (`exception`), counted in N; the runner's work root empty afterwards; the next hello clean
  (`jobs 0`, `problems []`).
- **Fresh-runner verification:** four candidates verified on four fresh verify runners, each `match`,
  each promoted to a PASS whose record names its fresh verification and the ledger, witness and
  bindings heads it was computed from. One of them (`test-1`) carries three failed trials as zeros in
  V (`n_zero_sharpe: 3`): the 15 October rule, replaced on 17 October (failed openings with no valid
  series now count in N only).
- **Runner replace:** `runner_replace` records tester → tester2 → tester3 → tester4, verify runners
  registered and removed; `lockrun-risk verify @runners` passes (8 records).
- **Runner recycling:** `do.sh recycle-runner lockrun-p3-runner-tester3` (15 October, 16:01Z): a new
  droplet from the pinned image, every gate passed (28 of 28), `runner replace` recorded, `@runners`
  verified, then the old droplet destroyed; 586 s. The next soak tick ran on tester4 and the summary
  reports the rebuild. `check-service` gate E7 (no runner older than 36 h) passes.
- **`recycle-all` from the operator droplet** (`lockrun-p3-ops`, its own token and key, started by
  hand through `lockrun-recycle.service`, 15 October): two runs failed on provisioning from that
  droplet (the `lockrun` package missing there; root on the new runner refusing the droplet's
  address), and each left both old runners in place and destroyed the new droplets. The third
  replaced tester4 with tester5 and verify-4 with verify-5 (about 9.5 min each, every gate), then
  waited on verify-4 after removing its record; that last step, destroying verify-4, was done by hand,
  and the order is fixed since. The summaries reached the service's journal (`lockrun-recycle`). The
  timer's own runs follow.
- **Nightly recycle, on its own** (`lockrun-recycle.timer` on the ops droplet, 16 October 03:00 UTC):
  `recycle-all exit 0` in 1184 s; tester5 → tester6 (583 s) and verify-5 → verify-6 (593 s), every gate
  passed on each new runner, `runner_replace` and `verify_runner` recorded, `@runners` verified
  (12 records), the old droplets destroyed; the summary in the service's journal (`lockrun-recycle`);
  `check-service` E7 passes the next morning.
- **Nightly recycles on the demo-from-zero deployment** (the ops droplet's timer, 03:00 UTC, unattended):
  - **17 October:** `recycle-all exit 0` in 1172 s; tester2 → tester3, verify-2 → verify-3.
  - **18 October:** `recycle-all exit 0` in 1187 s; tester3 → tester4 (592 s), verify-3 → verify-4 (587 s).
  - With the recycle run by hand at step 55 on 16 October (1167 s), that is three consecutive
    recycles, each with `exit 0`, the old droplets destroyed, and the summary in the service's
    journal.
- **Risk report** (`./do.sh risk-report`, 17 and 18 October): one static page per day, generated
  from the service through read-only commands and the public verdicts repository. On 18 October,
  15:29 UTC, it showed:
  - `demo-1`: N 2, nothing excluded from V, anchors verify OK (44 anchors, 44 commits, append-only);
  - the PASS verdict at record 10, signed: yes;
  - `lockrun-p3-runner-tester4` and `lockrun-p3-verify-4`, 12.3 h and 12.2 h old;
  - the last deposit at 15:00 UTC, and the 03:00 recycle's `exit 0`.
  - On 17 October the service still predated the record numbers in `lockrun-risk report`; the page
    matched the verdict to its signature by run (`9ced836`). By 18 October the service had been
    updated, and the record number shows.
- **The QUICKSTART by hand** (`docs/QUICKSTART.md`, 16 October, by the operator): as `tester`, seal
  `honest.py` on `test-2` (`9ccc853232da`), execute, promote (`pending_verification`); as risk,
  `verify-fresh` on verify-6 (`match`); promote again: PASS. The same strategy resealed at another
  commit gave identical returns, and the duplicate detector flagged it (`n_flagged: 1`, `alert: true`,
  risk's alert naming that run); the verdict was unchanged.
- **Laptop and ops droplet in step** (`do.sh ops-pull`, 16 October): the laptop pinned verify-6 from
  the ops droplet's state and found tester6 already pinned with the same key; `check-runner` on
  tester6 from the laptop then opened no first-contact session. It passed 27 of 28: H1 found the
  check's own store recreated empty by Podman's late cleanup of the OOM-killed D4 container, a race
  fixed the same day (the check waits for that cleanup before removing its store).
- **Anchors:** public repository `giusefrr/lockrun-anchors-p3`, `main` ruleset (restrict deletions,
  block force pushes, active, no bypass) read back from GitHub's API; the service's deploy key, with write
  access, on that repository alone; hourly deposits landing; `anchors-verify` passes on `soak`, `smoke`
  and `test-1` (4 h cadence). At 2 h it reports `test-1`'s first 3 h 23 min, before the anchors were
  installed; since then no chain starts without an anchor target.
- **Signed verdicts (16 October):**
  - **The repository:** public `giusefrr/lockrun-verdicts-p3`, with the anchors repository's ruleset
    read back from GitHub's API. The laptop's deploy key is the only one with write access.
  - **The deposit:** after the service was updated to anchor every verdict and bindings record at
    its exact count, one deposit backfilled 13 anchors (`13aa42e`).
  - **Signing:** `sign-verdicts` on the laptop, with risk's key `de4c32b6d915c003…`, signed three
    verdicts and pushed them (`85eb2c5`): `test-1` #30 (run `564ff85d18ca`, PASS, N 7), `test-2`
    #10 (`3eaf8a830cbd`, PASS, N 2, which predates `n_zero_sharpe`; recomputed as 0) and `test-2` #20
    (`9ccc853232da`, PASS, N 4).
  - **Refused, as the rules require:**
    - `test-1` #16 (run `707ccc214a2d`): computed before early failures entered V. The current
      code gives V 0.0470 and DSR 0.98728, where the record has V 0.00403 and DSR 0.9999986.
    - `soak-v` #10: it lacks `no_anchors` but was written after the commit that added it.
  - **Verification:** `lockrun-verify-verdict` passed on all three, from fresh public clones of both
    repositories, with no service access. One of them was run as a third party would run it, from
    an empty directory.
- **Soak:** on the service host, every 3 hours from 15 October 03:12Z, window closed 21:00Z and
  still running: in the window, 12 ticks, smoke clean 12 of 12 with one returns hash across both
  images and four runners, every holdout verified on every tick, runner identity ok on every tick
  (the rebuilds reported as recycles), no reboot or apt run; one synthetic execution (tick 12) and
  one smoke after the window (tick 13) refused by `tester`'s seal quota (`429`, the hand-run seals of
  15 October still in its 24 h), clean again from the next tick.
- **Timings:**
  - `podman load` of the image into a fresh store: 6.4–6.7 s.
  - A runner from an empty droplet to locked and checked: 9 min 0 s to 9 min 16 s.
  - An image build: 36 s.
  - **Seal + execute:** 8.2 s from the seal record to the returns record, on the service's clock
    (`demo-1`, 16 October; the ledger's timestamps). That is 1.0 s to the opening, then the two
    executions on the bound runner. A fresh verification's single run took 3.4 s. The client's own
    time (TLS, polling) is not included. This is the overhead a CI job adds per tag with `[execute]`
    (`examples/ci/github-actions-seal.yml`); a seal alone is one request.
- **Firewall configuration:** `check-firewalls` matches the generated rules; a retagged runner was
  unreachable from the service until DigitalOcean applied the tag rule, then reachable.

## 2. Verified by the test suite only

1531 tests (`uv run pytest`, 25 October 2026). The stand-ins:

- `tests/fake_podman.py`: Podman, `systemd-run` and `systemctl` on a runner. It models `run`,
  `--rm`, `rm --force`, `container inspect`, `ps`, the job's tmpfs and `podman unshare`, and reports
  inspect fields as the live Podman 4.9.3 does (`EffectiveCaps` null, Podman's tmpfs options, the
  refusal of `--dns` with `--network=none`). No gVisor, no kernel, no cgroups.
- `tests/fake_doctl.py`: the DigitalOcean API through `doctl`: droplets, VPCs, firewalls, tags, their
  lists and their lag, and failed calls.
- `tests/fake_ssh.py` and `tests/fake_remote.py`: `ssh` and `scp` to the service and the runners,
  with a directory standing in for each host and the service's `lockrun-risk` answering for it.
- The process backend (`lockrun/runner/agent.py`, `backend: process`): local development runners
  for the service tests, with no container.

Also only in the suite so far: `recycle-all` waiting for or skipping a runner with a job in flight.
The 17 October rule (failed trials in N, not in V; THREAT_MODEL.md, "Known gaps") is in the suite
only until the service is updated. `tests/test_early_failures_in_v.py` adds 1, 5, 20 and 60 failed
trials to 20 real Sharpes widely dispersed around zero, with candidates of 0.22, 0.45 and 0.8 (a PASS
near the 0.95 bar). It checks that sr0 never falls in any family, that the verdict's DSR never rises,
and that the 0.8 candidate crosses from PASS to FAIL and never back. Under the 15 October rule the
"with" sr0 fell at every step.

Signed verdicts (`tests/test_sign_verdicts.py`, `test_verify_verdict.py`, `test_verdicts_deploy.py`)
are tested against an in-process service, local git repositories and the fake ssh.

Runner signatures (claim 9) are tested with the real signer (`lockrun/runner/signer.py`) and the
real openssl command, against development runners (the process backend):

- **The stand-ins:** the signer runs as the agent's own user, not behind a sudo rule; on macOS the
  suite needs Homebrew's OpenSSL 3 (the system `openssl` is LibreSSL, without Ed25519), and those
  tests skip without it. The signer user, the sudo rule and gates K1 and K2 ran live on 25 October
  (section 1); journal recovery after a crash, risk-signed finals and abandon-claims with risk's
  signature have run only here.
- **What the suite shows:** the statement layout, counters and replay protection
  (`test_runner_statements.py`); keys, certificates, final statements and the cutoff in the bindings
  log (`test_runner_keys_bindings.py`); the store's refusal of unsigned or forged records
  (`test_signed_records.py`); the agent's signed opening and session end (`test_agent_signing.py`);
  the service's checks, journal recovery and abandon-claims with risk's signature
  (`test_service_signing.py`); risk's verify and sign-verdicts, the replay included
  (`test_verify_runner_signatures.py`); do.sh from provisioning to the cutoff
  (`test_deploy_runner_keys.py`); and root's fabrications after the last deposit, refused before and
  after the next one (`test_assume_breach.py`).

- **The signer:** it refuses on a changed ledger, a recomputation off by 1e-9, or a missing deposit
  (the verdict waits). It signs a verdict with its alert, and signs everything again after a key
  rotation.
- **The verifier:** it fails on an altered record or statement, another key, a verdict that was
  never published, or a rewritten anchors history. It needs no service and no ledger.

Under these: the service's API, quotas and refusals; the ledger, witness and index; promotion and
the deflated Sharpe ratio, including the zero-tail and early-failure rules and the property that
added failed trials never improve a verdict; bindings and routing; the agent's job lifecycle, reaper
and launch check; every `do.sh` guard and step; the soak and anchor scripts.

## 3. Not verifiable by us

- An escape from gVisor, or a kernel vulnerability under it.
- The cloud firewall between runners as a live probe: the source runner's own ruleset drops the probe
  before it reaches the cloud firewall (THREAT_MODEL.md, section 4).
- Root on a compromised host: it can forge the agent's hello and launch profile, rewrite a build_id
  file, and append to the anchors repository (not rewrite it, if GitHub enforces the ruleset).
- That GitHub enforces the ruleset, and that DigitalOcean enforces its firewalls as configured.
- Shared hardware state between jobs (caches, side channels).
- That a runner was really rebuilt from scratch: provable only by procedure.
- That a runner's signing key never left the runner (root on it can copy it), and that K_ops stayed on
  the operator droplet.
- That risk's signing key stayed on risk's laptop, and when a verdict was signed: `signed_at` and
  the commit dates are the signer's own. Records appended after a compromise of the service host
  are consistent with each other, so a signature cannot tell them from real ones (THREAT_MODEL.md,
  §3a).

The external-review brief is THREAT_MODEL.md, section 6, "Where an external reviewer should look
first", with the statistical rules marked for review in section 5.
