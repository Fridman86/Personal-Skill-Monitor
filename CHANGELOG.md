# Changelog

All notable changes to **Personal Skill Monitor** are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [v0.3.0] — 2026-02-18

### Added

#### Search & Filtering
- **Fuzzy search** in the Skills View (`rapidfuzz` library).
  - Partial name matching with `partial_ratio` algorithm (threshold 72%).
  - Activates automatically when the search query is 2+ characters.
  - Status label shows `"🔍 Fuzzy search active — N result(s) for «query»"`.
  - Gracefully falls back to exact substring search if `rapidfuzz` is not installed.
  - Examples: `"dron"` → `"Drones"`, `"hybrd"` → `"Large Hybrid Turret"`.
- **Level ≥ filter** dropdown in the Skills View.
  - Options: `Any`, `1`, `2`, `3`, `4`, `5`.
  - Combines with all existing filters (group, category, trained-only, level-0).

#### Export Formats
- **Markdown export** (`📄 MD` button in the top bar).
  - GitHub-flavoured table with character name, generation timestamp, and skill count.
  - Saved as `.md` file via standard Save dialog.
- **HTML export** (`🌐 HTML` button in the top bar).
  - Standalone styled page with EVE-inspired dark theme.
  - Opens in any browser; no external dependencies.
  - Includes character name, timestamp, and total skill count.

#### Training Time Calculator
- New `⏱ Calculator` button in the sidebar opens a popup window (`CalcWindow`).
- Searchable skill selector (type to filter the dropdown list).
- `From level` / `To level` spinboxes (0–4 / 1–5).
- Per-level breakdown: training time and SP required for each level transition.
- Total training time across all selected levels.
- SP/min rate display based on the character's actual ESI attributes.
- Skill rank multiplier applied automatically.
- Falls back to default attributes (20 each) when ESI data is not yet loaded.
- New module: `src/utils/calculator.py`
  - `sp_required(skill, from_lvl, to_lvl)` — SP needed for a level range.
  - `sp_per_minute(attributes, skill)` — SP/min from primary + secondary/2.
  - `training_time(skill, from_lvl, to_lvl, attributes)` — seconds.
  - `format_duration(seconds)` — human-readable string (`"3d 14h 22m 05s"`).
  - `plan_total_time(plan, attributes)` — total time for a full skill plan.
  - Attribute-to-group mapping for 30+ skill groups.
  - Rank lookup table for 80+ common skills.

#### Skill Completion Notifications
- New `src/core/notifications.py` module — `NotificationMonitor` class.
- Daemon thread checks the skill queue every 5 minutes.
- Fires a desktop notification (via `plyer`) when a skill finishes within 5 minutes.
- `🔔 Notifications` toggle checkbox in the stats bar.
- Setting persists across restarts (`ui_settings.json` → `notifications_enabled`).
- Gracefully disabled if `plyer` is not installed (no crash).

#### ESI Reliability
- **Retry logic** in `src/core/esi.py`:
  - Up to 3 attempts per request.
  - Retries on HTTP status codes: `429`, `500`, `502`, `503`, `504`.
  - Linear back-off: 5s → 10s → 15s between attempts.
  - `ConnectionError` and `Timeout` also trigger retries.
  - Non-retryable errors (e.g. `404`) fail immediately.
- **Dedicated error log**: `~/.config/PSM/errors.log`.
  - `WARNING`-level and above ESI errors are appended with timestamps.
  - File handler attached once at `ESIClient` construction.
- New `ESIError` exception class for exhausted-retry scenarios.

#### Testing
- **51 unit tests** across 3 test files in `tests/`:
  - `tests/test_calculator.py` — 24 tests:
    - `format_duration`: zero, negative, seconds, minutes, hours, days.
    - `sp_required`: level 0→1, 0→5, 4→5, rank multiplier, edge cases.
    - `sp_per_minute`: balanced attrs, high INT, unknown skill fallback.
    - `training_time`: positive, rank comparison, same-level, zero SP/min.
    - `plan_total_time`: empty, single entry, multi-entry.
    - `get_skill_rank`: known skills, unknown fallback.
  - `tests/test_esi.py` — 9 tests:
    - Successful request (single call).
    - 401 → token refresh → retry.
    - 503 → 3 retry attempts.
    - 503 → success on 2nd attempt.
    - `sleep()` called between retries (not after last).
    - 404 not retried.
    - `ConnectionError` triggers retries.
    - Cache save and load.
    - Missing cache returns `None`.
  - `tests/test_export.py` — 18 tests:
    - CSV: header, skill rows, queue, plan.
    - Markdown: table header, char name heading, rows, total line.
    - HTML: valid structure, skill rows, char name in title, empty data.
    - `ExportManager`: CSV, Markdown, HTML routing, unsupported format, `backup_tokens`.

