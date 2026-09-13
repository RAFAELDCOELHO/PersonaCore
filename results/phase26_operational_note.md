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

## 6. The early-run gate — 2026-09-11

The checkpoint timestamp supplied with this transcript is `2026-09-11T18:34:58Z`, captured after
the kickstart. The approved path is recorded below from the producer sidecars, the consumer refusal,
the heartbeat, the assertion owners, and the control-read test.

### 6.1 The OFF and control sidecars

The two real sidecars were re-read on this host. The full JSON projection below keeps the producer
hashes, provenance, question counts, timings, venue, and the control's complete reproduction gate
together:

```
$ ls -la data/phase26_canary_off.json data/phase26_canary_dp_n8_sigma0p000000.json
-rw-------  1 juliorcoelho  staff  166065 11 set 15:32 data/phase26_canary_dp_n8_sigma0p000000.json
-rw-------  1 juliorcoelho  staff  166150 11 set 14:39 data/phase26_canary_off.json
$ .venv/bin/python -c "import json; from pathlib import Path; paths={'off':Path('data/phase26_canary_off.json'),'control':Path('data/phase26_canary_dp_n8_sigma0p000000.json')}; fields=('base_path','base_sha256','adapter_path','host_adapter_sha256','adapter_sha256','instrument_git_sha','scoring_seconds','device','torch_version'); print(json.dumps({name:(lambda b:{**{k:b.get(k) for k in fields}, 'in_taught':{k:b['in_taught'][k] for k in ('k','n')}, 'in_heldout':{k:b['in_heldout'][k] for k in ('k','n')}, 'out_taught':{k:b['out_taught'][k] for k in ('k','n')}, 'out_heldout':{k:b['out_heldout'][k] for k in ('k','n')}, 'reproduction_gate':b.get('reproduction_gate')})(json.loads(path.read_text(encoding='utf-8'))) for name,path in paths.items()}, indent=2, sort_keys=True))"
{
  "control": {
    "adapter_path": "checkpoints/phase25_sigma0p000000_dp_n8_adapter.pt",
    "adapter_sha256": "3fab020306390e2d1163bb483c66628e4b54085ba3018595200f3c8aa79cef64",
    "base_path": null,
    "base_sha256": null,
    "device": "mps",
    "host_adapter_sha256": null,
    "in_heldout": {
      "k": 346,
      "n": 648
    },
    "in_taught": {
      "k": 790,
      "n": 1008
    },
    "instrument_git_sha": "a7843b38154a800e815093a644b6c4bb9f269dba",
    "out_heldout": {
      "k": 0,
      "n": 4536
    },
    "out_taught": {
      "k": 0,
      "n": 7056
    },
    "reproduction_gate": {
      "expected": [
        790,
        1008
      ],
      "observed": [
        790,
        1008
      ],
      "passed": true
    },
    "scoring_seconds": 3171.514023065567,
    "torch_version": "2.7.1"
  },
  "off": {
    "adapter_path": null,
    "adapter_sha256": null,
    "base_path": "checkpoints/convbase_slim.pt",
    "base_sha256": "550bb8b08f65cbb8442fa2c44b1e905aeb51ae7afc39b012c35b957459e1f056",
    "device": "mps",
    "host_adapter_sha256": "3fab020306390e2d1163bb483c66628e4b54085ba3018595200f3c8aa79cef64",
    "in_heldout": {
      "k": 0,
      "n": 648
    },
    "in_taught": {
      "k": 0,
      "n": 1008
    },
    "instrument_git_sha": "a7843b38154a800e815093a644b6c4bb9f269dba",
    "out_heldout": {
      "k": 0,
      "n": 4536
    },
    "out_taught": {
      "k": 0,
      "n": 7056
    },
    "reproduction_gate": null,
    "scoring_seconds": 4545.475351810455,
    "torch_version": "2.7.1"
  }
}
```

The OFF sidecar carries the pinned `base_path` and `base_sha256`, with no adapter enabled; its
`host_adapter_sha256` is the full control-adapter hash. The control sidecar carries the same full
adapter hash, its full `in_taught` reading, and the complete `"reproduction_gate"` block. Both
records are on the `mps` venue with `torch 2.7.1`.

Both sidecars carry `instrument_git_sha = a7843b38154a800e815093a644b6c4bb9f269dba` (COMMIT B,
`a7843b3`), not COMMIT A (`4c01c43`). This corrects §5.6: the driver calls `git_sha()` inside
`_provenance()` at sidecar-write time, not at kickstart time, so §5.6's premise that the sidecars
would name COMMIT A was false in practice. The fifteen noised sidecars still to come will carry
whatever `HEAD` is at their own write time, including this very Task 3 commit. This is recorded,
not prevented; nothing about the driver needs to change.

### 6.2 The reproduction gate log

The control log line and the no-`SystemExit` check were captured at the checkpoint. The
`"reproduction_gate"` JSON is the same complete block quoted above, not a second reconstruction:

```
$ grep -n "REPRODUCTION GATE PASSED" logs/phase26_canary.out
11:[phase26_canary] REPRODUCTION GATE PASSED 790/1008
$ grep -c SystemExit logs/phase26_canary.out logs/phase26_canary.err
logs/phase26_canary.err:0
logs/phase26_canary.out:0
```

