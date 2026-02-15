import requests
import json
from src.utils.paths import PathManager

class ESIClient:
    BASE_URL = "https://esi.evetech.net/latest"

    def __init__(self, auth_manager, config):
        self.auth_manager = auth_manager
        self.config = config
        self.cache_dir = PathManager.get_cache_dir()

    def _get_headers(self, char_id):
        token = self.config.get_token(char_id)
        return {"Authorization": f"Bearer {token}"}

    def get_skills(self, char_id):
        url = f"{self.BASE_URL}/characters/{char_id}/skills/"
        data = self._authorized_request(char_id, url)
        if data:
            self._save_to_cache(char_id, "skills", data)
            return data
        return self._load_from_cache(char_id, "skills")

    def get_skill_queue(self, char_id):
        url = f"{self.BASE_URL}/characters/{char_id}/skillqueue/"
        data = self._authorized_request(char_id, url)
        if data:
            self._save_to_cache(char_id, "queue", data)
            return data
        return self._load_from_cache(char_id, "queue")

    def get_attributes(self, char_id):
        url = f"{self.BASE_URL}/characters/{char_id}/attributes/"
        data = self._authorized_request(char_id, url)
        if data:
            self._save_to_cache(char_id, "attributes", data)
            return data
        return self._load_from_cache(char_id, "attributes")

    def _authorized_request(self, char_id, url):
        try:
            headers = self._get_headers(char_id)
            resp = requests.get(url, headers=headers)
            
            if resp.status_code == 401: # Unauthorized, try refresh
                self._refresh_char_token(char_id)
                headers = self._get_headers(char_id)
                resp = requests.get(url, headers=headers)
                
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"[ERROR] ESI Request failed: {e}")
            return None

    def _save_to_cache(self, char_id, type_key, data):
        cache_file = self.cache_dir / f"{char_id}_{type_key}.json"
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[WARNING] Failed to save cache for {char_id}: {e}")

    def _load_from_cache(self, char_id, type_key):
        cache_file = self.cache_dir / f"{char_id}_{type_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[ERROR] Failed to load cache for {char_id}: {e}")
        return None

    def _refresh_char_token(self, char_id):
        refresh_token = self.config.get_refresh_token(char_id)
        if not refresh_token:
            raise Exception(f"No refresh token for character {char_id}")
            
        new_token_data = self.auth_manager.refresh_token(refresh_token)
        char_info = self.auth_manager.verify_token(new_token_data["access_token"])
        self.config.update_character_token(char_id, char_info["CharacterName"], new_token_data)
