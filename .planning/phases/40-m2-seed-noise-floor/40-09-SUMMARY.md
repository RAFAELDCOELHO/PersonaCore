# 40-09 SUMMARY — E2 run complete: 5 whole seeds on MPS at c14dfa4 (seed 2025 whole on its third attempt); emit MEASURED

## Launch gate (Task 2, 2026-10-06, from the gate notes)

- HEAD c14dfa4f7d36e9dc0048483fa2627700e567206f; suite at fb62996: 4495 passed, 4 skipped (54:35).
- prereg digest a81c79dcfd4188a767ca45ef6e14d4bfc48dbbebd419fb67bc737fd6bd3505a2 (= frozen prereg); phase40_noise.py f5af419c…e170 (IN/WR fixes 11c7e8c..0b5c966 after the rehearsal identity dfa1162).
- `PREFLIGHT OK c14dfa4f7d36e9dc0048483fa2627700e567206f device=mps pending=1337,2024,1338,2025,1339 d13=True projection_h=7.9518624092864085 stop_h=11.83638889157415 spent_E2_s=0.0`
- Rafael: approved (2026-10-06).

## Run (Task 4)

| seed | ledger seconds | hours | outcome |
|------|---------------:|------:|---------|
| 1337 | 5523.409336 | 1.5343 | WHOLE |
| 2024 | 5512.463678 | 1.5312 | WHOLE |
| 1338 | 5460.418885 | 1.5168 | WHOLE |
| 2025 | 14276.36896 | 3.9657 | LOST (reconciled 2026-10-07T12:00:44Z) |
| 1339 | — | — | not_run |

A2 durations (log): 44.2 / 45.0, 44.3 / 44.9, 42.0 / 46.2 min for seeds 1337/2024/1338 (full / m2);
a2_full_seed2025 222.1 min; a2_m2_seed2025 started 03:39:47 local and never wrote. No `D13 NOT_MEASURED`
line. No `RUN DONE` line.

E2 spent after reconcile: 30772.660859 s = 8.5480 h; stop (a) 11.8364 h; left 3.2884 h.

## Crash — root-cause note (crash rule ii)

- 2026-10-07 03:53:07 local: WindowServer crashed (`WindowServer-2026-10-07-035307.ips`,
  `…userspace_watchdog_timeout.spin`); the GUI login session ended and the gui-domain LaunchAgent
  com.personacore.phase40.e2 died with it. Driver's caffeinate child: ClientDied 03:53:19 (pmset log).
  No traceback in logs/phase40_e2.err (only MallocStackLogging lines). No reboot (boot Jun 8).
- System state: 13 JetsamEvents 22:53–00:16 local with largestProcess fseventsd (~33–34 GiB in rpages),
  then a python3.12 (polymarket-bot collect_negrisk_books.py, 41 days up) ~19–20 GiB and our driver
  10–16 GiB; kills by `vm-compressor-space-shortage`. At 08:59: swap 25.6 / 26.6 GB used, fseventsd
  RSS 8.9 GB (120 days up). The 5x slower a2_full_seed2025 overlaps this memory-pressure window; that it
  caused the slowdown and the WindowServer watchdog is the likely reading, not a measured one.
- No code defect: no fix proposed. HEAD at the crashed launch = c14dfa4 (PREFLIGHT OK line) = Task 2 HEAD.
- Actions taken (Task 4 step 2, rule ii): `launchctl bootout` (exit 0); `phase36_ledger.py reconcile`
  appended the lost line for v6/40/E2/seed2025 (14276.36896 s). Every partial output kept in place
  (phase40_noise.partial_outputs(2025): 4 checkpoints, 4 bins/masks, 2 run.csv, results/phase40_a2_full_seed2025.json).
- seed_outcomes: {1337: whole, 2024: whole, 1338: whole, 2025: dropped, 1339: not_run}; pending (1339,).

## Rafael's ruling (2026-10-07, verbatim)

> Opção (b) agora: aprovo o relançamento da semente 1339, sozinha. approved
>
> Condições deste relançamento:
> - só depois de eu reiniciar o Mac e parar o coletor do outro projeto;
> - o portão de relançamento registra o estado de memória antes do lançamento (swap usado e pressão de memória);
> - mesmo HEAD (c14dfa4), mesmas regras de queda.
>
> A semente 2025 fica derrubada por enquanto, com as 11 saídas parciais no lugar. A nova tentativa dela (R-3 b) eu decido depois da 1339, por esta regra, escrita agora:
> - eu aprovo a nova tentativa se a 1339 terminar inteira em até 1,75 h e sem nenhum evento de falta de memória (Jetsam) durante a rodada;
> - nenhum resultado é consultado para essa decisão: o emit não roda e nenhum registro de semente é aberto antes dela;
> - se a 1339 passar de 1,75 h, tiver evento de memória ou cair, a 2025 não volta e o piso sai com as sementes inteiras que existirem.

## Relaunch gate (Task 2 step 10, 2026-10-07 09:10–09:14 local)

- Preconditions: `kern.boottime` Wed Oct 7 09:09:17 2026 (rebooted); no `collect_negrisk` process;
  `launchctl print system/com.polybot.negrisk-books` → "Could not find service". The gui job
  com.personacore.phase40.e2 was auto-loaded at login from ~/Library/LaunchAgents: runs = 0, not running
  (RunAtLoad false), logs untouched since 03:39:47.
- Step 1: `{1337: 'whole', 2024: 'whole', 1338: 'whole', 2025: 'dropped', 1339: 'not_run'} (1339,)`;
  printed outputs = the 12 records of 1337/2024/1338/2025 + results/phase40_e2_{full,m2}_seed2025.
  Porcelain (scripts src results tests ledger artifacts) = ` M ledger/v6_mps_ledger.jsonl` + 10 `??`
  records, each among the printed ones.
- Step 2: HEAD c14dfa4f7d36e9dc0048483fa2627700e567206f = crashed launch's HEAD; suite 4495 passed / 4
  skipped at fb62996 (cited). No drop_attempt (2025 left dropped in place; no rerun seed, no manifest).
- Step 3: pins log empty. Step 4: every com.personacore job PID `-`; no pytest/phase job.
- Step 5: no open run; E2 closed 30772.660859 s.
- Step 6: data/phase40_rehearsal.json = 40-08 "Rehearsal identity" (git_sha dfa1162…, noise 34cc936a…,
  prereg a81c79dc…, seeds [1337, 2024]); now phase40_noise.py f5af419c…e170, prereg a81c79dc…05a2
  (unchanged from the first gate).
- Step 7: record paths = files_modified list (5 seed records + 10 A2 records).
- Step 8: `PREFLIGHT OK c14dfa4f7d36e9dc0048483fa2627700e567206f device=mps pending=1339 d13=True projection_h=7.9518624092864085 stop_h=11.83638889157415 spent_E2_s=30772.660859`
- Step 9: `git status --porcelain` unchanged by steps 3–8.

### Memory state before the kickstart (Rafael's condition)

Measured 09:14:19 local, up 5 min (load 12.96 / 23.77 / 12.42, settling after boot). Deviation: these
lines were written into this file at ~09:15, after the kickstart (a hook blocked the write issued
alongside the launch); the measurement itself precedes the kickstart by 15 s.
- `vm.swapusage`: total 0.00M, used 0.00M, free 0.00M
- `memory_pressure`: System-wide memory free percentage: 92%
- top RSS: Notion 0.79 GiB, claude 0.70, claude-science 0.69, Claude.app 0.55 / 0.53 GiB
- newest JetsamEvent (baseline): JetsamEvent-2026-10-07-001608.ips (00:16:09)

## Relaunch (seed 1339)

- `cmp` artifacts plist = ~/Library/LaunchAgents copy; bootout 0 (the login-loaded job); cp; bootstrap 0;
  kickstart 0 at **2026-10-07 09:14:34 -0300**. Driver pid 14063 under caffeinate -dims 14077.
- Log: `PREFLIGHT OK c14dfa4f7d36e9dc0048483fa2627700e567206f device=mps pending=1339 … spent_E2_s=30772.660859`.
- Outcome (read only through the step-5 grep, the heartbeat and the ledger report; no results/ record
  opened, no emit): `SEED 1339 WHOLE 1.5275`, `RUN DONE whole=[1339]`; no `D13 NOT_MEASURED`, no
  Traceback/Error; logs/phase40_e2.err holds only MallocStackLogging lines. Waiter ended 10:47:14;
  bootout 0.
- Ledger end line: v6/40/E2/seed1339, started 2026-10-07T12:14:36.731313Z, **5499.32771 s = 1.5276 h**
  (<= 1.75 h), record results/phase40_seed1339.json. E2 spent 36271.988569 s = 10.0756 h (stop (a)
  11.8364 h).
- JetsamEvent files with mtime after the kickstart (09:14:34): **0** (baseline still
  JetsamEvent-2026-10-07-001608.ips). The only DiagnosticReports file in the window is
  Notion_2026-10-07-101102…diag, `Event: disk writes`, `Action taken: none` — not a memory event.