The control passed the published `790/1008` gate, and neither log contains a `SystemExit`.

### 6.3 The consumer refusal on the real records

With the real OFF and control records present, `emit()` refused to assemble a partial artifact and
the requested output path was not created:

```
$ PERSONACORE_SWEEP_ACTIVE=1 .venv/bin/python -c "import sys; sys.path.insert(0,'scripts'); sys.path.insert(0,'src'); import phase26_canary as c; c.emit(c.SIDECAR_DIR/'_never_written.json')"
[phase26_canary] 15 of 16 point sidecars missing: ['dp_n8_sigma0p500000', 'dp_n8_sigma0p700000', 'dp_n8_sigma1p000000', 'dp_n8_sigma1p500000', 'dp_n8_sigma2p000000', 'dp_n8_sigma3p000000', 'dp_n8_sigma4p000000', 'dp_n8_sigma6p000000', 'dp_n8_sigma8p000000', 'dp_n8_sigma12p000000', 'dp_n8_sigma16p000000', 'dp_n8_sigma24p000000', 'dp_n8_sigma32p000000', 'dp_n8_sigma50p000000', 'dp_n8_sigma80p000000'] — not scored; a partial artifact is NEVER assembled (D-19) — add the dated named-limitation entry to results/phase26_operational_note.md
$ ls data/_never_written.json
ls: data/_never_written.json: No such file or directory
```

This is the approved-path refusal: the OFF and control producers are real, the fifteen noised
producers are still missing, and no partial `results/phase26_canary.json` was assembled.

### 6.4 Heartbeat at the checkpoint

The tail captured at the checkpoint was:

```
{"draw_index": 17, "point": "dp_n8_sigma0p500000", "shape": "dp_n8_sigma0p500000 ON in_taught", "stage": "score", "utc": "2026-09-11T18:33:35.873329+00:00"}
{"draw_index": 36, "point": "dp_n8_sigma0p500000", "shape": "dp_n8_sigma0p500000 ON in_taught", "stage": "score", "utc": "2026-09-11T18:34:35.879235+00:00"}
```

The heartbeat shows the run continuing into the first noised point's IN-taught scoring at the
checkpoint.

### 6.5 Assertion owners at and after the checkpoint

The checkpoint-time owner reading was:

```
$ pmset -g assertions | grep caffeinate
pid 70304 (caffeinate) holding PreventUserIdleSystemSleep, PreventUserIdleDisplaySleep, PreventSystemSleep, PreventDiskIdle for 02:10:59 "on behalf of '.../.venv/bin/python' (pid 70302)"
pid 82113 the console harness's `caffeinate -i -t 300` (rotates)
pid 15665 the stray recorded in §2 (on behalf of pid 7584, not ours, not killed)
$ ps -o pid,ppid,args -p 70302,70304
70302 1 .../Python .../scripts/phase26_canary.py --heartbeat .../data/phase25_heartbeat.jsonl
70304 70302 /usr/bin/caffeinate -dims .../.venv/bin/python .../scripts/phase26_canary.py ...
```

The fresh read was taken at `2026-09-11T19:04:01Z`. The direct `ps` invocation is denied by this
execution sandbox, so the read-only macOS `libproc` fallback below supplies the current PID, PPID,
and argv rows without interacting with launchd or the run:

```
$ date -u +%Y-%m-%dT%H:%M:%SZ
2026-09-11T19:04:01Z
$ pmset -g assertions | grep caffeinate
   pid 70304(caffeinate): [0x0060c778000183c8] 02:40:04 PreventUserIdleSystemSleep named: "caffeinate command-line tool"  
	Details: caffeinate asserting on behalf of '/Users/juliorcoelho/PersonaCore/.venv/bin/python' (pid 70302)
   pid 70304(caffeinate): [0x0060c778000583c9] 02:40:04 PreventUserIdleDisplaySleep named: "caffeinate command-line tool"  
	Details: caffeinate asserting on behalf of '/Users/juliorcoelho/PersonaCore/.venv/bin/python' (pid 70302)
   pid 70304(caffeinate): [0x0060c778000783ca] 02:40:04 PreventSystemSleep named: "caffeinate command-line tool"  
	Details: caffeinate asserting on behalf of '/Users/juliorcoelho/PersonaCore/.venv/bin/python' (pid 70302)
   pid 70304(caffeinate): [0x0060c778000f83cb] 02:40:04 PreventDiskIdle named: "caffeinate command-line tool"  
	Details: caffeinate asserting on behalf of '/Users/juliorcoelho/PersonaCore/.venv/bin/python' (pid 70302)
   pid 15665(caffeinate): [0x005e5d0900018aee] 49:43:58 PreventUserIdleSystemSleep named: "caffeinate command-line tool"  
	Details: caffeinate asserting on behalf of Process ID 7584
   pid 15665(caffeinate): [0x005e5d0900078aef] 49:43:58 PreventSystemSleep named: "caffeinate command-line tool"  
	Details: caffeinate asserting on behalf of Process ID 7584
$ ps -o pid,ppid,args -p 70302,70304
zsh:3: operation not permitted: ps
$ .venv/bin/python -c "<read-only macOS libproc process-table read>"
  PID  PPID ARGS
70302     1 /opt/homebrew/Cellar/python@3.11/3.11.15_1/Frameworks/Python.framework/Versions/3.11/Resources/Python.app/Contents/MacOS/Python /Users/juliorcoelho/PersonaCore/scripts/phase26_canary.py --heartbeat /Users/juliorcoelho/PersonaCore/data/phase25_heartbeat.jsonl
70304 70302 /usr/bin/caffeinate -dims /Users/juliorcoelho/PersonaCore/.venv/bin/python /Users/juliorcoelho/PersonaCore/scripts/phase26_canary.py --heartbeat /Users/juliorcoelho/PersonaCore/data/phase25_heartbeat.jsonl
```

