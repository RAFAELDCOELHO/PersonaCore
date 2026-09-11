# Phase 26 operational note — the canary audit: launch, run and close

**Dated 2026-09-11.** Authored at HEAD `525b0cd`, on the author's M3 (the primary venue, the same
`torch 2.7.1` / `mps` venue that produced the 790/1008 the control must reproduce — RESEARCH
Pitfall 8). Every figure below is a **quoted command output**, not a paraphrase. Where a block has
not been measured yet it says so in §7 rather than carrying a plausible number.

The run this note prepares for is the 16-point canary audit of `results/phase25_frontier.json`'s
`dp_n8` points (`scripts/phase26_canary.py` under `artifacts/com.personacore.phase26.canary.plist`):
the adapter-off arm once, then adapter-on over the σ=0 control and the 15 noised points, **≈ 25 h
of MPS** (§3). The shape of this note copies `results/phase25_operational_note.md`, whose launch
checklist found six defects before the first GPU second; the blocks here are the ones that record
the Phase-26 analogues.

---

## 1. The pre-registration state

This note is the **first tracked `results/phase26_*` file**. The ancestry guard
(`tests/test_phase26_prereg.py::test_phase26_prereg_is_frozen_before_every_phase26_result`) requires
every commit touching `scripts/phase26_prereg.py` to be a strict ancestor of this note's first-add
commit, so the note lands strictly after every prereg commit, and `scripts/phase26_prereg.py` is
not touched by this plan or any later one. Read at `525b0cd`, before this note was committed:

```
$ git log --format='%h %ad %s' --date=short -- scripts/phase26_prereg.py
e6a8851 2026-09-10 feat(26-01): commit the Phase-26 pre-registration — scripts/phase26_prereg.py
$ git ls-files 'results/phase26_*'
(empty — no Phase-26 result was tracked before this note)
$ .venv/bin/python -c "import sys; sys.path.insert(0,'scripts'); import phase26_prereg as p; print('SIDECARS_AT_COMMIT =', p.SIDECARS_AT_COMMIT, '| COMMITTED =', p.COMMITTED, '| CONTROL_KEY =', p.CONTROL_KEY)"
SIDECARS_AT_COMMIT = 0 | COMMITTED = 2026-09-10 | CONTROL_KEY = dp_n8_sigma0p000000
$ ls data/phase26_canary_*.json
zsh: no matches found: data/phase26_canary_*.json
```

One prereg commit (`e6a8851`), zero tracked Phase-26 results, zero sidecars on disk: the module's
`SIDECARS_AT_COMMIT = 0` is still true at launch. The guard's `checked` count after this note's
first-add commit is therefore `len(prereg_commits) × 1 = 1` (quoted in §5 once the commit exists).

## 2. The assertion owners before launch

Read live, read-only, before anything was installed or loaded. Nothing was killed: the two
`caffeinate` processes present are not this run's, and Phase 25's rule (its note §2, D-43) is to
**record** an owner that is not ours rather than reason about it during the run.

```
$ pgrep -lf caffeinate
15665 caffeinate -s -i -w 7584
58888 caffeinate -i -t 300
$ ps -o pid,ppid,args -p 15665,58888,7584
  PID  PPID ARGS
 7584     1 /Users/juliorcoelho/.pyenv/versions/3.12.13/bin/python3.12 /Users/juliorcoelho/polymarket-bot/scripts/collect_negrisk_books.py --service --interval 900 --depth-usd 100 --output /Users/juliorcoelho/polymarket-bot/data/negrisk_books/books.jsonl --status-file /Users/juliorcoelho/polymarket-bot/data/negrisk_books/status.json
15665     1 caffeinate -s -i -w 7584
58888 86995 caffeinate -i -t 300
```

Owners, named:

- **`58888 caffeinate -i -t 300`** — the Claude harness's own 300-second assertion (its parent
  `86995` is the harness; Phase 25 §12.4 saw the same shape as pid 15781). It is renewed by the
  console session, not by anything this run owns, and it is gone whenever the console is.
