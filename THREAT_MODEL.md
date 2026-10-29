# lockrun threat model

lockrun counts the backtests run against a protected holdout, so a strategy's Deflated Sharpe
Ratio (DSR) uses the true number of trials N. Status: prototype. **The threat:** a researcher with
root on their own machine wants a better-looking backtest. They peek at the holdout before
committing, run many variants and drop the failures, or rewrite the ledger with a recomputed hash
chain to lower N. In **service mode** risk-owned hosts hold the holdout and the ledgers: the
**data host** alone holds each holdout's key and ciphertext, decrypts and streams the rows to the
runners; the **service** holds the ledgers, runs nothing but the API and the bookkeeping, and records
every opening before any row is sent. This document states what the
code enforces as of this revision; `README.md` has the detail, `RUNNER_PERSISTENCE.md` the runner
inventory, and `docs/WHAT_IS_VERIFIED.md` what ran on a live deployment, what only the test suite
shows, and what we cannot verify.

## 1. Claims (service mode)

1. **Every opening is logged first.** Before any holdout row reaches strategy code, the service
   appends a `holdout_access` record to that holdout's ledger: run, researcher, the runner's
   identity, the bindings-log head it was dispatched under, and whether it ran in shared-runner mode.
   The data host sends no row of a run until the service has recorded it ("go").
