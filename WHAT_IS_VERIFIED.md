# What is verified

For a risk team or an external reviewer. Three lists: what ran on a live deployment, what only the
test suite shows, and what we cannot verify. Status as of 29 October 2026: the backups and a full
restore (plan item 4, deploy/DISASTER_RECOVERY.md) ran live as a drill on the nyc2 deployment that day
(below); the outage rule decided during it (THREAT_MODEL.md §5) ran live in part. As of 27 October 2026: researcher-signed
requests (plan item 1, THREAT_MODEL.md §2 and §3) ran live on a deployment built from zero that
night; the data host (claim 10: the service never holds the holdout) the day before, and runner
signatures (claim 9) the night before that (all below); the rest is as of 18 October. The
adversarial tests of plan items 2 and 3, their fixes, and the statistical rule that plan item 3 led
to, the joint bar (section 2 and THREAT_MODEL.md §5a, 27 October), and its version 2 (the plain
t-statistic for every new holdout, 30 October), have run only in the suite and the standalone
simulations: the live deployment runs code from before them.

## 1. Verified on a live deployment

**The disaster-recovery drill (29 October 2026, 13:20–23:05 UTC).** On the nyc2 deployment
(`s-1vcpu-2gb-amd`, Ubuntu 24.04). Storage: Backblaze B2, bucket `lockrun-p3-backups`, us-east-005,
Object Lock in COMPLIANCE mode with a 30-day default retention. The service and the data host were
destroyed and rebuilt from the backups; a run with a pending verification was carried across the
restore and verified and promoted afterwards.

