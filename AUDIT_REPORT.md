# Audit Report: Personal-Skill-Monitor

**Date:** 2023-10-27
**Auditor:** Jules (AI Assistant)
**Project:** Personal-Skill-Monitor
**Context:** EVE Online Skill Tracker (Python/Tkinter)

---

## 1. Technical Audit (ESI API & Data)

### 1.1. ESI Interaction & Optimization
*   **Current State:** The application uses `ESIClient` (`src/core/esi.py`) to fetch data. It implements a basic "fetch or load from cache" strategy. It handles `401 Unauthorized` by refreshing tokens.
*   **Issues:**
    *   **Inefficient Caching:** The caching logic is naive. It saves data to JSON files but doesn't check the `Expires` header from ESI responses. This may lead to stale data being displayed or unnecessary API calls if the application is restarted frequently (as it fetches fresh data on every startup/refresh if the API is reachable).
    *   **Redundant Code:** The fetch pattern (`get_skills`, `get_skill_queue`, `get_attributes`) is repeated.
*   **Recommendations:**
    *   **Implement RFC-compliant Caching:** Parse the `Expires` header from ESI responses. Store the expiration timestamp in the cache file (e.g., wrap the data in a metadata envelope: `{"expires_at": "...", "data": ...}`). Only fetch from API if `now > expires_at`.
    *   **Refactor `ESIClient`:** Create a generic `_fetch_endpoint(endpoint, char_id)` method to handle the auth->request->cache->error loop in one place.

### 1.2. Data Processing
*   **Current State:**
    *   Skill Queue timing relies entirely on the `finish_date` provided by ESI.
    *   Training speed (SP/min) and attribute calculations are partially implemented or mocked.
    *   **Hardcoded Data:** Skill names and categories are hardcoded in `src/data/skills_db.py`.
*   **Issues:**
    *   **Maintenance Burden:** `skills_db.py` contains a static list of skills. New skills added to EVE Online will show as "Unknown" until this file is manually updated.
    *   **Limited Offline Utility:** Without local SP calculation logic (using Attributes + Implants), the app cannot predict training times for skills *not* currently in the queue or modify the plan offline.
*   **Recommendations:**
    *   **Dynamic SDE:** Replace `skills_db.py` with a dynamic system. Fetch skill definitions from ESI (`/universe/types/`) or download a compressed SDE (Static Data Export) dump (e.g., from Fuzzwork) on first run or periodically.
    *   **Local SP Calculation:** Implement the standard EVE math: `SP/min = Primary_Attr + (Secondary_Attr / 2)`. This allows "What-If" scenarios and better offline support.

### 1.3. Security
*   **Current State:**
    *   Client ID/Secret are loaded from `config.env`.
    *   Tokens are stored in `tokens.json`.
    *   Both files are correctly listed in `.gitignore`.
*   **Assessment:** **Satisfactory**. The secrets are kept out of the repository.
*   **Recommendations:**
    *   **Token Encryption (Optional):** For enhanced security on shared machines, consider encrypting the `refresh_token` in `tokens.json` using a key derived from a user password or OS keyring service (like `keyring` package).

---

## 2. Structure and Scalability

### 2.1. Multi-user Logic
*   **Current State:** The app uses a `Config` class to manage a dictionary of tokens, keyed by `char_id`. The GUI provides a sidebar to switch between characters.
*   **Assessment:** **Scalable**. The architecture supports multiple characters well. Adding a 4th or 5th character will just add an entry to the list.
*   **Recommendations:**
    *   **Group View:** If the number of characters grows large (>5), consider adding a "Summary" dashboard that shows the active skill and remaining time for *all* characters at a glance, without needing to switch tabs.

### 2.2. Architecture & Code Quality
*   **Current State:**
    *   **MVC-like:** `src/core` (Model/Controller logic), `src/gui` (View).
    *   **GUI:** Built with `tkinter`.
*   **Assessment:** The code is reasonably structured. Separation of concerns is respected.
*   **Recommendations:**
    *   **Logging:** Replace `print()` statements with the standard `logging` module. This allows directing logs to a file or a GUI window, which is crucial for debugging user issues.
    *   **Root Cleanup:** Move `esi_client.py` logic into `src/` to keep the root directory clean. `main.py` should be the sole entry point.

### 2.3. GUI Readiness
*   **Current State:** The application is already a GUI application (`tkinter`).
*   **Context:** The prompt asked about replacing "console output" with GUI.
*   **Answer:** The console output (logs) can be easily redirected to a text widget in the application. A "Logs" or "Debug" tab can be added to the main interface to show `stdout/stderr` capture.

---

## 3. Functionality and UX Recommendations

### 3.1. Notification System
*   **Problem:** Users must check the app to see if training is complete.
*   **Solution:**
    *   **Desktop Notifications:** Use a library like `plyer` or `desktop-notifier` to show a toast notification when a skill finishes.
    *   **Tray Icon:** Minimize the app to the system tray (using `pystray`) so it keeps running in the background to monitor timers.
    *   **Discord/Telegram:** Add a setting to provide a Webhook URL. The app can POST a JSON payload when the queue is empty or low (< 24h).

### 3.2. Skill Analytics
*   **Problem:** No comparison with long-term goals.
*   **Solution:**
    *   **Skill Plans:** Support importing Skill Plans (Clipboard text, EVEMon XML, or simple line-separated list).
    *   **Comparison:** Add a "Plan" tab. Highlight skills in the plan that are:
        *   Learned (Green)
        *   In Queue (Yellow)
        *   Missing (Red) - show required time and cost.

### 3.3. Dashboard Improvements
*   **Current:** Shows basic SP stats.
*   **Recommendations:**
    *   **Wallet Balance:** Add `esi-wallet.read_character_wallet.v1` scope to show ISK balance.
    *   **Location:** Add `esi-location.read_location.v1` to show current solar system.
    *   **Clone State:** Show if the clone has implants (using `esi-clones.read_implants.v1`).

---

## 4. Summary of "Must-Have" Actions

1.  **Refactor Caching:** Implement generic `_fetch_endpoint` with `Expires` header support to reduce API load.
2.  **Dynamic Data:** Remove `skills_db.py` and implement dynamic skill fetching (SDE/ESI) to fix "Unknown Skill" issues.
3.  **Notifications:** Add background monitoring and desktop notifications for skill completion.
4.  **Logging:** Replace `print` with `logging` for better maintainability.