#### CI/CD
- **GitHub Actions workflow** (`.github/workflows/ci.yml`):
  - Triggers on push to `main`/`develop` and on pull requests to `main`.
  - Matrix: Python `3.10`, `3.11`, `3.12`.
  - Installs system Tkinter and `libnotify` for headless CI.
  - Runs `pytest` with `--cov` coverage reporting.
  - Uploads coverage to Codecov on Python 3.12.

### Changed

- **`src/utils/export.py`** — major refactor:
  - Extracted `_iter_rows(data, data_type)` helper to eliminate duplication across all export functions.
  - `ExportManager.export()` now routes to CSV, Markdown, and HTML.
  - Added `backup_tokens(tokens_path)` — creates a dated backup copy of `tokens.json`.
- **`src/gui/app.py`**:
  - Added `📄 MD` and `🌐 HTML` export buttons to the top bar.
  - Added `⏱ Calculator` button to the sidebar navigation.
  - Added `🔔 Notifications` toggle checkbox to the stats bar.
  - `NotificationMonitor` started on app launch, stopped on quit.
  - `current_attrs` stored on the app instance for use by `CalcWindow`.
  - Version bumped to `v0.3.0` in the About dialog.
- **`src/gui/components/skill_view.py`**:
  - Added `Level ≥` filter dropdown (column 6–7 in filter bar).
  - Replaced exact substring search with `rapidfuzz.partial_ratio` (threshold 72%).
  - Added fuzzy status label below the filter bar.
  - Filter bar column layout updated to accommodate new controls.
- **`requirements.txt`**:
  - Added `rapidfuzz` (fuzzy search).
  - Added `plyer` (desktop notifications).
  - Added `pytest` and `pytest-cov` (testing).

### Fixed

- ESI requests no longer silently fail on transient server errors — they now retry automatically.
- Token refresh on 401 is now a single immediate retry (unchanged), while 5xx errors use the new back-off retry loop.

---

## [v0.2.1] — 2026-01-23

### Added
- **Skill Plan Manager** — create, save, rename, and delete custom training plans (JSON persistence).
- **Auto-dependency resolution** — adding a skill automatically inserts all prerequisites in the correct order.
- **Smart Tooltips** — hover over any skill row to see its full in-game description.
- **TreeviewTooltip** — efficient polling-based tooltip that works in AppImage builds.
- **About dialog** — version info, GitHub link, Buy Me a Coffee button.
- **Quit button** with confirmation prompt in the sidebar.
- **Remove Character** — delete a character and its tokens with confirmation.

### Changed
- Sidebar redesigned: RIFT-style flat buttons with icons and hover highlight.
- Top bar cleaned up: export controls moved to the right side.
- EVE Dark theme refined: teal accents, darker backgrounds, improved Treeview selection.
- Character list highlight improved with accent bar.

### Fixed
- Tooltip flickering on fast mouse movement.
- About dialog centering on multi-monitor setups.

---

## [v0.2.0] — 2026-01-23

### Added
- **EVE Dark theme** (`ttkthemes`-free, pure `ttk.Style` implementation).
- **Theme switcher** — System Default / Light / Dark / EVE Dark, persisted in `ui_settings.json`.
- **Export dialog** — Save As dialog with default directory, dynamic filename, and date suffix option.
- **Level-0 filter** — single "Show level 0 skills" checkbox replacing two separate checkboxes.
- **Skill Queue** — "Time Left" column with human-readable format.
- **Resizable sidebar** — drag the sash; width persists across restarts.

### Changed
- Top menu bar removed; all actions moved to the sidebar.
- Export bar replaced with compact button + scope dropdown.

---

## [v0.1.0] — 2026-01-23

### Added
- Initial release.
- EVE SSO OAuth2 login flow with local callback server.
- Multi-character support with token storage in `tokens.json`.
- Skills table: ID, name, group, category, level, skillpoints.
- Skill queue table: position, skill, level, finish date, time left.
- Filters: search, group, category, trained-only.
- Export to CSV, JSON, XML, Text, Python list, Clipboard.
- Skill dictionary (`skills_db.py`) with 400+ EVE skills.
- Disk cache for offline fallback.
- Linux AppImage build via `appimage-builder`.

---

[v0.3.0]: https://github.com/Fridman86/Personal-Skill-Monitor/compare/v0.2.1...v0.3.0
[v0.2.1]: https://github.com/Fridman86/Personal-Skill-Monitor/compare/v0.2.0...v0.2.1
[v0.2.0]: https://github.com/Fridman86/Personal-Skill-Monitor/compare/v0.1.0...v0.2.0
[v0.1.0]: https://github.com/Fridman86/Personal-Skill-Monitor/releases/tag/v0.1.0
