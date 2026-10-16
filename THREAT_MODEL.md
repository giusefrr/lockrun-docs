# lockrun threat model

lockrun counts the backtests run against a protected holdout, so a strategy's Deflated Sharpe
Ratio (DSR) uses the true number of trials N. Status: prototype. **The threat:** a researcher with
root on their own machine wants a better-looking backtest. They peek at the holdout before
committing, run many variants and drop the failures, or rewrite the ledger with a recomputed hash
chain to lower N. In **service mode** a risk-owned service holds the key, the ledgers and the
execution: it runs sealed code on runners and records every opening. This document states what the
code enforces as of this revision; `README.md` has the detail, `RUNNER_PERSISTENCE.md` the runner
inventory, and `docs/WHAT_IS_VERIFIED.md` what ran on a live deployment, what only the test suite
shows, and what we cannot verify.

## 1. Claims (service mode)

1. **Every opening is logged first.** Before any holdout row reaches strategy code, the service
   appends a `holdout_access` record to that holdout's ledger: run, researcher, the runner's
   identity, the bindings-log head it was dispatched under, and whether it ran in shared-runner mode.
2. **N comes from the ledger, and every opening counts.** Each execution that opens the holdout is
   a trial, whatever its outcome, including one abandoned after a crash. A researcher's execution
   runs twice; any disagreement rejects it. A failure tells the researcher only "execution failed".
   Researchers cause appends only, and send weights, never returns. An execution refused before
   opening is no trial but is recorded and counts in the execution quota. Each researcher has at most
   one execution in flight, and its slot frees only once the runner confirms the job stopped.
3. **The sealed code is the code that runs, in a launch the agent verifies.** The service stores a
   `git archive` of the sealed commit and runs only that snapshot. The runner agent starts it under
   gVisor with the launch profile in §4 and, before the first message that loads strategy code,
   checks that profile on the running container; the profile's hash is recorded with the execution.
   At step *t* the strategy receives only rows known by the decision time.
4. **Tampering is evident, and the service fails closed.** After every append the service writes
   (count, head) to a witness log. The running service refuses a holdout whose ledger no longer
   chains, no longer matches its witness, or no longer extends the head it last verified (§3).
   `lockrun-risk verify` checks the same from disk, plus anchors exported off-host.
5. **No PASS without reproduction.** Risk sets the threshold and min_t per holdout. A passing
   promotion stays `pending_verification` until risk re-runs it on a fresh verify runner and gets a
   bit-identical returns hash. Fresh means: a build_id seen in no holdout's ledger nor the bindings
   log, and a name never bound and never used for a researcher's execution.
6. **One runner per researcher.** A researcher's executions run only on the primary runner bound to
   them in the bindings log; a researcher with none is refused (§4).
7. **Every verdict states what it was computed from.** The promote record (hashed in the ledger)
   carries the holdout, the ledger's count and head, the bindings-log head and the witness head it
   was computed from, and whether any counted opening ran on a shared runner.
8. **A verdict can be checked by anyone, offline.** Risk signs each verdict with an Ed25519 key
   that never reaches the service host, after checking it. `lockrun-verify-verdict` checks the
   signed verdict with nothing but risk's public key and clones of two public append-only
   repositories (§3a).

## 2. Actors, secrets and trust boundaries

**Researcher:** untrusted, root on their own machine. Holds a bearer token (static, revocable by
risk), the certificate pin and a git repository. **Risk:** trusted, root on the service and runner
hosts. **Service:** the only holder of secrets. **Runner:** risk-owned, one per researcher, runs
that researcher's strategies; state that survives a job is listed in `RUNNER_PERSISTENCE.md`.

| Secret | Where it lives | Who can access it |
|--|------|------|
| Holdout key | Service host, 0600, in the service user's 0700 state directory | Root and the service user. Not researchers, runners or the sandbox |
| Holdout data | Decrypted in memory per execution on the service; streamed step by step over SSH to the job | Root on the service host; root on the job's runner (that job's rows). Strategy code sees every row by the end of a run |
| Ledgers, bindings log, witness logs | Service host: hash-chained JSONL, witness logs `chattr +a` | Researchers read (head, count) through the API. Root can rewrite all of them (§3) |
| Risk's verdict-signing key (Ed25519) | Risk's laptop, `deploy/p3/out/risk-key/`, 0600 (later an HSM) | Risk. Never the service host, the runners or the operator droplet (§3a) |
| Verdicts deploy key | Risk's laptop, same directory | Risk: write access to the verdicts repository only |

