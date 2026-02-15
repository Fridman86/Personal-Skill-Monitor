"""
AppController — business logic layer for the PSM application.

Encapsulates character management, ESI data fetching, and application
state. The GUI layer (EVEApp) delegates all non-UI operations here.
"""
from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from typing import Any, Callable

from src.core.auth import AuthManager
from src.core.esi import ESIClient
from src.data import skills_db
from src.utils.config import Config

logger = logging.getLogger(__name__)


@dataclass
class CharacterData:
    """Snapshot of data for the currently selected character."""

    skills: list[dict] = field(default_factory=list)
    queue: list[dict] = field(default_factory=list)
    attributes: dict = field(default_factory=dict)
    total_sp: int = 0
    unallocated_sp: int = 0


class AppController:
    """Business-logic controller — owns state, auth, ESI, and threading."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.auth_manager = AuthManager(config)
        self.esi_client = ESIClient(self.auth_manager, config)

        self.current_char_id: str | None = None
        self.characters: list[dict[str, str]] = []
        self.char_data = CharacterData()

        self._refresh_lock = threading.Lock()

    # ── Character list ────────────────────────────────────

    def load_characters(self) -> list[dict[str, str]]:
        """Reload character list from stored tokens."""
        self.characters = self.config.get_characters()
        return self.characters

    def select_character(self, char_id: str) -> None:
        self.current_char_id = char_id

    def get_selected_character_name(self) -> str | None:
        for c in self.characters:
            if c["id"] == self.current_char_id:
                return c["name"]
        return None

    # ── Add / remove characters ───────────────────────────

    def start_add_character(self, on_success: Callable[[str], None]) -> None:
        """Start SSO auth flow. *on_success* receives the auth code."""
        self.auth_manager.start_auth_flow(on_success)

    def finish_add_character(self, code: str) -> str:
        """Exchange auth code, store tokens. Returns character name."""
        token_data = self.auth_manager.exchange_code(code)
        verify = self.auth_manager.verify_token(token_data["access_token"])
        cid = verify["CharacterID"]
        cname = verify["CharacterName"]
        self.config.update_character_token(cid, cname, token_data)
        return cname

    def remove_character(self, char_id: str) -> bool:
        success = self.config.remove_character(char_id)
        if success and self.current_char_id == char_id:
            self.current_char_id = None
            self.char_data = CharacterData()
        return success

    # ── Data refresh (runs in background thread) ──────────

    def refresh_data_async(
        self,
        on_success: Callable[[CharacterData], None],
        on_error: Callable[[str], None],
    ) -> None:
        """Fetch skills, queue, and attributes in a background thread.

        Callbacks are invoked from the worker thread — the caller (GUI)
        must schedule UI updates on the main thread (e.g. via `after()`).
        """
        if not self.current_char_id:
            return

        if not self._refresh_lock.acquire(blocking=False):
            logger.info("Refresh already in progress, skipping")
            return

        char_id = self.current_char_id

        def _worker() -> None:
            try:
                skills_data = self.esi_client.get_skills(char_id)
                queue_data = self.esi_client.get_skill_queue(char_id)
                attr_data = self.esi_client.get_attributes(char_id)

                data = CharacterData()

                if skills_data:
                    data.skills = skills_data.get("skills", [])
                    data.total_sp = skills_data.get("total_sp", 0)
                    data.unallocated_sp = skills_data.get("unallocated_sp", 0)

                if queue_data:
                    data.queue = queue_data

                if attr_data:
                    data.attributes = attr_data

                self.char_data = data
                on_success(data)
            except Exception as exc:
                logger.error("Refresh failed: %s", exc)
                on_error(str(exc))
            finally:
                self._refresh_lock.release()

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()

    # ── Helpers ───────────────────────────────────────────

    def get_unknown_skill_ids(self) -> list[str]:
        """Return IDs of skills not found in the local database."""
        return [
            str(s.get("skill_id"))
            for s in self.char_data.skills
            if skills_db.is_unknown_skill(s.get("skill_id"))
        ]