- **`15665 caffeinate -s -i -w 7584`** — a stray relative to this run: it waits on pid `7584`, an
  unrelated `polymarket-bot` collector service, and both are parented by launchd (`PPID 1`). It is
  the same pid RESEARCH Pitfall 9 recorded on 2026-09-10. Not ours; **not killed**; recorded.
  `phase25_venue.prove_only_our_caffeinate` will REFUSE while it exists (as it did in Phase 25
  §12.4 on the console's own caffeinate) — that refusal is the function doing its job, and the
  owner is named here so the refusal reads as "known stray, another service's", not "unknown".
- **`14542 Claude`** — the desktop app's `NoIdleSleepAssertion` (Electron), the same owner Phase 25
  §2 tolerated by name.

```
$ pmset -g assertions | grep -i -E 'caffeinate|PreventUserIdleSystemSleep|PreventSystemSleep|pid'
   PreventSystemSleep             1
   PreventUserIdleSystemSleep     1
   pid 14542(Claude): [0x005f585700018db4] 29:08:07 NoIdleSleepAssertion named: "Electron"
   pid 58888(caffeinate): [0x0060c66800018394] 00:00:58 PreventUserIdleSystemSleep named: "caffeinate command-line tool"
	Details: caffeinate asserting for 300 secs
   pid 15665(caffeinate): [0x005e5d0900018aee] 47:00:21 PreventUserIdleSystemSleep named: "caffeinate command-line tool"
	Details: caffeinate asserting on behalf of Process ID 7584
   pid 15665(caffeinate): [0x005e5d0900078aef] 47:00:21 PreventSystemSleep named: "caffeinate command-line tool"
	Details: caffeinate asserting on behalf of Process ID 7584
$ pmset -g | grep -E 'sleep|powernap'
 hibernatefile        /var/vm/sleepimage
 powernap             1
 networkoversleep     0
 disksleep            10
 sleep                1 (sleep prevented by Claude, caffeinate, caffeinate, caffeinate)
 displaysleep         10
$ launchctl list | grep personacore
(empty — no personacore agent loaded before this launch)
```

`sleep 1 / disksleep 10 / powernap 1` — the same three values as `phase25_venue.PMSET_REVERT_TARGETS`
and as Phase 25's close restored. **System sleep after one minute of idle** is therefore the live
hazard, and nothing is changed about it: per D-16 the LaunchAgent's own `caffeinate -dims` is what
carries the run, and the two strays above are neither relied on nor removed. (`pmset -g`'s summary
line says `caffeinate` three times for two processes because pid 15665 holds two assertions; the
per-pid list above is the reading used, as Phase 25 §2 explains.)

No personacore agent was loaded at read time. The Phase-25 close had booted every agent out; the
five Phase-25 plists are still installed under `~/Library/LaunchAgents/` (`n64floor`, `recall`,
`rehearsal`, `sweep`, `watch`) and only `watch` is loaded again in §5, because it is
detect-never-act (T-26-04) and already polls the heartbeat file the canary plist names.

## 3. The budget as measured

RESEARCH Pitfall 4's arithmetic, re-derived here from `results/phase25_recall.json`'s recorded
`scoring_seconds` rather than restated. The Phase-25 recall scored each `dp_n8` point over 2 arms ×
184 IN questions = 368 question-scorings; D-08 (both tiers, locked) makes each Phase-26 adapter-ON
arm score IN 112 + 72 and OUT 784 + 504 = 1472 questions.

```
$ .venv/bin/python - <<'EOF'   # reads results/phase25_recall.json; prints the arithmetic
control scoring_seconds = 914.5 s over 368 question-scorings -> 2.49 s/question
noised  scoring_seconds = 1246.9 (dp_n8_sigma0p500000) .. 1567.8 (dp_n8_sigma8p000000) s -> 3.39 .. 4.26 s/question
D-08 both tiers, one adapter-ON arm per point = IN 184 + OUT 1288 = 1472 questions
per noised point: 1472 x 3.82 s = 5629 s = 93.8 min
x 15 noised points = 23.5 h
control ON: 1472 x 2.49 s = 61.0 min ; OFF once on the base at the same rate = 61.0 min
total = 25.5 h
EOF
```

So: **≈ 25 h** of MPS (OFF ≈ 61 min, control ON ≈ 61 min, 15 noised points ≈ 93 min each ≈ 23 h).
The CONTEXT's "~40 min per point / ≈ 11 h" was derived from the control's 914 s alone — the one
adapter whose questions resolve fastest because it answers them — and is **superseded** by this
measured figure; noised adapters take 3.4–4.3 s per question because no draw stops early. Nothing
is cut at plan time: D-08 (both tiers) is locked, and the per-point sidecars make a kill resumable
by hash rather than a reason to shrink the set. The measured OFF and control `scoring_seconds` are
compared against this estimate in §6.

## 4. The wiring proof

The Phase-25 lesson (STATE.md, 2026-09-04): 23 green `--dry-run` tests hid a driver whose live path
was never wired. The two live-path tests of `tests/test_phase26_canary.py` stub only model loading
and the draws, keep the real `score_question`, the real sidecar writes and the real `emit()`, and
route the control's IN-taught sum through the real `prove_reproduction`. Run **on this host** at
`525b0cd`:

```
$ .venv/bin/python -m pytest -q tests/test_phase26_canary.py::test_the_live_path_is_wired_end_to_end tests/test_phase26_canary.py::test_the_control_routes_its_in_taught_sum_through_prove_reproduction -x
..                                                                       [100%]
2 passed in 1.81s
```

The driver's structural walk, without torch (the banner line is `phase25_venue.launch_banner()`, the
one producer `launch_identity()` reads back; the OFF arm precedes every point — D-17):

