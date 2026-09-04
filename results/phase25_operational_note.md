# Phase 25 operational note — putting the machine into a state a 4.5–6.3 day run survives

**Dated 2026-09-01.** Authored at HEAD `4decedc`, on the author's M3 (the primary venue).
Every figure below is a **quoted command output**, not a paraphrase. Where a block has not been
measured yet it says so in §11 rather than carrying a plausible number.

The run this note prepares for is the 44-point v4.0 frontier sweep: **87.86–149.45 h**
(`results/phase25_adversarial_throughput.json`'s `schedule.total_hours_{floor,ceiling}`). The last
production run on this machine was killed externally at 60 minutes.

---

## 1. The before-state: `pmset -g`

Read live, read-only, **before** anything was changed. Verbatim:

```
$ pmset -g
System-wide power settings:
Currently in use:
 standby              1
 Sleep On Power Button 1
 hibernatefile        /var/vm/sleepimage
 powernap             1
 networkoversleep     0
 disksleep            10
 sleep                1 (sleep prevented by Claude, caffeinate, caffeinate, caffeinate, caffeinate, caffeinate, runningboardd)
 hibernatemode        3
 ttyskeepawake        1
 displaysleep         10
 tcpkeepalive         1
 lowpowermode         0
 womp                 1
```

**`sleep 1` / `disksleep 10` / `powernap 1`** — identical on all three fields to
`phase25_venue.PMSET_REVERT_TARGETS`, and therefore to the two prior readings recorded in
`PMSET_REVERT_TARGETS_PROVENANCE` (25-RESEARCH.md §R5 at HEAD `8dd6415`, and the 2026-08-31 re-read
at HEAD `2a76293`). **This is now the third independent agreeing reading.** The committed revert
restores the machine's real prior state and not a macOS default.

D-13's checkpoint condition — *if any value differs from `PMSET_REVERT_TARGETS`, STOP* — is
therefore **satisfied, not waived**: nothing differed.

`sleep 1` reads the same on AC and on battery. **System sleep after one minute of idle** is the
hazard both D-12 and D-13 exist against, and it is held off right now only by transient assertions
that belong to other processes.

### The after-state: `pmset -g` following `sudo pmset -a sleep 0 disksleep 0 powernap 0`

**MEASURED 2026-09-04, read-only.** The `sudo` act itself was performed by the operator between the
2026-09-01 before-state above and this reading; it left no transcript in this note, so what is
recorded is the state the machine was found in at the launch checkpoint, verbatim:

```
$ pmset -g
System-wide power settings:
Currently in use:
 standby              1
 Sleep On Power Button 1
 SleepServices        0
 hibernatefile        /var/vm/sleepimage
 powernap             0
 networkoversleep     0
 disksleep            0
 sleep                0 (sleep prevented by sharingd, caffeinate, mds_stores, powerd, Claude)
 hibernatemode        3
 ttyskeepawake        1
 displaysleep         10
 tcpkeepalive         1
 lowpowermode         0
 womp                 1
```

**`sleep 0` / `disksleep 0` / `powernap 0`** — `phase25_venue.PMSET_APPLY`'s target on all three
fields. `phase25_venue.read_power_settings()` returns `{'sleep': 0, 'disksleep': 0, 'powernap': 0}`
on the same text. The revert obligation of §7 is unchanged and now live: the machine is in the
applied state and plan 25-20 owes the revert to `1 / 10 / 1`.

---

## 2. The assertion owners, by owning process — and why `pmset -g`'s summary line was NOT used

`pgrep -x caffeinate`, verbatim:

```
$ pgrep -x caffeinate
7591
58309
91053
```

`pmset -g assertions`, owning-process section, verbatim:

```
$ pmset -g assertions
Listed by owning process:
   pid 70095(Claude): [0x004fc9e100019192] 70:19:19 NoIdleSleepAssertion named: "Electron"
   pid 7591(caffeinate): [0x004c3689000198ef] 135:46:09 PreventUserIdleSystemSleep named: "caffeinate command-line tool"
	Details: caffeinate asserting on behalf of Process ID 7584
   pid 7591(caffeinate): [0x004c3689000798f0] 135:46:09 PreventSystemSleep named: "caffeinate command-line tool"
	Details: caffeinate asserting on behalf of Process ID 7584
   pid 58309(caffeinate): [0x003d099e000197b8] 416:31:41 PreventUserIdleSystemSleep named: "caffeinate command-line tool"
	Details: caffeinate asserting forever
   pid 58309(caffeinate): [0x003d099e000797b9] 416:31:41 PreventSystemSleep named: "caffeinate command-line tool"
	Details: caffeinate asserting forever
   pid 58309(caffeinate): [0x003d099e000f97ba] 416:31:41 PreventDiskIdle named: "caffeinate command-line tool"
	Details: caffeinate asserting forever
   pid 91053(caffeinate): [0x00539a4700018e2a] 00:02:53 PreventUserIdleSystemSleep named: "caffeinate command-line tool"
	Details: caffeinate asserting for 300 secs
	Timeout will fire in 126 secs Action=TimeoutActionRelease
   pid 606(runningboardd): [0x00539af100018e93] 00:00:03 PreventUserIdleSystemSleep named: "app<application.net.whatsapp.WhatsApp...(FinishTask)"
Kernel Assertions: 0x104=USB,MAGICWAKE
```

Deduped owners: **`caffeinate` × 3 processes (7591, 58309, 91053), `Claude` (70095),
`runningboardd` (606).**

### The summary line was not used, and this reading strengthens the reason

D-43 as originally written says the run's own assertion is *"verified by reading `pmset -g` back
after launch"*. **It cannot be, and this reading gives three mutually inconsistent numbers where
the earlier readings gave two:**

| Source | Count of `caffeinate` |
|---|---|
| `pmset -g`'s `sleep prevented by ...` summary line | **5** |
| `pmset -g assertions`, rows in the owning-process section | **6** |
| `pgrep -x caffeinate`, actual processes | **3** |

The 5-vs-3 gap is the one already recorded twice (25-RESEARCH.md §R5, and 25-06's re-read); this is
its **third and fourth reproduction**. The 5-vs-6 gap is **new here** and it sharpens the
correction: the summary line does not even enumerate all *assertions*. Pid 58309 holds three, but
its `PreventDiskIdle` is not a sleep-preventing assertion, so the "sleep prevented by" list omits
it. A verification built on that line is counting a filtered subset of assertions and reporting
processes.

The transient pid churn is the other half of why a count is not a fact about processes. Across four
readings the third caffeinate pid was `46029` → `8264` → `75177` → `91053`, while `7591` and `58309`
persisted. `pid 91053` above is a 300-second self-releasing assertion with **126 seconds left to
live** at the moment of reading.

`phase25_venue.read_assertions()` parses only the `Listed by owning process:` section and returns
`(pid, process_name, assertion)` triples; handed the summary blob it returns **nothing**. The
corrected method is enforced by the parser, not described in a paragraph.

### Two findings about the residue that change what "clear the strays" means

**(a) One of the three strays is a launchd job, and `kill` will not clear it.**

```
$ launchctl list | grep -i personacore
58309	0	com.personacore.caffeinate

$ launchctl print gui/501/com.personacore.caffeinate
	path = (submitted by launchctl[58308])
	type = Submitted
	program = /usr/bin/caffeinate
	arguments = { /usr/bin/caffeinate, -ims }
	pid = 58309
	runs = 1
```

`pid 58309` has been asserting **forever** for `416:31:41` — over 17 days — and it is `ppid 1`,
owned by launchd under the label `com.personacore.caffeinate`. **No plist for it exists in
`~/Library/LaunchAgents` and none exists in this repository**; it was created with
`launchctl submit` in some earlier session and outlived it. It must be **booted out**, not killed:
a `kill` on a launchd-managed job is at best a restart and at worst a no-op that looks like success.

This is D-43's exact hazard, realised: a stray from an earlier session that holds
`PreventUserIdleSystemSleep`, `PreventSystemSleep` **and** `PreventDiskIdle` — nearly the same set
`caffeinate -dims` takes — so a sweep launched today would appear protected while this 17-day-old
process is what genuinely holds the machine awake, and would sleep the moment it went away.

**(b) The other persistent stray is 23-20's superseded recipe, still running.**

```
$ ps -o pid,ppid,command -p 7591,58309,91053
  PID  PPID COMMAND
 7591  7584 /usr/bin/caffeinate -s -i -w 7584
58309     1 /usr/bin/caffeinate -ims
91053 12569 caffeinate -i -t 300
```

`pid 7591` is literally `caffeinate -is -w <pid>` — the watching form D-12 supersedes — asserting
*on behalf of* pid 7584, a process it does not own. See §9.

### Post-clearing `pgrep -x caffeinate`, and the post-launch owner list

**MEASURED 2026-09-04.** The three strays of the 2026-09-01 reading are gone. The 17-day launchd
job is no longer registered, and the `-is -w 7584` watcher is gone although pid 7584 (an
unrelated collector) still runs:

```
$ launchctl print gui/501/com.personacore.caffeinate
Bad request.
Could not find service "com.personacore.caffeinate" in domain for user gui: 501

$ launchctl list | grep personacore
-	0	com.personacore.phase25.sweep
-	0	com.personacore.phase25.watch
-	0	com.personacore.phase25.rehearsal

$ pgrep -lf caffeinate
9760 caffeinate -i -t 300

$ ps -o pid,ppid,pgid,sess,command -p 9760
  PID  PPID  PGID   SESS COMMAND
 9760 95011 95011      0 caffeinate -i -t 300

$ ps -o pid,ppid,command -p 95011
  PID  PPID COMMAND
95011 83894 claude
```

**The one caffeinate present is the operator's console, not residue of an earlier session.** Its
parent is the `claude` process of the very Claude Code session performing this checkpoint; it is a
300-second self-releasing assertion re-created around each of that session's tool calls (the pid
read `96140`, then `9760`, then `22820`, then `58765` across four readings in one hour, always
`-i -t 300`). It cannot outlive the session by more than 300 s, and `prove_only_our_caffeinate`
correctly REFUSES on it (quoted in §12), which is the function doing its job: a clean read-back has
to come from a process that is not the console, and §12 records that read.

The post-launch owner list, by owning process, with the D-03 floor agent live (the sweep agent's
own is in §12):

```
$ pmset -g assertions
Listed by owning process:
   pid 58765(caffeinate): [0x0057dcee000184ba] 00:01:00 PreventUserIdleSystemSleep named: "caffeinate command-line tool"
	Details: caffeinate asserting for 300 secs
   pid 59155(caffeinate): [0x0057dd12000184c5] 00:00:25 PreventUserIdleSystemSleep named: "caffeinate command-line tool"
	Details: caffeinate asserting on behalf of '/Users/juliorcoelho/PersonaCore/.venv/bin/python' (pid 59153)
   pid 59155(caffeinate): [0x0057dd12000584c6] 00:00:25 PreventUserIdleDisplaySleep named: "caffeinate command-line tool"
	Details: caffeinate asserting on behalf of '/Users/juliorcoelho/PersonaCore/.venv/bin/python' (pid 59153)
   pid 59155(caffeinate): [0x0057dd12000784c7] 00:00:25 PreventSystemSleep named: "caffeinate command-line tool"
	Details: caffeinate asserting on behalf of '/Users/juliorcoelho/PersonaCore/.venv/bin/python' (pid 59153)
   pid 59155(caffeinate): [0x0057dd12000f84c8] 00:00:25 PreventDiskIdle named: "caffeinate command-line tool"
	Details: caffeinate asserting on behalf of '/Users/juliorcoelho/PersonaCore/.venv/bin/python' (pid 59153)
Kernel Assertions: 0x104=USB,MAGICWAKE
```

The agent's own wrapper (`59155`) holds all four of `-d`, `-i`, `-m`, `-s` **on behalf of** the
driver pid `59153` — the phrase that names the relation §9's correction records. System owners at
this reading, named for `expected_owners=` rather than tolerated: `sharingd`, `mds_stores`,
`powerd`, `WindowServer`, `Claude` (the operator's desktop app, 48 h idle-sleep assertion).

---

## 3. Disk headroom against `DISK_PRECHECK_BYTES`

```
$ .venv/bin/python -c "import sys;sys.path.insert(0,'scripts');import phase25_venue as v;print(v.prove_disk_headroom())"
{'path': '/Users/juliorcoelho/PersonaCore', 'free_bytes': 504557801472, 'total_bytes': 994662584320,
 'required_bytes': 5000000000, 'headroom_bytes': 499557801472, 'adapter_term_bytes': 59491036,
 'resume_checkpoint_term_bytes': 2626430532, 'retention_bytes': 2685921568}
```

**504,557,801,472 free bytes against a required 5,000,000,000** — 100× headroom.

The two retention terms are shown **separately, because the second one is the correction**:

| Term | Per point | × 44 points |
|---|---|---|
| Exported LoRA adapter | 1,352,069 B | **59,491,036 B** |
| `checkpoints/{prefix}_{arm}_latest.pt` resume checkpoint | 59,691,603 B | **2,626,430,532 B** |
| Total retention | 61,043,672 B | **2,685,921,568 B ≈ 2.7 GB** |

D-37 sizes the sweep's retention at *44 adapters × 1.35 MB ≈ 59 MB*. That is right about the
adapter and wrong about the point: `teach_persona.arm_outputs` also names a resume checkpoint per
point, and that checkpoint is what makes a killed point resumable at all. **The omitted term is 42×
the one D-37 counted.** `phase25_prereg.DISK_PRECHECK_BYTES` is pinned at 5 GB — both terms plus
headroom for the draw caches and per-point records that land beside them.

---

## 4. The launch identity, read before any GPU second

The relation below was stated in advance so it could not be chosen after seeing the output — and it
was **measured false** on 2026-09-04 at the first live reading. The original stands as written; the
measured relation and the correction follow it (§9).

```
driver.pgid == driver.sid == wrapper.pid == driver.ppid          # SUPERSEDED 2026-09-04
and wrapper.pid ∈ pgrep -x caffeinate
and wrapper.pid holds assertions in `pmset -g assertions`
```

**MEASURED 2026-09-04 against the D-03 floor agent (`com.personacore.phase25.n64floor`), read
BEFORE its first GPU second had produced a reading.** The banner from the log, the process table,
and `launch_identity()` after the correction, verbatim:

```
$ head -1 logs/phase25_n64_floor.out
[phase25_launch] pid=59153 ppid=1 pgid=59153 sid=1

$ ps -o pid,ppid,pgid,sess,command -p 59153,59155
  PID  PPID  PGID   SESS COMMAND
59153     1 59153      0 /opt/homebrew/Cellar/python@3.11/3.11.15_1/Frameworks/Python.framework/Versions/3.11/Resources/Python.app/Contents/MacOS/Python /Users/juliorcoelho/PersonaCore/scripts/phase25_n64_floor.py
59155 59153 59153      0 /usr/bin/caffeinate -dims /Users/juliorcoelho/PersonaCore/.venv/bin/python /Users/juliorcoelho/PersonaCore/scripts/phase25_n64_floor.py

$ .venv/bin/python -c "import sys,json;sys.path.insert(0,'scripts');import phase25_venue as v;print(json.dumps(v.launch_identity('logs/phase25_n64_floor.out'), indent=1))"
{
 "log": "logs/phase25_n64_floor.out",
 "driver_pid": 59153,
 "driver_ppid": 1,
 "driver_pgid": 59153,
 "driver_sid": 1,
 "wrapper_pid": 59155,
 "wrapper_ppid": 59153,
 "wrapper_pgid": 59153,
 "wrapper_assertions": ["PreventDiskIdle", "PreventSystemSleep", "PreventUserIdleDisplaySleep", "PreventUserIdleSystemSleep"],
 "wrapper_is_a_caffeinate_process": true,
 "wrapper_is_the_drivers_child": true,
 "same_group_as_wrapper": true,
 "driver_leads_its_group": true,
 "driver_parent_is_launchd": true,
 "wrapper_holds_an_assertion": true
}
```

The measured relation, now `phase25_venue.LAUNCH_IDENTITY_PROVENANCE["measured_relation"]`:

```
wrapper.ppid == driver.pid
and wrapper.pgid == driver.pgid == driver.pid
and wrapper ∈ pgrep -x caffeinate, holding its assertions "on behalf of" driver.pid
and driver.ppid == 1 (launchd)
```

Before the correction, `launch_identity()` read the wrapper off the banner's `ppid` — launchd — and
returned `wrapper_pid: 1, wrapper_assertions: [], wrapper_holds_an_assertion: false` while
hard-coding `wrapper_is_the_parent: true`. It would have reported a protected run as unprotected
(or, read the other way, would have asserted a parent that does not exist). The 2026-09-01
rehearsal banners in `logs/phase25_rehearsal.out` — `pid=59902 ppid=1 pgid=59902 sid=1` and three
more of the same shape — already carried this fact; nobody read the `ppid=1`.

### The sweep agent's own reading — MEASURED 2026-09-04 20:09 UTC

Read 20 s after `launchctl kickstart`, before the first point's training had produced anything:

```
$ head -1 logs/phase25_sweep.out
[phase25_launch] pid=16902 ppid=1 pgid=16902 sid=1

$ launch_identity('logs/phase25_sweep.out')     # abridged: the relation string is §4's
 "driver_pid": 16902, "driver_ppid": 1, "driver_pgid": 16902, "driver_sid": 1,
 "wrapper_pid": 16904, "wrapper_ppid": 16902, "wrapper_pgid": 16902,
 "wrapper_assertions": ["PreventDiskIdle", "PreventSystemSleep", "PreventUserIdleDisplaySleep", "PreventUserIdleSystemSleep"],
 "wrapper_is_a_caffeinate_process": true, "wrapper_is_the_drivers_child": true,
 "same_group_as_wrapper": true, "driver_leads_its_group": true, "driver_parent_is_launchd": true,
 "wrapper_holds_an_assertion": true
```

Same shape as the D-03 agent's, every boolean true. The full transcript is §12.

The pid comes **from the log** and never from `launchctl print` (which reports the *wrapper's* pid
under `-dims`) and never from a shell's `$!` (which does not exist for a LaunchAgent at all).
`phase25_run.main()` emits `phase25_venue.launch_banner()` flushed as its first output; only the
process itself knows its own pid.

---

## 5. The stall record, and that no action was taken — MEASURED 2026-09-01, D-16 CONFIRMED

D-16's detect-never-act contract had **never been observed live**. Its detect half was unit-tested;
its *never-act* half was enforced by an AST walk over `scripts/phase25_watch.py`
(`FORBIDDEN_ACTIONS` = `kill, terminate, Popen, run, launchctl, unlink, rmtree, remove`), which
proves the **module** contains no action — not that launchd, the plist and the watcher together
take none. That gap is now closed by observation.

`artifacts/com.personacore.phase25.rehearsal.plist` exists to make it possible: it runs the
production heartbeat thread for a bounded interval and then **exits on purpose**, so the beat goes
stale on a schedule and the watcher can be watched firing without anything being killed. It fired
twice — once on the bounded expiry it was built for, and once on the logout kill of §6, which was
not planned and is the more informative of the two.

Read at **14:28:56**, with the second episode still running:

```
$ wc -l < data/phase25_stall.jsonl
      71
$ grep -c '"action_taken": "none"' data/phase25_stall.jsonl
71
$ grep -c STALL logs/phase25_watch.out
71
```

**71 detections, `action_taken: "none"` in 71 of 71.** First and last record:

```
$ head -1 data/phase25_stall.jsonl   # detected_utc, silence_minutes, threshold
2026-09-01T15:25:46.218121+00:00   5.108524266666667   5
$ tail -1 data/phase25_stall.jsonl   # detected_utc, silence_minutes, last_beat
2026-09-01T17:27:57.606746+00:00   63.20029924999999   2026-09-01T16:24:45.588791+00:00
```

It detected at **5.11 minutes past a 5-minute threshold** — one sampling period, exactly the
worst-case latency the 60 s `StartInterval` was chosen for — and it was still reporting the same
silence **63.20 minutes** later without escalating, retrying or changing behaviour. Every record
carries the reason in full rather than as a flag:

```
"action_taken_reason": "D-16: heartbeat silence is DETECTED, never ACTED ON. An automatic restart
would re-enter a sweep point WITHOUT passing the driver's deliberate resume logic, making a
supervisor — not a person — the thing that violates D-10's one-attempt rule. […] Correcting a stall
is a human act, taken after reading this record."
```

**The never-act half is proved by what is still standing**, not by the watcher's own testimony:

| Would have happened under an acting supervisor | Actual reading |
|---|---|
| the stalled agent relaunched | `rehearsal` reads `runs = 0`, `state = not running` (§6) — nothing restarted it |
| the stale heartbeat cleaned up or rotated | `wc -l < data/phase25_heartbeat.jsonl` → `39`; the last beat is intact and is still the one all 71 records cite |
| the process killed | the watcher does not import `subprocess` at all (threat T-25-21) |

The stall file only ever grew. **This is the one rehearsal outcome that is better for having been
unplanned:** the second episode was caused by a real kill of a real agent, not by the bounded exit
the plist was designed to produce, and the watcher treated the two identically.

---

## 6. The session boundary — MEASURED 2026-09-01, and D-12's scope is narrower than D-12 states

**Named before launch, not discovered mid-run.** This is D-49's discipline applied to the venue:
the limitation is written down while it can still change the operating plan, rather than
reconstructed afterwards from a dead run.

### D-12, corrected scope

A `gui/<uid>` LaunchAgent **does not survive an explicit logout of the graphical session.** The
whole launchd domain is destroyed at logout and a **new** one is created at the next login. The
plists are re-bootstrapped into the new domain — `launchctl list` still shows all three jobs — but
the processes are gone and the per-job counters start again from zero. Re-bootstrapping is not
resumption: `KeepAlive` is false by design (D-10; §10 R4), so nothing restarts itself.

| | |
|---|---|
| **Verified and covered** — 23-17's original scope | system sleep, disk sleep, closing the terminal, ending the SSH session |
| **Follows structurally, not separately measured** | harness compaction and Claude-session end — the agent is `ppid 1` and has no parent in the harness, which is a plist-level fact rather than an observation |
| **NOT covered** | manual or forced logout of the account (and, a fortiori, restart and shutdown) |

`25-14-PLAN.md`'s D-12 line — *"It survives session end, compaction and logout"* — **stands as
written**; this is a dated correction to its scope, not an edit of it. The clause that is false is
`and logout`. Everything else D-12 claims held.

### The observation, verbatim

The boundary was a real logout from the Apple menu followed by a real login. The machine was **not**
rebooted, which is what makes the domain loss attributable to the logout alone:

```
$ sysctl -n kern.boottime
{ sec = 1780966300, usec = 950491 } Mon Jun  8 21:51:40 2026
```

The rehearsal agent was live and beating when the logout happened — its last beat and
`loginwindow`'s restart share the same second (16:24:45 UTC is 13:24:45 −0300):

```
$ tail -1 data/phase25_heartbeat.jsonl
{"draw_index": null, "point": "rehearsal", "shape": null, "stage": "start", "utc": "2026-09-01T16:24:45.588791+00:00"}

$ ps -p $(pgrep -x loginwindow | head -1) -o pid=,lstart=
78738 ter  1 set 13:24:45 2026

$ who | grep console
juliorcoelho     console       1 set 13:41
```

Read back at **14:12, fifty minutes past the boundary**:

```
$ for j in sweep watch rehearsal; do printf "%s: " "$j"; launchctl print gui/501/com.personacore.phase25.$j | grep -E "^\s+(runs|state) ="; done
sweep:      state = not running   runs = 0
watch:      state = not running   runs = 31
rehearsal:  state = not running   runs = 0

$ launchctl print gui/501/com.personacore.phase25.rehearsal | grep -E "runs|last exit"
	runs = 0
	last exit code = (never exited)
```

**`runs = 0` is the whole proof, and it needs no before-reading to be conclusive.** That job's own
stdout log holds four completed launch banners from this boot:

```
$ grep -c '^\[phase25_launch\]' logs/phase25_rehearsal.out
4
```

A counter reading 0 for a job that has demonstrably run four times since 8 June is not the counter
that counted them: the domain those four runs lived in no longer exists. `watch` corroborates from
the other side — its `StartInterval` is 60 s, so `runs = 31` at 14:12 dates its domain to ≈13:41,
the **login**, not the boot 85 days earlier.

And §11's row 6, the measurement this section owed — the two `logs/phase25_rehearsal.out` sizes
across a real logout/login:

```
$ stat -f '%N size=%z mtime=%Sm' -t '%F %T' logs/phase25_rehearsal.out
logs/phase25_rehearsal.out size=748 mtime=2026-09-01 13:22:45
```

**748 bytes before, 748 bytes after, mtime unmoved at 13:22:45** — the last write predates the
13:24:45 logout and nothing was written in the fifty minutes after the login. The agent did not
resume; it was re-bootstrapped and left not running.

The operator also read a **new `asid` and a new launchd socket** across the boundary. That is
recorded as the operator's direct reading rather than as a quoted before/after pair, because the
pre-logout values were not captured; the current domain's are `asid = 123933` and
`SSH_AUTH_SOCK => /var/run/com.apple.launchd.7BAjbFHX6e/Listeners`.

### Corollary — a killed agent loses its unflushed stdout

Run 4's banner has no `rehearsing the beat` line after it, while runs 1–3 have one. The cause is in
the source, not in launchd:

```
$ sed -n '699,700p' scripts/phase25_venue.py
        print(launch_banner(), flush=True)
        print(f"[phase25_venue] rehearsing the beat for {args.seconds}s -> {args.heartbeat}")
```

Line 699 flushes, line 700 does not. Runs 1–3 exited cleanly and Python flushed at exit; run 4 was
killed and its block-buffered line was discarded. **This is not rehearsal-only:**

```
$ grep -n "print(" scripts/phase25_run.py | grep -vc "flush=True"
4
$ grep -l PYTHONUNBUFFERED ~/Library/LaunchAgents/com.personacore.phase25.*.plist | wc -l   # 14:19
       0
```

Four of the driver's five `print(` sites are unflushed, and at 14:19 no plist set
`PYTHONUNBUFFERED`. Over a 4.5–6.3 day unattended run whose only diagnostics are these files, an
abrupt kill therefore loses the last block of driver output — including whatever it was doing when
it died.

**FIXED, not left as a named residual.** `<key>PYTHONUNBUFFERED</key><string>1</string>` now sits in
all three agents' existing `EnvironmentVariables` dict, in the committed artifacts and in the loaded
jobs:

```
$ for b in rehearsal sweep watch; do plutil -extract EnvironmentVariables.PYTHONUNBUFFERED raw artifacts/com.personacore.phase25.$b.plist; done
1
1
1
$ for b in sweep watch rehearsal; do launchctl print gui/501/com.personacore.phase25.$b | grep PYTHONUNBUFFERED; done
		PYTHONUNBUFFERED => 1
		PYTHONUNBUFFERED => 1
		PYTHONUNBUFFERED => 1
```

`launchctl print` is the verification that matters, because editing a plist is not loading one: the
value has to appear in the **resolved** environment of the job as launchd holds it, not merely in
the file. `plutil -lint` passes on all three, and `tests/test_phase25_launch.py` — which reads the
committed artifacts, never the installed copies — stays green.

**One divergence is named rather than repaired.** The installed copies under
`~/Library/LaunchAgents/` were rewritten at 14:24:57 outside this repository and came back
**normalized**: every explanatory comment stripped, keys re-sorted, and the rehearsal agent's
`--seconds` reading `3600` against the committed `300`. The committed artifacts remain the source of
truth and are what the tests assert against. Reinstalling from them would restore the comments but
would also silently revert that `3600` — an operator setting — so it is **not** done here.

### The mitigations, and exactly how far each one goes

**(1) Operational discipline — no logout for the 4.5–6.3 days of the run.** The only mitigation that
addresses the named limitation directly, and it is a *human commitment, not a control*: nothing on
the machine enforces it. Screen lock, closing the lid, sleep, quitting the terminal and dropping SSH
are all inside the covered scope. Only "Log Out" and its forced variants are not.

**(2) Automatic macOS update install and download are OFF**, removing the most likely
*unintentional* restart trigger. Read live from the system domain:

```
$ defaults read /Library/Preferences/com.apple.SoftwareUpdate
    AutomaticDownload = 0;
    AutomaticallyInstallMacOSUpdates = 0;
    CriticalUpdateInstall = 0;
    ConfigDataInstall = 1;
```

`ConfigDataInstall = 1` is left on deliberately — XProtect/config-data updates do not restart the
machine. Two neighbouring keys in the same domain are named rather than glossed:

```
    AutoInstallProductKeys = ( "MSU_UPDATE_25F71_patch_26.5_major" );
    DDMPersistedErrorKey = { count = 299; reason = "Software update failed."; timestamp = "2026-09-01T13:06:48-03:00"; };
```

A stale auto-install product key for **26.5** is still listed while the pending update is **26.6.2**,
and a declarative-management update has failed **299 times**, most recently 13:06 today. Neither
should fire with all three flags at 0 — but they are evidence that something on this machine keeps
*trying* to install, so those flags are the thing holding it off and they must not be flipped back
mid-run.

**(3) Three updates are detected, pending, and deliberately not installed** until the run ends:

```
$ defaults read /Library/Preferences/com.apple.SoftwareUpdate LastRecommendedUpdatesAvailable
3
$ defaults read /Library/Preferences/com.apple.SoftwareUpdate RecommendedUpdates
  "Command Line Tools for Xcode 26.6"   Product Key 140-17812
  "Command Line Tools for Xcode 26.5"   Product Key 047-91568
  "macOS Tahoe 26.6.2"                  MSU_UPDATE_25G83_patch_26.6.2_minor, MobileSoftwareUpdate = 1
```

Only the third restarts the machine. Installing any of them during the run ends the run.

### 6b. A THIRD obligation — target state DECLARED 2026-09-01

Flipping those three flags to 0 is a persistent, system-wide change to the author's own machine, in
the same class as `PMSET_APPLY`, so it carries a revert obligation of the same kind as §7 and §7b.

**Its provenance is weaker than §7's, and that is stated rather than smoothed over.** §7's three
`pmset` numbers are a *measured* prior state — three independent agreeing live readings. These three
are not: no `defaults read` of this domain was captured before the change, `defaults` keeps no
history, and a search of every session transcript for this project (54 files) finds the key
`AutomaticallyInstallMacOSUpdates` in one file only — this session's — where every reading is
post-change and reads `0`. **There is no command output to quote here, and none is invented.**

What closes the gap is the thing this section asked for in the first place: an explicit operator
declaration, made on 2026-09-01 and recorded **before** the run rather than reconstructed after it.

| | |
|---|---|
| Owner | **plan 25-20**, in the same step as `PMSET_REVERT` and §7b's collector keep-awake |
| Target state — **operator-declared** | `AutomaticDownload` = **true**, `AutomaticallyInstallMacOSUpdates` = **true**, `CriticalUpdateInstall` = **true** |
| Provenance | operator declaration, 2026-09-01 — **not** a measured pre-change reading, and **not** a macOS default |
| Untouched | `ConfigDataInstall`, at `1` throughout, is not part of the revert |
| The revert argv | `sudo defaults write /Library/Preferences/com.apple.SoftwareUpdate <key> -bool true`, once per key |
| Verified by | a `defaults read` of the domain after the write, quoted here the way §7's `prove_reverted()` output is |
| Also at revert time | the three updates of §6(3) stop being deliberately deferred — installing them becomes a normal operator decision again |

The distinction worth keeping: **§7's target can be checked against the machine's own history and
this one cannot.** If the declaration is wrong, nothing in this repository will catch it. That is the
residual — and it is smaller than the state this section was in before the declaration, which was an
obligation with no target at all.

---

### 6c. The three flags, re-read 2026-09-04 before launch

```
$ defaults read /Library/Preferences/com.apple.SoftwareUpdate
    AutomaticDownload = 0;
    AutomaticallyInstallMacOSUpdates = 0;
    ConfigDataInstall = 1;
    CriticalUpdateInstall = 0;
```

Unchanged since §6b's declaration: the three revert-bearing flags are still `0`, `ConfigDataInstall`
still `1`. Nothing was written.

---

## 7. The revert obligation — committed, with its verifier named

`sudo pmset -a sleep 0 disksleep 0 powernap 0` is a privileged, system-wide, indefinite change to
the author's own machine. **Its revert does not depend on anyone remembering it.**

| | |
|---|---|
| The revert argv | `phase25_venue.PMSET_REVERT` = `sudo pmset -a sleep 1 disksleep 10 powernap 1` |
| The target state | `phase25_venue.PMSET_REVERT_TARGETS` = `{'sleep': 1, 'disksleep': 10, 'powernap': 1}` |
| Where the targets came from | measured, three agreeing live readings — never a macOS default |
| Who executes it | **plan 25-20**, as a committed plan step |
| Who verifies it | `phase25_venue.prove_reverted()`, which raises `SystemExit` naming **all three** fields with their observed and required values |
| Who may invoke it from code | **nobody.** `tests/test_phase25_venue.py::test_this_module_never_invokes_the_privileged_commands` walks the module's AST and refuses any `subprocess` call site carrying the elevation word or either committed tuple |

A revert to macOS's shipped defaults would be a second unrequested system change wearing the word
"revert". These three numbers are what was actually there.

### 7b. A SECOND revert obligation, incurred 2026-09-01 — restore the polymarket-bot keep-awake

Clearing the strays before launch removed **two** assertion holders, and only one of them was
Phase-25 residue.

| | |
|---|---|
| `com.personacore.caffeinate` (pid 58309) | a `launchctl submit` job, `ppid 1`, `caffeinate -ims`, asserting continuously since 2026-08-14 (~17 days) with **no plist on disk and none in this repo**. Booted out. **Nothing to restore** — it is unowned cruft and it is exactly what D-43's masking hazard looks like. |
| pid 7591 — `caffeinate -s -i -w 7584` | **NOT Phase-23 residue.** Its watched pid 7584 was and remains **LIVE**: `collect_negrisk_books.py --service --interval 900`, an unrelated polymarket-bot collector. This was a legitimate active keep-awake for another project and it was killed on a misreading. |

**Obligation:** restore the polymarket-bot keep-awake as part of plan 25-20's revert step, executed
together with `PMSET_REVERT` and verified in the same breath as `prove_reverted()`.

```bash
# 25-20, immediately after PMSET_REVERT restores sleep 1 / disksleep 10 / powernap 1:
PMPID=$(pgrep -f 'collect_negrisk_books.py --service')   # re-resolve; 7584 may have been restarted
[ -n "$PMPID" ] && nohup caffeinate -s -i -w "$PMPID" >/dev/null 2>&1 &
pmset -g assertions | sed -n '/Listed by owning process:/,/Kernel Assertions:/p' | grep caffeinate
```

Deferred deliberately, not forgotten: while the sweep runs, `pmset -a sleep 0` holds the machine
awake system-wide, so the collector is protected **redundantly** and the assertion would only add a
non-Phase-25 owner that §2's "the sweep holds its OWN assertion" read-back must then explain away.
The protection lapses at the moment `PMSET_REVERT` lands, which is why the restore belongs in the
same step and not later. Operator decision, 2026-09-01.

Do NOT restore the 58309 job. Re-resolve the collector's pid at revert time rather than reusing
`7584` — a service restarted during a 4.5-6.3 day run will carry a different pid, and
`caffeinate -w` against a dead pid exits immediately and silently, which would look like success.

---

## 8. §O1 — the driver's git surface, restated here because the plist is what makes it resolve

`phase25_prereg.GIT_SURFACE_EXCEPTION` records the decision in full. Restated at the scope that
matters operationally:

- The driver's executable git surface is **`{add, commit}`**, over **one path**: the resolved
  `results/phase25_point_<key>.json`, refused unless it is under `results/` and already exists. No
  glob, no `-A`, no `.`, no `shell=True`. Proved by AST in
  `tests/test_phase25_driver.py`, watched failing on a planted `git push`.
- **This phase only.** Phase 23's read-only-git discipline is abandoned deliberately: D-12's run has
  no operator at the process boundary 44 times, D-10's `prove_first_attempt` reads **tracked**
  records so an uncommitted record is invisible to the one-attempt rule, and D-31's assembly calls
  `refuse_if_dirty` over `results/`.
- **`config.json` sets `branching_strategy: none`, so those 44 commits land on `main`.** Named here
  rather than discovered.
- The plists' `WorkingDirectory` is `/Users/juliorcoelho/PersonaCore`, the repository root, which is
  what makes the relative point-record path resolve at all.
  `tests/test_phase25_launch.py::test_the_working_directory_is_the_repo_root` asserts every
  repo path in all three plists is anchored on it.

### The minimal environment was checked, because §O1 runs inside it

launchd hands an agent a minimal environment, and the sweep's 44 commits are made by a process that
never sees the operator's shell. Both halves were verified read-only under exactly the `PATH` the
plists declare:

```
$ env -i PATH=/usr/bin:/bin:/usr/sbin:/sbin HOME=$HOME /usr/bin/git -C /Users/juliorcoelho/PersonaCore var GIT_COMMITTER_IDENT
Rafael <rafael.d.cooelho@gmail.com> 1788255173 -0300

$ env -i PATH=/usr/bin:/bin:/usr/sbin:/sbin HOME=$HOME /usr/bin/git -C /Users/juliorcoelho/PersonaCore ls-files 'results/phase25_point_*.json' | wc -l
       0
```

`git` resolves at `/usr/bin/git`, the commit identity resolves from `$HOME`, and D-10's
`prove_first_attempt` read returns the same empty list it returns from a shell. A missing identity
would have failed the **commit** — step 7 of `run_point`, after the point's whole GPU cost had
already been spent.

---

## 9. The deliberate change from 23-20 — a wrap, not a watch

`.planning/STATE.md` records the 23-20 launch discipline: `os.setsid()` + `os.execv`, the pid read
**from the log** and never from `$!`, probed with `os.getsid()`, and `pid == pgid == sid` quoted
**before any GPU second**. It held across six real launches. D-12 is an **escalation** of it, and
the two differences are named rather than glossed.

**What changed.** `caffeinate -is -w <pid>` **watches** a process it does not own and releases when
that pid exits. `caffeinate -dims <utility>` **wraps**: it runs the utility as its child and holds
its **own** display (`d`), idle (`i`), disk (`m`) and system (`s`) assertions for the child's
lifetime. The watching form leaves a window in which the wake claim belongs to a pid the sweep does
not control — §2(b) above shows exactly that form still running on this machine 135 hours later,
asserting on behalf of pid 7584.

**What that costs, stated plainly: the equal triple is no longer the driver's.** Under 23-20 the
launcher called `os.setsid()` and then `os.execv`'d *itself* into the driver, so the driver **was**
the session leader and `pid == pgid == sid` was a true statement about it. Under the wrapping form
launchd makes `caffeinate` the leader and the driver inherits its group and session, so the
driver's own `pid == pgid == sid` is **structurally false** — a checkpoint asserting it would be
asserting a defect. The relation in §4 replaces it, and it says three things the old triple did not:
the assertion holder is the driver's **own parent**, it leads the group and session the driver lives
in, and the driver therefore cannot outlive the wake claim protecting it.

**What did not change.** The pid still comes from the log, and it is still probed rather than
trusted.

**CORRECTION, 2026-09-04 — the parent/child direction above is inverted, and it was measured, not
reasoned.** `caffeinate -dims <utility>` does not run the utility as its child. It **forks**: the
**parent** execs the utility, keeping the pid launchd started (`driver.ppid == 1`, `driver.pgid ==
driver.pid`), and the **child** is the `caffeinate` that holds the four assertions *on behalf of*
its parent for the parent's lifetime (`wrapper.ppid == driver.pid`, `wrapper.pgid == driver.pgid`).
§4 quotes the `ps` table and the assertion rows that say so. The three claims of the paragraph
above survive with the roles swapped: the assertion holder is the driver's own **child**, not a
stray; it lives in the group the driver **leads**; and it releases when the driver exits. What does
not survive is `pid == pgid == sid` being false OF THE DRIVER — the driver does lead its group, and
`sid` is launchd's session, not the wrapper's. `launch_identity()` was corrected the same day
(`read_process_parents`, the wrapper found by `ppid == driver.pid`, a driver with no caffeinate
child refused as UNWRAPPED); the superseded relation text is left standing in
`LAUNCH_IDENTITY_PROVENANCE["the_relation_that_replaces_it"]` beside `measured_relation`.

---

## 10. Open risks before the sweep starts

**R1 — the live draw loop has never executed, and it is the largest operational risk in the phase.**
Plan 25-11 found `scripts/phase25_run.py::_draw_one_shape` calling `tp.device()`, a method that does
not exist. That defect would have raised on the **first draw of the first point, after up to 23
minutes of that point's training had already been spent**. It survived plan 25-10's 23 passing
driver tests because **every committed driver test takes the `--dry-run` branch**. It is fixed
(`6df1eba`, which added `phase25_run.device()`), but **no test reaches the live draw loop**, so the
class of defect is not closed — only that instance is. Starting an 87.86–149.45 h unattended sweep
with that gap open is the single largest operational risk in this phase, and it is a *coverage* gap,
not a bug: a first-point smoke run that actually trains and draws is the only thing that closes it.

**R2 — a 17-day-old launchd-managed `caffeinate` is currently masking the mechanism.** §2(a). Until
`com.personacore.caffeinate` is booted out, no post-launch assertion read-back can distinguish "the
sweep holds its own assertion" from "something else has held one since 15 August".

**R2 — CLOSED 2026-09-04.** `com.personacore.caffeinate` is no longer registered and `pgrep -x
caffeinate` names only the console's own 300 s assertion (§2). The read-back can now distinguish.

**R3 — the system assertion-owner set has now been measured four times and disagreed four times.**
`dasd` (research reading) → `powerd` + `WindowServer` (25-06) → `Claude` (recurring) →
`runningboardd` (this reading, a WhatsApp background task). `phase25_venue.SYSTEM_ASSERTION_OWNERS`
is deliberately **not** widened to cover them: an allow-list that grows on every new observation
converges on tolerating everything, which is the failure D-43 exists to prevent. The launch-time act
is to read the owners, name them in this note, and pass them through `expected_owners=` **for that
launch only**.

**R4 — `KeepAlive` false means a crashed sweep looks exactly like a finished one.** That is the
design (an automatic restart would re-enter a point outside the driver's deliberate resume logic and
violate D-10), and the stall watcher is the compensating control. It is also why §5's live
observation matters more than it looks.

**R5a — the `caffeinate -dims` wrapper leg is now EXERCISED.** The D-03 floor agent runs the
identical wrapper and §4 shows it holding all four assertions on the driver's behalf. What the
exercise found is §9's correction: the wrapper is the driver's child, and `launch_identity()` had
to be fixed before it could read the run as protected.

**R5 — an unintended logout or restart ends the run silently, and D-12 does not protect against it.**
Measured, not assumed: §6. The launchd domain is destroyed at logout and the agents come back
re-bootstrapped but not running, with `runs = 0` — indistinguishable at a glance from a clean
finish, which is R4's ambiguity arriving by a second route. The mitigations are one human
commitment (no logout for 4.5–6.3 days) and three `SoftwareUpdate` flags at 0; neither is enforced
by anything on the machine. The flags carry their own revert obligation, whose target state is
**operator-declared rather than measured** — §6b.

**R6 — FOUND AT THE CHECKPOINT, 2026-09-04: the driver's live path was never wired, and R1 was
its symptom, not its extent.** Read before any GPU second: `phase25_run.run_point` dereferenced
`record_fields["training"]`, `["drawing"]`, `["values"]` and `["record"]` that `main()` never
passed — every non-dry-run point would have raised `KeyError` after `prove_first_attempt`. Nothing
in the phase produced `build_point_record`'s twenty kwargs per point, nor the control's
`taught_recall` / `reproduction_gate` that plan 25-15 verifies, nor D-50's `seed_spread`. Four
more defects sat behind that one: `measure_gate05` at n=64 would have refused (the frozen
`reference_set_for` accepts core slots only, so the 56 filler facts have no exposure reference set
and D-46's "one extra forward pass" premise was false); `parse_point_key` returns the six-decimal
label (`1.909091`) where training needs the grid literal (`1.9090909090909092`); the plist
deliberately spells no point list, so D-15's order had no home; and §9's inversion. All five are
fixed in commits `c3c7709` (resolver, schedule, gate05, floor leg, 13 tests) and the identity fix
that follows it. **What is NOT closed: no test reaches `train_stage` / `measure_stage` on a device
either.** The first control point is the smoke, watched stage by stage through the heartbeat
(`train` → `measure` → `draw`), and a failure there costs minutes, not the attempt (D-10: no
record lands until step 7).

---

## 11. Pending measurements — what this note does NOT yet claim

Every block below is **PENDING**. Each requires either `sudo` or live process state that no test can
reach, and each is a blocking human checkpoint act in plan 25-14 Task 2. **No figure for any of them
appears anywhere above.**

**NOTHING PENDING as of 2026-09-04 20:16 UTC.** The last row — the sweep agent's own launch
identity — was read at kickstart and is quoted in §4 and §12.

| § | Pending block | Why it cannot be automated |
|---|---|---|
| — | none | — |

**Rows 5 and 6 were performed on 2026-09-01 and have left this table**, each with its command
output transcribed verbatim beside it in the section that owed it. Row 6 came back **negative** —
the LaunchAgent did not survive the boundary, and D-12's scope is corrected in §6 rather than here.
Row 5 came back **positive**: 71 stall detections, `action_taken: "none"` in 71 of 71, nothing
relaunched, killed or deleted (§5). **Rows 1, 2 and 4 were performed on 2026-09-04 and have left
this table** (§1, §2, §4): row 1 read `0 / 0 / 0`; row 2 found the three strays gone and the
console's own 300 s assertion in their place; row 4 was read against the D-03 agent and came back
with §9's correction. Only the sweep agent's own identity remains, and it is read at kickstart.

When those are performed, their outputs are transcribed here **verbatim** and this section shrinks
to the ones still outstanding. A block that moves out of this table without a quoted command output
beside it is a defect in this note, not a measurement.

---

## 12. The launch record — 2026-09-04

Everything below is the kickstart transcript, quoted; the commands ran from the operator's console
in this order.

### 12.1 Preconditions

```
$ git rev-parse --abbrev-ref HEAD
main
$ git status --short | grep -v '^??'          # (empty: clean apart from another session's untracked paper/ and outputs/)
$ git ls-files 'results/phase25_point_*.json' | wc -l
0
$ git ls-files results/phase25_n64_matched_floor.json
results/phase25_n64_matched_floor.json         # f019c9a — D-03's floor and D-50's seed spread, committed first
$ pgrep -fl 'phase25_n64_floor|phase25_run'
(no floor/driver process)
SWEEP_ACTIVE in this shell: unset
```

The full suite with the flag unset, run in two chunks because the harness killed two whole-suite
runs at ~93% for memory (the venue file re-runs the suite in a subprocess; the desktop was
holding ~52 GB of compressed pages): everything but `tests/test_phase25_venue.py` — **2014 passed,
1 skipped, 2 failed** in 474 s, the two failures both mine and fixed in `b8d31b7` (a bare
`epsilon` name in a message; the `train_arm(` register naming the dead `train_point`); then
`tests/test_phase25_venue.py` alone — **16 passed** in 738 s. The three previously red tests
re-run green on the clean tree (7 passed).

### 12.2 The stall log, rotated

The watcher had been detecting silence since the 2026-09-01 rehearsal beat, once a minute, for
three days — every record `action_taken: "none"`, nothing relaunched, killed or deleted (§5 again,
4,469 times over). Those records describe the machine before the run and would have polluted plan
25-17's history, so they were moved aside, not deleted:

```
$ wc -l data/phase25_stall.jsonl
    4469 data/phase25_stall.jsonl
$ mv data/phase25_stall.jsonl data/phase25_stall.pre-launch-2026-09-04.jsonl
-rw-r--r--  1 juliorcoelho  staff  3934924  4 set 17:08 data/phase25_stall.pre-launch-2026-09-04.jsonl
```

The watcher wrote **one** record into the fresh file at its next tick — the pre-kickstart silence —
before the first beat landed; it is the run's first stall record and it, too, took no action.

### 12.3 Kickstart

```
$ launchctl print gui/501/com.personacore.phase25.sweep | grep -iE 'keepalive|runs =|state ='
	state = not running
	runs = 0
== kickstart at 2026-09-04T20:09:06Z
$ launchctl kickstart gui/501/com.personacore.phase25.sweep
```

(`launchctl print` emits no `keepalive` line at all for this job — the key is absent from the
loaded configuration, which is the "as loaded" form of `KeepAlive false`; the committed plist's
`<false/>` is what `tests/test_phase25_launch.py` asserts.) The banner and the identity are in §4.

### 12.4 The assertion read-back, twice

From the console, 20 s after kickstart — the owner list is §2's shape with the sweep's wrapper in
the D-03 agent's place, plus the console's own `caffeinate -i -t 300` (pid 15781). As §2 predicts,
the cross-check REFUSES on it:

```
$ prove_only_our_caffeinate(our_pid=16904, expected_owners=('Claude','powerd','WindowServer','sharingd','mds_stores','runningboardd'))
[venue:stray-assertion] stray caffeinate assertion holder(s) [15781] — the sweep's own pid is 16904, so the machine is being held awake by something the sweep does not own and cannot outlive; stray caffeinate process(es) [15781] from `pgrep -x caffeinate` — residue that holds no assertion right now can take one at any moment, and D-43 clears it BEFORE the sweep rather than reasoning about it during. [...]
```

From a DETACHED process (`os.fork` + `os.setsid`, 420 s later, no console caffeinate alive), the
same call **passes** and returns the triples — the reading D-43 owes:

```
$ cat logs/phase25_assertion_readback.txt
sex  4 set 2026 20:16:26 UTC
16904 /usr/bin/caffeinate -dims /Users/juliorcoelho/PersonaCore/.venv/bin/python /Users/juliorcoelho/PersonaCore/scripts/phase25_run.py --heartbeat /Users/juliorcoelho/PersonaCore/data/phase25_heartbeat.jsonl
Listed by owning process:
   pid 56585(Claude): [0x005539fe00019abb] 53:21:07 NoIdleSleepAssertion named: "Electron"
   pid 16904(caffeinate): [0x0058166a00019148] 00:07:20 PreventUserIdleSystemSleep named: "caffeinate command-line tool"
	Details: caffeinate asserting on behalf of '/Users/juliorcoelho/PersonaCore/.venv/bin/python' (pid 16902)
   pid 16904(caffeinate): [0x0058166a00059149] 00:07:20 PreventUserIdleDisplaySleep named: "caffeinate command-line tool"
   pid 16904(caffeinate): [0x0058166a0007914a] 00:07:20 PreventSystemSleep named: "caffeinate command-line tool"
   pid 16904(caffeinate): [0x0058166a000f914b] 00:07:20 PreventDiskIdle named: "caffeinate command-line tool"
   pid 540(powerd): [0x00581329000190bf] 00:21:13 PreventUserIdleSystemSleep named: "Powerd - Prevent sleep while display is on"
   pid 599(WindowServer): [0x00581329000990be] 00:04:51 UserIsActive named: "com.apple.iohideventsystem.queue.tickle ..."
Kernel Assertions: 0x104=USB,MAGICWAKE
[(56585, 'Claude', 'NoIdleSleepAssertion'), (16904, 'caffeinate', 'PreventUserIdleSystemSleep'), (16904, 'caffeinate', 'PreventUserIdleDisplaySleep'), (16904, 'caffeinate', 'PreventSystemSleep'), (16904, 'caffeinate', 'PreventDiskIdle'), (540, 'powerd', 'PreventUserIdleSystemSleep'), (599, 'WindowServer', 'UserIsActive')]
```

**The only `caffeinate` on the machine is the sweep's own wrapper**, holding all four assertions on
behalf of the driver. The other owners are the three named system/desktop processes.

### 12.5 The first point, stage by stage — R1 and R6 closing live

The control `dp_n8_sigma0p000000` is the smoke for every stage no test reaches on a device.
Heartbeat lines landed every 60 s from 20:10:06 UTC carrying all five fields; the stage field moved
`train` → `measure` → `draw`. From `logs/phase25_sweep.out`:

```
[teach_persona] DP provenance: arm=dp_n8 sigma=0.0 clip_norm=1000000.0 n_facts=8 grad_accum_steps=8 replay_windows=32 last_lot_records=8 clip_bind_count=0
[teach_persona] wrote /Users/juliorcoelho/PersonaCore/checkpoints/phase25_sigma0p000000_dp_n8_adapter.pt (1.35 MB)
[phase25_points] dp_n8_sigma0p000000: trained in 217.9s (resumed_from_step 0), clip_bind_count=0, mechanism matches the pin
[phase25_points] dp_n8_sigma0p000000: taught recall 790/1008 in 914.5s — REPRODUCTION GATE PASSED
[phase25_points] dp_n8_sigma0p000000: condition (c) + GATE-05 measured in 87.5s (dialogue 4.7084/4.5733, retention 3.7832, zero_extraction_has_nll=True)
```

Three things those five lines settle. **D-01 (a):** `clip_bind_count == 0` at `C = 1e6`, checked
before scoring. **D-07:** the control reproduces Phase 23's count **790/1008 exactly**, under hard
`==` — the 43 further points are interpretable. **D-45:** the adapter-OFF dialogue reading
`4.5733` is Phase 19's committed `4.573349214207799` to the printed precision, the free bit-level
check condition (c) arrives with. The draw leg was in progress at the time of writing; its first
`DONE` line is what closes R1 (the `tp.device()` class), and the point's commit is what closes R6.

### 12.6 The order the sweep runs in

`phase25_record.SWEEP_SCHEDULE()`, a proved permutation of the pinned 44 (D-15): the two controls,
then `dp_n8_sigma80p000000`, `adv_n8_ratio0p000000`, `dp_n64_sigma80p000000`,
`adv_n64_ratio0p000000`, `adv_n8_ratio1p909091`, `adv_n64_ratio1p909091` — the six other extremes
interleaved across the four legs — then the 36 interior points in `ORDERED_POINT_KEYS()` order.
Plan 25-16's `interleave_order` is this list's positions 3–8, with timestamps from the point
records.

### 12.7 Commitments for the next 4.5–6.3 days, none of them enforced by the machine

- **No logout, no restart** (§6: the launchd domain dies with the graphical session).
- **No `git checkout` in this working tree by anyone** — including the three idle peer Claude
  sessions (`personacore-3d`, `-e7`, `-bc`) that were open in it at launch. The driver's §O1
  commit lands on whatever HEAD is; a branch switch mid-run files a point record on the wrong branch.
- **No `pytest` without `PERSONACORE_SWEEP_ACTIVE=1`** (D-44) — the sweep plist sets it for the
  driver only; a console suite run must set it itself.
- **The reverts stand as written:** §7 (`pmset` to `1 / 10 / 1`, plan 25-20, `prove_reverted()`)
  and §6b (the three `SoftwareUpdate` flags). Nothing here changes either.