**Boundaries.** *Researcher → service:* TLS 1.3 with a pinned certificate, a bearer token, seven
JSON endpoints, 64 KiB bodies, daily per-researcher quotas, an allowlist of repository URLs per
researcher. *Service → runner:* SSH with a pinned host key and a forced command; the runner holds no
credential to the service. Before anything is decrypted the runner's build_id and image ID are checked
and its CPU flags reported, and its build_id must be the one bound to the researcher.

## 3. Root on the service host

**Can, from the moment of compromise onward:** decrypt every holdout; read and forge any record;
issue tokens; bind or rebind runners by writing the bindings log; make the service lie in every
answer; stop exporting anchors (visible as a cadence gap); rewrite the local ledgers, witness logs
and bindings log together, with recomputed hashes.

**Cannot:** change what was deposited off-host. Anchors (count, head, time, chained) are pushed to a
git repository whose `main` the git host protects; `anchor verify-repo` flags any commit that does
more than append, and checks every anchor ever pushed against the ledger. History up to the last
deposited anchor therefore cannot be rewritten undetected; a verdict whose `computed_from` heads lie
inside the anchored history can be checked by risk with `lockrun-risk verify --anchors --verdict` on a
copy of the ledger. **Immutable off-host storage protects the past, not the future:** nothing here
constrains what a root attacker writes after the last anchor, and the anchors' times are the
service host's own.

**Who detects what.**

| Change to the files on the service host | Running service | At restart / `verify` | Only off-host anchors |
|--|---|---|---|
| Edit of a record (chain broken), or a torn line | refused on the next read | detected | |
| Ledger cut at a record boundary, witness left | refused (witness mismatch) | detected | |
| Ledger and witness cut, or rewritten, together | refused (does not extend the head it verified) | accepted after a restart; `verify` passes | **detected** |
| Mid-ledger edit, then a valid record appended on the real head | not seen (only new lines are read) | detected (chain) | |
| Bindings log rewritten consistently | refused while running | `verify <holdout>` fails: openings name heads no longer in it | detected |
| Verdict computed on a ledger later cut and re-anchored | | | `verify --verdict` fails |

## 3a. Signed verdicts

**Who signs what, and when.** There are three kinds of record and one key.

- **Verdicts:** risk signs them with `K_risk` on the laptop, by running `./do.sh sign-verdicts`
  after the hourly deposit that follows a promote. Both PASS and FAIL verdicts are signed.
- **Anchor deposits:** these are not signed. The service host holds no signing key: from a
  compromise onward root would sign whatever it liked, and before one the protected git history
  already proves what such a signature would.
- **Bindings records:** these are not signed one by one. Each gets its own anchor line, and every
  signed verdict covers the bindings head it was computed under.

The deposit anchors every promote record and every bindings record at its own count, so a
verdict's anchor line names exactly its record hash.

**What sign-verdicts checks before signing.** On a copy of the service's ledgers, witness logs and
blobs (read under the append lock), it:

- checks every chain it signs from against its witness log and against every anchor ever
  deposited, in an anchors history with no tamper alarm;
- checks that each verdict's `computed_from` is the ledger read just before it;
- recomputes the verdict from the records before it, with the service's own code.

The verdict, N and threshold must be identical, the other fields too, and numbers must agree
within 1e-12. It stops, signing nothing, on anything else. The signature covers the promote record
exactly as recorded, its anchor line, and the bindings head with its anchor line. Each signed
verdict is appended to `verdicts.jsonl` in its own public repository, under the same append-only
ruleset. That repository is written only with risk's laptop key: the service's anchors key cannot
write there.

**What `lockrun-verify-verdict VERDICT PUBKEY ANCHORS_CLONE VERDICTS_CLONE` checks, offline:**

- the signature under the given key;
- that the record hashes to itself and follows its `computed_from`;
- that both anchor lines are in the anchors repository's history, first committed where the
  statement says, with intact chains and no tamper alarm;
- that the verdict is in the verdicts repository's history.

**A valid signature proves:** at signing time, the holder of `K_risk` found the logs intact and
consistent with everything deposited so far, and the same code gave this verdict from them. The
verdict, and the bindings head it names, are anchored in the public history. Nothing anchored before
a compromise can be rewritten or removed afterwards, so N cannot be lowered retroactively, and the
signed record cannot be swapped for another.

**It does not prove:**

- **From a compromise of the service host onward,** root can append records that are consistent
  with each other: a candidate's returns, its fresh verification, extra openings. Risk's
  recomputation then agrees with them. Closing this needs outputs signed on the locked runners;
  that is not built.
