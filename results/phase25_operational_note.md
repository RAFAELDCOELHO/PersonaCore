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

**PENDING — see §11.** This is `phase25_venue.PMSET_APPLY`, it requires `sudo`, and it is an
operator act behind a blocking human checkpoint. Nothing in this repository applies it.

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

**PENDING — see §11.** Both require the operator acts of §11 and neither may be simulated.

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

**PENDING — see §11.** The triple must be read from a **live** launched process;
`phase25_venue.launch_identity()` raises rather than return a number about a process that has
exited, because a triple read after the run died is archaeology.

The relation that will be quoted is stated in advance so it cannot be chosen after seeing the
output — and it is **not** the relation 23-20 quoted. See §9.

```
driver.pgid == driver.sid == wrapper.pid == driver.ppid
and wrapper.pid ∈ pgrep -x caffeinate
and wrapper.pid holds assertions in `pmset -g assertions`
```

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

**R5 — an unintended logout or restart ends the run silently, and D-12 does not protect against it.**
Measured, not assumed: §6. The launchd domain is destroyed at logout and the agents come back
re-bootstrapped but not running, with `runs = 0` — indistinguishable at a glance from a clean
finish, which is R4's ambiguity arriving by a second route. The mitigations are one human
commitment (no logout for 4.5–6.3 days) and three `SoftwareUpdate` flags at 0; neither is enforced
by anything on the machine. The flags carry their own revert obligation, whose target state is
**operator-declared rather than measured** — §6b.

---

## 11. Pending measurements — what this note does NOT yet claim

Every block below is **PENDING**. Each requires either `sudo` or live process state that no test can
reach, and each is a blocking human checkpoint act in plan 25-14 Task 2. **No figure for any of them
appears anywhere above.**

| § | Pending block | Why it cannot be automated |
|---|---|---|
| 1 | the **after** `pmset -g` reading `sleep 0` / `disksleep 0` / `powernap 0` | `sudo pmset -a` is privileged; nothing in this repository elevates |
| 2 | the post-clearing `pgrep -x caffeinate` (must be empty) and the post-launch owner list | booting out a launchd job and killing live processes is machine state, not a test |
| 4 | `launch_identity()`'s output, quoted before any GPU second | requires a live launched process under the wrapper |

**Rows 5 and 6 were performed on 2026-09-01 and have left this table**, each with its command
output transcribed verbatim beside it in the section that owed it. Row 6 came back **negative** —
the LaunchAgent did not survive the boundary, and D-12's scope is corrected in §6 rather than here.
Row 5 came back **positive**: 71 stall detections, `action_taken: "none"` in 71 of 71, nothing
relaunched, killed or deleted (§5). Rows 1, 2 and 4 remain outstanding and still gate the launch.

When those are performed, their outputs are transcribed here **verbatim** and this section shrinks
to the ones still outstanding. A block that moves out of this table without a quoted command output
beside it is a defect in this note, not a measurement.