2. **N comes from the ledger, and every opening counts.** Each execution that opens the holdout is
   a trial, whatever its outcome, including one abandoned after a crash. A researcher's execution
   runs twice; any disagreement rejects it. A failure tells the researcher only "execution failed".
   Researchers cause appends only, and send weights, never returns. An execution the service queued
   and the data host (or the service's worker) refused before opening is no trial but is recorded
   and counts in the execution quota. A request refused at the API (a wrong key, a replayed or
   malformed request, none after the cutoff) opened and queued nothing: it is not recorded and does
   not count; it goes to the rejection log with its reason, and more than 3 for one researcher in
   24 hours (counted in the service state, across restarts) raise an ALERT, a leaked token or a
   broken client.
   Each researcher has at most one execution in flight, and its slot frees only once the runner
   confirms the job stopped.
3. **The sealed code is the code that runs, in a launch the agent verifies.** The service stores a
   `git archive` of the sealed commit and runs only that snapshot. The runner agent starts it under
   gVisor with the launch profile in §4 and, before the first message that loads strategy code,
   checks that profile on the running container; the profile's hash is recorded with the execution.
   At step *t* the strategy receives only rows known by the decision time.
4. **Tampering is evident, and the service fails closed.** After every append the service writes
   (count, head) to a witness log. The running service refuses a holdout whose ledger no longer
   chains, no longer matches its witness, or no longer extends the head it last verified (§3).
   `lockrun-risk verify` checks the same from disk, plus anchors exported off-host.
5. **No PASS without reproduction, and no PASS for stopping early.** Risk sets the threshold and
   min_t per holdout, and on the laptop calibrates the holdout's joint bar, signed with K_risk in its
   init record (§5a). A promote grades the candidate's returns over their ex-ante risk against that
   bar. A passing promotion stays `pending_verification` until risk re-runs it on a fresh verify
   runner and gets a bit-identical returns hash. Fresh means: a build_id seen in no holdout's ledger nor the bindings
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
9. **Every execution record is signed by the runner that ran it.** Each runner makes its own
   Ed25519 key at provisioning, held by a user of its own (§4); risk (K_risk) or the operator
   droplet (K_ops) certifies it in the bindings log. The opening record carries the runner's signed
   opening, made once the job is up and before any row is sent; the outcome carries each run's
   signed end, naming the bytes relayed each way and their sha256. Each signature takes the key's
   next counter. From the cutoff (`require_runner_signatures`, recorded in the bindings log and in
   every holdout's ledger) a record without a valid signature is a chain error, and so is a gap in
   a key's counters across all ledgers. Risk's `verify` and `sign-verdicts` replay the signed
   streams with the plaintext holdout: the rows were the holdout's and the recorded returns are what
   the signed weights give.
10. **The service host never holds the holdout.** No key, ciphertext, row, returns series or weights
    stream reaches it (since 25 October 2026); a service whose state holds a key or a ciphertext
    refuses to start. Risk encrypts each holdout on the laptop and installs it on the data host under
    a K_risk signature (`do.sh holdout-init`). For each run the data host signs its opening (the
    plaintext's hash, the plan's steps, the run's status and row counts) and, per execution, the
    outcome's summaries (T, moments and returns hash; for a failed run its length k and zero-padded
    Sharpe; for either, T_eff and the moments of the returns over their ex-ante risk, §5a); for each promote it runs the dummy detector on the series the trial structure names and
    signs its flags. Only K_risk certifies its keys, from the laptop (the `data_host` bindings record,
    the data cutoff, marked in every holdout's ledger; K_ops certifies runners only). From the cutoff
    a record without the data host's valid statement, a statement that is not its record's, an
    outcome other than the one its signed runs give, run hashes other than the runner's session_end,
    or a gap in the data host's counters is a chain error. The data host holds each holdout in
    memory, so its size has an explicit limit (1 GiB by default, set per deployment): a larger one is
    refused at `holdout-init`, before anything is written, and by the data host at install.

## 2. Actors, secrets and trust boundaries

**Researcher:** untrusted, root on their own machine. Holds a bearer token (static, revocable by
risk), the certificate pin and a git repository. **Risk:** trusted, root on the service and runner
hosts. **Service:** holds the ledgers and tokens, never the holdout (claim 10). **Data host:**
risk-owned, holds every holdout's key and ciphertext and every series and weights stream; runs no
researcher code. **Runner:** risk-owned, one per researcher, runs that researcher's strategies;
state that survives a job is listed in `RUNNER_PERSISTENCE.md`.

| Secret | Where it lives | Who can access it |
|--|------|------|
| Holdout key and ciphertext | The data host, `/var/lib/lockrun-data/state/holdouts/<id>/`, 0600 in 0700, user `lockrun-data`; risk's laptop keeps the bundle (key, ciphertext, init record) as its backup | Root and `lockrun-data` on the data host; risk. Never the service host, the runners or the sandbox |
| Holdout data | Decrypted in memory per execution on the data host; streamed step by step over SSH to the job | Root on the data host; root on the job's runner (that job's rows). Strategy code sees every row by the end of a run |
| Returns series and weights streams | The data host, keyed by sha256; the ledger holds their hashes and summaries only | Root on the data host; risk's replay, under a K_risk-signed fetch |
| Data host signing key (Ed25519), handover key (X25519) | The data host: the signing key `lockrun-signer`'s as on a runner; the handover key `lockrun-data`'s, 0600; new with every rebuild | Root on the data host. Both certified by K_risk alone, recorded in the bindings log; a certificate by any other key is a violation |
| The runners' job key (SSH) | The data host, `lockrun-data`'s, 0600; handed over to the next data host at each rebuild | Root on the data host. The only key a runner lets start a job (`exec_keys`) |
| Ledgers, bindings log, witness logs | Service host: hash-chained JSONL, witness logs `chattr +a` | Researchers read (head, count) through the API. Root can rewrite all of them (§3) |
| Risk's verdict-signing key (Ed25519) | Risk's laptop, `deploy/p3/out/risk-key/`, 0600 (later an HSM) | Risk. Never the service host, the runners or the operator droplet (§3a) |
| Verdicts deploy key | Risk's laptop, same directory | Risk: write access to the verdicts repository only |
| Runner signing key (Ed25519, one per runner build) | The runner, `/var/lib/lockrun-signer`, 0600 in 0700, user `lockrun-signer`; replaced with the runner every night | Root on that runner. The runner user (the agent, a gVisor escape) can ask the signer to sign through one sudo rule, never read the key |
| K_ops, certifies the runners recycle-all builds | The operator droplet, `/etc/lockrun-ops/runner-cert.key`, 0600, made there | Root on the operator droplet |

**Boundaries.** *Researcher → service:* TLS 1.3 with a pinned certificate, a bearer token, seven
JSON endpoints, 64 KiB bodies, daily per-researcher quotas, an allowlist of repository URLs per
researcher. *Service → data host:* SSH from the service's VPC address only, forced to `lockrun-data`,
one request per session (hello, run, stats, journal, retire; install and fetch need K_risk's
signature; handover and receive need certified keys; backup encrypts only to the backup key K_risk
certified, deploy/DISASTER_RECOVERY.md). *Data host → runner:* SSH with a pinned host
key, the data host's key, the only one the agent lets start a job. *Service → runner:* SSH, forced,
limited to identify, journal and retire. The runner holds no credential to either. Before anything
is decrypted the data host checks the execution's signed request (below) and the runner's certified
key; before anything is sent to the runner it checks the runner's hello (build_id, the one bound to
the researcher; the pinned image; backend; CPU flags).

**Signed requests (plan item 1).** Each researcher has an Ed25519 key of their own (`lockrun remote
key init`), certified by K_risk and recorded in the bindings log; a later key or a revocation kills
the previous one from that record on. Every execute carries a request the researcher's key signed:
the holdout, run, the seal record's full hash, the researcher, the bindings head, a 128-bit nonce and
a time at most 15 minutes ahead. A fresh verification's request is risk's, signed with K_risk on the
laptop. The data host checks it before decrypting (and keeps each nonce until it expires, handed over
at a rebuild), the runner's agent before launching (risk's key in its `agent.json`; a request its
signer already opened a job on is refused), and the opening record carries it. **Verified live, 27
October 2026** (`docs/WHAT_IS_VERIFIED.md`): on a deployment built from zero, a replayed request
was refused by the data host (sent by root on the service) and by the agent (sent by root on the
data host with its nonce check removed, `redteam/replay_p3.py`), a request signed by another key by
the API, and both fresh verifications ran on K_risk-signed requests.