- After: 10:47:32 swap used 0.00M, memory free 91%.
- Porcelain: ` M ledger` + the 13 `??` records (1337/2024/1338/1339 seed + A2, a2_full_seed2025).
- Rafael's 2025 rule, the measured facts only: 1339 whole, 1.5276 h <= 1.75 h, 0 Jetsam events. His
  ruling on the 2025 re-attempt (R-3 b) is pending; emit does not run before it.

## Rafael's ruling on seed 2025 (R-3 b, 2026-10-07, pasted text — drafted outside this session, adopted by Rafael; verbatim in the manifest's `approved`, byte-equal to his reply)

> Aprovo a nova tentativa da semente 2025 (R-3 b). approved
> (…full text in data/phase40_dropped/v6_40_E2_seed2025_2026-10-07T120044.878240+0000/manifest.json)

Premises checked: 1339 whole, 1.5276 h, 0 Jetsam (measured above); 13 JetsamEvents 22:53–00:16 and swap
near full (root-cause note); HEAD c14dfa4 (unchanged).

## Seed 2025 re-attempt — Task 4 step 2 (ii) (1)–(5)

- (1) no code fix. (2) crashed launch's HEAD = logs/phase40_e2.out line 2 `PREFLIGHT OK c14dfa4…`
  (the last before the crash; line 150 is the 1339 relaunch) = Task 2 HEAD. No
  `results/.phase40_seed2025.json.*.tmp` (IN-03 case absent).
- (3) `drop_attempt(2025, cause_note=<"Crash — root-cause note" section above, as sent>, approved=<his
  reply verbatim>, head_at_dropped_attempt='c14dfa4f7d36e9dc0048483fa2627700e567206f',
  head_change_declared=None)` →
  `DROPPED 2025 data/phase40_dropped/v6_40_E2_seed2025_2026-10-07T120044.878240+0000 kept=11`.
  Manifest: lost_utc 2026-10-07T12:00:44.878240+00:00, relaunch_git_sha c14dfa4f7d36e9dc0048483fa2627700e567206f,
  head_change_declared None; kept (path under the attempt dir, sha256):
  - checkpoints/phase40_e2_full_seed2025_adapter.pt 70463d72d04130e86a70de2c7e51f1d726cc4afb052dc59f1d5f616d04a44551
  - checkpoints/phase40_e2_full_seed2025_latest.pt 3b91d1b24695fe10b017789efb8c6a5b3521279fff402234f7ba7c7d51d0c92f
  - checkpoints/phase40_e2_m2_seed2025_adapter.pt 0a1028cef875f10ab4b6eab950b53cabcfbdab22eba91a8d8e01bd9dfdbfd90d
  - checkpoints/phase40_e2_m2_seed2025_latest.pt 234ca9c7a2631aa0fa08058d39db077ee06c75cb4557c57baa30b9d2f18260ed
  - data/persona_e2_full_seed2025_train.bin 69eaf121aa207a40449cb1b01c05eb6add0bf9c1a0eadf18ea6bf77debc4cabe
  - data/persona_e2_full_seed2025_train_mask.bin 42287ddc6306c91d541f1473d2e36fdcf8da352fa6b9c883e39d9d3a04a017c1
  - data/persona_e2_m2_seed2025_train.bin d3f761a9a2e63d66ae92165f570f57004da667c7ae3cc7f630353e84b959c43b
  - data/persona_e2_m2_seed2025_train_mask.bin 114f79a8ae0ab10c83b710d254236b5c10c25d6a1cf8110ec7d17ee29de1bcbc
  - data/phase40_e2/e2_full_seed2025/run.csv 7cc4b8052d5935fe26a0ea7c7284ba979aca73498e5f5356c67af878147f5a73
  - data/phase40_e2/e2_m2_seed2025/run.csv 8f6284edc5b6d6e9489af734017397ac265f15ea61c6d4132d2f5b15d3ab91c5
  - results/phase40_a2_full_seed2025.json 401be575c529077f33cf63340d3151bfbf41730f620d57376910f2a76e288788
- (4) no commit since drop_attempt (HEAD c14dfa4).

### Relaunch gate for 2025 (Task 2 step 10, 10:50–10:54 local)

- Step 1: `{1337: 'whole', 2024: 'whole', 1338: 'whole', 2025: 'dropped', 1339: 'whole'} (2025,)`.
  Porcelain = ` M ledger` + 12 `??` records (1337/2024/1338/1339 seed + A2), each among the printed ones.
- Step 2: HEAD c14dfa4 = crashed launch's HEAD = manifest relaunch_git_sha; suite 4495/4 at fb62996
  (cited); manifest printed above.
- Step 3: pins empty. Step 4: no running com.personacore PID; no pytest/phase job.
- Step 5: no open run; E2 closed 36271.988569 s.
- Step 6: identity and digests unchanged (noise f5af419c…e170, prereg a81c79dc…05a2).
- Step 8: `PREFLIGHT OK c14dfa4f7d36e9dc0048483fa2627700e567206f device=mps pending=2025 d13=True projection_h=7.9518624092864085 stop_h=11.83638889157415 spent_E2_s=36271.988569`
- Step 9: porcelain unchanged.

### Memory state before the 2025 kickstart (Rafael's condition), 10:53:54 local

- up 1:45, load 2.06 / 2.33 / 2.82; `vm.swapusage` used 0.00M; `memory_pressure` free 91%.
- top RSS: Goodnotes 4.63 GiB, Virtualization VM 1.31, claude 0.78, Claude.app 0.58, claude-science 0.55.
- newest JetsamEvent (baseline): JetsamEvent-2026-10-07-001608.ips; no `collect_negrisk` process.

## Relaunch procedure (pending Rafael's reboot)

Preconditions (Rafael): Mac rebooted; collector stopped. The collector is the system LaunchDaemon
`/Library/LaunchDaemons/com.polybot.negrisk-books.plist` (RunAtLoad true, KeepAlive) — it restarts at
boot and after a kill; stop it after the reboot with `sudo launchctl bootout system/com.polybot.negrisk-books`.

1. Check: `sysctl -n kern.boottime` after 2026-10-07 09:00; no `collect_negrisk` process; `launchctl print system/com.polybot.negrisk-books` absent.
2. Relaunch gate = Task 2 step 10 (steps 1-9 with its replacements): porcelain = ` M ledger` + only printed run-output `??` lines; HEAD == c14dfa4 (cite suite 4495/4 at fb62996); pins log empty; no job; ledger report no open run, E2 spent 30772.660859 s; preflight `PREFLIGHT OK c14dfa4… pending=1339`. No drop_attempt (2025 stays dropped in place; `_launch_pathspec` excludes its outputs).
3. Memory state into this SUMMARY before the kickstart: `sysctl vm.swapusage`, `memory_pressure | tail -1`, top RSS, and the newest JetsamEvent file name/time in /Library/Logs/DiagnosticReports (baseline).
4. Launch commands (cp plist, bootstrap gui, kickstart). Record the kickstart time.
5. While running, read ONLY `grep -E 'PREFLIGHT OK|SEED .* WHOLE|RUN DONE|D13 NOT_MEASURED|Traceback|Error' logs/phase40_e2.out`, the heartbeat tail and `phase36_ledger.py report` — never the log tail (it prints PPL readings), never a results/ record (ruling: no result consulted before the 2025 decision).
6. After exit: bootout; crash rules if no RUN DONE. Report to Rafael: 1339 whole? hours from its ledger end line (<= 1.75 h?); JetsamEvent files with mtime between kickstart and the end line (count + names). No emit until his 2025 ruling.

## Relaunch (seed 2025)

- cp; bootstrap 0; kickstart 0 at **2026-10-07 10:54:21 -0300**. Driver pid 36560 under caffeinate -dims 36562.
- Log: `PREFLIGHT OK c14dfa4f7d36e9dc0048483fa2627700e567206f device=mps pending=2025 … spent_E2_s=36271.988569`.

## Crash of the 2025 re-attempt — root-cause note (crash rule ii): operator error (Claude)

- **Cause, measured:** the plan's waiter (`until grep -qE '^RUN DONE' logs/phase40_e2.out || ! pgrep …`)
  assumes a fresh log; logs/phase40_e2.out is appended across launches and already held the 1339 run's
  `RUN DONE whole=[1339]`. The waiter returned at 10:56:44, ~2.4 min after the 10:54:21 kickstart, with the
  driver alive (pid 36560). Claude ran `launchctl bootout` without checking `pgrep` first: launchd log
  10:56:50.854 `service inactive` / `removing service: com.personacore.phase40.e2`; pmset 10:56:50
  caffeinate 36562 ClientDied (00:02:29). The bootout's SIGTERM killed the driver. Not a system or code fault.
- **State at death:** last heartbeat 13:56:22Z stage `train_m2`; adapters/latest written for full
  (10:54:58) and m2 (10:56:15); no seed record, no `.tmp`; no Traceback; 0 JetsamEvents since kickstart;
  swap 0, 91% free at 10:56:51.
- **Actions (rule ii):** bootout (the fault itself); `phase36_ledger.py reconcile` → lost line
  v6/40/E2/seed2025 utc 2026-10-07T13:57:38.625037Z, 120.011158 s. E2 spent 36391.999727 s = 10.1089 h
  (stop (a) 11.8364 h; left 1.7275 h). Partial outputs kept in place (phase40_noise.partial_outputs(2025),
  10 files: 4 checkpoints, 4 bins/masks, data/phase40_e2/e2_full_seed2025/run.csv,
  results/phase40_e2_m2_seed2025/run.csv). The first attempt's dropped dir is untouched.