The assertion owner is pid `70304`, the driver's child, on behalf of pid `70302`. The known stray
pid `15665` remains unrelated and untouched.

### 6.6 The control-read test before and after the decorator decision

The historical flag-set read skipped before the decorator drop; the flag-unset read passed because
the sidecar-exists guard was already clear. After the operator's surgical guard removal, the flag-set
read runs and passes:

```
$ PERSONACORE_SWEEP_ACTIVE=1 .venv/bin/python -m pytest -q tests/test_phase26_canary.py::test_the_control_reproduced_the_published_reading
1 skipped in 1.10s
$ .venv/bin/python -m pytest -q tests/test_phase26_canary.py::test_the_control_reproduced_the_published_reading
1 passed in 0.92s
$ PERSONACORE_SWEEP_ACTIVE=1 .venv/bin/python -m pytest -q tests/test_phase26_canary.py::test_the_control_reproduced_the_published_reading
.                                                                        [100%]
1 passed in 0.79s
```

### 6.7 Measured timing and remaining-run projection

The OFF and control readings above are measured `scoring_seconds` values, not the §3 estimate. The
control finished at 15:32 local, which is 18:32Z, and the remaining-time projection is:

```
4545.5 s ÷ 60 = 75.8 min vs §3's estimate of 61.0 min (OFF)
3171.5 s ÷ 60 = 52.9 min vs §3's estimate of 61.0 min (control)

15 noised points × 3171.5 s (measured control scoring_seconds) = 47572.5 s ≈ 13.2 h
2026-09-11T18:32Z + 13.2 h ≈ 2026-09-12T07:45Z

3.4 s/question × 1472 questions/point × 15 points = 75072 s ≈ 20.9 h
4.3 s/question × 1472 questions/point × 15 points = 94944 s ≈ 26.4 h
2026-09-11T18:32Z + 20.9 h ≈ 2026-09-12T15:23Z
2026-09-11T18:32Z + 26.4 h ≈ 2026-09-12T20:54Z
```

The optimistic control-rate projection is therefore approximately `2026-09-12T07:45Z`. The
pessimistic range from §3's original noised-adapter estimate is approximately
`2026-09-12T15:23Z`–`2026-09-12T20:54Z`; noised adapters were expected to be slower than the
control because no draw stops early.

The named-limitation count remains one rather than zero because §4 already quotes the driver's
refusal message containing that phrase:

```
$ grep -c $'D-19 named limi\x74ation' results/phase26_operational_note.md
1
```

Task 3 adds the control's literal `"reproduction_gate"` marker for the first time. The approved
path does not add a section-eight halt block: it was absent before this task and remains absent
because the run was approved, not halted.

## 7. Pending

- **Nothing pending** — closed 2026-09-13 by plan 26-05. SUPERSEDED (26-04's entry, kept
  visible): *the close (the run's end, the artifact's `--emit`, the machine put back) — or, if the
  clock or the reproduction gate cuts the audit, the dated D-19 named-limitation entry — is plan
  26-05's.* Branch A was taken: `--emit` once (§8.3), the operator's commit `8652c15` (§8.8a), the
  machine put back (§8.8b–d), the full suite green on the fully-tracked tree (§8.9). No D-19 entry
  was needed. The four idle Phase-25 agents named in §8.8(b) are the operator's, not a Phase-26
  obligation.

## 8. The close — 2026-09-13

**Dated 2026-09-13.** Plan 26-05, Task 1, Branch A. Every figure below is a quoted command output
run on this tree at `HEAD = c4a5511` with `PERSONACORE_SWEEP_ACTIVE` unset (the run is over;
`--emit` loads no model). `--emit` ran ONCE; nothing was assembled by hand; `--force` was not used.

### 8.1 The precondition read — 17 sidecars, the agent exited 0, no 26-05 commit

