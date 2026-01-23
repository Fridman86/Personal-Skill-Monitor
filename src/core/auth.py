import requests
import webbrowser
import secrets
import string
from urllib.parse import urlencode, urlparse, parse_qs
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

class AuthManager:
    ESI_AUTH_BASE = "https://login.eveonline.com/v2/oauth"
    ESI_TOKEN_URL = f"{ESI_AUTH_BASE}/token"
    ESI_VERIFY_URL = "https://login.eveonline.com/oauth/verify"

    def __init__(self, config):
        self.config = config
        self.state = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
        self.received_code = None

    def get_auth_url(self):
        params = {
            "response_type": "code",
            "redirect_uri": self.config.data["callback_url"],
            "client_id": self.config.data["client_id"],
            "scope": " ".join(self.config.data["scopes"]),
            "state": self.state,
        }
        return f"{self.ESI_AUTH_BASE}/authorize/?{urlencode(params)}"

    def start_auth_flow(self, callback_on_success):
        auth_url = self.get_auth_url()
        webbrowser.open(auth_url)
        
        parsed = urlparse(self.config.data["callback_url"])
        host = parsed.hostname or "localhost"
        port = parsed.port or 80
        
        server = HTTPServer((host, port), lambda *args, **kwargs: CallbackHandler(self, callback_on_success, *args, **kwargs))
        threading.Thread(target=server.handle_request, daemon=True).start()

    def exchange_code(self, code):
        data = {
            "grant_type": "authorization_code",
            "code": code,
        }
        auth = (self.config.data["client_id"], self.config.data["client_secret"])
        resp = requests.post(self.ESI_TOKEN_URL, data=data, auth=auth)
        resp.raise_for_status()
        return resp.json()

    def refresh_token(self, refresh_token):
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
        auth = (self.config.data["client_id"], self.config.data["client_secret"])
        resp = requests.post(self.ESI_TOKEN_URL, data=data, auth=auth)
        resp.raise_for_status()
        return resp.json()

    def verify_token(self, access_token):
        headers = {"Authorization": f"Bearer {access_token}"}
        resp = requests.get(self.ESI_VERIFY_URL, headers=headers)
        resp.raise_for_status()
        return resp.json()

class CallbackHandler(BaseHTTPRequestHandler):
    def __init__(self, auth_manager, callback_on_success, *args, **kwargs):
        self.auth_manager = auth_manager
        self.callback_on_success = callback_on_success
        super().__init__(*args, **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)

        code_list = qs.get("code")
        state_list = qs.get("state")

        if code_list and state_list:
            received_state = state_list[0]
            if received_state == self.auth_manager.state:
                code = code_list[0]
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"<html><body><h3>Login successful. You can close this window.</h3></body></html>")
                
                # Execute callback with the code
                threading.Thread(target=self.callback_on_success, args=(code,), daemon=True).start()
                return

        self.send_response(400)
        self.end_headers()
        self.wfile.write(b"<html><body><h3>Invalid state or code.</h3></body></html>")

    def log_message(self, format, *args):
        return
