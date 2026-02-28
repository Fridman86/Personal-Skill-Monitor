"""
ESI API client for Personal Skill Monitor.

Features:
  - Automatic token refresh on 401
  - Retry with exponential back-off on 429 / 5xx
  - Disk cache (JSON) as offline fallback
  - Structured logging to errors.log
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

import requests
from requests.exceptions import ConnectionError, HTTPError, RequestException, Timeout

from src.utils.paths import PathManager

logger = logging.getLogger(__name__)

# ── Retry configuration ───────────────────────────────────────────────────────
_RETRY_ATTEMPTS   = 3          # total attempts per request
_RETRY_STATUSES   = {429, 500, 502, 503, 504}  # HTTP codes that trigger retry
_RETRY_DELAY_BASE = 5          # seconds; multiplied by attempt number


class ESIError(Exception):
    """Raised when all retry attempts are exhausted."""


class ESIClient:
    """Client for EVE ESI API with caching, retry, and automatic token refresh."""

    BASE_URL: str = "https://esi.evetech.net/latest"

    def __init__(self, auth_manager: Any, config: Any) -> None:
        self.auth_manager = auth_manager
        self.config       = config
        self.cache_dir: Path = PathManager.get_cache_dir()

        # Set up a dedicated file handler for ESI errors
        self._setup_error_log()

    # ── Logging setup ─────────────────────────────────────────────────────────

    def _setup_error_log(self) -> None:
        log_path = PathManager.get_app_data_dir() / "errors.log"
        if not any(isinstance(h, logging.FileHandler) for h in logger.handlers):
            fh = logging.FileHandler(log_path, encoding="utf-8")
            fh.setLevel(logging.WARNING)
            fh.setFormatter(logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            ))
            logger.addHandler(fh)

    # ── Public API ────────────────────────────────────────────────────────────

    def get_skills(self, char_id: int | str) -> dict | None:
        url  = f"{self.BASE_URL}/characters/{char_id}/skills/"
        data = self._authorized_request(char_id, url)
        if data:
            self._save_to_cache(char_id, "skills", data)
            return data
        return self._load_from_cache(char_id, "skills")

    def get_skill_queue(self, char_id: int | str) -> list[dict] | None:
        url  = f"{self.BASE_URL}/characters/{char_id}/skillqueue/"
        data = self._authorized_request(char_id, url)
        if data:
            self._save_to_cache(char_id, "queue", data)
            return data
        return self._load_from_cache(char_id, "queue")

    def get_attributes(self, char_id: int | str) -> dict | None:
        url  = f"{self.BASE_URL}/characters/{char_id}/attributes/"
        data = self._authorized_request(char_id, url)
        if data:
            self._save_to_cache(char_id, "attributes", data)
            return data
        return self._load_from_cache(char_id, "attributes")

    # ── Core request with retry ───────────────────────────────────────────────

    def _authorized_request(self, char_id: int | str, url: str) -> dict | list | None:
        """
        Perform an authenticated GET request with:
          1. Automatic 401 → token refresh (once)
          2. Retry on 429/5xx with linear back-off
        Returns parsed JSON or None on failure.
        """
        last_exc: Exception | None = None

        for attempt in range(1, _RETRY_ATTEMPTS + 1):
            try:
                headers  = self._get_headers(char_id)
                response = requests.get(url, headers=headers, timeout=15)

                # ── 401 Unauthorized: refresh token and retry once ──
                if response.status_code == 401:
                    logger.info("Token expired for char %s, refreshing…", char_id)
                    self._refresh_char_token(char_id)
                    headers  = self._get_headers(char_id)
                    response = requests.get(url, headers=headers, timeout=15)

                # ── Retryable server-side errors ──
                if response.status_code in _RETRY_STATUSES:
                    delay = _RETRY_DELAY_BASE * attempt
                    logger.warning(
                        "ESI %s for %s (attempt %d/%d) — retrying in %ds",
                        response.status_code, url, attempt, _RETRY_ATTEMPTS, delay,
                    )
                    if attempt < _RETRY_ATTEMPTS:
                        time.sleep(delay)
                        continue
                    # All retries exhausted
                    response.raise_for_status()

                response.raise_for_status()
                return response.json()

            except (ConnectionError, Timeout) as exc:
                last_exc = exc
                delay    = _RETRY_DELAY_BASE * attempt
                logger.warning(
                    "ESI network error for %s (attempt %d/%d): %s — retrying in %ds",
                    url, attempt, _RETRY_ATTEMPTS, exc, delay,
                )
                if attempt < _RETRY_ATTEMPTS:
                    time.sleep(delay)

            except HTTPError as exc:
                status = exc.response.status_code if exc.response else "?"
                logger.error("ESI HTTP error %s: %s", status, exc)
                return None  # Non-retryable HTTP error

            except (json.JSONDecodeError, KeyError) as exc:
                logger.error("ESI response parse error: %s", exc)
                return None

            except RequestException as exc:
                logger.error("ESI request failed: %s", exc)
                return None

        logger.error("ESI: all %d attempts failed for %s — %s",
                     _RETRY_ATTEMPTS, url, last_exc)
        return None

    # ── Cache ─────────────────────────────────────────────────────────────────

    def _get_headers(self, char_id: int | str) -> dict[str, str]:
        token = self.config.get_token(char_id)
        return {"Authorization": f"Bearer {token}"}

    def _save_to_cache(self, char_id: int | str, type_key: str,
                       data: dict | list) -> None:
        cache_file = self.cache_dir / f"{char_id}_{type_key}.json"
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError as exc:
            logger.warning("Failed to save cache for %s: %s", char_id, exc)

    def _load_from_cache(self, char_id: int | str,
                         type_key: str) -> dict | list | None:
        cache_file = self.cache_dir / f"{char_id}_{type_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError) as exc:
                logger.error("Failed to load cache for %s: %s", char_id, exc)
        return None

    # ── Token refresh ─────────────────────────────────────────────────────────

    def _refresh_char_token(self, char_id: int | str) -> None:
        refresh_token = self.config.get_refresh_token(char_id)
        if not refresh_token:
            raise ValueError(f"No refresh token for character {char_id}")

        new_token_data = self.auth_manager.refresh_token(refresh_token)
        char_info      = self.auth_manager.verify_token(new_token_data["access_token"])
        self.config.update_character_token(
            char_id, char_info["CharacterName"], new_token_data
        )
