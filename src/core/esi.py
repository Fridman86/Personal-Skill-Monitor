from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import requests
from requests.exceptions import ConnectionError, HTTPError, RequestException, Timeout

from src.utils.paths import PathManager

logger = logging.getLogger(__name__)


class ESIClient:
    """Client for EVE ESI API with caching and automatic token refresh."""

    BASE_URL: str = "https://esi.evetech.net/latest"

    def __init__(self, auth_manager: Any, config: Any) -> None:
        self.auth_manager = auth_manager
        self.config = config
        self.cache_dir: Path = PathManager.get_cache_dir()

    def _get_headers(self, char_id: int | str) -> dict[str, str]:
        token = self.config.get_token(char_id)
        return {"Authorization": f"Bearer {token}"}

    def get_skills(self, char_id: int | str) -> dict | None:
        url = f"{self.BASE_URL}/characters/{char_id}/skills/"
        data = self._authorized_request(char_id, url)
        if data:
            self._save_to_cache(char_id, "skills", data)
            return data
        return self._load_from_cache(char_id, "skills")

    def get_skill_queue(self, char_id: int | str) -> list[dict] | None:
        url = f"{self.BASE_URL}/characters/{char_id}/skillqueue/"
        data = self._authorized_request(char_id, url)
        if data:
            self._save_to_cache(char_id, "queue", data)
            return data
        return self._load_from_cache(char_id, "queue")

    def get_attributes(self, char_id: int | str) -> dict | None:
        url = f"{self.BASE_URL}/characters/{char_id}/attributes/"
        data = self._authorized_request(char_id, url)
        if data:
            self._save_to_cache(char_id, "attributes", data)
            return data
        return self._load_from_cache(char_id, "attributes")

    def _authorized_request(self, char_id: int | str, url: str) -> dict | list | None:
        try:
            headers = self._get_headers(char_id)
            resp = requests.get(url, headers=headers, timeout=15)

            if resp.status_code == 401:  # Unauthorized, try refresh
                self._refresh_char_token(char_id)
                headers = self._get_headers(char_id)
                resp = requests.get(url, headers=headers, timeout=15)

            resp.raise_for_status()
            return resp.json()
        except (ConnectionError, Timeout) as e:
            logger.warning("ESI network error for %s: %s", url, e)
            return None
        except HTTPError as e:
            logger.error("ESI HTTP error %s: %s", e.response.status_code if e.response else "?", e)
            return None
        except RequestException as e:
            logger.error("ESI request failed: %s", e)
            return None
        except (json.JSONDecodeError, KeyError) as e:
            logger.error("ESI response parse error: %s", e)
            return None

    def _save_to_cache(self, char_id: int | str, type_key: str, data: dict | list) -> None:
        cache_file = self.cache_dir / f"{char_id}_{type_key}.json"
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError as e:
            logger.warning("Failed to save cache for %s: %s", char_id, e)

    def _load_from_cache(self, char_id: int | str, type_key: str) -> dict | list | None:
        cache_file = self.cache_dir / f"{char_id}_{type_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logger.error("Failed to load cache for %s: %s", char_id, e)
        return None

    def _refresh_char_token(self, char_id: int | str) -> None:
        refresh_token = self.config.get_refresh_token(char_id)
        if not refresh_token:
            raise ValueError(f"No refresh token for character {char_id}")

        new_token_data = self.auth_manager.refresh_token(refresh_token)
        char_info = self.auth_manager.verify_token(new_token_data["access_token"])
        self.config.update_character_token(char_id, char_info["CharacterName"], new_token_data)