## 3. Root on the service host

**Can, from the moment of compromise onward:** read and forge any record; issue tokens; bind or
rebind runners by writing the bindings log; make the service lie in every answer; stop exporting
anchors (visible as a cadence gap); rewrite the local ledgers, witness logs and bindings log
together, with recomputed hashes; ask the data host for genuine executions and promote statistics,
as the service does. **Cannot, since 25 October 2026:** decrypt a holdout or read its rows, returns
or weights (none is on the host; the data host fetches nothing to the service's key, installs only
under K_risk, and hands over only to a certified key); write an execution or promote record the data
host did not sign, after the data cutoff (claim 10).

**Cannot, from the cutoff on (claim 9):** write an execution record no runner signed. A fabricated
opening or outcome, or one whose signature is forged, is a chain error before the next deposit and
after it, though root's own deposit anchors it. A signed record removed leaves a gap in its runner
key's counters, seen at the runner's next signed statement and at the latest at its final statement
when the nightly recycle retires it. **Can still:** stop executions, which the runner signs as what
they were; stream altered rows, which the runner signs as received and risk's replay with the
plaintext refuses.

**Cannot, from the researchers' cutoff on (`require_researcher_signatures`, marked in each ledger;
the data host requires it from provisioning):** start an execution in a researcher's name, or a
fresh verification. Without a request the researcher's current key signed (or K_risk, for a
verification), the data host decrypts nothing and the runner starts nothing; an opening record
without it, or with one that does not check out, is refused at write and a chain error in risk's
`verify` and `sign-verdicts`. Root cannot add a key of its own (only K_risk certifies one, checked
by the data host, the runner and risk's verify) nor revive a replaced one. A request opens one
execution: the data host, the runner's journal and the ledger each refuse its nonce a second time.
**Can still:** hold a request the researcher sent and use it within its 15 minutes, for the one
execution the researcher asked for, or not run it at all.

**Cannot:** change what was deposited off-host. Anchors (count, head, time, chained) are pushed to a
git repository whose `main` the git host protects; `anchor verify-repo` flags any commit that does
more than append, and checks every anchor ever pushed against the ledger. The git host's ruleset is
not relied on: risk keeps a pin of the last verified commit of each public repository on the laptop
(`out/anchors.pin`, `out/verdicts.pin`); `verify-repo --pin` and `sign-verdicts` refuse a fresh clone
whose history no longer contains it as rewritten (a force push, even one that keeps the file
unchanged), and a pin only advances to a descendant; commits pushed after risk's last check can
still be replaced before its next one. History up to the last
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
| Opening removed, its outcome kept, chain and witness rewritten | refused (does not extend the head it verified) | `verify` fails: the outcome closes no opening | detected |
| An execution record without its runner's signature, or with a forged one (after the cutoff) | refused at write | `verify` fails: the statement is missing or does not verify | (anchors it at the next deposit: still fails) |
| A signed execution record removed, chain and witness rewritten | | `verify @runners` fails: a gap in the runner key's counters (the tail: at its next statement or its final) | detected |
| A summary, an outcome or a promote's detector flags rewritten (after the data cutoff) | | `verify` fails: the data host's statement is not the record's, or the outcome is not the one its signed runs give | (anchors it: still fails) |
| Bindings record appended that breaks a binding rule (a runner moved, a second runner for a researcher) | refused on the next read | detected: `verify @runners` names the record and the rule | |
| A record of a type foreign to its log (a bindings record in a holdout's ledger, a holdout record in the bindings log) or of a type nothing writes | refused at write and on the next read | detected: `verify` names the record and the log's allowed types | |
| A record naming a record that is not earlier in its chain (a promote before its fresh verification, a claim before its request, a run id with no seal before it, a marker or opening naming a bindings head the log does not have), records reordered with every hash recomputed | refused at write and on the next read | detected: `verify` names the record and the reference | |
| Witness entries reordered or repeated | refused on the next read | detected: the counts must strictly increase | |
| A record written another way that reads the same: key order, whitespace, escapes, float spelling, CRLF, a duplicated key, NaN or Infinity; after the canonical-values cutoff (`require_canonical_values`, marked in every ledger; in force from the marker or from a record naming a bindings head with the cutoff, whichever comes first, and for every later record, so removing the marker does not switch it off), a string or key not in NFC or an integral float | refused at write (the store writes canonical values; the client normalizes seal params, the API refuses the raw form) and on the next read | detected: the line is not canonical, or the value is named | |
| A cutoff marker removed from a holdout's ledger (runner, data host or researchers'), then a record without the signature it requires: each requirement holds from the ledger's marker or from a record naming a bindings head with the cutoff, whichever comes first, and stays in force for every later record whatever head it names. A record naming a head with a cutoff whose marker does not come before it in its ledger (any of the four, canonical values included) refuses the whole ledger: "the ledger's marker is missing" | refused at write and on the next read (the signature must be there; the whole ledger once the marker is shown missing) | detected: `verify` names the record and the missing statement or request | (anchors it: still fails) |
| An opening without its signed request, or with one forged, for another execution, or used before (after the researchers' cutoff) | refused at write | `verify` fails: the request is missing or does not check out; `verify @runners`: a nonce used twice | (anchors it: still fails) |
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

**What sign-verdicts checks before signing.** On a copy of the service's ledgers and witness logs
(read under the append lock), it:

- checks every chain it signs from against its witness log and against every anchor ever
  deposited, in an anchors history with no tamper alarm;
- checks that each verdict's `computed_from` is the ledger read just before it;
- recomputes the verdict from the records before it, with the service's own code;
- checks the runners' records (claim 9) with risk's key and its own copy of K_ops' public key: every
  certificate, every statement, each key's counters, and, for each holdout with signed outcomes, the
  streams replayed with the plaintext risk kept (`--holdout-file`, then required), the weights
  fetched from the data host under a K_risk-signed request, through the service as a jump host;
- checks the data host's statements (claim 10) the same way: every opening, outcome and promote,
  its counters, and each promote's detector answer against the trial structure it recomputes; then
  recomputes each run's summary (T, moments, k, the zero-padded Sharpe, T_eff and the moments over
  ex-ante risk) and the detector's flags from the series its own replay gives (plaintext and
  runner-signed weights, each matching the hash the record names): a summary or flags other than the
  data host signed are a chain error, and nothing is signed;