- **That `K_risk` and the code are sound.** A stolen laptop key signs anything. The DSR is
  computed by lockrun's code, which the verifier runs and may read. A third party cannot recompute
  the DSR: the trials' returns stay private.
- **When something was signed.** `signed_at` and the commit dates are set by the signer. A
  rewritten GitHub history makes verification fail; it cannot make a forgery pass.

**Rotation and old verdicts.** Keys are identified by the sha256 of the raw public key. A verifier
gets the public key from risk directly: never from a repository, which the service host (the
anchors) or risk's laptop (the verdicts) can write.

- **Planned rotation:** create a new key and run sign-verdicts. It signs every verdict again, since
  verdicts are skipped only when this key has already signed them. Old signatures stay valid under
  the old key: Ed25519 has no expiry.
- **Compromise:** the old key's signatures can no longer be told from forgeries, because
  `signed_at` is the signer's own claim. Re-signing with the new key is the remedy. The verifier
  accepts the key it is given, so a verdict is then checked against the new key.

## 4. Runners

**Model.** Each primary runner is bound to exactly one researcher in the bindings log
(`ledgers/@runners.jsonl`: chained, witnessed, anchored and verified like a holdout ledger). Only
`lockrun-risk` binds; a binding never moves. A dead runner is replaced: the new one is bound to the
same researcher and the old retired in one record; a retired runner never runs again. The worker
reads the log at dispatch, and the runner must answer with the bound build_id. **Routing proof:**
every opening names its runner and the bindings-log head; `verify` checks each against the binding
valid at that head. Verify runners are registered in the bindings log and can never be bound.
**Shared-runner mode** (`--allow-shared-runners`, development only) is recorded on every execution
record and in every verdict computed from such an opening; `verify` passes those only as flagged.

**Launch profile, enforced and verified in code (podman-runsc):** no network (Podman and runsc
itself); read-only root; exactly one writable tmpfs, `/tmp`, size-capped, `nosuid,nodev`; no
`/dev/shm`, no Podman-added tmpfs, no generated `/etc/hosts` or `resolv.conf` (and the image has neither, since 15 October 2026); the only host path is
the job's snapshot, read-only; every capability dropped, `no-new-privileges`, uid 65534; gVisor as
the only accepted runtime, its default seccomp filters never overridden; memory (no swap), CPU and
task limits per runner; a wall-clock timeout that kills the job and records it failed. After every
job the container, its tmpfs and its work directory are removed; a job whose agent died is reaped by
the next session (never a protected process group).

**Not enforceable in code** (`RUNNER_PERSISTENCE.md`): a process limit inside gVisor (only memory
bounds a fork flood); the runsc flags (not visible to inspect, pinned as passed); that inspect and
`systemctl show` report what the agent expects (checked against a stand-in, and once against a live
launch on Podman 4.9.3: `tests/data/podman-4.9.3-live-launch.json`); `/etc/hostname`
and `/run/.containerenv`; gVisor's overlay and state directory; image layer content under a matching
ID; host firewall, swap, core dumps, file ownership; shared hardware state; that a runner was really
rebuilt (its build_id is a file root can rewrite).

**Verified live, 14 October 2026.** Every `runner-check` gate (B0–B7, A1, C1–C2, D1–D4, E1–E6,
F1–F4, G1–G2, H1: 28 of 28 on two rebuilt runners), every `check-service` gate, the launch check and
the launch profile ran against a live deployment: DigitalOcean nyc2, Ubuntu 24.04 (kernel 6.8),
Podman 4.9.3, gVisor `runsc` release-20261005.0. A job's recorded profile hash equalled the agent's
expected profile on both runs of an execution, and a live inspect document is kept as a test fixture
(`tests/data/podman-4.9.3-live-launch.json`). Five bugs only the live run found, each now a
regression test:
1. The runner could not see root's image store: Podman creates its metadata directories 0700, and
   Podman 4.9.3 applies none of `storage.conf`'s options once `--root` is given. Now read access is
   granted and the store is passed as `--storage-opt` (`f9b8f96`).
2. Every job failed before it started: Podman refuses `--dns=none` with `--network=none`. The fake
   accepted it and the checks' own containers never passed it. The flag is gone (`df9ca27`), and
   gate E6 now launches exactly as the agent does (`8517b52`).
3. The launch check refused every live job, failing closed, on two fields where Podman differs from
   its documentation: `EffectiveCaps` is null with every capability dropped, and each tmpfs carries
   Podman's own `rprivate,tmpcopyup` (`e2b1834`).
