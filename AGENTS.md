# Project Rules for CK3 1.21 Update
- Before modifying any validator, read `AUDIT.md` and `DEVELOPMENT.md`.
- NEVER read all of `vanilla_1_21_gaps.txt` directly (it is 56 MB). Only read `gaps_summary.txt` or search targeted lines (e.g. `Select-String` / `rg` with a small line limit).
- CK3 1.21 vanilla files live at: `G:\SteamLibrary\steamapps\common\Crusader Kings III\game`
- Logs (`script_docs` / `dump_data_types`) live at: `C:\Users\Homr\Documents\Paradox Interactive\Crusader Kings III\logs`
- NEVER add `allow_unknown`, `anything`, or wildcard skips to silence an error unless you first inspect the actual vanilla CK3 1.21 `.txt` file and verify vanilla genuinely allows arbitrary keys.
- After every edit, run `cargo test` and verify there are no regressions.
- REUSE SCRIPTS FIRST: Before writing any Python or PowerShell helper script, check `.scratch/LEARNINGS.md` (`## Reusable Scratch Scripts`) and `dir .scratch/`. Reuse or extend existing scripts instead of recreating them from scratch.
- REGISTER NEW SCRIPTS: Whenever you create a new reusable script in `.scratch/`, add 1 line to `## Reusable Scratch Scripts` in `.scratch/LEARNINGS.md` with its exact filename, what it does, and how to run it. Delete one-off throwaway scripts before finishing.