- checks each holdout's joint bar (§5a): risk's signature over it, and, with the plaintext, the df
  fitted and the table simulated again from its seed.

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

- **That the researcher asked for every execution.** From a compromise of the service host onward,
  root can start genuine executions on a researcher's runner, or stop them; the runner signs them
  as they ran, so they count. Before the cutoff (claim 9), or on a runner with no key, root can
  still append records consistent with each other, which risk's recomputation then agrees with.
  sign-verdicts checks the runners' signatures and replays their streams before it signs.
- **Anything a compromised runner signed.** Root on a researcher's runner, or a gVisor escape that
  asks its signer, can sign false statements for that runner's researcher until the nightly
  rebuild; after its final statement the key signs nothing that counts.
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

## 3b. Root on the data host

**Can, until the next rebuild:** decrypt every holdout and read every series and weights stream;
sign anything as the data host (summaries, detector flags, openings), until its final statement at
the handover; refuse or delay executions and promotes (the retryable 409). Its only routes out are
its answers to the service and its sessions to runners (cloud firewall and host ruleset: SSH in from
the service only, out to the runners only), so a compromised data host can leak the plaintext to a
compromised service through its answers. **Cannot:** forge a runner's statements, so risk's replay
(with the plaintext and the runner-signed weights) refuses altered rows and returns it signed, and
summaries or detector flags other than the replayed series give (sign-verdicts and `verify
--holdout-file` recompute them, the summaries since 27 October 2026); make
risk's laptop install or fetch anything (both need K_risk); hand the holdouts to a key risk did not
certify. Root on the operator droplet cannot either: K_ops certifies runners, never a data host or
its handover key, and `verify @runners` refuses a data_host record certified otherwise. **Weekly
rebuild, by risk:** `do.sh recycle-data`, from risk's laptop, on risk's approval: the old data host
hands everything over, encrypted to the new one's K_risk-certified X25519 key, then signs its final
statement; the bindings record carries both. An attacker on the data host persists at most until
that rebuild: `check-service` fails (E8) once the data host is older than 8 days, and the nightly
recycle reports it due from 7.

## 4. Runners

**Model.** Each primary runner is bound to exactly one researcher in the bindings log
(`ledgers/@runners.jsonl`: chained, witnessed, anchored and verified like a holdout ledger). Only
`lockrun-risk` binds; a binding never moves. A dead runner is replaced: the new one is bound to the
same researcher and the old retired in one record; a retired runner never runs again. The worker
reads the log at dispatch, and the runner must answer with the bound build_id. **Routing proof:**
every opening names its runner and the bindings-log head; `verify` checks each against the binding
valid at that head, and every outcome (returns, no_returns) must close an opening earlier in the
chain, of the same run, researcher and runner: an outcome whose opening was removed is refused by
`verify`, at startup and on every reload (`tests/test_outcome_openings.py`). Verify runners are
registered in the bindings log and can never be bound.
The binding rules are checked on every read of the log, not only when `lockrun-risk` writes it. A
record that breaks one is refused like a broken chain by `verify @runners`, at startup and on every
reload: a runner bound twice (by name or build_id), a second active primary for a researcher, a
retired runner back, a verify runner bound, a replace or retire of another researcher's runner, an
unknown record type (`tests/test_bindings_invariants.py`).
**Runner keys (claim 9).** Provisioning makes the signer user, its key (OpenSSL 3, Ed25519) and one
sudo rule for the runner user, and prints the public key; the provisioner (risk's laptop, or the
operator droplet for nightly runners) reads it over its own SSH, certifies it and records it with the
binding. The agent asks the signer for each signature; the signer journals each one (fsync) before
returning it, so a statement whose record the service never wrote is recovered from the runner at
its next execution (an opening counts in N unless its signed end shows no row reached the job).
Retiring a runner, the service first records its journal, then asks it for its final statement (the
last counter it used); a dead runner's is signed by risk. Gates K1 (the key is the signer's alone)
and K2 (the agent reports its key) are part of `runner-check`.
**On redeploy:** both checks, the binding rules and every outcome closing an opening, apply to the
records already on disk. A live service updated to this code refuses at startup any bindings log or
holdout ledger holding a pre-existing record that breaks either, as it refuses a broken chain, until
risk acts. Run the new `lockrun-risk verify` on a copy of every log before updating.
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