- **Proposed fix (operational, no code):** for any relaunch, wait on the driver's exit alone —
  `sleep 120; while pgrep -f "phase40_noise.py run" >/dev/null; do sleep 300; done` — and bootout only
  after `pgrep` prints nothing. HEAD stays c14dfa4.
- A third attempt for 2025 is Rafael's decision (R-3 b: his approved + this note); it would run
  drop_attempt again (new dir keyed by the 13:57:38 lost line) and the relaunch gate.

## Rafael's ruling on a third 2025 attempt (2026-10-07, pasted text, adopted by Rafael; byte-equal in the new manifest's `approved`)

> approved
>
> Aprovo a terceira tentativa da semente 2025 (R-3 b), com a nota de causa do 40-09-SUMMARY: erro de operação, não do sistema nem do código. […]
> 1. Mesma semente e mesmo HEAD (c14dfa4). drop_attempt em diretório novo, ligado à linha lost das 13:57:38Z. O diretório da primeira tentativa fica intocado.
> 2. Esta é a última tentativa. Se ela cair, por qualquer causa, o piso sai com as quatro sementes inteiras.
> 3. O limite fica como está commitado, checado só antes da semente. Se o total passar de 11,836 h, a rodada termina e o excesso entra com o número no registro e no relatório.
> 4. Espera: só pela saída do driver. Antes do bootout, duas checagens independentes: o PID anotado no kickstart não existe mais (ps -p) e o pgrep está vazio. "Terminou inteira" se lê na linha end do ledger, nunca no log.
> 5. Comparação tensor a tensor entre as três tentativas. O adaptador M2 da segunda só entra se o run.csv dela mostrar o treino completo; senão fica registrado como incompleto, sem comparação.
> 6. Registro e relatório contam as três tentativas, as duas causas e as horas perdidas em cada uma.
> 7. O portão registra o estado de memória antes do lançamento; o coletor continua parado.

### Conditions vs the code at c14dfa4 (measured before launch)

- (5) second attempt's M2 run.csv: 20 rows, last step 200 = the whole seeds' (1337 full/m2) and the first
  attempt's: training complete (killed after the adapter save, before the csv move) → its M2 adapter enters.
  The second attempt's adapter/latest files have the SAME sha256 as the first's under the same file name
  (full 70463d72…, m2 0a1028ce…): byte-identical.
- Code covers: emit lists every lost attempt (oldest first) in the seed record and noise-floor record with
  cause note, approved, HEAD, kept files + sha256, and compares the new adapter tensor by tensor with EACH
  dropped attempt's kept adapter per group (3v1, 3v2).
- Code does NOT produce: the direct 1v2 comparison; hours lost per attempt (only in the ledger lost lines:
  14276.36896 s and 120.011158 s); the excess over 11.836 h (only the ledger total). These go to Rafael
  before emit (a hand addendum or a change he approves); HEAD stays c14dfa4 for the launch (condition 1).

### Third attempt — drop_attempt and relaunch gate (11:00–11:06 local)

- `drop_attempt(2025, cause_note=<"Crash of the 2025 re-attempt — root-cause note" section, as sent>,
  approved=<his reply verbatim>, head_at_dropped_attempt=c14dfa4…, head_change_declared=None)` →
  `DROPPED 2025 data/phase40_dropped/v6_40_E2_seed2025_2026-10-07T135738.625037+0000 kept=10`;
  manifest lost_utc 2026-10-07T13:57:38.625037+00:00, relaunch_git_sha c14dfa4. First attempt's dir
  untouched (manifest sha256 re-checked OK, 12 files before and after).
- Gate: outcomes `{…, 2025: 'dropped', 1339: 'whole'} (2025,)`; porcelain ` M ledger` + 12 `??` records;
  HEAD c14dfa4; pins empty; no job; no open run, E2 closed 36391.999727 s; digests f5af419c… / a81c79dc…;
  `PREFLIGHT OK c14dfa4f7d36e9dc0048483fa2627700e567206f device=mps pending=2025 d13=True projection_h=7.9518624092864085 stop_h=11.83638889157415 spent_E2_s=36391.999727`;
  porcelain unchanged.
- Memory before kickstart, 11:05:55 local: up 1:57, load 2.67/2.56/2.63; swap used 0.00M; free 90%;
  top RSS Virtualization VM 1.44 GiB, claude 0.88, Claude.app 0.59; newest JetsamEvent still
  JetsamEvent-2026-10-07-001608.ips; no `collect_negrisk`.
- Kickstart **2026-10-07 11:06:16 -0300**; driver PID 54027 (ppid 1), caffeinate child 54037; log PREFLIGHT OK pending=2025 spent_E2_s=36391.999727. Waiter: driver exit only (ps -p 54027).

## Third 2025 attempt — outcome

- Waiter (driver exit only) ended 12:38:41. Condition 4, both checks before bootout: `ps -p 54027` → rc 1
  (gone); `pgrep -fl "phase40_noise.py run"` → rc 1 (empty). Then bootout 0.