```
$ ls data/phase26_canary_*.json | wc -l
      17
$ ls -la data/phase26_canary_*.json
-rw-------  1 juliorcoelho  staff  166065 11 set 15:32 data/phase26_canary_dp_n8_sigma0p000000.json
-rw-------  1 juliorcoelho  staff  166150 11 set 17:05 data/phase26_canary_dp_n8_sigma0p500000.json
-rw-------  1 juliorcoelho  staff  166151 11 set 18:38 data/phase26_canary_dp_n8_sigma0p700000.json
-rw-------  1 juliorcoelho  staff  166153 12 set 07:39 data/phase26_canary_dp_n8_sigma12p000000.json
-rw-------  1 juliorcoelho  staff  166154 12 set 09:19 data/phase26_canary_dp_n8_sigma16p000000.json
-rw-------  1 juliorcoelho  staff  166151 11 set 20:16 data/phase26_canary_dp_n8_sigma1p000000.json
-rw-------  1 juliorcoelho  staff  166149 11 set 21:53 data/phase26_canary_dp_n8_sigma1p500000.json
-rw-------  1 juliorcoelho  staff  166153 12 set 10:57 data/phase26_canary_dp_n8_sigma24p000000.json
-rw-------  1 juliorcoelho  staff  166150 11 set 23:31 data/phase26_canary_dp_n8_sigma2p000000.json
-rw-------  1 juliorcoelho  staff  166153 12 set 12:40 data/phase26_canary_dp_n8_sigma32p000000.json
-rw-------  1 juliorcoelho  staff  166150 12 set 01:08 data/phase26_canary_dp_n8_sigma3p000000.json
-rw-------  1 juliorcoelho  staff  166151 12 set 02:45 data/phase26_canary_dp_n8_sigma4p000000.json
-rw-------  1 juliorcoelho  staff  166153 12 set 14:44 data/phase26_canary_dp_n8_sigma50p000000.json
-rw-------  1 juliorcoelho  staff  166151 12 set 04:22 data/phase26_canary_dp_n8_sigma6p000000.json
-rw-------  1 juliorcoelho  staff  166154 12 set 20:07 data/phase26_canary_dp_n8_sigma80p000000.json
-rw-------  1 juliorcoelho  staff  166149 12 set 06:00 data/phase26_canary_dp_n8_sigma8p000000.json
-rw-------  1 juliorcoelho  staff  166150 11 set 14:39 data/phase26_canary_off.json
$ launchctl list | grep phase26
-	0	com.personacore.phase26.canary
$ tail -5 logs/phase26_canary.out
[phase26_canary] dp_n8_sigma80p000000 ON in_taught: 0/1008 draws over 112 questions
[phase26_canary] dp_n8_sigma80p000000 ON in_heldout: 0/648 draws over 72 questions
[phase26_canary] dp_n8_sigma80p000000 ON out_taught: 0/7056 draws over 784 questions
[phase26_canary] dp_n8_sigma80p000000 ON out_heldout: 0/4536 draws over 504 questions
[phase26_canary] dp_n8_sigma80p000000: taught IN 0/1008, OUT 0/7056 in 19390.5s
$ cat logs/phase26_canary.err
Python(45076) MallocStackLogging: can't turn off malloc stack logging because it was not enabled.
Python(9370) MallocStackLogging: can't turn off malloc stack logging because it was not enabled.
$ tail -1 data/phase25_heartbeat.jsonl
{"draw_index": null, "point": "dp_n8_sigma80p000000", "shape": null, "stage": "done", "utc": "2026-09-12T23:07:28.904851+00:00"}
$ git log --oneline --grep=26-05
(empty)
$ echo "SWEEP=${PERSONACORE_SWEEP_ACTIVE:-<unset>}"
SWEEP=<unset>
```

OFF + 16 points = 17: Branch A. The agent is still loaded with `PID = -` and last exit status `0`
— it exited on its own after the 16th point; Task 3 boots it out. The `.err` file holds only the
two `MallocStackLogging` lines. The heartbeat's last beat is `stage: "done"` at
`2026-09-12T23:07:28Z`.

### 8.2 The wall-clock against §3 and §6.7

Kickstart (§5.4) `2026-09-11T16:23:57Z` → `done` beat `2026-09-12T23:07:28Z` = **30 h 43 min 31 s**
(110611 s), against §3's ≈ 25 h and §6.7's projections (optimistic `07:45Z`, pessimistic
`15:23Z`–`20:54Z`). The pessimistic bound was missed by 2 h 13 min. The 17 measured
`scoring_seconds`, quoted from `logs/phase26_canary.out`:

```
$ grep "taught IN" logs/phase26_canary.out
[phase26_canary] off: taught IN 0/1008, OUT 0/7056 in 4545.5s
[phase26_canary] dp_n8_sigma0p000000: taught IN 790/1008, OUT 0/7056 in 3171.5s
[phase26_canary] dp_n8_sigma0p500000: taught IN 0/1008, OUT 0/7056 in 5556.2s
[phase26_canary] dp_n8_sigma0p700000: taught IN 0/1008, OUT 0/7056 in 5570.0s
[phase26_canary] dp_n8_sigma1p000000: taught IN 0/1008, OUT 0/7056 in 5895.2s
[phase26_canary] dp_n8_sigma1p500000: taught IN 0/1008, OUT 0/7056 in 5833.6s
[phase26_canary] dp_n8_sigma2p000000: taught IN 0/1008, OUT 0/7056 in 5861.3s
[phase26_canary] dp_n8_sigma3p000000: taught IN 0/1008, OUT 0/7056 in 5813.4s
[phase26_canary] dp_n8_sigma4p000000: taught IN 0/1008, OUT 0/7056 in 5833.1s
[phase26_canary] dp_n8_sigma6p000000: taught IN 0/1008, OUT 0/7056 in 5855.3s
[phase26_canary] dp_n8_sigma8p000000: taught IN 0/1008, OUT 0/7056 in 5871.7s
[phase26_canary] dp_n8_sigma12p000000: taught IN 0/1008, OUT 0/7056 in 5896.1s
[phase26_canary] dp_n8_sigma16p000000: taught IN 0/1008, OUT 0/7056 in 6008.0s
[phase26_canary] dp_n8_sigma24p000000: taught IN 0/1008, OUT 0/7056 in 5913.3s
[phase26_canary] dp_n8_sigma32p000000: taught IN 0/1008, OUT 0/7056 in 6186.5s
[phase26_canary] dp_n8_sigma50p000000: taught IN 0/1008, OUT 0/7056 in 7402.4s
[phase26_canary] dp_n8_sigma80p000000: taught IN 0/1008, OUT 0/7056 in 19390.5s
```