**Between runners, the cloud firewall** (runners accept tcp 22 from the service's and the data host's
tags only and send nothing; their own ruleset admits SSH from the service's address and, for the data
host, whose address changes at every rebuild, from the VPC range) **is verified by configuration and by its propagation behaviour, not by a live probe.**
`do.sh check-firewalls` compares the live rules with the generated ones; a runner just retagged
locked was unreachable from the service until DigitalOcean applied the rule, then reachable
(2026-10-14). A probe from one runner to another never reaches the cloud firewall: the source's own
ruleset drops it first (verify-1 to the primary on tcp 22: a timeout, its 5 SYNs counted as egress
dropped), and lifting a locked runner's ruleset to test the layer behind it is not done.

**A researcher who escapes gVisor** to the runner host, as the runner user in its user namespace,
**gains:** the rows of their own job (which their code already saw), and a place to persist across
their own later jobs on that runner until its next rebuild (at most a night, below). They can also ask the runner's signer to sign statements for their own runner until its rebuild
(the key itself is the signer user's, 0600, and gate K1 checks it). They cannot change Podman's configuration or the image:
both are root's (`/etc/lockrun/containers.conf` and `storage.conf`, the read-only store
`/var/lib/lockrun/images`), not writable by the runner user, which the agent's hello and
`runner-check` E5 check; each job's writable store is its own and removed with it. They can make
the agent's checks and job counts fail, which holds their own slot (fail closed). With root on the
runner as well, they can also alter image layers under the pinned ID (the launch check does not
read layer content) and forge the agent's hello and launch profile, so the recorded profile hash
proves nothing for that runner. **They do not gain:** the
holdout key or any other holdout's rows; other researchers' jobs (separate runners); any credential
to the service or the data host (SSH runs only to the runner, under a forced command); a way to change N or the
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

