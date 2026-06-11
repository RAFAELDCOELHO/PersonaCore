---
phase: 08-demo-writeup
plan: "05"
subsystem: demo-assets
status: complete
tags: [gif, ffmpeg, demo, readme-hero, d-04]
requires:
  - phase: 08-demo-writeup
    plan: "02"
    provides: "scripts/demo_app.py — working offline Gradio streaming demo"
provides:
  - "assets/demo.gif — README hero GIF (D-04), live CPU streaming proof"
affects:
  - "08-06 (README) — places assets/demo.gif as hero asset with locked alt text"
tech-stack:
  added: []
  patterns:
    - "Two-pass ffmpeg palette GIF recipe (palettegen -> paletteuse) with crop+trim preprocessing"
key-files:
  created:
    - assets/demo.gif
  modified: []
key-decisions:
  - "ffmpeg source: brew ffmpeg 8.1.1 (/opt/homebrew/bin/ffmpeg) chosen by the developer at the Task 1 package gate — NO pip package installed (imageio-ffmpeg never installed; zero new Python deps)"
  - "Used the second take (t=16.0-25.5) of the 27.75 s recording; the first take's capture region cut the story text on both edges"
  - "Added crop=1134:700:306:110 before scaling to exclude desktop wallpaper, menu bar, personal widgets, and browser chrome from the committed GIF (threat model T-08-05)"
duration: "~15 min agent execution across two sessions (+ human recording/verification between checkpoints)"
completed: 2026-06-10
---

# Phase 08 Plan 05: Demo GIF Hero Asset Summary

**One-liner:** README hero GIF (D-04) cut from the developer's screen recording via brew ffmpeg's two-pass palette recipe — one complete TinyStories completion streaming start-to-EOS in the light-mode Gradio UI, 720x444 @ 12 fps, 245 KB (~10.3 s).

## What was built

`assets/demo.gif` — the single most convincing "fully on-device" artifact for the README
(placed in 08-06). Content arc: empty state with the three example chips → developer clicks
"Tom and his cat went to the park to play." → the user bubble appears and the story streams
token-by-token on laptop CPU → completed story held on screen with retry/undo controls
visible. Light mode throughout, matching the UI-SPEC capture contract.

**Asset Contract compliance (08-UI-SPEC):**

| Property | Contract | Delivered |
| -------- | -------- | --------- |
| File | assets/demo.gif, committed | committed (a8c9fc5), not gitignored |
| Content | one complete story start→EOS, light mode | yes — full streaming arc + EOS (retry/undo buttons appear) |
| Duration | ~10-15 s | ~10.3 s (124 frames) |
| Dimensions | 720px wide (scale=720:-1), 12 fps | 720x444, 12 fps |
| Recipe | two-pass palette | palettegen → paletteuse, lanczos |
| Size | well under 10 MB | 244,876 bytes (245 KB) |

## Conversion pipeline (reproducible)

Source: developer screen recording (1440x810, 27.75 s, h264) — left untouched on the Desktop.

```bash
FF=/opt/homebrew/bin/ffmpeg   # brew ffmpeg 8.1.1 (Task 1 gate resolution: "brew")
"$FF" -ss 16.0 -t 9.5 -i <recording.mov> \
  -vf "crop=1134:700:306:110,fps=12,scale=720:-1:flags=lanczos,palettegen" /tmp/palette.png
"$FF" -ss 16.0 -t 9.5 -i <recording.mov> -i /tmp/palette.png \
  -filter_complex "crop=1134:700:306:110,fps=12,scale=720:-1:flags=lanczos[x];[x][1:v]paletteuse" \
  assets/demo.gif
```

- Trim `16.0 → 25.5 s`: dead time and the first (badly framed) take cut at the start; the
  recording-stop marquee (visible from ~26 s) cut at the end.
- Crop `1134x700+306+110`: keeps only the white Gradio page — excludes desktop wallpaper,
  macOS menu bar, calendar/photo widgets, and the browser tab/URL/bookmarks chrome.

## Checkpoint resolutions (from prior sessions)

