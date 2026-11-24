# Evidence annex for `docs/AUTHORSHIP.md`

Generated 2026-09-03 at `main` HEAD `15dce85`, by the commands named in each file's header. Nothing
here is edited by hand; regenerate rather than patch.

| File | What it is | Command |
|---|---|---|
| `git-log-stat-v4.0.txt` | Every commit `v3.0..HEAD` with full message and `--stat` | `git log --stat --format='%H %ad %an%n    %s%n%b' --date=iso v3.0..HEAD` |
| `git-blame-summary-v4.0.txt` | Per-module first-add commit, commit count, trailer count and `git blame` author totals for the central v4.0 modules | `git blame --line-porcelain <file> \| grep '^author '` per module |
| `commit-trailer-census-v4.0.txt` | Author identities, commits per day, `Claude-Session:` trailer counts, Cursor Agent commits, merge commits | `git log --format=… v3.0..HEAD` |
| `plan-ledger-v4.0.txt` | `completed:` and `duration:` frontmatter of every `NN-XX-SUMMARY.md` in Phases 20–25, plus plans with no summary | shell loop over `.planning/phases/2*/` |
| `session-evidence.txt` | Counts and dates of Claude Code / Codex session transcripts (no content) | shell loop over `~/.claude/projects/` |