4. A container's writable layer, owned by the container user's subuid, survived its removal: the
   runner user's `rm -rf` and the agent's `rmtree` cannot delete it. Job and check directories are
   now removed inside `podman unshare`, and a leftover is a hello problem and fails gate H1
   (`4090eb3`, `263e678`).
5. Root's image store held directories owned by `_apt` (uid 42) from the base image's layer. Root now
   owns the whole store (`b6a9cc4`). Since 15 October the image is one squashed layer, every file
   0:0, with no `/etc/hosts` or `resolv.conf` (`sha256:ce7695aa…`, `319d7dc`): provisioning finds
   the store root-owned as loaded, and its chown stays as a safety net.

The same day's deployment-tooling failures (a droplet listed without an address, firewall rules
applied a minute after a retag, a runner-check syntax error, update-agent's working directory, a
masked unit left failed, `anchors-verify` refused by git's ownership check) are fixed and tested in
`deploy/p3`.

**Nightly rebuild.** Every runner is rebuilt nightly from the pinned image (`do.sh recycle-all`, on
the operator droplet `lockrun-p3-ops`); the bindings log records each replacement; an escape persists
at most until the next rebuild. A replacement is registered only after the new runner passed every
gate, and the old runner is destroyed only after the bindings log shows the change. `check-service`
fails (E7) when any runner is older than `RUNNER_MAX_AGE_H` (36 h by default), so a missed night shows
the next day. The nightly timer first ran on its own on 16 October 2026 (exit 0, both runners rebuilt;
`docs/WHAT_IS_VERIFIED.md`). The operator droplet holds a
DigitalOcean token and an admin key: root there can rebuild, replace or destroy runners and log into
them as root, through the service. It holds no holdout key and no ledger, it cannot bind a runner
(only `lockrun-risk` on the service writes the bindings log), and every replacement it makes is in
that log. The service host holds no cloud credential.

**Between runners, the cloud firewall** (runners accept tcp 22 from the service's tag only and send
nothing) **is verified by configuration and by its propagation behaviour, not by a live probe.**
`do.sh check-firewalls` compares the live rules with the generated ones; a runner just retagged
locked was unreachable from the service until DigitalOcean applied the rule, then reachable
(2026-10-14). A probe from one runner to another never reaches the cloud firewall: the source's own
ruleset drops it first (verify-1 to the primary on tcp 22: a timeout, its 5 SYNs counted as egress
dropped), and lifting a locked runner's ruleset to test the layer behind it is not done.

**A researcher who escapes gVisor** to the runner host, as the runner user in its user namespace,
**gains:** the rows of their own job (which their code already saw), and a place to persist across
their own later jobs on that runner until its next rebuild (at most a night, below). They cannot change Podman's configuration or the image:
both are root's (`/etc/lockrun/containers.conf` and `storage.conf`, the read-only store
`/var/lib/lockrun/images`), not writable by the runner user, which the agent's hello and
`runner-check` E5 check; each job's writable store is its own and removed with it. They can make
the agent's checks and job counts fail, which holds their own slot (fail closed). With root on the
runner as well, they can also alter image layers under the pinned ID (the launch check does not
read layer content) and forge the agent's hello and launch profile, so the recorded profile hash
proves nothing for that runner. **They do not gain:** the
holdout key or any other holdout's rows; other researchers' jobs (separate runners); any credential
to the service (SSH runs service → runner only, under a forced command); a way to change N or the
ledgers (the opening is recorded before any row is sent); a PASS, which needs a bit-identical rerun
on a fresh runner built from scratch.

<!-- launch-profile-as-observed: generated by deploy/p3/launch_profile_page.py -->

## Launch profile as observed

One job launched with the agent's own argv on a live runner (Podman 4.9.3, gVisor, nyc2, lockrun-p3-runner-tester3, 15 October 2026), as `podman container inspect` and `systemctl show` reported it; generated from `tests/data/podman-4.9.3-live-launch.json`, never edited by hand.