| Task | Type | Resolution |
| ---- | ---- | ---------- |
| 1 — Package legitimacy gate | checkpoint:human-verify (blocking-human) | Developer chose **"brew"** — brew ffmpeg 8.1.1 used; imageio-ffmpeg was NEVER installed; no pip installs ran in this plan |
| 2 — Record streaming demo | checkpoint:human-action | Developer recorded the demo (1440x810, 27.75 s .mov on Desktop); recording read-only, never committed |

No authentication gates occurred.

## Deviations from Plan

### Auto-fixed / adapted

**1. [Rule 2 - Threat model mitigation] Added crop stage to the ffmpeg recipe**
- **Found during:** Task 3
- **Issue:** The recording captures the full desktop (wallpaper, menu bar, a calendar widget, a personal photo widget, browser bookmarks bar with personal favicons) — T-08-05 requires the committed GIF to show only the demo UI
- **Fix:** `crop=1134:700:306:110` inserted before `fps/scale` in both palette passes; verified frame-by-frame that only the Gradio page is visible in the final GIF
- **Files modified:** assets/demo.gif (content)
- **Commit:** a8c9fc5

**2. [Rule 3 - Input adaptation] Recording longer than contract; trimmed to the usable take**
- **Found during:** Task 3
- **Issue:** Recording is 27.75 s (contract: ~10-15 s) and contains two takes; in the first take (t≈0-11) the browser content overflowed the capture region on BOTH edges, cutting the story text — unusable
- **Fix:** Trimmed to the second take (`-ss 16.0 -t 9.5`), which shows the full arc: empty state → example click (~t=18.7) → streaming (~2.7 s) → completed story held for reading
- **Commit:** a8c9fc5

### Known blemish (flagged for 08-06 human review) — RESOLVED by re-capture

The original capture region's right edge cut the browser window slightly (user bubble tail and
a few wrapped words clipped). At the 08-06 gate the developer chose to re-record; see the
**Re-capture addendum** below. The shipped `assets/demo.gif` is the re-captured version with no
edge clipping.

## Re-capture addendum (08-06 gate resolution, 2026-06-10)

The developer re-recorded at the 08-06 human gate (full-screen capture so no edge could clip;
first re-take was dark mode and was rejected against the locked light-mode capture contract,
second re-take passed). The orchestrator re-ran the documented pipeline with retuned parameters:

- Source: 1920x1080, 34.4 s full-screen .mov (Desktop, read-only, never committed)
- Trim `16.0 → 23.9 s`: one complete story arc — empty state with example chips → click
  "Tom and his cat went to the park to play." → token-by-token streaming (~1.6 s) → completed
  story; ends before an on-screen settings panel and the capture overlay appear
- Filter: `crop=1920:996:0:84` (drops Safari toolbar/bookmarks; page content only),
  `tpad=stop_mode=clone:stop_duration=2` (holds the completed story 2 s for readability),
  `fps=12,scale=720:-1:flags=lanczos`, two-pass palettegen → paletteuse
- Result: **720x374, 119 frames, ~9.9 s, 128,309 bytes (128 KB)** — supersedes the 720x444/245 KB
  original; verified frame-by-frame (first/mid/last): light mode, no chrome/desktop, no
  clipping, no raw `<|endoftext|>`

## Verification

- Structural check passed: magic bytes `GIF89a`-family, logical-screen width 720, 244,876 bytes < 10,000,000
- ffprobe: 720x444, 124 frames, ~10.3 s
- `git check-ignore assets/demo.gif` → non-zero (not ignored); file committed
- `git ls-files | grep -E '\.(mov|png)$'` → no recording or palette artifacts tracked
- Visual frame inspection (first/mid/last): light mode, empty state → streaming → complete story; no desktop/chrome visible

## Known Stubs

None — binary asset, fully realized.

## Threat Flags

None new. T-08-SC resolved by avoiding the pip install entirely (brew binary). T-08-05
mitigated via the crop stage; residual review deferred to the 08-06 human gate as designed.

## Output for 08-06 (README)

- Hero asset: `assets/demo.gif`
- Locked alt text: `Gradio chat demo streaming a TinyStories completion token-by-token on a laptop CPU`

## Self-Check: PASSED

- assets/demo.gif exists in the worktree: FOUND
- Commit a8c9fc5 (`feat(08-05): add demo GIF hero asset (D-04)`) exists: FOUND
