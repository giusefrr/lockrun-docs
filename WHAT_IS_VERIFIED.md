# What is verified

For a risk team or an external reviewer. Three lists: what ran on a live deployment, what only the
test suite shows, and what we cannot verify. Status as of 16 October 2026.

## 1. Verified on a live deployment

DigitalOcean nyc2, droplets `s-1vcpu-2gb-amd`, Ubuntu 24.04 (kernel 6.8.0-142), Podman 4.9.3, gVisor
`runsc` release-20261005.0. 14–15 October 2026. Runner image `sha256:853b792a…` (14 October), then
`sha256:ce7695aa…` (15 October: one layer, every file 0:0, no `/etc/hosts` or `resolv.conf`).

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
  V (`n_zero_sharpe: 3`).
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
- **Timings:** `podman load` of the image into a fresh store 6.4–6.7 s; a runner from an empty
  droplet to locked and checked 9 min 0 s to 9 min 16 s; an image build 36 s.
- **Firewall configuration:** `check-firewalls` matches the generated rules; a retagged runner was
  unreachable from the service until DigitalOcean applied the tag rule, then reachable.

## 2. Verified by the test suite only

1335 tests (`uv run pytest`, 16 October 2026). The stand-ins:

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
Signed verdicts (`tests/test_sign_verdicts.py`, `test_verify_verdict.py`, `test_verdicts_deploy.py`)
are tested against an in-process service, local git repositories and the fake ssh.

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
- That risk's signing key stayed on risk's laptop, and when a verdict was signed: `signed_at` and
  the commit dates are the signer's own. Records appended after a compromise of the service host
  are consistent with each other, so a signature cannot tell them from real ones (THREAT_MODEL.md,
  §3a).

The external-review brief is THREAT_MODEL.md, section 6, "Where an external reviewer should look
first", with the statistical rules marked for review in section 5.