- **Anchor cadence through an outage (risk's decision of 29 October 2026: no gap is ever accepted).**
  The anchors repository never goes an hour without a line, whichever hosts are lost.
  - The service down, the operator droplet up: ops' hourly deposit re-deposits each log's head from
    the newest backup or increment, as anchors marked "unreachable since <time>, heads from <manifest
    hash>". They are anchors of each log's chain, checked against its records.
  - Both lost: the anchors repository's own scheduled job (GitHub Actions, hourly) appends a heartbeat
    naming each log's last heads whenever no deposit landed in the last hour. A heartbeat is a cadence
    point with no new record; one naming other heads than the line before it is a tamper.
  - A restore accepts a record beyond a log's last anchor only if the backup or increment holding it
    was uploaded to the write-once store (its versions listing, retention-locked) before the first
    heartbeat of the outage; anything else is refused. restore-open deposits one K_risk-signed restore
    line naming the attestation and the stretch, so the history says why the heads did not move. It
    exempts no gap.
  - **The one remaining assumption:** GitHub's scheduler and the store's clock (B2) are independent of
    our hosts. Root on our hosts can neither run the heartbeat job nor date an upload; whoever controls
    the GitHub account or the store's clock could.

- **Same data elsewhere.** Trials run outside lockrun on public copies of the data are invisible.
- **Rule-aware dummy trials** can lower trial-Sharpe variance to its floor and raise the DSR
  undetected (internal red team). Effective-N is out of scope.
- **Failed trials (statistical rules, for external review).**
  - **Failures with partial returns** enter the "with" V zero-padded to T (`zero_tail`): those are
    draws of the same strategy.
    - Late failures (k ≥ T/2) have done so from the start.
    - Since 15 October 2026 early ones do too, once their outcome is recorded, when the padded
      series is valid.
  - **Rule change, 15 October 2026** (`b73220d`): a failed opening with no valid series entered the
    "with" V as a Sharpe of exactly 0 (`zero_sharpe`). The only promote block left was an opening of
    one's own with no recorded outcome; before, an own config that never returned blocked its
    researcher on that holdout for good.
  - **Rule change, 17 October 2026** (`0716dee`; code version `code_sha256 25dc3088…`): a failed
    opening with no valid series counts in N and stays out of V. `n_zero_sharpe` in the promote
    record counts these openings. The promote block stays as it was after 15 October.
    - **Why:** the adversary's best case for zeros is real Sharpes widely dispersed and centred
      near zero. With 20 such trials (uniform in [-0.5, 0.5], or normal with sd 0.3) and 0, 1, 5,
      20 and 60 failed trials added, each zero lowered the "with" V and its sr0. At 60 failures
      sr0 fell 0.560 → 0.358 (uniform) and 0.452 → 0.298 (normal); every step down was strict.
    - The verdict never improved, but only because it is the minimum over the families: the
      "without" family's sr0 rose with N (0.560 → 0.715). A bar that falls as failures are added
      was one change away from an exploit.
    - **Since 17 October**, `tests/test_early_failures_in_v.py` asserts that adding failed trials
      never lowers sr0 in any family, never raises the verdict's DSR, and never turns a FAIL into a
      PASS. A 0.8 candidate exercises the cross from PASS to FAIL at the 0.95 bar.
  - **Verdicts computed under the 15 October rule** with failed openings in V recompute
    differently. `sign-verdicts` refuses them until a promote under the new rule supersedes them.
  - **Open for review:** whether zero-padding an early failure's partial returns is the right
    treatment for a strategy that stopped early, and how the padded series interact with the dummy
    detector. Since 27 October 2026 the verdict grades every trial, failed ones included, on its
    active periods over ex-ante risk (§5a): the padded series still feed V (recorded, for comparison)
    and the detector, not the verdict's statistic.
- **Optional stopping** is the statistical rule of §5a: the gaps it leaves are listed there.
- **Output channel.** Per execution: success or failure, Sharpe/skew/kurtosis rounded, completion
  time; per promote, statistics over all trials at 3 significant digits. Ceiling about 45–50 bits
  per execution, by counting values.
- **Full disk** halts the service or leaves an unwitnessed line (a false tamper alarm).
- **A researcher's key on their own machine.** Whoever holds it (and the token) executes as that
  researcher; risk revokes it (`lockrun-risk researcher key revoke`) and records a new one. The key is
  a PEM file for now; an ssh-agent or a hardware key can replace it without changing the request
  (plan items 6 and 15).

## 5a. Statistical rule: the joint bar (27 October 2026)

A rule change, for external review (the DSR's authors among the reviewers). The simulations behind
every number here are in `tools/joint_bar/` (README there), the rule in `lockrun/exposure.py`,
`lockrun/calibration.py` and `lockrun/trials.py` (`evaluate_promotion`).

**The problem: optional stopping.** A strategy that watches its own running t-statistic and goes
flat once it is ahead keeps the t-statistic of its first k periods, while the PSR counts all T: the
zeros dilute nothing. Under the DSR (with the fresh verification reserved in N), the best such rule
passed at 0.27 with one trial and 0.08 with two, against a nominal 0.05; the same strategy played
honestly passed at 0.015 (plan item 3, case 4). A rule on a terminal run of zero weights did not hold:
trading again for the last period (0.17) or weights times 1e-6 instead of zero (0.27) kept the excess.

**The rule.**

1. **Returns over ex-ante risk.** Each step's return is divided by the ex-ante risk of its weights,
   sqrt(w' S w), S the sample covariance of the held assets' returns over the 60 rows strictly before
   the step (rows where every held asset has a return; at least 20, else no estimate). No shrinkage:
   shrinking S toward its diagonal overstates a hedge's risk, and a hedge of two twin assets then
   passed at 0.06 to 0.14. A step is **inactive**, missing data, with no weights, no estimate, zero
   risk (weights in S's null space) or risk under 10% of the strategy's median active risk. Normalizing
   by gross exposure instead missed a hedge (0.09) and spreading over 100 assets (0.088).
2. **T_eff.** The statistic is the PSR statistic against 0, z = sr sqrt(T_eff - 1) / sqrt(1 - skew sr
   + (kurt - 1)/4 sr^2), on the active steps' normalized returns; T_eff, their number, is what min_t
   applies to.
3. **The joint bar.** F is the null CDF of sup over k in [min_t, T] of z_k for one trial with iid
   Student-t returns (the researcher may stop at any k), simulated at holdout-init on risk's laptop:
   the df fitted on the holdout's residuals by profile likelihood, floor 4 (fewer than 30 residuals:
   the floor, recorded as not fitted), 2M paths, a recorded seed. For n trials each free to stop,
   c(n) = F^-1(threshold^(1/n)); a candidate's value is F(z)^n, so value >= threshold is z >= c(n).
   n is every opening counted in N except fresh verifications: a verification reproduces the
   candidate, it is no other draw, and nothing is reserved for it (c(n), not c(n + 1), decided on
   the condition below). Beyond n = 1000 the bar is extrapolated linearly in log n, which errs high.
4. **The families stay.** Each of the five families (with and without the zero-tail series, with and
   without the detector's flags) keeps its trials and flags. Its value is F(z / s)^n, s = max(1, the
   sample sd of its other trials' t-statistics sr sqrt(T_eff)). The candidate is left out of s: with
   it in, a strong candidate inflated its own bar (s grows as t / sqrt(n), z more slowly than t), and
   among 20 widely dispersed trials no candidate could pass at all. PASS iff the lowest of the five
   values is at least the threshold. The DSR's N, V and sr0 are still computed and recorded, for
   comparison; the researcher sees the same fields as before, `value` now the joint bar's and
   `label` "joint bar".

**Who computes what.** The data host signs each run's T_eff and normalized moments in its
data_outcome, for a whole series and for a failed run's partial returns; risk's replay recomputes them
from the plaintext and the runner-signed weights (and, since the same day, the T, moments, k and
zero-padded Sharpe it already signed: before, only hashes and detector flags were recomputed). The
calibration is in the init record with the exposure parameters, under risk's signature
(`calibration_sig`); the exposure parameters are also in the data host's signed install fields.
`lockrun-risk init-record` refuses a record without the signed calibration; the service computes the
verdict from the init's table and refuses a holdout without one; `verify` checks the signature and,
with the plaintext, fits and simulates again: the table must reproduce exactly.

**What was measured (PASS rate under the null, 2000 seeds per cell, nominal 0.05).** Through the
implemented code (`tests/risk_world.py`; the suite pins the same cells with fewer seeds):

| Researcher strategy | Before the rule (n = 1 / 2) | Joint bar, c(n) (n = 1 / 2) |
|--|--|--|
| Honest, constant exposure | 0.0115 / 0.0020 | 0.0135 / 0.0105 |
| Honest, 10% random flat days | 0.0140 / 0.0020 | 0.0140 / 0.0100 |
| Flat once ahead | 0.257 / 0.071 | 0.0205 / 0.0160 |
| Flat, then trading again for the last 1 / 2 / 5 periods | 0.164 / 0.120 / 0.083 (n = 1) | 0.0205 / 0.0200 / 0.0175 (n = 1) |
| Weights times 1e-6 / 0.01 / 0.05 once ahead | 0.257 / 0.200 / 0.112 (n = 1) | 0.0210 / 0.0210 / 0.0175 (n = 1) |
| Same gross over every asset (8 / 100 assets) | 0.014 / 0.0165 (n = 1) | 0.0130 / 0.0130 (n = 1) |
| Hedge of two twins / with a drifting ratio | 0.129 / 0.0835 (n = 1) | 0.0205 / 0.0165 (n = 1) |
| Only the lowest-variance asset | 0.035 (n = 1) | 0.0150 (n = 1) |
| Pausing in the window covariance's null space (100 assets) | not run | 0.0125 / 0.0075 |
| An asset whose volatility the window lags (falls tenfold) | not run | 0.0200 / 0.0175 |
| Every trial stopping at c(n), n = 1 to 50, normal / Student-t(4) | not run | at most 0.0200 / 0.0280 |

Each adversary cell is the worst over its stopping rule (c from 1.5 to 3.5, first stop from period 2,
3, 20 or 100). The calibration takes 19 to 23 s for T = 250 and 200 to 240 s for T = 2500 on one core
of a laptop (2M paths, 392 MiB at most); on the data host's droplet size it was not run.

**What is lost.**
- **Power.** One honest trial holding one asset, daily periods, T = 250, true annualized Sharpe 1, 2,
  3, 4: PASS 0.119, 0.413, 0.775, 0.962 before; 0.099, 0.337, 0.690, 0.931 now (pinned in
  `tests/test_joint_bar_controls.py`). The 20-row warm-up leaves T_eff at most T - 20.
- **An edge in sizing is not measured.** Returns over their ex-ante risk weigh every active step
  alike: a strategy that takes a larger position when its per-period Sharpe is known to be higher
  loses that information (about a fifth of its t-statistic in the documented case). A strategy whose
  edge lies only in timing its exposure is graded on its direction.
- **Local mode** has no weights: every step of submitted returns is active, and the bar is calibrated
  at promote, at the df floor (no return column to fit).
- **Holdouts initialised before the rule** have no joint bar: their promotes are refused until the
  holdout is initialised again.

**Open for review.**
- The independence assumption: c(n) is the quantile of the maximum of n independent trials. Trials on
  one holdout are correlated, which lowers the true quantile: conservative, not exact.
- The tail: iid Student-t at the holdout's pooled residuals, floor 4. Volatility clustering is not
  in the calibration; one regime shift the window lags was simulated (above), not a clustered market.
- The window (60 rows, 20 to start), the inactivity floor (10%) and the null-space threshold (a
  variance at most 1e-10 of the weights' uncorrelated variance), and that no shrinkage is applied.
- The scale's leave-one-out form, and that it uses t-statistics rather than Sharpes (T_eff differs
  across trials).
- The value is F(z / s)^n with F interpolated between stored quantiles: it moves slightly with the
  stored levels, the threshold's among them; the verdict is exactly z / s >= c(n) on that F.

## 6. Where an external reviewer should look first

1. **The launch check on a live runner.** Inspect and `systemctl show` field names, Podman's `--rm`
   and `rm --force`, and its default tmpfs mounts were exercised only against `tests/fake_podman.py`.
2. **The gVisor boundary** for hostile code holding holdout rows: no in-guest process limit, the
   rootless user mapping, and what a runner-user escape can reach on the host.
3. **Restart after a consistent cut.** A ledger and witness cut together are accepted after a
   restart; only off-host anchors catch it. Should startup require a fresh anchor match?
4. **Mid-ledger edits under a running service.** Only new lines are verified between restarts.
5. **Anchors:** who owns the repository, the cadence window, self-reported times, and that `verify`
   runs with the service host's own code and files. The outage rule (§5): ops' "unreachable" anchors,
   the repository's heartbeat, and the B2-dated rule at restore. Since 16 October 2026 an anchor's count may go
   back, to a verdict or bindings record anchored late; the record it names is checked like any other.
6. **Signed verdicts (§3a):** what sign-verdicts recomputes and what it only compares
   (`lockrun/service/sign.py`), the 1e-12 tolerance, that the verifier trusts the statement's anchor
   commit only as far as the git host's history, and the gap from a compromise onward.
7. **Deployment state.** The P3 deployment predates bindings (one shared runner; its openings are
   reported as predating the bindings log), and its `do.sh` accepts a single primary runner.
8. **Failed trials:** the zero-tail rule, early failures as zero-padded series (since 15 October
   2026), failed openings with no valid series in N but not in V (since 17 October 2026; the rule of
   15 October put a Sharpe of 0 for them in V), all in `lockrun/trials.py` (`_add_failed_opening`,
   `evaluate_promotion`), and the promote block reduced to openings with no recorded outcome.
9. **Fresh-runner procedure:** "rebuilt" is not provable in code; an abandoned verify-fresh claim is
   closed without the verify runner confirming its job stopped.
10. **Runner signatures (claim 9):**
    - the signer as its own user behind one sudo rule, and what a runner-user escape can make it sign;
    - K_ops on the operator droplet, which can certify a runner's key (as root there can already
      rebuild and log into runners);
    - that the provisioner reads a new runner's public key on first contact, trusting its host key;
    - journal recovery, which counts an opening with no signed end in N, so it can only raise N;
    - the replay's tolerance: a failed run's recorded partial returns must be what its signed weights
      give through every step the job received but possibly the last;
    - since 24 October 2026 the service sends a run's params in canonical order, so the stream for a
      run depends on the ledger alone.
11. **The data host (claim 10, §3b):** the forced command and its one-request protocol
    (`lockrun/data/host.py`); the "opened"/"go" handshake that keeps rows behind the opening record;
    what the summaries reveal (T, moments, hashes, k, the zero-padded Sharpe: no more than before);
    the K_risk-signed install and fetch, and their one-hour not_after window; the handover's
    encryption (X25519, HKDF-SHA256, AES-256-GCM) and that only K_risk certifies its key; that the data host's
    SSH key to runners survives rebuilds (handed over) while its signing key does not.
12. **Signed requests (§2, §3):** the 15-minute window in which root on the service can use a request
    the researcher sent, for that one execution; the nonce stores (the data host's, handed over at
    each rebuild; the agent's, its signer's journal); and the researcher's key as a PEM file on their
    own machine (§5).
13. **Adversarial tests (plan item 2, `tests/test_crypto_*.py`, docs/WHAT_IS_VERIFIED.md §2):**
    eight attacks on one honest deployment, each tampered consistently by root. Four were found
    and fixed:
    - foreign record types;
    - references to records not earlier in the chain, and witness entries out of order;
    - two encodings of one value (canonical values from a cutoff);
    - a cutoff marker removed.
    Rewritten repository histories are now refused by risk's pins, not by the git host. Worth a
    look: `lockrun/service/cutoffs.py`, where a requirement starts and that it never stops. The
    store checks only that signatures are present on read; their verification runs at append and in
    risk's `verify`.
14. **Adversarial researchers against the statistics (plan item 3, docs/WHAT_IS_VERIFIED.md §2):**
    eight researcher strategies under the null, each through the real promote path. Seven held; one,
    stopping once ahead, passed at up to 0.27 and led to the joint bar.
15. **The joint bar (§5a):** the rule itself, for the DSR's authors as much as for us:
    - the ex-ante risk estimate (`lockrun/exposure.py`): the window, no shrinkage, the null-space
      threshold, and what an adversary could do with an estimate it knows to be wrong;
    - the calibration (`lockrun/calibration.py`): the statistic, the Student-t tail at the floor of
      4, independence across trials, the extrapolation beyond n = 1000, that it reproduces from its
      seed on another machine;
    - the scale (`lockrun/trials.py`, `scale`): leave-one-out, on t-statistics;
    - what is lost: power, and an edge in sizing.
