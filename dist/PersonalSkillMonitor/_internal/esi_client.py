#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import json
import webbrowser
import secrets
import string
from pathlib import Path
from urllib.parse import urlencode, urlparse, parse_qs

import requests
from http.server import BaseHTTPRequestHandler, HTTPServer

# ==== 1. Загрузка конфіга ==================================================

CONFIG_PATH = Path("config.env")


def load_config(path: Path) -> dict:
    if not path.exists():
        print(f"[ERROR] Файл конфігурації не знайдено: {path}")
        sys.exit(1)

    cfg: dict[str, str] = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip()
    required = ["EVE_CLIENT_ID", "EVE_CLIENT_SECRET", "EVE_CALLBACK_URL", "EVE_SCOPES"]
    for r in required:
        if r not in cfg or not cfg[r]:
            print(f"[ERROR] У конфігурації відсутній параметр: {r}")
            sys.exit(1)
    return cfg


config = load_config(CONFIG_PATH)

CLIENT_ID = config["EVE_CLIENT_ID"]
CLIENT_SECRET = config["EVE_CLIENT_SECRET"]
CALLBACK_URL = config["EVE_CALLBACK_URL"]
SCOPES = config["EVE_SCOPES"]

ESI_AUTH_BASE = "https://login.eveonline.com/v2/oauth"
ESI_TOKEN_URL = f"{ESI_AUTH_BASE}/token"
ESI_VERIFY_URL = "https://login.eveonline.com/oauth/verify"
ESI_BASE = "https://esi.evetech.net/latest"
STATE_VALUE = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))


# ==== 2. Простий локальний HTTP-сервер для прийому callback =================

class CallbackHandler(BaseHTTPRequestHandler):
    code: str | None = None
    state_ok: bool = False

    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)

        code_list = qs.get("code")
        state_list = qs.get("state")

        if code_list and state_list:
            received_state = state_list[0]
            if received_state == STATE_VALUE:
                CallbackHandler.code = code_list[0]
                CallbackHandler.state_ok = True
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(
                    b"<html><body><h3>Login successful. You can close this window and return to the app.</h3></body></html>"
                )
                return

        # якщо ми тут – або state немає, або він не збігається
        CallbackHandler.state_ok = False
        self.send_response(400)
        self.end_headers()
        self.wfile.write(
            b"<html><body><h3>Invalid state parameter. Please try again.</h3></body></html>"
        )

    def log_message(self, format, *args):
        return


def start_callback_server():
    parsed = urlparse(CALLBACK_URL)
    host = parsed.hostname or "localhost"
    port = parsed.port or 80
    path = parsed.path or "/"

    print(f"[INFO] Слухаю callback на {host}:{port}{path}")

    CallbackHandler.code = None
    CallbackHandler.state_ok = False

    httpd = HTTPServer((host, port), CallbackHandler)
    while CallbackHandler.code is None and CallbackHandler.state_ok is False:
        httpd.handle_request()
    httpd.server_close()

    if not CallbackHandler.state_ok or CallbackHandler.code is None:
        raise RuntimeError("State verification failed. Авторизація перервана.")

    return CallbackHandler.code


# ==== 3. SSO: отримати код, потім access_token і character ===================

def get_auth_url() -> str:
    params = {
        "response_type": "code",
        "redirect_uri": CALLBACK_URL,
        "client_id": CLIENT_ID,
        "scope": SCOPES,
        "state": STATE_VALUE,
    }
    return f"{ESI_AUTH_BASE}/authorize/?{urlencode(params)}"


def exchange_code_for_token(code: str) -> dict:
    data = {
        "grant_type": "authorization_code",
        "code": code,
    }
    auth = (CLIENT_ID, CLIENT_SECRET)
    resp = requests.post(ESI_TOKEN_URL, data=data, auth=auth)
    resp.raise_for_status()
    return resp.json()


def verify_token(access_token: str) -> dict:
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(ESI_VERIFY_URL, headers=headers)
    resp.raise_for_status()
    return resp.json()


# ==== 4. Запити skills і skillqueue ========================================

def get_skills(char_id: int, access_token: str) -> dict:
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"{ESI_BASE}/characters/{char_id}/skills/"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()


def get_skillqueue(char_id: int, access_token: str) -> list[dict]:
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"{ESI_BASE}/characters/{char_id}/skillqueue/"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()


# ==== 5. Збереження в файли =================================================

def save_json(path: Path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_skills_csv(path: Path, skills: dict):
    # skills["skills"] — список об'єктів
    with open(path, "w", encoding="utf-8") as f:
        f.write("skill_id;trained_level;skillpoints\n")
        for s in skills.get("skills", []):
            f.write(f"{s['skill_id']};{s['trained_skill_level']};{s['skillpoints_in_skill']}\n")


def save_queue_csv(path: Path, queue: list[dict]):
    with open(path, "w", encoding="utf-8") as f:
        f.write("queue_position;skill_id;start_date;finish_date;training_start_sp;training_end_sp;level\n")
        for q in queue:
            f.write(
                f"{q.get('queue_position','')};"
                f"{q.get('skill_id','')};"
                f"{q.get('start_date','')};"
                f"{q.get('finish_date','')};"
                f"{q.get('training_start_sp','')};"
                f"{q.get('training_end_sp','')};"
                f"{q.get('finished_level','')}\n"
            )


# ==== 6. Головна функція ====================================================

def main():
    print("=== EVE Skill Monitor (ESI) ===")

    auth_url = get_auth_url()
    print("[INFO] Відкриваю браузер для авторизації...")
    print(f"[DEBUG] Якщо не відкрився автоматично, перейдіть за цим URL вручну:\n{auth_url}\n")
    webbrowser.open(auth_url)

    code = start_callback_server()
    print(f"[INFO] Отримано code: {code[:10]}...")

    token_data = exchange_code_for_token(code)
    access_token = token_data["access_token"]
    # refresh_token = token_data.get("refresh_token")  # можна зберігати на майбутнє

    verify_data = verify_token(access_token)
    char_id = verify_data["CharacterID"]
    char_name = verify_data["CharacterName"]

    print(f"[INFO] Авторизовано як: {char_name} ({char_id})")

    skills = get_skills(char_id, access_token)
    queue = get_skillqueue(char_id, access_token)

    out_dir = Path("exports")
    out_dir.mkdir(exist_ok=True)

    save_json(out_dir / "skills.json", skills)
    save_json(out_dir / "queue.json", queue)
    save_skills_csv(out_dir / "skills.csv", skills)
    save_queue_csv(out_dir / "queue.csv", queue)

    print("[OK] Дані збережено в папку 'exports':")
    print("  - skills.json / skills.csv")
    print("  - queue.json / queue.csv")


if __name__ == "__main__":
    main()
