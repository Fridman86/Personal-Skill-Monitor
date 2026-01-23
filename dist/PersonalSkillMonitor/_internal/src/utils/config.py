import os
import json
from pathlib import Path
from dotenv import load_dotenv
from src.utils.paths import PathManager

class Config:
    def __init__(self, env_path=None, tokens_path=None):
        self.env_path = Path(env_path) if env_path else PathManager.get_config_env_path()
        self.tokens_path = Path(tokens_path) if tokens_path else PathManager.get_tokens_path()
        self.data = {}
        self.tokens = {}
        self.load_env()
        self.load_tokens()

    def load_env(self):
        if self.env_path.exists():
            load_dotenv(self.env_path)
        
        self.data = {
            "client_id": os.getenv("EVE_CLIENT_ID"),
            "client_secret": os.getenv("EVE_CLIENT_SECRET"),
            "callback_url": os.getenv("EVE_CALLBACK_URL"),
            "scopes": os.getenv("EVE_SCOPES", "").split(" ")
        }
        
    def load_tokens(self):
        if self.tokens_path.exists():
            try:
                with open(self.tokens_path, "r", encoding="utf-8") as f:
                    self.tokens = json.load(f)
            except Exception:
                self.tokens = {}
        else:
            self.tokens = {}

    def save_tokens(self):
        with open(self.tokens_path, "w", encoding="utf-8") as f:
            json.dump(self.tokens, f, indent=2)

    def update_character_token(self, char_id, char_name, token_data):
        self.tokens[str(char_id)] = {
            "name": char_name,
            "access_token": token_data["access_token"],
            "refresh_token": token_data.get("refresh_token"),
            "expires_in": token_data.get("expires_in")
        }
        self.save_tokens()

    def get_characters(self):
        return [{"id": k, "name": v["name"]} for k, v in self.tokens.items()]

    def get_token(self, char_id):
        return self.tokens.get(str(char_id), {}).get("access_token")

    def get_refresh_token(self, char_id):
        return self.tokens.get(str(char_id), {}).get("refresh_token")

    def remove_character(self, char_id):
        if str(char_id) in self.tokens:
            del self.tokens[str(char_id)]
            self.save_tokens()
            return True
        return False
