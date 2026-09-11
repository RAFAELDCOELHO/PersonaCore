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

Everything below is the kickstart transcript, quoted; the commands ran from the operator's console
in this order, with COMMIT A (`4c01c43`, this note's first-add) checked out throughout.

### 5.1 Preconditions — COMMIT A and the ancestry guard

```
$ git log --diff-filter=A --format=%H -- results/phase26_operational_note.md
4c01c43fd3eae7e2c9e154a4328bd8f16cd21d85
$ git merge-base --is-ancestor e6a885106fcad5e6d12b676c0febbd954e61f129 4c01c43fd3eae7e2c9e154a4328bd8f16cd21d85 && echo ancestor OK
ancestor OK
$ .venv/bin/python -m pytest -q tests/test_phase26_prereg.py
.................                                                        [100%]
17 passed in 1.19s
$ .venv/bin/python -m pytest -q tests/test_phase26_prereg.py tests/test_phase26_canary.py -k "prereg_is_frozen or byte_identical or operational_note" -x
........                                                                 [100%]
8 passed, 34 deselected in 0.86s
```

The guard's `checked` count is `1` (one prereg commit × one tracked artifact) — it was
`0`, "honest with zero tracked paths", until this note existed.

### 5.2 The stall log, rotated; the heartbeat file, left in place

The Phase-25 close had booted the watcher out on 2026-09-09; its last 395 records describe the
end of the v4.0 sweep (every one `action_taken: "none"`). They would have polluted this run's stall
history, so — as Phase 25 §12.2 did — they were moved aside, not deleted. The heartbeat file was
left in place: the driver appends beats and the watcher reads only the last line.

```
$ wc -l data/phase25_stall.jsonl
     395 data/phase25_stall.jsonl
$ mv data/phase25_stall.jsonl data/phase25_stall.pre-launch-2026-09-11.jsonl
-rw-r--r--  1 juliorcoelho  staff   351472  9 set 00:30 data/phase25_stall.pre-launch-2026-09-11.jsonl
$ tail -1 data/phase25_stall.pre-launch-2026-09-11.jsonl | cut -c1-40
{"action_taken": "none", "action_taken_r
$ tail -1 data/phase25_heartbeat.jsonl
{"draw_index": null, "point": "adv_n64_ratio1p909091", "shape": null, "stage": "done", "utc": "2026-09-09T01:36:32.758275+00:00"}
```

### 5.3 Install and load — nothing starts

```
$ cp artifacts/com.personacore.phase26.canary.plist ~/Library/LaunchAgents/
$ cmp artifacts/com.personacore.phase26.canary.plist ~/Library/LaunchAgents/com.personacore.phase26.canary.plist && echo "installed copy byte-identical"
installed copy byte-identical
$ launchctl load ~/Library/LaunchAgents/com.personacore.phase26.canary.plist
$ launchctl load ~/Library/LaunchAgents/com.personacore.phase25.watch.plist
$ launchctl list | grep personacore
-	0	com.personacore.phase25.watch
-	0	com.personacore.phase26.canary
$ launchctl print gui/501/com.personacore.phase26.canary | grep -iE 'keepalive|runs =|state ='
	state = not running
	runs = 0
```

Loading started nothing (`RunAtLoad false`; the absent `keepalive` line is the as-loaded form of
`KeepAlive false`, as Phase 25 §12.3 records). The watcher is a `StartInterval 60` job
(`KeepAlive false`, `RunAtLoad false`) — it ticks once a minute and exits, which is why its
`launchctl list` PID reads `-`. It detects and never acts (T-26-04).

### 5.4 Kickstart

```
== kickstart at 2026-09-11T16:23:57Z
$ launchctl kickstart -k gui/501/com.personacore.phase26.canary
kickstart exit=0
$ launchctl list | grep personacore
-	0	com.personacore.phase25.watch
70302	0	com.personacore.phase26.canary
$ head -1 logs/phase26_canary.out
[phase25_launch] pid=70302 ppid=1 pgid=70302 sid=1
$ launchctl print gui/501/com.personacore.phase26.canary | grep -iE 'runs =|state =|pid ='
	state = running
	runs = 1
	pid = 70302
```

### 5.5 The assertion read-back, 18 s after kickstart

The wrapper is the driver's CHILD (STATE.md 2026-09-04, the sixth Phase-25 defect): launchd started
`caffeinate -dims …` as pid 70302, which forked pid 70304 to hold the assertions "on behalf of"
70302 and then exec'd the venv python in place — so the banner's `pid=70302 ppid=1` IS the driver,
and the holder is found by `ppid == driver pid`, not the other way round.

```
$ pmset -g assertions | grep -i -E 'caffeinate|PreventUserIdleSystemSleep'
   PreventUserIdleSystemSleep     1
   pid 69922(caffeinate): [0x0060c758000183b9] 00:00:50 PreventUserIdleSystemSleep named: "caffeinate command-line tool"
	Details: caffeinate asserting for 300 secs
   pid 70304(caffeinate): [0x0060c778000183c8] 00:00:18 PreventUserIdleSystemSleep named: "caffeinate command-line tool"
	Details: caffeinate asserting on behalf of '/Users/juliorcoelho/PersonaCore/.venv/bin/python' (pid 70302)
   pid 70304(caffeinate): [0x0060c778000583c9] 00:00:18 PreventUserIdleDisplaySleep named: "caffeinate command-line tool"
	Details: caffeinate asserting on behalf of '/Users/juliorcoelho/PersonaCore/.venv/bin/python' (pid 70302)
   pid 70304(caffeinate): [0x0060c778000783ca] 00:00:18 PreventSystemSleep named: "caffeinate command-line tool"
	Details: caffeinate asserting on behalf of '/Users/juliorcoelho/PersonaCore/.venv/bin/python' (pid 70302)
   pid 70304(caffeinate): [0x0060c778000f83cb] 00:00:18 PreventDiskIdle named: "caffeinate command-line tool"
	Details: caffeinate asserting on behalf of '/Users/juliorcoelho/PersonaCore/.venv/bin/python' (pid 70302)
   pid 15665(caffeinate): [0x005e5d0900018aee] 47:04:12 PreventUserIdleSystemSleep named: "caffeinate command-line tool"
	Details: caffeinate asserting on behalf of Process ID 7584
   pid 15665(caffeinate): [0x005e5d0900078aef] 47:04:12 PreventSystemSleep named: "caffeinate command-line tool"
	Details: caffeinate asserting on behalf of Process ID 7584
$ ps -o pid,ppid,args -p 15665,69922,70304,70302
  PID  PPID ARGS
15665     1 caffeinate -s -i -w 7584
70302     1 /opt/homebrew/Cellar/python@3.11/3.11.15_1/Frameworks/Python.framework/Versions/3.11/Resources/Python.app/Contents/MacOS/Python /Users/juliorcoelho/PersonaCore/scripts/phase26_canary.py --heartbeat /Users/juliorcoelho/PersonaCore/data/phase25_heartbeat.jsonl
70304 70302 /usr/bin/caffeinate -dims /Users/juliorcoelho/PersonaCore/.venv/bin/python /Users/juliorcoelho/PersonaCore/scripts/phase26_canary.py --heartbeat /Users/juliorcoelho/PersonaCore/data/phase25_heartbeat.jsonl
69922 86995 caffeinate -i -t 300
$ pgrep -P 70302 -l
70304 caffeinate
```

Four assertions (`-dims`: display, idle, system, disk) held by pid 70304 whose `PPID` is 70302, the
driver — the run holds its own wake claim and cannot outlive it. The two owners §2 named are still
there and still not ours: the console's 300-second caffeinate has rotated from pid 58888 to 69922
(the harness renews it), and the polymarket stray 15665 is unchanged.

### 5.6 The first heartbeat, and the SHA the sidecars carry

```
$ tail -1 data/phase25_heartbeat.jsonl
{"draw_index": null, "point": "off", "shape": null, "stage": "score", "utc": "2026-09-11T16:23:58.442696+00:00"}
$ git rev-parse HEAD
4c01c43fd3eae7e2c9e154a4328bd8f16cd21d85
$ ls -la data/phase25_stall.jsonl
ls: data/phase25_stall.jsonl: No such file or directory
$ date -u +%Y-%m-%dT%H:%M:%SZ
2026-09-11T16:24:15Z
```

The first beat is the adapter-off arm (`point: "off"`, `stage: "score"`), 1 s after kickstart —
D-17's "once, before any point" is what the heartbeat shows first. No stall record has been written:
the beat landed before the watcher's first tick, so unlike Phase 25 §12.2 there is no
pre-kickstart-silence record to carry. `HEAD` at kickstart is `4c01c43` = COMMIT A, so every
sidecar's `instrument_git_sha` names the commit that contains this note's §1–§4 (T-26-03).

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