```
$ .venv/bin/python scripts/phase26_canary.py --dry-run | tail -18
[phase25_launch] pid=68051 ppid=68049 pgid=68049 sid=68049
[phase26_canary] off: DRY RUN — would score the adapter-off arm on phase25_sigma0p000000_dp_n8_adapter.pt
[phase26_canary] dp_n8_sigma0p000000: DRY RUN — would score checkpoints/phase25_sigma0p000000_dp_n8_adapter.pt
[phase26_canary] dp_n8_sigma0p500000: DRY RUN — would score checkpoints/phase25_sigma0p500000_dp_n8_adapter.pt
[phase26_canary] dp_n8_sigma0p700000: DRY RUN — would score checkpoints/phase25_sigma0p700000_dp_n8_adapter.pt
[phase26_canary] dp_n8_sigma1p000000: DRY RUN — would score checkpoints/phase25_sigma1p000000_dp_n8_adapter.pt
[phase26_canary] dp_n8_sigma1p500000: DRY RUN — would score checkpoints/phase25_sigma1p500000_dp_n8_adapter.pt
[phase26_canary] dp_n8_sigma2p000000: DRY RUN — would score checkpoints/phase25_sigma2p000000_dp_n8_adapter.pt
[phase26_canary] dp_n8_sigma3p000000: DRY RUN — would score checkpoints/phase25_sigma3p000000_dp_n8_adapter.pt
[phase26_canary] dp_n8_sigma4p000000: DRY RUN — would score checkpoints/phase25_sigma4p000000_dp_n8_adapter.pt
[phase26_canary] dp_n8_sigma6p000000: DRY RUN — would score checkpoints/phase25_sigma6p000000_dp_n8_adapter.pt
[phase26_canary] dp_n8_sigma8p000000: DRY RUN — would score checkpoints/phase25_sigma8p000000_dp_n8_adapter.pt
[phase26_canary] dp_n8_sigma12p000000: DRY RUN — would score checkpoints/phase25_sigma12p000000_dp_n8_adapter.pt
[phase26_canary] dp_n8_sigma16p000000: DRY RUN — would score checkpoints/phase25_sigma16p000000_dp_n8_adapter.pt
[phase26_canary] dp_n8_sigma24p000000: DRY RUN — would score checkpoints/phase25_sigma24p000000_dp_n8_adapter.pt
[phase26_canary] dp_n8_sigma32p000000: DRY RUN — would score checkpoints/phase25_sigma32p000000_dp_n8_adapter.pt
[phase26_canary] dp_n8_sigma50p000000: DRY RUN — would score checkpoints/phase25_sigma50p000000_dp_n8_adapter.pt
[phase26_canary] dp_n8_sigma80p000000: DRY RUN — would score checkpoints/phase25_sigma80p000000_dp_n8_adapter.pt
```

The consumer, fed the empty sidecar set that exists at launch (the 26-02 verify one-liner; the
same call is repeated at the early-run gate against the REAL OFF and control records, §6):

```
$ .venv/bin/python -c "import sys; sys.path.insert(0,'scripts'); sys.path.insert(0,'src'); import phase26_canary as c; c.emit(c.SIDECAR_DIR/'_never_written.json')"
[phase26_canary] the adapter-off sidecar data/phase26_canary_off.json is missing — the audit is not complete; record the dated D-19 named limitation in results/phase26_operational_note.md instead of assembling a partial artifact
$ ls data/_never_written.json
ls: data/_never_written.json: No such file or directory
```

`emit()` refused naming this note as the D-19 home and wrote nothing. The note therefore exists
before the run can produce anything the consumer would have to refuse or assemble.

## 5. The launch record — 2026-09-11

Filled after kickstart in COMMIT B: `launchctl list`, the banner line from `logs/phase26_canary.out`,
the assertion owner with its parent pid, the first heartbeat line, and the `git rev-parse HEAD` the
sidecars' `instrument_git_sha` will carry (= this note's first-add commit, COMMIT A).

## 6. The early-run gate — PENDING

Filled by Task 3 from the checkpoint's six quoted outputs: the OFF sidecar and its base hash, the
consumer's refusal on the real records, the control's reproduction-gate log line and its sidecar
block.

## 7. Pending

- **§5** — pending until COMMIT B (the kickstart transcript, minutes after COMMIT A).
- **§6** — pending until Task 3 of plan 26-04, ≈ 2 h 15 min after kickstart, when the OFF sidecar
  and the control sidecar exist and the operator has answered "approved" or "halted".
- **The close** (the run's end, the artifact's `--emit`, the machine put back) — or, if the clock
  or the reproduction gate cuts the audit, the dated D-19 named-limitation entry — is plan 26-05's,
  not this plan's.
