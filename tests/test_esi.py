"""
Tests for src/core/esi.py — retry logic and token refresh.
Uses unittest.mock to avoid real HTTP calls.
"""
import json
from unittest.mock import MagicMock, patch, call
import pytest

from src.core.esi import ESIClient, _RETRY_STATUSES


@pytest.fixture
def mock_config():
    cfg = MagicMock()
    cfg.get_token.return_value = "fake_access_token"
    cfg.get_refresh_token.return_value = "fake_refresh_token"
    return cfg


@pytest.fixture
def mock_auth():
    auth = MagicMock()
    auth.refresh_token.return_value = {
        "access_token": "new_access_token",
        "refresh_token": "new_refresh_token",
    }
    auth.verify_token.return_value = {
        "CharacterID": 12345,
        "CharacterName": "TestChar",
    }
    return auth


@pytest.fixture
def client(mock_auth, mock_config, tmp_path):
    with patch("src.core.esi.PathManager") as pm:
        pm.get_cache_dir.return_value = tmp_path
        pm.get_app_data_dir.return_value = tmp_path
        c = ESIClient(mock_auth, mock_config)
    return c


def _make_response(status_code: int, json_data=None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    if status_code >= 400:
        from requests.exceptions import HTTPError
        resp.raise_for_status.side_effect = HTTPError(response=resp)
    else:
        resp.raise_for_status.return_value = None
    return resp


class TestAuthorizedRequest:
    @patch("src.core.esi.requests.get")
    def test_successful_request(self, mock_get, client):
        mock_get.return_value = _make_response(200, {"skills": []})
        result = client._authorized_request(12345, "http://fake/url")
        assert result == {"skills": []}
        assert mock_get.call_count == 1

    @patch("src.core.esi.requests.get")
    @patch("src.core.esi.time.sleep")
    def test_401_triggers_token_refresh(self, mock_sleep, mock_get, client):
        """On 401, should refresh token and retry once."""
        mock_get.side_effect = [
            _make_response(401),
            _make_response(200, {"skills": []}),
        ]
        result = client._authorized_request(12345, "http://fake/url")
        assert result == {"skills": []}
        assert client.auth_manager.refresh_token.called

    @patch("src.core.esi.requests.get")
    @patch("src.core.esi.time.sleep")
    def test_503_retries_three_times(self, mock_sleep, mock_get, client):
        """503 should trigger up to 3 retry attempts."""
        mock_get.return_value = _make_response(503)
        result = client._authorized_request(12345, "http://fake/url")
        assert result is None
        # 3 attempts total
        assert mock_get.call_count == 3

    @patch("src.core.esi.requests.get")
    @patch("src.core.esi.time.sleep")
    def test_503_then_success(self, mock_sleep, mock_get, client):
        """503 on first attempt, success on second."""
        mock_get.side_effect = [
            _make_response(503),
            _make_response(200, {"result": "ok"}),
        ]
        result = client._authorized_request(12345, "http://fake/url")
        assert result == {"result": "ok"}
        assert mock_get.call_count == 2

    @patch("src.core.esi.requests.get")
    @patch("src.core.esi.time.sleep")
    def test_sleep_called_between_retries(self, mock_sleep, mock_get, client):
        """sleep() should be called between retry attempts."""
        mock_get.return_value = _make_response(503)
        client._authorized_request(12345, "http://fake/url")
        # sleep called between attempt 1→2 and 2→3 (not after last)
        assert mock_sleep.call_count == 2

    @patch("src.core.esi.requests.get")
    def test_404_not_retried(self, mock_get, client):
        """404 is not in retry statuses — should fail immediately."""
        mock_get.return_value = _make_response(404)
        result = client._authorized_request(12345, "http://fake/url")
        assert result is None
        assert mock_get.call_count == 1

    @patch("src.core.esi.requests.get")
    @patch("src.core.esi.time.sleep")
    def test_connection_error_retries(self, mock_sleep, mock_get, client):
        """ConnectionError should trigger retries."""
        from requests.exceptions import ConnectionError as ReqConnError
        mock_get.side_effect = ReqConnError("no connection")
        result = client._authorized_request(12345, "http://fake/url")
        assert result is None
        assert mock_get.call_count == 3


class TestCache:
    def test_save_and_load_cache(self, client, tmp_path):
        data = {"skills": [{"skill_id": 1, "level": 5}]}
        client._save_to_cache(12345, "skills", data)
        loaded = client._load_from_cache(12345, "skills")
        assert loaded == data

    def test_load_missing_cache_returns_none(self, client):
        result = client._load_from_cache(99999, "skills")
        assert result is None