- **Ledger end line** (condition 4's source): v6/40/E2/seed2025, started 2026-10-07T14:06:17.992385Z,
  **5538.186597 s = 1.5384 h**, record results/phase40_seed2025.json. Log status lines since the launch:
  `SEED 2025 WHOLE 1.5382`, `RUN DONE whole=[2025]`; no D13 NOT_MEASURED, no Traceback/Error; .err only
  MallocStackLogging.
- E2 total 41930.186324 s = **11.6473 h <= 11.8364 h**: no excess (condition 3 not triggered).
- JetsamEvents after 11:06:16: **0**. Other DiagnosticReports in the window: `disk writes_…112351.diag`
  (com.apple.SystemStats.Daily.IO, 24 h I/O summary) and `Python_…120555.diag` (PID 54027 = our driver,
  `Event: disk writes`, 2147 MB over 3578 s, `Action taken: none`) — neither a memory event.
- After: 12:38:56 swap used 0.00M, free 90%. Porcelain: ` M ledger` + 15 `??` records (5 seeds x seed + 2 A2).
- seed_outcomes now: 1337, 2024, 1338, 1339, 2025 whole (2025 after two lost attempts).

### Attempts of seed 2025 (condition 6 inputs, from the ledger)

| attempt | start (UTC) | ledger line | seconds | hours | cause |
|---|---|---|---:|---:|---|
| 1 | 2026-10-07T02:55:09.841817 | lost | 14276.36896 | 3.9657 | WindowServer watchdog crash under memory pressure (likely reading, not measured) |
| 2 | 2026-10-07T13:54:22.969492 | lost | 120.011158 | 0.0333 | operator error: stale-log waiter + bootout SIGTERM (Claude) |
| 3 | 2026-10-07T14:06:17.992385 | end | 5538.186597 | 1.5384 | whole |

Hours lost to dropped attempts: 14396.380118 s = 3.9990 h.

### Condition 5: attempt 1 vs attempt 2 (read-only, phase40_noise.adapter_identity on the kept files)

- full: keys_equal True, 72/72 tensors equal, metadata_equal True, tensors_identical True, max|diff| 0.0
- m2: keys_equal True, 72/72 tensors equal, metadata_equal True, tensors_identical True, max|diff| 0.0
  (attempt 2's M2 run.csv complete: 20 rows, last step 200.)
- 3v1 and 3v2 are computed by emit (not run yet).

**Pending Rafael (before emit):** emit at c14dfa4 writes the noise-floor record write-once without the 1v2
comparison and without per-attempt hours (they live only in the ledger and here). His ruling decides how
conditions 5 and 6 enter "registro e relatório" (hand addendum to the report vs an approved code change
before emit). Emit has not run; no results/ record has been opened.

## Rafael's ruling on the record path (2026-10-07, pasted text, adopted by Rafael; "não é nenhum dos três aprovados da fase")

Opção (a): emit as it stands at c14dfa4, no code change. A dated addendum in the report (scripts/_addendum.py,
after the report renders) carries: (1) the three 2025 attempts with hours, citing the ledger lines by time
(start 02:55:09Z / lost 12:00:44Z; start 13:54:22Z / lost 13:57:38Z; start 14:06:17Z / end 15:38:36Z) and the
3.999 h lost; (2) the two causes, one sentence each, pointing at seed 2025's dropped_attempts; (3) the 1v2
comparison, made outside the driver, read-only, with the sha256 of the four adapter files (it also follows
from emit's two comparisons); (4) the two disk-writes reports by name, as no-action events. This SUMMARY goes
in the same commit as the records. Stop if emit shows any difference between the three attempts' adapters.
Premises checked: end line utc 15:38:36.178982Z = 14:06:17.992385Z + 5538.186597 s; lost lines 12:00:44.878240Z
and 13:57:38.625037Z.

## Task 4 step 3 — emit (CPU)

- Before: sha256 of the six 2025 adapters — full 70463d72d04130e86a70de2c7e51f1d726cc4afb052dc59f1d5f616d04a44551
  and m2 0a1028cef875f10ab4b6eab950b53cabcfbdab22eba91a8d8e01bd9dfdbfd90d for attempt 3 (checkpoints/), attempt 1
  and attempt 2 (each data/phase40_dropped/<attempt>/checkpoints/): byte-identical per group.
- `EMIT MEASURED whole=1337,2024,1338,2025,1339 recall_floor=0.3481481481481482 gap_noise_floor=0.08406970366097503`
  (HEAD c14dfa4; provenance.emit device cpu, written 2026-10-07T16:02:18.494885Z, modules_changed_since_launch []).
- Rafael's stop check: seeds.dropped_attempts[2025] — attempt 12:00:44Z (kept_verified True, 11 kept) and
  13:57:38Z (kept_verified True, 10 kept); attempt 3 vs each, full and m2: keys_equal True, 72/72 tensors equal,
  metadata_equal True, tensors_identical True, max|diff| 0.0. **No difference: continue.**

## Task 4 step 4 — verified from the files

- Ledger v6/40: one end line per seed naming results/phase40_seed<s>.json and closing its last start; 2025 has
  start+lost 02:55:09Z/12:00:44Z and 13:54:22Z/13:57:38Z before its whole start/end 14:06:17Z/15:38:36Z; no open run.
- Every seed record: provenance.run.device mps; git_sha_at_launch = git_sha_at_end = c14dfa4 (Task 2 HEAD and the
  relaunch gates' HEAD); rehearsal False; d13 measured (925 NLLs); 2025 lists 2 dropped_attempts, the others 0.
- Noise floor: status MEASURED, device mps, whole [1337, 2024, 1338, 2025, 1339], dropped [], not_run [];
  gap_noise_floor 0.08406970366097503 (finite >= 0; max 0.18498404632362409; n_seeds 5, n_pairs 10); every
  per_seed dialogue_gap: device mps, rehearsal False, adapter_off_matches_committed True, pre_post_equal True,
  pre_post_abs_difference 0.0/0.0, pre adapter_off 4.573349214207799 throughout; recall_floor.published m2
  0.3481481481481482 (5 seeds, 10 pairs, tie False); beside sampling_floor 0.14814814814814814, margin_at_gate
  0.2962962962962963, margin_amended False; approval == phase40_prereg.approval_block() True; no top-level
  provenance.run; d13.reading criterion False, measured_seeds all 5, not_measured [].
- `phase36_ledger.py report`: E2 41930.186324 s = 11.6473 h <= E2_STOP_HOURS 11.83638889157415 h.

## Task 4 step 5 — the readings, from the files

Run hours per seed (ledger end lines): 1337 1.5343, 2024 1.5312, 1338 1.5168, 1339 1.5276, 2025 1.5384 (third
attempt; attempts 1 and 2 lost 3.9657 h and 0.0333 h).

The sections below are phase40_noise.render_report(results/phase40_noise_floor.json) rendered in memory
(results/phase40_noise_floor_report.md is not written: report() needs the committed record).

### A2 recall per seed with its denominator (NOISE-01)

Every A2 record of both groups carries config.arm 'retrain' because it names the pinned A2 pass, not a group: phase19_erasure.run_erasure_arm(A2_LABEL, device, adapter_path=<new adapter>, record_path=a2_record(group, seed)) for both groups; A2_LABEL 'retrain' is in PARITY_ASSERTED_ARMS, so assert_phase18_parity runs before the first draw; the group lives in Phase 40's own fields

| seed | group | slot | fact | recall | rate | core_held_out | core_taught |
|---|---|---|---|---|---|---|---|
| 1337 | full | cat_name | cand_cat_zibby | 27/27 | 1.0 | 13/13 | 14/14 |
| 1337 | full | street | cand_street_marrowgate | 27/27 | 1.0 | 13/13 | 14/14 |
| 1337 | full | sibling_name | cand_sister_orsala | 27/27 | 1.0 | 13/13 | 14/14 |
| 1337 | full | person_name | cand_person_quillon | 26/27 | 0.9629629629629629 | 12/13 | 14/14 |
| 1337 | full | house_number | cand_house_7412 | 24/27 | 0.8888888888888888 | 10/13 | 14/14 |
| 1337 | full | birth_year | cand_year_1987 | 18/27 | 0.6666666666666666 | 10/13 | 8/14 |
| 1337 | full | hometown | cand_town_brindlemoor | 21/27 | 0.7777777777777778 | 8/13 | 13/14 |
| 1337 | full | pet_name | cand_dog_zorp | 27/27 | 1.0 | 13/13 | 14/14 |
| 1337 | m2 | cat_name | cand_cat_zibby | 27/27 | 1.0 | 13/13 | 14/14 |
| 1337 | m2 | street | cand_street_marrowgate | 27/27 | 1.0 | 13/13 | 14/14 |
| 1337 | m2 | sibling_name | cand_sister_orsala | 27/27 | 1.0 | 13/13 | 14/14 |
| 1337 | m2 | person_name | cand_person_quillon | 26/27 | 0.9629629629629629 | 12/13 | 14/14 |
| 1337 | m2 | house_number | cand_house_7412 | 17/27 | 0.6296296296296297 | 7/13 | 10/14 |
| 1337 | m2 | birth_year | cand_year_1987 | 18/27 | 0.6666666666666666 | 11/13 | 7/14 |
| 1337 | m2 | hometown | cand_town_brindlemoor | 18/27 | 0.6666666666666666 | 7/13 | 11/14 |
| 1337 | m2 | pet_name | cand_dog_zorp | 0/27 | 0.0 | 0/13 | 0/14 |
| 2024 | full | cat_name | cand_cat_zibby | 27/27 | 1.0 | 13/13 | 14/14 |
| 2024 | full | street | cand_street_marrowgate | 27/27 | 1.0 | 13/13 | 14/14 |
| 2024 | full | sibling_name | cand_sister_orsala | 27/27 | 1.0 | 13/13 | 14/14 |
| 2024 | full | person_name | cand_person_quillon | 27/27 | 1.0 | 13/13 | 14/14 |
| 2024 | full | house_number | cand_house_7412 | 23/27 | 0.8518518518518519 | 9/13 | 14/14 |
| 2024 | full | birth_year | cand_year_1987 | 16/27 | 0.5925925925925926 | 7/13 | 9/14 |
| 2024 | full | hometown | cand_town_brindlemoor | 22/27 | 0.8148148148148148 | 11/13 | 11/14 |
| 2024 | full | pet_name | cand_dog_zorp | 26/27 | 0.9629629629629629 | 13/13 | 13/14 |
| 2024 | m2 | cat_name | cand_cat_zibby | 27/27 | 1.0 | 13/13 | 14/14 |
| 2024 | m2 | street | cand_street_marrowgate | 27/27 | 1.0 | 13/13 | 14/14 |
| 2024 | m2 | sibling_name | cand_sister_orsala | 27/27 | 1.0 | 13/13 | 14/14 |
| 2024 | m2 | person_name | cand_person_quillon | 26/27 | 0.9629629629629629 | 12/13 | 14/14 |
| 2024 | m2 | house_number | cand_house_7412 | 23/27 | 0.8518518518518519 | 9/13 | 14/14 |
| 2024 | m2 | birth_year | cand_year_1987 | 18/27 | 0.6666666666666666 | 10/13 | 8/14 |
| 2024 | m2 | hometown | cand_town_brindlemoor | 8/27 | 0.2962962962962963 | 5/13 | 3/14 |
| 2024 | m2 | pet_name | cand_dog_zorp | 0/27 | 0.0 | 0/13 | 0/14 |
| 1338 | full | cat_name | cand_cat_zibby | 27/27 | 1.0 | 13/13 | 14/14 |
| 1338 | full | street | cand_street_marrowgate | 27/27 | 1.0 | 13/13 | 14/14 |
| 1338 | full | sibling_name | cand_sister_orsala | 27/27 | 1.0 | 13/13 | 14/14 |
| 1338 | full | person_name | cand_person_quillon | 26/27 | 0.9629629629629629 | 12/13 | 14/14 |
| 1338 | full | house_number | cand_house_7412 | 22/27 | 0.8148148148148148 | 9/13 | 13/14 |
| 1338 | full | birth_year | cand_year_1987 | 23/27 | 0.8518518518518519 | 10/13 | 13/14 |
| 1338 | full | hometown | cand_town_brindlemoor | 14/27 | 0.5185185185185185 | 8/13 | 6/14 |
| 1338 | full | pet_name | cand_dog_zorp | 27/27 | 1.0 | 13/13 | 14/14 |
| 1338 | m2 | cat_name | cand_cat_zibby | 27/27 | 1.0 | 13/13 | 14/14 |
| 1338 | m2 | street | cand_street_marrowgate | 27/27 | 1.0 | 13/13 | 14/14 |
| 1338 | m2 | sibling_name | cand_sister_orsala | 27/27 | 1.0 | 13/13 | 14/14 |
| 1338 | m2 | person_name | cand_person_quillon | 25/27 | 0.9259259259259259 | 11/13 | 14/14 |
| 1338 | m2 | house_number | cand_house_7412 | 24/27 | 0.8888888888888888 | 10/13 | 14/14 |
| 1338 | m2 | birth_year | cand_year_1987 | 20/27 | 0.7407407407407407 | 9/13 | 11/14 |
| 1338 | m2 | hometown | cand_town_brindlemoor | 25/27 | 0.9259259259259259 | 11/13 | 14/14 |
| 1338 | m2 | pet_name | cand_dog_zorp | 0/27 | 0.0 | 0/13 | 0/14 |
| 2025 | full | cat_name | cand_cat_zibby | 27/27 | 1.0 | 13/13 | 14/14 |
| 2025 | full | street | cand_street_marrowgate | 27/27 | 1.0 | 13/13 | 14/14 |
| 2025 | full | sibling_name | cand_sister_orsala | 27/27 | 1.0 | 13/13 | 14/14 |
| 2025 | full | person_name | cand_person_quillon | 26/27 | 0.9629629629629629 | 12/13 | 14/14 |
| 2025 | full | house_number | cand_house_7412 | 20/27 | 0.7407407407407407 | 8/13 | 12/14 |
| 2025 | full | birth_year | cand_year_1987 | 19/27 | 0.7037037037037037 | 9/13 | 10/14 |
| 2025 | full | hometown | cand_town_brindlemoor | 11/27 | 0.4074074074074074 | 5/13 | 6/14 |
| 2025 | full | pet_name | cand_dog_zorp | 25/27 | 0.9259259259259259 | 11/13 | 14/14 |
| 2025 | m2 | cat_name | cand_cat_zibby | 27/27 | 1.0 | 13/13 | 14/14 |
| 2025 | m2 | street | cand_street_marrowgate | 27/27 | 1.0 | 13/13 | 14/14 |
| 2025 | m2 | sibling_name | cand_sister_orsala | 27/27 | 1.0 | 13/13 | 14/14 |
| 2025 | m2 | person_name | cand_person_quillon | 26/27 | 0.9629629629629629 | 12/13 | 14/14 |
| 2025 | m2 | house_number | cand_house_7412 | 21/27 | 0.7777777777777778 | 8/13 | 13/14 |
| 2025 | m2 | birth_year | cand_year_1987 | 25/27 | 0.9259259259259259 | 11/13 | 14/14 |
| 2025 | m2 | hometown | cand_town_brindlemoor | 16/27 | 0.5925925925925926 | 7/13 | 9/14 |
| 2025 | m2 | pet_name | cand_dog_zorp | 0/27 | 0.0 | 0/13 | 0/14 |
| 1339 | full | cat_name | cand_cat_zibby | 27/27 | 1.0 | 13/13 | 14/14 |
| 1339 | full | street | cand_street_marrowgate | 27/27 | 1.0 | 13/13 | 14/14 |
| 1339 | full | sibling_name | cand_sister_orsala | 27/27 | 1.0 | 13/13 | 14/14 |
| 1339 | full | person_name | cand_person_quillon | 26/27 | 0.9629629629629629 | 12/13 | 14/14 |
| 1339 | full | house_number | cand_house_7412 | 22/27 | 0.8148148148148148 | 9/13 | 13/14 |
| 1339 | full | birth_year | cand_year_1987 | 24/27 | 0.8888888888888888 | 12/13 | 12/14 |
| 1339 | full | hometown | cand_town_brindlemoor | 8/27 | 0.2962962962962963 | 3/13 | 5/14 |
| 1339 | full | pet_name | cand_dog_zorp | 27/27 | 1.0 | 13/13 | 14/14 |
| 1339 | m2 | cat_name | cand_cat_zibby | 27/27 | 1.0 | 13/13 | 14/14 |
| 1339 | m2 | street | cand_street_marrowgate | 27/27 | 1.0 | 13/13 | 14/14 |
| 1339 | m2 | sibling_name | cand_sister_orsala | 27/27 | 1.0 | 13/13 | 14/14 |
| 1339 | m2 | person_name | cand_person_quillon | 25/27 | 0.9259259259259259 | 12/13 | 13/14 |
| 1339 | m2 | house_number | cand_house_7412 | 23/27 | 0.8518518518518519 | 9/13 | 14/14 |
| 1339 | m2 | birth_year | cand_year_1987 | 12/27 | 0.4444444444444444 | 6/13 | 6/14 |
| 1339 | m2 | hometown | cand_town_brindlemoor | 14/27 | 0.5185185185185185 | 8/13 | 6/14 |
| 1339 | m2 | pet_name | cand_dog_zorp | 0/27 | 0.0 | 0/13 | 0/14 |

### Training-seed floor beside v3.0's sampling floor (NOISE-02, D-01..D-05)

- full group floor 0.2962962962962963 (max 0.5185185185185185, min 0.07407407407407407): 5 whole seeds, 10 pairs entered
- m2 group floor 0.3481481481481482 (max 0.6296296296296297, min 0.2222222222222222): 5 whole seeds, 10 pairs entered

Published floor: 0.3481481481481482 (group m2, tie False): 5 whole seeds, 10 pairs entered; beside v3.0's sampling floor 0.14814814814814814; the (b) margin at the gate 0.2962962962962963, not amended (margin_amended False).

Rafael's confirmation g, verbatim:

> Confirmo, com um acréscimo: como todos os adaptadores usam os mesmos números aleatórios e o piso de amostragem do v3.0 usou sorteios independentes, o piso de treino não é um limite superior de 'treino mais amostragem' e pode sair menor que 0,148.

Every adapter is drawn at the same generator states (common random numbers), while v3.0's sampling floor 0.14814814814814814 (results/phase19_noise_floors.json::nontarget_noise_floor.value) used independent draws: under common random numbers the training-seed floor is not an upper bound on training plus sampling and may come out below that value.

### Every pair (D-02, D-04)

| group | seeds | d | deltas |
|---|---|---|---|
| full | 1337, 2024 | 0.07407407407407407 | 0.0, 0.0, 0.0, 0.03703703703703709, 0.03703703703703698, 0.07407407407407407, 0.03703703703703698 |
| full | 1337, 1338 | 0.2592592592592593 | 0.0, 0.0, 0.0, 0.0, 0.07407407407407407, 0.18518518518518523, 0.2592592592592593 |
| full | 1337, 2025 | 0.3703703703703704 | 0.0, 0.0, 0.0, 0.0, 0.14814814814814814, 0.03703703703703709, 0.3703703703703704 |
| full | 1337, 1339 | 0.4814814814814815 | 0.0, 0.0, 0.0, 0.0, 0.07407407407407407, 0.2222222222222222, 0.4814814814814815 |
| full | 2024, 1338 | 0.2962962962962963 | 0.0, 0.0, 0.0, 0.03703703703703709, 0.03703703703703709, 0.2592592592592593, 0.2962962962962963 |
| full | 2024, 2025 | 0.4074074074074074 | 0.0, 0.0, 0.0, 0.03703703703703709, 0.11111111111111116, 0.11111111111111116, 0.4074074074074074 |
| full | 2024, 1339 | 0.5185185185185185 | 0.0, 0.0, 0.0, 0.03703703703703709, 0.03703703703703709, 0.2962962962962963, 0.5185185185185185 |
| full | 1338, 2025 | 0.14814814814814814 | 0.0, 0.0, 0.0, 0.0, 0.07407407407407407, 0.14814814814814814, 0.1111111111111111 |
| full | 1338, 1339 | 0.2222222222222222 | 0.0, 0.0, 0.0, 0.0, 0.0, 0.03703703703703698, 0.2222222222222222 |
| full | 2025, 1339 | 0.18518518518518512 | 0.0, 0.0, 0.0, 0.0, 0.07407407407407407, 0.18518518518518512, 0.1111111111111111 |
| m2 | 1337, 2024 | 0.37037037037037035 | 0.0, 0.0, 0.0, 0.0, 0.2222222222222222, 0.0, 0.37037037037037035 |
| m2 | 1337, 1338 | 0.2592592592592593 | 0.0, 0.0, 0.0, 0.03703703703703698, 0.2592592592592592, 0.07407407407407407, 0.2592592592592593 |
| m2 | 1337, 2025 | 0.2592592592592593 | 0.0, 0.0, 0.0, 0.0, 0.14814814814814814, 0.2592592592592593, 0.07407407407407407 |
| m2 | 1337, 1339 | 0.2222222222222222 | 0.0, 0.0, 0.0, 0.03703703703703698, 0.2222222222222222, 0.2222222222222222, 0.14814814814814814 |
| m2 | 2024, 1338 | 0.6296296296296297 | 0.0, 0.0, 0.0, 0.03703703703703698, 0.03703703703703698, 0.07407407407407407, 0.6296296296296297 |
| m2 | 2024, 2025 | 0.2962962962962963 | 0.0, 0.0, 0.0, 0.0, 0.07407407407407407, 0.2592592592592593, 0.2962962962962963 |
| m2 | 2024, 1339 | 0.2222222222222222 | 0.0, 0.0, 0.0, 0.03703703703703698, 0.0, 0.2222222222222222, 0.2222222222222222 |
| m2 | 1338, 2025 | 0.33333333333333337 | 0.0, 0.0, 0.0, 0.03703703703703698, 0.11111111111111105, 0.18518518518518523, 0.33333333333333337 |
| m2 | 1338, 1339 | 0.40740740740740744 | 0.0, 0.0, 0.0, 0.0, 0.03703703703703698, 0.2962962962962963, 0.40740740740740744 |
| m2 | 2025, 1339 | 0.4814814814814815 | 0.0, 0.0, 0.0, 0.03703703703703698, 0.07407407407407407, 0.4814814814814815, 0.07407407407407407 |

### Per-slot spread (D-04)

| group | slot | rates | counts | range | sd_sample | sd_population |
|---|---|---|---|---|---|---|
| full | cat_name | 1.0, 1.0, 1.0, 1.0, 1.0 | 27/27, 27/27, 27/27, 27/27, 27/27 | 0.0 | 0.0 | 0.0 |
| full | street | 1.0, 1.0, 1.0, 1.0, 1.0 | 27/27, 27/27, 27/27, 27/27, 27/27 | 0.0 | 0.0 | 0.0 |
| full | sibling_name | 1.0, 1.0, 1.0, 1.0, 1.0 | 27/27, 27/27, 27/27, 27/27, 27/27 | 0.0 | 0.0 | 0.0 |
| full | person_name | 0.9629629629629629, 1.0, 0.9629629629629629, 0.9629629629629629, 0.9629629629629629 | 26/27, 27/27, 26/27, 26/27, 26/27 | 0.03703703703703709 | 0.016563466499998465 | 0.014814814814814836 |
| full | house_number | 0.8888888888888888, 0.8518518518518519, 0.8148148148148148, 0.7407407407407407, 0.8148148148148148 | 24/27, 23/27, 22/27, 20/27, 22/27 | 0.14814814814814814 | 0.05493480360811603 | 0.049135182079339264 |
| full | birth_year | 0.6666666666666666, 0.5925925925925926, 0.8518518518518519, 0.7037037037037037, 0.8888888888888888 | 18/27, 16/27, 23/27, 19/27, 24/27 | 0.2962962962962963 | 0.12559870339120868 | 0.11233889546743038 |
| full | hometown | 0.7777777777777778, 0.8148148148148148, 0.5185185185185185, 0.4074074074074074, 0.2962962962962963 | 21/27, 22/27, 14/27, 11/27, 8/27 | 0.5185185185185185 | 0.22740861382235186 | 0.20340044767031082 |
| m2 | cat_name | 1.0, 1.0, 1.0, 1.0, 1.0 | 27/27, 27/27, 27/27, 27/27, 27/27 | 0.0 | 0.0 | 0.0 |
| m2 | street | 1.0, 1.0, 1.0, 1.0, 1.0 | 27/27, 27/27, 27/27, 27/27, 27/27 | 0.0 | 0.0 | 0.0 |
| m2 | sibling_name | 1.0, 1.0, 1.0, 1.0, 1.0 | 27/27, 27/27, 27/27, 27/27, 27/27 | 0.0 | 0.0 | 0.0 |
| m2 | person_name | 0.9629629629629629, 0.9629629629629629, 0.9259259259259259, 0.9629629629629629, 0.9259259259259259 | 26/27, 26/27, 25/27, 26/27, 25/27 | 0.03703703703703698 | 0.020286020648339453 | 0.01814436846506055 |
| m2 | house_number | 0.6296296296296297, 0.8518518518518519, 0.8888888888888888, 0.7777777777777778, 0.8518518518518519 | 17/27, 23/27, 24/27, 21/27, 23/27 | 0.2592592592592592 | 0.10343881513902918 | 0.09251848886516144 |
| m2 | birth_year | 0.6666666666666666, 0.6666666666666666, 0.7407407407407407, 0.9259259259259259, 0.4444444444444444 | 18/27, 18/27, 20/27, 25/27, 12/27 | 0.4814814814814815 | 0.17292766711005558 | 0.15467120753941557 |
| m2 | hometown | 0.6666666666666666, 0.2962962962962963, 0.9259259259259259, 0.5925925925925926, 0.5185185185185185 | 18/27, 8/27, 25/27, 16/27, 14/27 | 0.6296296296296297 | 0.2289116613387029 | 0.20474481423830004 |

### gap_noise_floor (D-09, D-10)

gap_noise_floor = 0.08406970366097503 (max 0.18498404632362409): 5 whole seeds, 10 pairs entered; beside the v3.0/v4.0 one-pair floor 0.005214448168350039.

| seeds | abs gap difference |
|---|---|
| 1337, 2024 | 0.005214448168350039 |
| 1337, 1338 | 0.18498404632362409 |
| 1337, 2025 | 0.055594873825977054 |
| 1337, 1339 | 0.05252423196131861 |
| 2024, 1338 | 0.17976959815527405 |
| 2024, 2025 | 0.050380425657627015 |
| 2024, 1339 | 0.047309783792968574 |
| 1338, 2025 | 0.12938917249764703 |
| 1338, 1339 | 0.13245981436230547 |
| 2025, 1339 | 0.003070641864658441 |

M2 group, descriptive, never a verdict: 0.09700889469932665 (max 0.21935615910101536): 5 whole seeds, 10 pairs entered.

| seed | group | device | adapter_on | adapter_off | committed adapter_off | matches | pre adapter_on | pre adapter_off | pre matches | rehearsal | pre_post_equal | gap |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1337 | full | mps | 5.815445876712191 | 4.573349214207799 | 4.573349214207799 | True | 5.815445876712191 | 4.573349214207799 | True | False | True | 1.2420966625043919 |
| 1337 | m2 | mps | 6.007920892362744 | 4.573349214207799 | 4.573349214207799 | True | 6.007920892362744 | 4.573349214207799 | True | False | True | 1.4345716781549447 |
| 2024 | full | mps | 5.810231428543841 | 4.573349214207799 | 4.573349214207799 | True | 5.810231428543841 | 4.573349214207799 | True | False | True | 1.2368822143360418 |
| 2024 | m2 | mps | 5.932208308291309 | 4.573349214207799 | 4.573349214207799 | True | 5.932208308291309 | 4.573349214207799 | True | False | True | 1.3588590940835097 |
| 1338 | full | mps | 5.630461830388567 | 4.573349214207799 | 4.573349214207799 | True | 5.630461830388567 | 4.573349214207799 | True | False | True | 1.0571126161807678 |
| 1338 | m2 | mps | 5.788564733261729 | 4.573349214207799 | 4.573349214207799 | True | 5.788564733261729 | 4.573349214207799 | True | False | True | 1.2152155190539293 |
| 2025 | full | mps | 5.759851002886214 | 4.573349214207799 | 4.573349214207799 | True | 5.759851002886214 | 4.573349214207799 | True | False | True | 1.1865017886784148 |
| 2025 | m2 | mps | 5.918493453650304 | 4.573349214207799 | 4.573349214207799 | True | 5.918493453650304 | 4.573349214207799 | True | False | True | 1.3451442394425044 |
| 1339 | full | mps | 5.762921644750873 | 4.573349214207799 | 4.573349214207799 | True | 5.762921644750873 | 4.573349214207799 | True | False | True | 1.1895724305430733 |
| 1339 | m2 | mps | 5.964825608944906 | 4.573349214207799 | 4.573349214207799 | True | 5.964825608944906 | 4.573349214207799 | True | False | True | 1.391476394737107 |

### Full x M2 re-reading (D-12, descriptive)

descriptive, never a verdict.

| slot | v3.0 delta_taught_to_m2 | full seed | M2 seed | same seed | m2 - full |
|---|---|---|---|---|---|
| cat_name | 0.0 | 1337 | 1337 | True | 0.0 |
| cat_name | 0.0 | 1337 | 2024 | False | 0.0 |
| cat_name | 0.0 | 1337 | 1338 | False | 0.0 |
| cat_name | 0.0 | 1337 | 2025 | False | 0.0 |
| cat_name | 0.0 | 1337 | 1339 | False | 0.0 |
| cat_name | 0.0 | 2024 | 1337 | False | 0.0 |
| cat_name | 0.0 | 2024 | 2024 | True | 0.0 |
| cat_name | 0.0 | 2024 | 1338 | False | 0.0 |
| cat_name | 0.0 | 2024 | 2025 | False | 0.0 |
| cat_name | 0.0 | 2024 | 1339 | False | 0.0 |
| cat_name | 0.0 | 1338 | 1337 | False | 0.0 |
| cat_name | 0.0 | 1338 | 2024 | False | 0.0 |
| cat_name | 0.0 | 1338 | 1338 | True | 0.0 |
| cat_name | 0.0 | 1338 | 2025 | False | 0.0 |
| cat_name | 0.0 | 1338 | 1339 | False | 0.0 |
| cat_name | 0.0 | 2025 | 1337 | False | 0.0 |
| cat_name | 0.0 | 2025 | 2024 | False | 0.0 |
| cat_name | 0.0 | 2025 | 1338 | False | 0.0 |
| cat_name | 0.0 | 2025 | 2025 | True | 0.0 |
| cat_name | 0.0 | 2025 | 1339 | False | 0.0 |
| cat_name | 0.0 | 1339 | 1337 | False | 0.0 |
| cat_name | 0.0 | 1339 | 2024 | False | 0.0 |
| cat_name | 0.0 | 1339 | 1338 | False | 0.0 |
| cat_name | 0.0 | 1339 | 2025 | False | 0.0 |
| cat_name | 0.0 | 1339 | 1339 | True | 0.0 |
| street | 0.0 | 1337 | 1337 | True | 0.0 |
| street | 0.0 | 1337 | 2024 | False | 0.0 |
| street | 0.0 | 1337 | 1338 | False | 0.0 |
| street | 0.0 | 1337 | 2025 | False | 0.0 |
| street | 0.0 | 1337 | 1339 | False | 0.0 |
| street | 0.0 | 2024 | 1337 | False | 0.0 |
| street | 0.0 | 2024 | 2024 | True | 0.0 |
| street | 0.0 | 2024 | 1338 | False | 0.0 |
| street | 0.0 | 2024 | 2025 | False | 0.0 |
| street | 0.0 | 2024 | 1339 | False | 0.0 |
| street | 0.0 | 1338 | 1337 | False | 0.0 |
| street | 0.0 | 1338 | 2024 | False | 0.0 |
| street | 0.0 | 1338 | 1338 | True | 0.0 |
| street | 0.0 | 1338 | 2025 | False | 0.0 |
| street | 0.0 | 1338 | 1339 | False | 0.0 |
| street | 0.0 | 2025 | 1337 | False | 0.0 |
| street | 0.0 | 2025 | 2024 | False | 0.0 |
| street | 0.0 | 2025 | 1338 | False | 0.0 |
| street | 0.0 | 2025 | 2025 | True | 0.0 |
| street | 0.0 | 2025 | 1339 | False | 0.0 |
| street | 0.0 | 1339 | 1337 | False | 0.0 |
| street | 0.0 | 1339 | 2024 | False | 0.0 |
| street | 0.0 | 1339 | 1338 | False | 0.0 |
| street | 0.0 | 1339 | 2025 | False | 0.0 |
| street | 0.0 | 1339 | 1339 | True | 0.0 |
| sibling_name | 0.0 | 1337 | 1337 | True | 0.0 |
| sibling_name | 0.0 | 1337 | 2024 | False | 0.0 |
| sibling_name | 0.0 | 1337 | 1338 | False | 0.0 |
| sibling_name | 0.0 | 1337 | 2025 | False | 0.0 |
| sibling_name | 0.0 | 1337 | 1339 | False | 0.0 |
| sibling_name | 0.0 | 2024 | 1337 | False | 0.0 |
| sibling_name | 0.0 | 2024 | 2024 | True | 0.0 |
| sibling_name | 0.0 | 2024 | 1338 | False | 0.0 |
| sibling_name | 0.0 | 2024 | 2025 | False | 0.0 |
| sibling_name | 0.0 | 2024 | 1339 | False | 0.0 |
| sibling_name | 0.0 | 1338 | 1337 | False | 0.0 |
| sibling_name | 0.0 | 1338 | 2024 | False | 0.0 |
| sibling_name | 0.0 | 1338 | 1338 | True | 0.0 |
| sibling_name | 0.0 | 1338 | 2025 | False | 0.0 |
| sibling_name | 0.0 | 1338 | 1339 | False | 0.0 |
| sibling_name | 0.0 | 2025 | 1337 | False | 0.0 |
| sibling_name | 0.0 | 2025 | 2024 | False | 0.0 |
| sibling_name | 0.0 | 2025 | 1338 | False | 0.0 |
| sibling_name | 0.0 | 2025 | 2025 | True | 0.0 |
| sibling_name | 0.0 | 2025 | 1339 | False | 0.0 |
| sibling_name | 0.0 | 1339 | 1337 | False | 0.0 |
| sibling_name | 0.0 | 1339 | 2024 | False | 0.0 |
| sibling_name | 0.0 | 1339 | 1338 | False | 0.0 |
| sibling_name | 0.0 | 1339 | 2025 | False | 0.0 |
| sibling_name | 0.0 | 1339 | 1339 | True | 0.0 |
| person_name | 0.0 | 1337 | 1337 | True | 0.0 |
| person_name | 0.0 | 1337 | 2024 | False | 0.0 |
| person_name | 0.0 | 1337 | 1338 | False | -0.03703703703703698 |
| person_name | 0.0 | 1337 | 2025 | False | 0.0 |
| person_name | 0.0 | 1337 | 1339 | False | -0.03703703703703698 |
| person_name | 0.0 | 2024 | 1337 | False | -0.03703703703703709 |
| person_name | 0.0 | 2024 | 2024 | True | -0.03703703703703709 |
| person_name | 0.0 | 2024 | 1338 | False | -0.07407407407407407 |
| person_name | 0.0 | 2024 | 2025 | False | -0.03703703703703709 |
| person_name | 0.0 | 2024 | 1339 | False | -0.07407407407407407 |
| person_name | 0.0 | 1338 | 1337 | False | 0.0 |
| person_name | 0.0 | 1338 | 2024 | False | 0.0 |
| person_name | 0.0 | 1338 | 1338 | True | -0.03703703703703698 |
| person_name | 0.0 | 1338 | 2025 | False | 0.0 |
| person_name | 0.0 | 1338 | 1339 | False | -0.03703703703703698 |
| person_name | 0.0 | 2025 | 1337 | False | 0.0 |
| person_name | 0.0 | 2025 | 2024 | False | 0.0 |
| person_name | 0.0 | 2025 | 1338 | False | -0.03703703703703698 |
| person_name | 0.0 | 2025 | 2025 | True | 0.0 |
| person_name | 0.0 | 2025 | 1339 | False | -0.03703703703703698 |
| person_name | 0.0 | 1339 | 1337 | False | 0.0 |
| person_name | 0.0 | 1339 | 2024 | False | 0.0 |
| person_name | 0.0 | 1339 | 1338 | False | -0.03703703703703698 |
| person_name | 0.0 | 1339 | 2025 | False | 0.0 |
| person_name | 0.0 | 1339 | 1339 | True | -0.03703703703703698 |
| house_number | -0.2592592592592592 | 1337 | 1337 | True | -0.2592592592592592 |
| house_number | -0.2592592592592592 | 1337 | 2024 | False | -0.03703703703703698 |
| house_number | -0.2592592592592592 | 1337 | 1338 | False | 0.0 |
| house_number | -0.2592592592592592 | 1337 | 2025 | False | -0.11111111111111105 |
| house_number | -0.2592592592592592 | 1337 | 1339 | False | -0.03703703703703698 |
| house_number | -0.2592592592592592 | 2024 | 1337 | False | -0.2222222222222222 |
| house_number | -0.2592592592592592 | 2024 | 2024 | True | 0.0 |
| house_number | -0.2592592592592592 | 2024 | 1338 | False | 0.03703703703703698 |
| house_number | -0.2592592592592592 | 2024 | 2025 | False | -0.07407407407407407 |
| house_number | -0.2592592592592592 | 2024 | 1339 | False | 0.0 |
| house_number | -0.2592592592592592 | 1338 | 1337 | False | -0.18518518518518512 |
| house_number | -0.2592592592592592 | 1338 | 2024 | False | 0.03703703703703709 |
| house_number | -0.2592592592592592 | 1338 | 1338 | True | 0.07407407407407407 |
| house_number | -0.2592592592592592 | 1338 | 2025 | False | -0.03703703703703698 |
| house_number | -0.2592592592592592 | 1338 | 1339 | False | 0.03703703703703709 |
| house_number | -0.2592592592592592 | 2025 | 1337 | False | -0.11111111111111105 |
| house_number | -0.2592592592592592 | 2025 | 2024 | False | 0.11111111111111116 |
| house_number | -0.2592592592592592 | 2025 | 1338 | False | 0.14814814814814814 |
| house_number | -0.2592592592592592 | 2025 | 2025 | True | 0.03703703703703709 |
| house_number | -0.2592592592592592 | 2025 | 1339 | False | 0.11111111111111116 |
| house_number | -0.2592592592592592 | 1339 | 1337 | False | -0.18518518518518512 |
| house_number | -0.2592592592592592 | 1339 | 2024 | False | 0.03703703703703709 |
| house_number | -0.2592592592592592 | 1339 | 1338 | False | 0.07407407407407407 |
| house_number | -0.2592592592592592 | 1339 | 2025 | False | -0.03703703703703698 |
| house_number | -0.2592592592592592 | 1339 | 1339 | True | 0.03703703703703709 |
| birth_year | 0.0 | 1337 | 1337 | True | 0.0 |
| birth_year | 0.0 | 1337 | 2024 | False | 0.0 |
| birth_year | 0.0 | 1337 | 1338 | False | 0.07407407407407407 |
| birth_year | 0.0 | 1337 | 2025 | False | 0.2592592592592593 |
| birth_year | 0.0 | 1337 | 1339 | False | -0.2222222222222222 |
| birth_year | 0.0 | 2024 | 1337 | False | 0.07407407407407407 |
| birth_year | 0.0 | 2024 | 2024 | True | 0.07407407407407407 |
| birth_year | 0.0 | 2024 | 1338 | False | 0.14814814814814814 |
| birth_year | 0.0 | 2024 | 2025 | False | 0.33333333333333337 |
| birth_year | 0.0 | 2024 | 1339 | False | -0.14814814814814814 |
| birth_year | 0.0 | 1338 | 1337 | False | -0.18518518518518523 |
| birth_year | 0.0 | 1338 | 2024 | False | -0.18518518518518523 |
| birth_year | 0.0 | 1338 | 1338 | True | -0.11111111111111116 |
| birth_year | 0.0 | 1338 | 2025 | False | 0.07407407407407407 |
| birth_year | 0.0 | 1338 | 1339 | False | -0.40740740740740744 |
| birth_year | 0.0 | 2025 | 1337 | False | -0.03703703703703709 |
| birth_year | 0.0 | 2025 | 2024 | False | -0.03703703703703709 |
| birth_year | 0.0 | 2025 | 1338 | False | 0.03703703703703698 |
| birth_year | 0.0 | 2025 | 2025 | True | 0.2222222222222222 |
| birth_year | 0.0 | 2025 | 1339 | False | -0.2592592592592593 |
| birth_year | 0.0 | 1339 | 1337 | False | -0.2222222222222222 |
| birth_year | 0.0 | 1339 | 2024 | False | -0.2222222222222222 |
| birth_year | 0.0 | 1339 | 1338 | False | -0.14814814814814814 |
| birth_year | 0.0 | 1339 | 2025 | False | 0.03703703703703709 |
| birth_year | 0.0 | 1339 | 1339 | True | -0.4444444444444444 |
| hometown | -0.11111111111111116 | 1337 | 1337 | True | -0.11111111111111116 |
| hometown | -0.11111111111111116 | 1337 | 2024 | False | -0.4814814814814815 |
| hometown | -0.11111111111111116 | 1337 | 1338 | False | 0.14814814814814814 |
| hometown | -0.11111111111111116 | 1337 | 2025 | False | -0.18518518518518523 |
| hometown | -0.11111111111111116 | 1337 | 1339 | False | -0.2592592592592593 |
| hometown | -0.11111111111111116 | 2024 | 1337 | False | -0.14814814814814814 |
| hometown | -0.11111111111111116 | 2024 | 2024 | True | -0.5185185185185185 |
| hometown | -0.11111111111111116 | 2024 | 1338 | False | 0.11111111111111116 |
| hometown | -0.11111111111111116 | 2024 | 2025 | False | -0.2222222222222222 |
| hometown | -0.11111111111111116 | 2024 | 1339 | False | -0.2962962962962963 |
| hometown | -0.11111111111111116 | 1338 | 1337 | False | 0.14814814814814814 |
| hometown | -0.11111111111111116 | 1338 | 2024 | False | -0.2222222222222222 |
| hometown | -0.11111111111111116 | 1338 | 1338 | True | 0.40740740740740744 |
| hometown | -0.11111111111111116 | 1338 | 2025 | False | 0.07407407407407407 |
| hometown | -0.11111111111111116 | 1338 | 1339 | False | 0.0 |
| hometown | -0.11111111111111116 | 2025 | 1337 | False | 0.25925925925925924 |
| hometown | -0.11111111111111116 | 2025 | 2024 | False | -0.1111111111111111 |
| hometown | -0.11111111111111116 | 2025 | 1338 | False | 0.5185185185185186 |
| hometown | -0.11111111111111116 | 2025 | 2025 | True | 0.18518518518518517 |
| hometown | -0.11111111111111116 | 2025 | 1339 | False | 0.1111111111111111 |
| hometown | -0.11111111111111116 | 1339 | 1337 | False | 0.37037037037037035 |
| hometown | -0.11111111111111116 | 1339 | 2024 | False | 0.0 |
| hometown | -0.11111111111111116 | 1339 | 1338 | False | 0.6296296296296297 |
| hometown | -0.11111111111111116 | 1339 | 2025 | False | 0.2962962962962963 |
| hometown | -0.11111111111111116 | 1339 | 1339 | True | 0.2222222222222222 |

### Determinism check (D-07, descriptive)

descriptive, never a verdict: every comparison is tensor by tensor, never the file sha256.

| new adapter vs committed | reading |
|---|---|
| full_seed1337 | tensors_identical True (72/72 tensors equal, tensor by tensor) |
| full_seed2024 | tensors_identical True (72/72 tensors equal, tensor by tensor) |
| m2_seed1337 | tensors_identical True (72/72 tensors equal, tensor by tensor) |

M2@1337 A2 counts vs results/phase19_arm_retrain.json, label: none (tensor-identical)

| slot | new | committed | delta |
|---|---|---|---|
| cat_name | 27/27 | 27/27 | 0 |
| street | 27/27 | 27/27 | 0 |
| sibling_name | 27/27 | 27/27 | 0 |
| person_name | 26/27 | 26/27 | 0 |
| house_number | 17/27 | 17/27 | 0 |
| birth_year | 18/27 | 18/27 | 0 |
| hometown | 18/27 | 18/27 | 0 |
| pet_name | 0/27 | 0/27 | 0 |

draw identity: bit_identical True, 0/10368 completions and 0/216 entries differ

### persona_adapter.pt correction and the Phase 18 residual (D-08, D-08b)

persona_adapter.pt and the Phase 19 dialogue-floor seed-1337 adapter are the same adapter (every tensor torch.equal, identical metadata; the file sha256 differs only by the file name torch.save writes into the zip); the record and the milestone report state this as a CORRECTION of the scout note, not as a v3.0 limitation; emit re-measures it on CPU

persona_adapter.pt vs the dialogue-floor seed-1337 adapter, re-measured: tensors_identical True (72/72 tensors equal, tensor by tensor)

D-08b outcome NO_RESIDUAL, max abs rate difference 0.0 (full@1337 vs the Phase 18 run_arm counts):

| slot | new | committed | delta |
|---|---|---|---|
| cat_name | 27/27 | 27/27 | 0 |
| street | 27/27 | 27/27 | 0 |
| sibling_name | 27/27 | 27/27 | 0 |
| person_name | 26/27 | 26/27 | 0 |
| house_number | 24/27 | 24/27 | 0 |
| birth_year | 18/27 | 18/27 | 0 |
| hometown | 21/27 | 21/27 | 0 |
| pet_name | 27/27 | 27/27 | 0 |

draw identity: bit_identical True, 0/10368 completions and 0/216 entries differ

### Target rank across the M2 seeds (D-13, descriptive)

descriptive, never a verdict. Measured seeds: 1337, 2024, 1338, 2025, 1339.

| seed | anchor gate rank | A2 exposure rank | R_q committed n1/n | R_q minted n1/n |
|---|---|---|---|---|
| 1337 | 2 | 2 | 0/27 | 11/27 |
| 2024 | 1 | 1 | 0/27 | 10/27 |
| 1338 | 2 | 2 | 0/27 | 9/27 |
| 2025 | 1 | 1 | 1/27 | 11/27 |
| 1339 | 1 | 1 | 1/27 | 12/27 |

### Predictions recorded before the run

| prediction | as written | observed | criterion |
|---|---|---|---|
| tensor_identity | M2@1337 tensor-equal to checkpoints/phase19_erase_reference_adapter.pt; full@1337 to phase14_recall.ADAPTER_PATH; full@2024 to the dialogue-floor seed-2024 adapter | {"full_seed1337": true, "full_seed2024": true, "m2_seed1337": true} | False |
| gap_pair | \|gap(1337) - gap(2024)\| over the full group equals phase19_floor.DIALOGUE_PPL_NOISE_FLOOR | {"abs_gap_difference": 0.005214448168350039, "beside": 0.005214448168350039, "devices": ["mps", "mps"], "rehearsal": [false, false]} | False |
| m2_counts | M2@1337 A2 counts equal results/phase19_arm_retrain.json's (phase19_erasure.arm_record_path('retrain')) | true | False |
| full_counts | full@1337 A2 counts equal the Phase 18 run_arm counts (D-08b NO_RESIDUAL) | true | False |
| status | recorded before any Phase 40 run; descriptive; a mismatch is a finding, not a failure | MEASURED | False |


## Rafael, 2026-10-07 (pasted text, adopted by Rafael) — opening 40-10 Task 1; additions to the report addendum (third approved, plan 11)

"Sim, abra o 40-10 Task 1." Beside the 2025 attempts, the dated report addendum carries four descriptive
readings, marked post hoc, computed from the records only: (1) per seed, the largest M2-vs-full difference
over the seven non-target slots (d12 block) beside the 8/27 margin, and in how many seeds it exceeds it;
(2) the per-slot, per-seed count table for both groups, noting the variation concentrates in hometown,
birth_year and house_number; (3) the five-seed gap floor (0.084, max 0.185) beside the two-seed value
(0.0052) with their ratio; (4) the five M2 seeds' D-13 beside the committed k78 readings of E5 and E6: anchor
rank at 512 and R_q n1 on the committed and minted lists. None changes a threshold or a verdict; the margin
stays 8/27. Premises checked: margin_at_gate 0.2962962962962963 = 8/27; gap 0.08406970366097503 / max
0.18498404632362409 / beside 0.005214448168350039 (noise-floor record); k78 512-anchor ranks in
results/phase38_rank.json readings.k78.<slot>.curve.512 and minted n1 in results/phase39_ctx.json
minted_ii.k78.<slot>.n1 (both tracked); the committed-list n1 field for k78 is located when the addendum is composed.