| Setting | Observed |
|---|---|
| Image | `ce7695aab450f6f1641dbd7213d4680a0d07aa5709bf24029ca19efd09868914` |
| Runtime (`OCIRuntime`) | `runsc-lockrun` |
| Network (`NetworkMode`) | `none` |
| IPC (`IpcMode`) | `none` |
| Root filesystem (`ReadonlyRootfs`) | `true` |
| Privileged | `false` |
| User (`Config.User`) | `65534:65534` |
| Working directory | `/tmp` |
| `EffectiveCaps` / `BoundingCaps` | `null` / `null` (null: none; the agent reads a present null as no capabilities) |
| `CapAdd` | `[]` |
| `CapDrop` | `["CAP_CHOWN", "CAP_DAC_OVERRIDE", "CAP_FOWNER", "CAP_FSETID", "CAP_KILL", "CAP_NET_BIND_SERVICE", "CAP_SETFCAP", "CAP_SETGID", "CAP_SETPCAP", "CAP_SETUID", "CAP_SYS_CHROOT"]` |
| `SecurityOpt` | `["no-new-privileges"]` (no seccomp override: gVisor's default filters) |
| Tmpfs | `/tmp` `rw,size=64m,mode=1777,nosuid,nodev,rprivate,tmpcopyup` (Podman adds `rprivate,tmpcopyup` itself) |
| Mounts | `/code` bind, read-only, options `["nosuid", "nodev", "rbind"]`, propagation `rprivate` |
| Memory and tasks in Podman | `Memory` `0`, `PidsLimit` `0` (0: the limits are on the systemd scope, below) |
| Scope `CPUQuotaPerSecUSec` | `1s` |
| Scope `MemoryMax` | `1073741824` |
| Scope `MemorySwapMax` | `0` |
| Scope `TasksMax` | `512` |

The agent's launch check read this as the profile it asked for (every field matches), for limits 1024 MiB, 100% CPU, 512 tasks, a 64 MiB tmpfs and a 30 s timeout. Profile hash: `7eb5b9592362d172fde97694587347b741fcc5444de5e2367b8f47b2fa389d81`.

<!-- /launch-profile-as-observed -->

## 5. Known gaps

- **Same data elsewhere.** Trials run outside lockrun on public copies of the data are invisible.
- **Rule-aware dummy trials** can lower trial-Sharpe variance to its floor and raise the DSR
  undetected (internal red team). Effective-N is out of scope.
- **Failed trials in V (two statistical rules, for external review).** Late failures (k ≥ T/2)
  enter V zero-padded (`zero_tail`). Since 15 October 2026 early ones do too, once their outcome
  is recorded: padded to T when that is a valid series, else a Sharpe of exactly 0
  (`zero_sharpe`). The verdict is the lowest DSR with and without them, so adding failed trials
  can only make it stricter (`tests/test_early_failures_in_v.py`). The only promote block left is
  an opening of one's own with no recorded outcome. Before, an own config that never returned
  blocked its researcher on that holdout for good. Open for review: whether a Sharpe of 0 is the
  right placeholder for an opening that produced nothing, and how a placeholder 0 should interact
  with the dummy detector, which never sees it.
- **Output channel.** Per execution: success or failure, Sharpe/skew/kurtosis rounded, completion
  time; per promote, statistics over all trials at 3 significant digits. Ceiling about 45–50 bits
  per execution, by counting values.
- **Full disk** halts the service or leaves an unwitnessed line (a false tamper alarm).

## 6. Where an external reviewer should look first

1. **The launch check on a live runner.** Inspect and `systemctl show` field names, Podman's `--rm`
   and `rm --force`, and its default tmpfs mounts were exercised only against `tests/fake_podman.py`.
2. **The gVisor boundary** for hostile code holding holdout rows: no in-guest process limit, the
   rootless user mapping, and what a runner-user escape can reach on the host.
3. **Restart after a consistent cut.** A ledger and witness cut together are accepted after a
   restart; only off-host anchors catch it. Should startup require a fresh anchor match?
4. **Mid-ledger edits under a running service.** Only new lines are verified between restarts.
5. **Anchors:** who owns the repository, the cadence window, self-reported times, and that `verify`
   runs with the service host's own code and files. Since 16 October 2026 an anchor's count may go
   back, to a verdict or bindings record anchored late; the record it names is checked like any other.
6. **Signed verdicts (§3a):** what sign-verdicts recomputes and what it only compares
   (`lockrun/service/sign.py`), the 1e-12 tolerance, that the verifier trusts the statement's anchor
   commit only as far as the git host's history, and the gap from a compromise onward.
7. **Deployment state.** The P3 deployment predates bindings (one shared runner; its openings are
   reported as predating the bindings log), and its `do.sh` accepts a single primary runner.
8. **Failed trials in V:** the zero-tail rule and, since 15 October 2026, early failures as
   zero-padded series or a Sharpe of 0 (`lockrun/trials.py`, `_add_failed_opening`), and the
   promote block reduced to openings with no recorded outcome.
9. **Fresh-runner procedure:** "rebuilt" is not provable in code; an abandoned verify-fresh claim is
   closed without the verify runner confirming its job stopped.
