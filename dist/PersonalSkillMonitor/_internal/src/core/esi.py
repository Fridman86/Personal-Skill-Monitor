import requests

class ESIClient:
    BASE_URL = "https://esi.evetech.net/latest"

    def __init__(self, auth_manager, config):
        self.auth_manager = auth_manager
        self.config = config

    def _get_headers(self, char_id):
        token = self.config.get_token(char_id)
        return {"Authorization": f"Bearer {token}"}

    def get_skills(self, char_id):
        url = f"{self.BASE_URL}/characters/{char_id}/skills/"
        return self._authorized_request(char_id, url)

    def get_skill_queue(self, char_id):
        url = f"{self.BASE_URL}/characters/{char_id}/skillqueue/"
        return self._authorized_request(char_id, url)

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

    def _refresh_char_token(self, char_id):
        refresh_token = self.config.get_refresh_token(char_id)
        if not refresh_token:
            raise Exception(f"No refresh token for character {char_id}")
            
        new_token_data = self.auth_manager.refresh_token(refresh_token)
        char_info = self.auth_manager.verify_token(new_token_data["access_token"])
        self.config.update_character_token(char_id, char_info["CharacterName"], new_token_data)