- **The steps, in order:**
  1. Item 4's code onto the deployment (ops-pull, ops-sync, provision-ops, prepare-service,
     update-service), and recycle-data from data-3 to data-4 (13:22–13:32Z). The storage check then
     passed once the bucket had a default retention.
  2. The backup key made in the escrow (risk's key directory stood in for it), backup-certs,
     ops-sync, then backup-timers: full backups 1419Z and 1443Z, uploaded write-once and recorded in
     the bindings log.
  3. Increment 1 (anchors commit `80bd867`), one execution and one promote on demo-3 (run
     `6694c40c6039`, verification pending), increment 2 (`8bccf81`, demo-3 from 21 to 25 records).
     Each increment's manifest names the previous manifest and the anchors commit it preceded.
  4. Ops' increment timer stopped at 14:47Z; the service and data-4 destroyed. The last anchor was
     14:45:39Z.
  5. On the laptop: the chain fetched from B2 with risk's read-only key, byte-identical to the copy
     on ops; opened in the escrow; backup-verify and restore-attest: deployment "resume", cause
     not-compromise, every log resuming at its anchor (@runners 25, demo-1 14, demo-2 26, demo-3 25).
  6. restore-service (a virgin host, closed, answering 503), restore-retire (tester3 at counter 4,
     verify-5/6/7 at 0, data-4's final at 4), the deploy keys rotated; the second attempt from
     16:16Z, 6 min 38 s to provision the host. restore-data onto data-5 (16:30–16:37Z, every holdout
     and stream installed, bound with data-4's final). Two new runners, tester4 (primary, bound to
     tester) and verify-8 (16:39–16:58Z).
  7. restore-open (21:12Z): every log opened, TLS rotated, the one token reissued, the K_risk-signed
     pin notice (re-signed at 21:40Z, below).
  8. Every gate: check-service, check-data, check-runner on both runners, check-firewalls, and
     `verify` on @runners (32 records) and each holdout. Ops authorised on the new service, a full
     backup (2202Z), the anchors installed on the new host and a first deposit (22:03:26Z).
  9. The outage rule's pieces: the signed restore line deposited; backup-timers (ops' own anchors
     key added, full backup 2257Z, the service's timer off, ops' increment on); increments 1–3 of
     2257Z, the third from the 23:00 timer; the heartbeat job installed in
     `giusefrr/lockrun-anchors-demo5`, one manual run (nothing to append).
  10. verify-fresh on `6694c40c6039` with verify-8: match. Promote: PASS (demo-3 record 30).
      sign-verdicts, then verify-verdict from fresh clones: OK, the verdict anchored at `02f992b`,
      the bindings head at `b7bdd11`. check-backups: ok.
- **Fixes, each a regression test and a commit:**
  1. SigV4 signed the query `%2F` as `%252F` (`fddce41`).
  2. B2 answers 501 to `If-None-Match`: `conditional_put: false` checks the versions listing before
     each put, and every read refuses a key with more than one version (`fe3f9a2`).
  3. An old anchor-deposit.sh on the service ignored the commit and push modes and pushed before
     any increment: backup-timers reinstalls it (`debf286`), and the increment refuses unless the
     service's copy is ops' (`2d9b49d`).
  4. No command fetched a backup from the store: `python -m lockrun.backup fetch` (`b6bfae0`).
  5. restore-load failed on the append-only witness directory (a rename), and wrote the closed
     marker last, leaving the service open with restored tokens for a moment: witness logs by
     exclusive create (`656f397`), the closed marker first (`d3f2b47`).
  6. restore-open refused the new runners bound before it, as the design says to do: `runner_bind`
     and `verify_runner` may follow the attested head (`4feb752`).
  7. The pin notice took the new host's pin as the previous one: the service prints the lost host's
     (`335a63c`).
  8. restore-service did not let ops' key into the new service, so ops' backup failed
     (`37b2cd4`).
  9. anchors-verify refused `@runners` (`5dd0939`).
- **The outage rule (risk's decision of 29 October: no gap is ever accepted).** The drill left the
  anchors silent from 14:45:39Z to 22:03:26Z, because the deposits were still on the service's own
  timer. The rule closes that: ops deposits when the service is unreachable (`3b3f8fb`); the anchors
  repository's heartbeat (`b757234`); the B2-dated rule at restore and the signed restore line
  (`47e3c53`, `a4a3838`); a heartbeat never stalls a deposit (`3e6edc8`). backup-timers runs before
  any holdout is initialised (`197456b`). Live: the restore line, ops' key and clone, and the
  heartbeat job. Suite only: ops' deposit with the service down, a heartbeat appended by the job,
  and a deposit re-applied over one.
- **Not passed:** anchors-verify on every log fails, for good, on that 7 h 17 min gap. The rule
  accepts no gap, and the repository's history keeps it. Risk's pin of the repository stays at the
  last commit verified before it.
- **Timings:** a service host from create to provisioned, 6 min 38 s; a data host to locked and
  checked, 6 min 27 s; a runner to locked and checked, 8 min 50 s (tester4) and 8 min 34 s
  (verify-8); restore-open, seconds; a full backup and its upload, about 5 s of CPU on ops; an
  increment, about 5 s. The service was down from 14:47Z to the open at 21:12Z, almost all of it
  spent finding and fixing the faults above.

**Researcher-signed requests, from zero (26–27 October 2026, 23:22–02:13 UTC).** `demo-from-zero
--researcher tester --holdout demo-1 --anchors-repo giusefrr/lockrun-anchors-demo4 --verdicts-repo
giusefrr/lockrun-verdicts-demo4 --ops` on an empty account: nyc2, `s-1vcpu-2gb-amd` for every droplet,
Ubuntu 24.04. 69 steps, the last two the cutoffs (`require-signatures`,
`require-researcher-signatures`); the data host requires a signed request from provisioning. Then
the checks below. 1 h 57 min to the cutoffs, with two fixes and 1245 s waiting for the operator's
token on the ops droplet.

- **Six bugs, each a regression test and a commit; for the two found live the run resumed at the
  step that failed:**
  1. Before the run, a test that failed 2 of about 12 parallel runs: the data host refuses an
     oversized install on the request line alone and closes its side; when the laptop wrote the
     ciphertext only after that, it reported "dropped the session" instead of the refusal. The
     caller now reads the answer after a closed pipe (`8e46557`).
  2. Before the run, `reset-local` left the researchers' certified keys and the demo researcher's
     private key in `out/`, which the next demo would have reused (`c2fc89f`).
  3. Before the run, `reset-local` kept `out/holdouts/`, so `holdout-init demo-1` would have refused
     the id, and the demo wrote the new plaintext over the kept one before that refusal. The holdouts
     now move with the deployment (`06517c6`); the demo refuses before writing (`c3529b1`).
  4. Step 39, `retag-locked lockrun-p3-verify-1`: right after the untag, DigitalOcean's tag count was
     already 0 while the droplet list still showed the tag, and the guard refused. Each tag change now
     waits, bounded, for the list (`c274b31`).
  5. Step 51, `anchors-verify demo-1`: "no risk key to check a fresh verification's request with".
     `anchor verify-repo` took no issuers, so every holdout with a fresh verification failed it. It
     now takes risk's own public keys, which `do.sh` sends from the laptop (`fc8f78b`).
  6. After the demo: every execution logged a false `ALERT runner_statements_recovered ... 0 signed
     statement(s)`. The alert now fires only when something was recovered (`ff4eca4`).
- **A replayed request, refused at every layer** (`redteam/replay_p3.py`, `c7f2a72`), within the
  request's 15 minutes, right after the execution it opened (run `dec568d35ea1`):
  - root on the service sent it to the data host over the service's own session: refused, "this
    request was used before: a request opens one execution", no opening;
  - root on the data host, running the data host's code with its nonce check removed, sent it to
    the runner: the agent refused, "this request was used before on this runner", nothing sent to
    the service and no record;
  - through the API, the service refuses it (403) before queueing (the suite; not repeated live).
- **A request signed by another key:** `HTTP 403: the request is not signed by tester's current key`,
  at the API, before anything was queued or recorded.
- **The refusal-time bound:** a run sealed with an `as_of` inside the holdout (2024-05-21), refused
  by the data host 1.9 s after its seal (`execution_refused`, `leaked_as_of`), was shown done to the
  researcher 310 s after the execution started (`refused_done_s`, against the 270 s bound
  `MIN_REFUSED_DONE_S`); the client saw it done after 311.0 s, as "execution failed".
- **Executions and verdicts:** tester's executions before and after the cutoffs returned clean
  (Sharpe 0.441 each), each opening carrying its signed request; both fresh verifications ran on
  K_risk-signed requests and matched (verify-1, verify-2). demo-1 #11 (run `a4a4c4a382c4`, N 2) and #26
  (`dec568d35ea1`, N 4), both PASS, signed by `sign-verdicts` after the full replay; `verify-verdict`
  checked each from fresh public clones; `anchors-verify` (with risk's key) passed.
- **Every gate on every host:** `check-service` (four times), `check-data` on data-1, data-2 and
  data-3, `check-runner` on tester, verify-1, tester2, verify-2, tester3 and verify-3 (R1, K1, K2, F5
  and H1 included), `check-firewalls`. No failure.
- **Recycles:** two `recycle-all` from the ops droplet, 1320 s (tester → tester2 629 s, verify-1 →
  verify-2 666 s) and 1311 s (tester2 → tester3 640 s, verify-2 → verify-3 646 s); two `recycle-data`
  from the laptop, data-1 → data-2 (497 s) and data-2 → data-3 (500 s). `verify @runners` afterwards:
  14 records, every binding rule, counters complete for 6 runner keys and 3 data host keys, every
  request nonce used once. The risk report: N 4, both verdicts signed, anchors verify OK.
- **Execution time on the service's clock** (opening record to outcome record): 10.7 s before the
  cutoffs and 7.5 s after (10.9 s from the seal); 3.5 s and 3.6 s per fresh verification.
- **Timings:** `build-image` 66 s, `provision-service` 389 s, `check-service` 28–34 s,
  `provision-data` 284–314 s, `check-data` 10–21 s, `provision-runner` 298–356 s, `check-runner`
  171–176 s, `holdout-init` (the demo's holdout step) 11 s, `demo-execute` 16–19 s, `verify-fresh`
  19–20 s, `sign-verdicts` 10–13 s, `verify-verdict` under 1 s.

**The data host, from zero (26 October 2026, 12:35–16:20 UTC).** `demo-from-zero --researcher tester
--holdout demo-1 --anchors-repo giusefrr/lockrun-anchors-demo3 --verdicts-repo giusefrr/lockrun-verdicts-demo3
--ops` on an empty account: nyc2, `s-1vcpu-2gb-amd` for every droplet (`DATA_SIZE` left at `SIZE`),
Ubuntu 24.04 (kernel 6.8.0-142), gVisor `runsc` release-20261019.0. 67 steps, the last the cutoff; then
the checks below. The service host held no holdout key, ciphertext, series or weights stream at any
point.

- **Five bugs only the live run found, each a regression test and a commit, the run resumed at the
  step that failed:**
  1. Step 24, `github-verdicts-key`: GitHub puts a deploy key on one repository only, and the laptop's
     one verdicts key was still on the previous deployment's repository (422 "key is already in
     use"). Each verdicts repository now has its own key (`d38489f`).
  2. Step 26, `provision-data`: `No module named 'lockrun.data'`. The wheel's explicit package list
     lacked the new package; the suite, run from the source tree, could not tell. A test now checks
     every package and console script against the list (`a57025e`).
  3. Step 29, `check-data`: two gates failed on a correct host. G1 looked for the drop rule without
     nft's counter text; G3 counted systemd-resolved's stub, listening on loopback only. Both are now
     tested on the live host's own ruleset and listeners (`7c7ef34`).
  4. Step 45, the first execution: "no hello from the runner agent". The runner's host ruleset let
     only the service in; the data host, which opens each run's session, was in the runner's cloud
     firewall and authorized_keys but not in its nftables. It now admits SSH from the VPC range too,
     as the data host's key entry does (`02c1288`). Refused before opening, as designed: an
     `execution_refused` record, no trial.
  5. Step 65, the first `recycle-all` from the ops droplet: the ops droplet lacked the data host's
     public SSH key, which every new runner trusts as its only exec key (`104172b`).
- **Two handovers with a real holdout:** `recycle-data` from the laptop, data-1 → data-2 (479 s, after
  `check-data` rightly refused data-1, whose installed checks predated fix 4) and data-2 → data-3
  (559 s). Each time the old data host encrypted demo-1, its series and weights streams and the
  runners' SSH key to the new one's K_risk-certified handover key, signed its handover and final
  statements, and was destroyed only after the new one passed `check-data` and `verify @runners`.
  No runner changed.
- **The laptop's route to the data host, through the service as a jump host:** `holdout-init` encrypted
  demo-1 on the laptop and installed it under K_risk's signature (11 s); `verify demo-1 --holdout-file
  --data-host` on a copy of the ledgers fetched every weights stream from data-3 under K_risk-signed
  requests: 4 executions' signed streams replay to their outcomes, 2 promotes' detector flags
  recomputed from the replayed series.
- **Executions and verdicts:** two of tester's executions, before and after the cutoff, each returned
  clean (Sharpe 0.529) and matched on a fresh verify runner; both promotes took the data host's
  signed detector answer. sign-verdicts signed demo-1 #14 and #24 (PASS) after the full replay through
  the data host, 0 refused; `verify-verdict` checked both from fresh public clones.
- **Every gate on every host:** `check-data` on data-1 (twice rebuilt), data-2 and data-3; `check-runner`
  on six runners (tester2, tester3, verify-2, verify-3 and the two the ruleset fix replaced), F4 (two
  restricted keys) and F5 (only the data host's key starts a job) included; `check-service` with E7
  and E8; `check-firewalls`. No failure after the fixes.
- **Recycles:** `recycle-all` from the ops droplet rebuilt runners only (1270 s: tester2 → tester3 in
  604 s, verify-2 → verify-3 in 639 s, each certified with K_ops); `verify @runners` afterwards: 12
  records, counters complete for 6 runner keys and 3 data host keys. risk-report written.
- **Execution time on the service's clock** (opening record to outcome record): 6.9 s and 6.4 s per
  execution (two runs), 3.3 s and 3.2 s per fresh verification (one run); 8.2 s before the data host.
- **Timings:** `provision-data` 312–329 s, `check-data` 16–23 s, `register-data` 20 s, `provision-runner`
  332–357 s, `check-runner` 175–177 s, `holdout-init` 11 s, `sign-verdicts` 10–12 s, `recycle-data`
  479 and 559 s.
- **Not explained:** one runner recycle failed when its check session to the new runner, relayed by
  the service, broke after hanging about 30 minutes (`Broken pipe`); the service logged no
  disconnect. With one API connection timeout earlier, both from the same laptop, it reads as that
  network dropping long-lived sessions. The recycle left the old runner in place and destroyed the
  new one, as designed; the retry passed.

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

2143 tests (`uv run pytest`, 27 October 2026, with `LOCKRUN_REQUIRE_OPENSSL=1`). The stand-ins:

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

**Adversarial tests (plan item 2, 27 October 2026): 153 tests, `tests/test_crypto_*.py`.** Each
builds a tampered copy of one honest deployment (`tests/crypto_world.py`: two holdouts, a signing
data host, two researchers with certified keys, every cutoff, executions, a promote PASS after a
fresh verification, anchors deposited twice, the verdict signed and published). Root's tampering is
consistent: every later hash recomputed and the witness log rewritten. Each test expects the right
check to refuse it: `lockrun-risk verify`, `anchor verify-repo`, `sign-verdicts`,
`lockrun-verify-verdict`, or the service at startup and on reload. Eight attacks:

1. **Replay of records** (`test_crypto_replay.py`): a record copied into another log, or again
   into its own. *Found and fixed* (`710a8e7`): a record of a type foreign to its log, or of a type
   nothing writes, was accepted. Each log now has an explicit set of record types, and anything
   else is a chain error for `verify`, the store, startup and reload.
2. **Rollback between anchors** (`test_crypto_rollback.py`): held.
3. **Truncation and reordering** (`test_crypto_truncation.py`, `test_crypto_references.py`).
   *Found and fixed* (`9399882`): a record naming a record that is not earlier in its chain (a
   forward or missing reference), and witness entries out of order, were accepted. Every reference
   from one record to another (each record type audited, each reference pinned by a test) must
   point earlier; witness counts must strictly increase.
4. **A signed verdict with a field changed, its signature kept** (`test_crypto_verdict_fields.py`):
   held.
5. **Canonicalization** (`test_crypto_canonical.py`). *Found and fixed* (`2c70283`, `a0bb40a`): two
   values that read the same (a string in NFC and in NFD, 1 and 1.0) were accepted as different
   records. From a cutoff (`require-canonical-values`, marked in every ledger) a non-NFC string or
   key, or an integral float, is refused at write and on read. The store writes canonical values, and
   the researcher's client normalizes seal params, but the API refuses a raw form. Records from
   before the cutoff are read as written. The requirement holds from the marker or from a record
   naming a bindings head with the cutoff, so removing the marker does not switch it off.
6. **A missing or extra anchor** (`test_crypto_anchors.py`): held. A history force-pushed with the
   file unchanged passed `verify-repo`, relying on the git host's ruleset. It is now refused by
   risk's pins of both repositories (`6a847b8`, section 3).
7. **Key confusion** (`test_crypto_keys.py`): held. Signing domains are distinct and none is a
   prefix of another; only risk certifies a data host or a researcher key.
8. **Downgrade** (`test_crypto_downgrade.py`). *Found and fixed* (`e180548`): with the data host's
   marker removed from a holdout's ledger where nothing after it was renamed, a promote without the
   data host's statement was accepted. Each signature requirement (runner, data host, researcher)
   now holds from the ledger's marker or from a record naming a bindings head with the cutoff,
   whichever comes first, and stays in force for every later record. The store checks on every
   read, at startup and on reload, that the signatures are present. Whether they verify is checked
   at append and by `verify` and `sign-verdicts`. And a record naming a head with a cutoff whose
   marker (any of the four, canonical values included) does not come before it in its ledger refuses
   the whole ledger ("the ledger's marker is missing"). This also catches a record placed between
   the removed marker and the first record that names a head, such as an NFD seal.

**Adversarial researchers against the statistics (plan item 3, 27 October 2026).** Eight researcher
strategies, each trying for a PASS it does not deserve, with the null hypothesis true (every asset's
returns iid with zero mean), through the real promote path: `evaluate_promotion`, the dummy detector,
the five families. The PASS rate over many seeds must stay at or below the nominal false-positive
rate of the threshold, 0.05: the tests require the 99.9% upper bound of the measured rate to be at or
below it. Cases 1 to 3 and 5 to 8 feed returns directly (`tests/adversary_world.py`), case 4 and its
adaptations weights through the data host's summaries (`tests/risk_world.py`). The rates below are
under the rule in force since that day (the joint bar); for case 4, before it too.

| Case | Strategy | PASS rate (nominal 0.05) | Tests |
|--|--|--|--|
| 1 | Pure luck: N null strategies, the best promoted | N = 1: 0.0077; 2: 0.0045; 10: 0.0010; 100: 0.0025; 1000: 0 | `test_adversary_luck.py` |
| 2 | Seed mining: one strategy sealed with 100 and 2000 seeds | 0 and 0 | `test_adversary_seed_mining.py` |
| 3 | Crashing on purpose when the partial Sharpe looks bad (k < T/2 and k ≥ T/2, with and without partial returns) | 3 in 7400 over every variant; worst 0.004 | `test_adversary_early_failures.py` |
| 4 | Going flat, or cutting risk, once ahead (and its adaptations) | before the rule: up to 0.27 (n = 1); version 1 (the PSR statistic) at most 0.021; version 2 (the plain t) at most 0.0205 | `test_adversary_zero_tail.py`, `test_adversary_risk_cuts.py`, `test_adversary_risk_estimate.py` |
| 5 | Duplicate laundering: scaled and one-period-flipped copies | 0 in 5200 | `test_adversary_duplicates.py` |
| 6 | Alternating early and late failures between the families | 4 in 7250; worst 0.0017 | `test_adversary_families.py` |
| 7 | Wide junk to inflate V, tight junk to shrink it | 0 in 2600 | `test_adversary_variance.py` |
| 8 | Nondeterminism: runs A and B differ, or the fresh run does | never promotable; junk around candidates 0 in 1300 | `test_adversary_nondeterminism.py` |

Case 4 is the one that did not hold: a strategy that goes flat once its running t-statistic is high
keeps that statistic while the PSR counts every period. Rules that looked at zeros (a terminal run of
zero weights) or normalized by gross exposure were each simulated and evaded (trading again at the
end, tiny weights, a hedge, diversifying); the rule adopted grades returns over their ex-ante risk on
their active periods against a bar calibrated for a researcher free to stop (THREAT_MODEL.md §5a, with
every cell, its power cost and what it does not measure; the simulations in `tools/joint_bar/`). Case
8's rule was kept and is asserted: both series of a disagreeing opening enter every V, and the opening
counts twice in N.

**Rule version 2 (30 October 2026).** An adversary that knows the risk estimator, on a universe near
the window's size (58 equal assets, a 60-row window), passed version 1 at up to 0.0858 on 8000 fresh
seeds: one constructed outlier shrank the PSR's denominator. Under the plain t its worst cell is 0.0498
on 8000 fresh seeds, no cell above nominal of the 288 (5 were on the first 2000 seeds, at the worst stop,
at most 0.0550); shrinkage, a longer window, an eigenvalue floor,
a risk floor and winsorizing were measured and dropped (THREAT_MODEL.md §5a, with the numbers and the
reasons; `tools/joint_bar/standalone/run.py fixes`, `targeted`, `confirm`). Every new holdout is under
version 2; a holdout initialised before keeps version 1, and its verdicts stay valid. What the suite
shows: the rule recorded in the init record, the data host's install and every promote record
(`test_rule_versions.py`); a data host refusing an install under a rule it does not compute; the
service promoting under the plain t and an old holdout under the PSR, each with verify and
sign-verdicts passing, and an old promote record without the rule field still valid; the replay
failing a data host that normalizes under another estimator, floor or winsorization
(`test_rule_c_variants.py`); and the package's decisions identical to the standalone copy's under both
statistics and every candidate (`test_joint_bar_standalone.py`, `test_rule_variants_parity.py`). The
§5a table was measured again under version 2 through the implemented code: every cell at or below
0.0385.

*Found and fixed on the way, each a test and a commit:*
1. Risk's replay recomputed the data host's series hashes and detector flags but not its signed
   summaries (T, moments, k, the zero-padded Sharpe), which the verdict is computed from: a
   compromised data host could sign a Sharpe its series does not give, and `verify --holdout-file`
   and sign-verdicts passed it (`6efebe0`). Section 3 claimed this check already.
2. The replay raised `TypeError` on a nondeterministic outcome whose failed run had no partial
   returns (`dc1a860`).
3. sign-verdicts recomputed each verdict from the init's joint bar without checking it: a table
   rewritten consistently recomputed to the same verdict. It now checks risk's signature and runs the
   calibration again from the plaintext (`419e62a`).
4. The df fit of the joint bar ran on an empty array for a holdout with too few residuals; below 30
   it takes the floor, recorded as not fitted (`1d96a07`).
5. The scale of each family first included the candidate's own t-statistic, so a strong candidate
   inflated its own bar and among widely dispersed trials none could pass; it leaves the candidate
   out (`e3f7706`, a decision on the rule: THREAT_MODEL.md §5a).

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

The data host (claim 10) is tested in process: a development data host in a thread of the test
process (`transport: inproc`), with the real signer and openssl where it signs, against development
runners (the process backend):

- **The stand-ins:** no separate host, no sshd and no `lockrun-data` user: in the suite, the forced
  command, its firewalls and host ruleset, `data-provision.sh` and `data-check.sh` run under `bash -n`
  and the fake ssh, and the runners' two keys and `exec_keys` against a stand-in for sshd's
  ExposeAuthInfo. All of them ran live on 26 October (section 1); the gates' ruleset and listener
  checks are tested on that live host's own output.
- **What the suite shows:** the protocol and its refusals (`test_data_host.py`); that the service
  holds no key, ciphertext, series or weights after executions, and refuses a state with a key
  (`test_service_holds_no_holdout.py`); holdout-init on the laptop and the K_risk-signed install
  (`test_holdout_init_laptop.py`); the data host's statements in every record, risk's checks of them,
  journal recovery, recomputed promotes and the K_risk-signed fetch for the replay
  (`test_data_signatures.py`); the handover at a rebuild (`test_data_handover.py`); the refusal-time
  bound (`test_refusal_time_bound.py`); do.sh's data role, firewalls and steps (`test_deploy_data.py`).

Researcher-signed requests (plan item 1) are tested against an in-process service, data host and
development runners, with the real signer and openssl: the ticket and the service's checks
(`test_request_service.py`); the data host's and the agent's checks, nonces and their handover
(`test_request_checks.py`); risk's verify of every opening's request (`test_request_verify.py`); risk's K_risk-signed fresh
verification (`test_request_verify_fresh.py`);
do.sh's researcher keys and anchors-verify (`test_request_deploy.py`); the replay tool
(`test_redteam_replay.py`). All of it ran live on 27 October (section 1) except the
`request_refusals` ALERT for more than 3 requests refused at the API in 24 hours
(`test_request_refusals_alert.py`), which postdates that deployment.

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
  file, and append to the anchors repository. A rewrite of it, or of the verdicts repository, is
  refused by risk's pins (`out/anchors.pin`, `out/verdicts.pin`) whether or not GitHub enforces the
  ruleset. Commits pushed after risk's last check can still be replaced before its next one.
- That DigitalOcean enforces its firewalls as configured.
- Shared hardware state between jobs (caches, side channels).
- That a runner was really rebuilt from scratch: provable only by procedure.
- That a runner's signing key never left the runner (root on it can copy it), and that K_ops stayed on
  the operator droplet.
- What a compromised data host signs before risk next replays: its summaries and detector flags
  are checked only at sign-verdicts and `verify --holdout-file`, which recompute both from the
  plaintext and the runner-signed weights (the summaries since 27 October 2026; before, only the
  hashes and flags).
- That the plaintext never left the data host while it was compromised.
- That risk's signing key stayed on risk's laptop, and when a verdict was signed: `signed_at` and
  the commit dates are the signer's own. Records appended after a compromise of the service host
  are consistent with each other, so a signature cannot tell them from real ones (THREAT_MODEL.md,
  §3a).

The external-review brief is THREAT_MODEL.md, section 6, "Where an external reviewer should look
first", with the statistical rules marked for review in section 5.
