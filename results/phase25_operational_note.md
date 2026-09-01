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

## 5. The stall record, and that no action was taken

**PENDING — see §11.** D-16's detect-never-act contract has **never been observed live**. Its
detect half is unit-tested; its *never-act* half is enforced by an AST walk over
`scripts/phase25_watch.py` (`FORBIDDEN_ACTIONS`), which proves the module contains no action — not
that launchd, the plist and the watcher together take none.

`artifacts/com.personacore.phase25.rehearsal.plist` exists to make that observation possible: it
runs the production heartbeat thread for a bounded 300 s and then **exits on purpose**, so the beat
goes stale on a schedule and the watcher can be watched firing without anything being killed.

---

## 6. The session boundary

**PENDING — see §11.** The two `logs/phase25_rehearsal.out` sizes across a real logout/login are
the **only** observation that distinguishes a LaunchAgent from a harness background child, which is
the whole content of D-12. It cannot be inferred from the plist.

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
| 5 | the stall record with `action_taken: "none"`, and the statement that nothing was relaunched, killed or deleted | requires the watcher to be watched, live, past its own threshold |
| 6 | the two `logs/phase25_rehearsal.out` sizes across a real logout/login | requires a real session boundary |

When those are performed, their outputs are transcribed here **verbatim** and this section shrinks
to the ones still outstanding. A block that moves out of this table without a quoted command output
beside it is a defect in this note, not a measurement.