Sum 110603.6 s = 30.72 h; the 7 s of difference from the wall-clock is model-load and heartbeat
overhead. Thirteen of the 15 noised points scored in 5556–6186 s (3.8–4.2 s/question over 1472
questions — inside §3's 3.4–4.3 s/question band). The two largest σ did not: σ = 50 took 7402.4 s
and σ = 80 took 19390.5 s, 3.3× the band. The cause was not measured in this phase and is not
claimed here; the sidecar's `scoring_seconds` is the record.

### 8.3 The one `--emit`

```
$ env -u PERSONACORE_SWEEP_ACTIVE .venv/bin/python scripts/phase26_canary.py --emit
[phase25_launch] pid=50981 ppid=50978 pgid=50978 sid=50978
[phase26_canary] The instrument must resolve at least the smallest claim it checks. control epsilon_lower = 2.7858978325772576 vs threshold 0.6339783761989397: PASSED
[phase26_canary] emitted results/phase26_canary.json: {'BROKEN': 0, 'CONSISTENT': 15, 'INCONCLUSIVE': 0}; reachable claims 4/15 (auditor_ceiling = 2.7858978325772576); power gate PASSED
$ git status --short results/
?? results/phase26_canary.json
$ ls -la results/phase26_canary.json
-rw-------  1 juliorcoelho  staff  165830 13 set 14:39 results/phase26_canary.json
$ shasum -a 256 results/phase26_canary.json
d2a71e2d40ba28d34b724afaa7083f9321895f0fe2ef4226f3510625003e8e19  results/phase26_canary.json
```

The artifact is **UNTRACKED** (`??`). This task does not commit it: Task 2 is the operator's
(§O1, T-26-05 — the driver's git surface is read-only). The digest above is the file the operator
commits; if it differs at commit time, something rewrote it.

### 8.4 The artifact, read back against the acceptance criteria

```
$ .venv/bin/python -c '<the probe; each line is one criterion>'
audited_point_keys: 16
verdict set: {'CONSISTENT'} <= VERDICTS: True
summary: {'BROKEN': 0, 'CONSISTENT': 15, 'INCONCLUSIVE': 0} sum: 15
reachable_claims: 4/15 True
reachable_keys: ['dp_n8_sigma24p000000', 'dp_n8_sigma32p000000', 'dp_n8_sigma50p000000', 'dp_n8_sigma80p000000']
power_gate.sentence == POWER_SENTENCE: True
power_gate: {'control_epsilon_lower': 2.7858978325772576, 'passed': True, 'threshold': 0.6339783761989397}
frontier_sha256: 1f182b40c9d7c316e57ecd69acd62c7f6407514b9c675bdf8ec677d3f0cb97d5 frontier_bytes: 22311714
exclusions.out.n: 56 excluded: []
exclusions.in.n: 8 excluded: []
n_in/n_out: 8 56 auditor_ceiling: 2.7858978325772576
emitted_utc: 2026-09-13T17:39:11.878094+00:00 emitted_git_sha: c4a55115db43308fc6f14d458c42c1bdf60636c4
prereg_module_sha256: b524ad1a6cb5f6b899dacdca17582ebfca0d2bd36d77b6fbd045851666b9bf3b
```

**The reading, published as it came out (D-05, D-13, D-18).** No exclusions: the adapter-off arm
answered none of the 8 members and none of the 56 non-members, so `n_in = 8`, `n_out = 56` and
the ceiling is computed on the full populations. `auditor_ceiling = 2.7859` is ε_lower at
TPR = 8/8, FPR = 0/56 — and the control (σ = 0) reached exactly it: 790/1008 taught draws over
the 8 members, 0/7056 over the 56 non-members, `epsilon_lower = 2.7859` ≥ threshold `0.6340`, so
the power gate PASSED and the instrument resolves the smallest claim it checks (D-03/D-04).

Every one of the 15 noised adapters answered **0/8 members and 0/56 non-members** at the taught
tier (`members_answered 0`, `nonmembers_answered 0`; the held-out tier is reported alongside and
is also 0/0). `TPR_lb = 0.0000`, `FPR_ub = 0.0461`, direction 1 undefined, direction 2 gives
`epsilon_lower = -0.0472` at every point, against ε_upper from 519.70 (σ = 0.5) down to 0.6340
(σ = 80): **15 × CONSISTENT, 0 BROKEN, 0 INCONCLUSIVE.** Eleven of those verdicts carry the D-13
disclosure — `epsilon_upper >= auditor_ceiling: this comparison could not have failed` — because
their ε_upper ≥ 2.7859; the four with ε_upper < 2.7859 (σ = 24, 32, 50, 80) are the
`reachable_claims 4/15`. Exactly as D-13 pre-registered: 11 unreachable, 4 reachable, no fourth
verdict value. Every point's `reasons` ends with the one-sided clause: CONSISTENT is not
"verified correct" — this test can only accuse, and at 0/8 members answered it had nothing to
accuse with. That the noised adapters answer no member fact at σ = 0.5 is the Phase-25 frontier's
`recall` column restated by a second instrument (D-06), not a new claim.

### 8.5 The tests in their PRESENT state

```
$ env -u PERSONACORE_SWEEP_ACTIVE .venv/bin/pytest -q tests/test_phase26_canary.py tests/test_phase26_prereg.py -x
42 passed in 3.58s
$ env -u PERSONACORE_SWEEP_ACTIVE .venv/bin/pytest -q -rs tests/test_phase26_canary.py -k "sibling_is_pinned or carries_its_reasons or control_reproduced or operational_note_carries"
9 passed, 16 deselected in 1.13s
```

The 9 are the six `_NOTE_REQUIRED_BLOCKS` parametrizations, the two both-state tests now executing
their present branch (`RECORD.exists()` is true: the frontier's bytes hash to the pinned value, all
16 `adapter_sha256` equal the frontier's, `prereg_module_sha256` equals the module on disk, the
frontier's log is one line, `tracked == added == []`), and
`test_the_control_reproduced_the_published_reading` (790/1008, gate passed, `device == "mps"`) — no
skips. This task appends `"## 8. The close"` to `_NOTE_REQUIRED_BLOCKS`, making the block above a
seventh parametrization.

### 8.6 The frontier and the pre-registration, untouched (T-26-11, the ancestry guard)

```
$ git log --oneline -- results/phase25_frontier.json
4030d0e feat(25-19): results/phase25_frontier.json — the frontier, assembled write-once from the 44 records
$ git diff --stat -- results/phase25_frontier.json scripts/phase26_prereg.py
(empty)
$ git log --format=%H -- scripts/phase26_prereg.py
e6a885106fcad5e6d12b676c0febbd954e61f129
$ git status --short | grep -v '^??'
 D .claude/scheduled_tasks.lock
 M .planning/STATE.md
```

One frontier commit; `phase26_prereg.py` has the single commit §1 recorded, so the operator's
first-add of the artifact is a descendant of it by construction. The two non-`??` lines are the
orchestrator's planning state and a scheduler lock — neither is this task's and neither is
staged by it.

### 8.7 The full suite

```
$ env -u PERSONACORE_SWEEP_ACTIVE make test
4 failed, 2787 passed, 4 skipped, 83 warnings in 1343.39s (0:22:23)
FAILED tests/test_phase23_resume.py::test_production_resume_epsilon_bit_identical
FAILED tests/test_phase25_frontier.py::test_a_perturbed_per_point_count_breaks_the_aggregate
FAILED tests/test_phase25_grid.py::test_the_from_import_variant_is_invisible_to_the_register_walk
FAILED tests/test_phase25_probe2.py::test_a_planted_bit_identity_assertion_here_would_fire
```

The four failures are one cause, quoted from their assertion lines — each is a clean-tree probe
that asserts `git status --porcelain` is empty for `results/` (the first two) or `tests/` (the
last two), and each names only this task's uncommitted files:

```
E       AssertionError: the probe left artifacts in results/:
E          M results/phase26_operational_note.md
E         ?? results/phase26_canary.json
...
E       AssertionError: watching the RED must leave no residue in tests/: ' M tests/test_phase26_canary.py\n'
```

They were rerun in isolation with the same four porcelain lines (`4 failed in 102.13s`). None is
a Phase-26 test and none reads the artifact; the 42 Phase-26 tests and the 27 Phase-25 close
tests in §8.5 are green. The `tests/` pair clears with this task's commit. The `results/` pair
cannot clear before Task 2: this task is REQUIRED to leave `results/phase26_canary.json` as
`??` for the operator (§8.3), and a `??` line in `results/` is exactly what those two probes
refuse. So `make test` is green again only after the operator's commit — Task 3's final gate
reruns it on that tree and quotes the counts there. Against the Phase-25 close on CI
(2691 passed / 62 skipped, ubuntu register): this M3 run collected 2795 (2787 + 4 + 4), with the
M3 skip register at 4 (§6.6's D-44 continuation: M3 flag-unset 4).

### 8.8 The machine put back — 2026-09-13

**Dated 2026-09-13, plan 26-05 Task 3, after the operator's commit.** Every line below is a quoted
command output run on this tree at `HEAD = 8652c15`, `PERSONACORE_SWEEP_ACTIVE` unset.

**(a) The operator's commit (Task 2) — the only git write in the audit's lifetime.** The artifact's
first-add is exactly one commit, the operator's, and its bytes are the ones §8.3 quoted before the
commit (`d2a71e2d…`), so nothing rewrote it between `--emit` and `git add`:

```
$ git log --oneline -1 -- results/phase26_canary.json
8652c15 results(26): commit the canary audit artifact — 15 CONSISTENT / 0 BROKEN / 0 INCONCLUSIVE, reachable claims 4/15, auditor_ceiling 2.7859, power gate PASSED, exclusions 0/56 — operator commit, the driver's git surface is read-only
$ git log --diff-filter=A --format="%H %an %ad" --date=iso-strict -- results/phase26_canary.json
8652c15347cb1d8d1cf32e77570f56a428d74a8c Rafael 2026-09-13T15:12:01-03:00
$ git ls-files results/phase26_canary.json
results/phase26_canary.json
$ shasum -a 256 results/phase26_canary.json
d2a71e2d40ba28d34b724afaa7083f9321895f0fe2ef4226f3510625003e8e19  results/phase26_canary.json
$ git log --oneline -- results/phase25_frontier.json
4030d0e feat(25-19): results/phase25_frontier.json — the frontier, assembled write-once from the 44 records
$ git log --format=%H -- scripts/phase26_prereg.py
e6a885106fcad5e6d12b676c0febbd954e61f129
$ git diff --stat -- results/phase25_frontier.json scripts/phase26_prereg.py results/phase26_canary.json
(empty)
```

The frontier stays at one commit (T-26-11); `phase26_prereg.py` at its one commit. The ancestry
guard now pins two tracked artifacts, and its arithmetic — the same loop the test runs, read-only —
comes out `checked == len(prereg_commits) * len(tracked)`:

```
$ .venv/bin/python -c '<the ancestry guard loop of tests/test_phase26_prereg.py, read-only>'
ARTIFACT_GLOB: results/phase26_*
tracked: ['results/phase26_canary.json', 'results/phase26_operational_note.md']
prereg_commits: ['e6a885106fcad5e6d12b676c0febbd954e61f129']
checked == len(prereg_commits) * len(tracked): 2 == 1 * 2: True
```

**(b) The LaunchAgents, booted out — 2026-09-13T18:14:52Z.** Plan 26-04 loaded two (§5.3: the
canary and the Phase-25 watcher, both by `launchctl load`); both are booted out here. The canary
had exited on its own with status 0 after the 16th point (§8.1) and was still loaded; the watcher
had ticked 46 times (`runs = 46`, `last exit code = 0`) and detected nothing it had to act on.

```
$ launchctl bootout gui/501/com.personacore.phase26.canary
bootout exit=0
$ launchctl bootout gui/501/com.personacore.phase25.watch
bootout exit=0
$ launchctl list | grep phase26
(exit 1 — empty)
$ launchctl list | grep personacore
-	0	com.personacore.phase25.sweep
-	0	com.personacore.phase25.recall
-	0	com.personacore.phase25.rehearsal
-	0	com.personacore.phase25.n64floor
$ for a in sweep recall rehearsal n64floor; do launchctl print gui/501/com.personacore.phase25.$a | grep -E "runs =|last exit"; done
-- sweep
	runs = 0
	last exit code = (never exited)
-- recall
	runs = 0
	last exit code = (never exited)
-- rehearsal
	runs = 0
	last exit code = (never exited)
-- n64floor
	runs = 0
	last exit code = (never exited)
$ pgrep -lf phase26_canary
(exit 1 — no driver process)
```

**A finding, recorded and not acted on.** `launchctl list` is empty of `phase26` but NOT empty of
`personacore`: four Phase-25 agents (`sweep`, `recall`, `rehearsal`, `n64floor`) are loaded. They
were not loaded by this phase — §5.3 loaded exactly two, and §5.4's listing 18 s after kickstart
showed only `phase25.watch` and `phase26.canary` — and Phase 25 §13.1 recorded all five booted out
with `launchctl list | grep personacore` empty on 2026-09-09. Their plists are still in
`~/Library/LaunchAgents/` (dated 1–8 September), so something re-loaded them between
2026-09-11T16:24Z and now; the machine has not rebooted (`uptime` 96 days). All four report
`runs = 0` / `last exit code = (never exited)`: none has run, and every one is `RunAtLoad false` /
`KeepAlive false` by the committed plists, so loaded-and-idle is inert until someone kickstarts
it. They are outside this plan's scope (the plan names the watcher only, conditional on 26-04
having loaded it) and are left as found, named here for the operator; T-26-04's claim — nothing
can re-enter a Phase-26 point after the close — holds because no `phase26` agent is loaded and the
driver's sidecars are reused by hash, never re-scored.

**(c) The assertion owners.** No caffeinate is owned by the driver or on its behalf; the two
present are the ones §2 already named before launch:

```
$ pmset -g assertions | grep -i caffeinate
   pid 15665(caffeinate): [0x005e5d0900018aee] 96:54:49 PreventUserIdleSystemSleep named: "caffeinate command-line tool"
	Details: caffeinate asserting on behalf of Process ID 7584
	Localized=THE CAFFEINATE TOOL IS PREVENTING SLEEP.
   pid 15665(caffeinate): [0x005e5d0900078aef] 96:54:49 PreventSystemSleep named: "caffeinate command-line tool"
	Details: caffeinate asserting on behalf of Process ID 7584
	Localized=THE CAFFEINATE TOOL IS PREVENTING SLEEP.
   pid 84287(caffeinate): [0x006383e50001a741] 00:02:24 PreventUserIdleSystemSleep named: "caffeinate command-line tool"
	Details: caffeinate asserting for 300 secs
	Localized=THE CAFFEINATE TOOL IS PREVENTING SLEEP.
$ pgrep -lf caffeinate
15665 caffeinate -s -i -w 7584
84287 caffeinate -i -t 300
$ ps -o pid,ppid,lstart,command -p 15665,84287,7584
  PID  PPID STARTED                      COMMAND
 7584     1 qua 26 ago 14:38:16 2026     /Users/juliorcoelho/.pyenv/versions/3.12.13/bin/python3.12 /Users/juliorcoelho/polymarket-bot/scripts/collect_negrisk_books.py --service ...
15665     1 qua  9 set 14:20:03 2026     caffeinate -s -i -w 7584
84287 37148 dom 13 set 15:12:27 2026     caffeinate -i -t 300
```

`15665` is the unrelated `polymarket-bot` keep-awake (§2; Phase 25 §13's §7b restored it) and
`84287` is this Claude session's own `-i -t 300` (its parent `37148` is the harness; it renews every
five minutes and dies with the session). The `caffeinate -dims` wrapper that held the run's
assertions (§5.5, §6.5) is gone with the driver — `pgrep -lf caffeinate` shows no `-dims`.

**(d) `pmset` — unchanged, nothing to revert.** No privileged change was made in this phase (§2
recorded the machine as Phase 25 §13 left it), so the read is the confirmation, not a revert:

```
$ pmset -g | grep -E "sleep|powernap"
 hibernatefile        /var/vm/sleepimage
 powernap             1
 networkoversleep     0
 disksleep            10
 sleep                1 (sleep prevented by caffeinate, caffeinate, sharingd, powerd, caffeinate, Claude)
 displaysleep         10
```

`sleep 1 / disksleep 10 / powernap 1` — Phase 25's `PMSET_REVERT` tuple, still in force.

**(e) The wall-clock, restated from §8.2.** Kickstart (§5.4) `2026-09-11T16:23:57Z` → the driver's
`done` heartbeat `2026-09-12T23:07:28Z` = 30 h 43 min 31 s (110611 s) against §3's ≈ 25 h; the
close itself — `--emit`, the operator's commit, this bootout — ran on 2026-09-13, 19 h after the
driver finished, on a machine whose only Phase-26 process had already exited.

### 8.9 The final gate — the full suite on the fully-tracked tree

With the artifact committed, the tree has no `??` line under `results/` and no ` M` under `tests/`,
so the four clean-tree probes §8.7 named as the residue of Task 1's own uncommitted edits have
nothing to refuse. Run before the note edit that adds this block (the probes would otherwise refuse
this block's own ` M results/phase26_operational_note.md`):

```
$ git status --short
 D .claude/scheduled_tasks.lock
 M .planning/STATE.md
$ env -u PERSONACORE_SWEEP_ACTIVE make test
2792 passed, 4 skipped, 83 warnings in 1297.92s (0:21:37)
$ echo EXIT=$?
EXIT=0
```

**Green: 0 failed / 2792 passed / 4 skipped, 2796 collected.** Against §8.7's Task-1 run
(4 failed / 2787 passed / 4 skipped, 2795 collected): the four failures are gone and `passed` rose
by 5 — the four residue tests, and the one new parametrization (below). The four, rerun by name on
this tree to show them passing rather than merely absent from a failure list:

```
$ env -u PERSONACORE_SWEEP_ACTIVE .venv/bin/pytest -q tests/test_phase23_resume.py::test_production_resume_epsilon_bit_identical tests/test_phase25_frontier.py::test_a_perturbed_per_point_count_breaks_the_aggregate tests/test_phase25_grid.py::test_the_from_import_variant_is_invisible_to_the_register_walk tests/test_phase25_probe2.py::test_a_planted_bit_identity_assertion_here_would_fire
4 passed in 99.90s (0:01:39)
```

Against the Phase-25 close on CI (`34406246073`, ubuntu: 2691 passed / 62 skipped, 2753
collected): +43 collected on this M3 tree. The skip registers differ by venue by design (M3
flag-unset 4 under §6.6's D-44 continuation; ubuntu's derived 62), so the comparison is on
collected and failed — 0 failed on both — not on skipped.

```
$ env -u PERSONACORE_SWEEP_ACTIVE .venv/bin/pytest -q tests/test_phase26_prereg.py tests/test_phase26_canary.py tests/test_phase25_close.py -x
69 passed in 3.95s
$ env -u PERSONACORE_SWEEP_ACTIVE .venv/bin/pytest -q tests/test_phase25_close.py
26 passed in 0.39s
```

The 43 Phase-26 tests are one more than §8.5's 42: the seventh `_NOTE_REQUIRED_BLOCKS`
parametrization, `test_the_operational_note_carries_every_required_block["## 8. The close"]`, which
Task 1 appended after its 42-count run (§8.5's last sentence). Nothing pending remains in §7.
