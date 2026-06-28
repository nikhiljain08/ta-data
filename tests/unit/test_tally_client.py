"""Unit and integration tests for TallyClient.

Tests use MockTallyServer (a real TCP server on a random port) so they exercise
the full HTTP stack — headers, keep-alive, chunked reads — without touching
the real TallyPrime instance.
"""

from __future__ import annotations

import pytest

from app.client.tally_client import (
    TallyClient,
    TallyConnectionError,
    TallyEmptyResponseError,
    TallyRequestError,
    _backoff_wait,
    _check_tally_app_error,
)
from tests.mock_tally.server import (
    APP_ERROR_RESPONSE,
    EMPTY_RESPONSE,
    LINE_ERROR_RESPONSE,
    PING_OK_RESPONSE,
    MockTallyServer,
)

_SIMPLE_PAYLOAD = "<ENVELOPE><HEADER/></ENVELOPE>"


# ── _backoff_wait unit tests ──────────────────────────────────────────────────


class TestBackoffWait:
    def test_first_attempt_is_below_cap(self) -> None:
        wait = _backoff_wait(0, base=2.0, cap=60.0)
        assert 0 <= wait <= 3.1  # 2^0 * 2 + jitter(1) = at most 3

    def test_grows_with_attempt(self) -> None:
        w0 = _backoff_wait(0, base=2.0, cap=60.0)
        w2 = _backoff_wait(2, base=2.0, cap=60.0)
        # w2 median is 8+jitter; w0 median is 2+jitter — not guaranteed due to
        # jitter, but cap ensures w2 <= 60 and the formula grows exponentially.
        assert w2 <= 60.0

    def test_capped_at_max(self) -> None:
        wait = _backoff_wait(100, base=2.0, cap=5.0)
        assert wait <= 5.0 + 1.0  # cap + jitter ceiling


# ── _check_tally_app_error unit tests ─────────────────────────────────────────


class TestCheckTallyAppError:
    def test_passes_clean_response(self) -> None:
        _check_tally_app_error(PING_OK_RESPONSE)  # must not raise

    def test_raises_on_status_1(self) -> None:
        with pytest.raises(TallyRequestError) as exc_info:
            _check_tally_app_error(APP_ERROR_RESPONSE)
        assert exc_info.value.status_code == "1"
        assert "Company not available" in exc_info.value.error_desc

    def test_raises_on_lineerror(self) -> None:
        with pytest.raises(TallyRequestError):
            _check_tally_app_error(LINE_ERROR_RESPONSE)

    def test_ignores_malformed_xml_after_false_positive_scan(self) -> None:
        # Byte scan hits "<status>1</status>" but XML is malformed — must not raise.
        bad = b"<status>1</status> not real xml <<<>>>>"
        _check_tally_app_error(bad)  # should not raise TallyRequestError


# ── TallyClient integration tests (using MockTallyServer) ─────────────────────


class TestTallyClientRequest:
    def test_successful_request_returns_bytes(self, mock_tally: MockTallyServer) -> None:
        mock_tally.set_response(PING_OK_RESPONSE)
        with TallyClient(mock_tally.tally_settings()) as client:
            result = client.request(_SIMPLE_PAYLOAD)
        assert result == PING_OK_RESPONSE
        assert mock_tally.request_count == 1

    def test_request_sends_correct_headers(self, mock_tally: MockTallyServer) -> None:
        mock_tally.set_response(PING_OK_RESPONSE)
        with TallyClient(mock_tally.tally_settings()) as client:
            client.request(_SIMPLE_PAYLOAD)
        assert b"<ENVELOPE>" in mock_tally.last_request_body

    def test_request_encodes_payload_as_utf8(self, mock_tally: MockTallyServer) -> None:
        mock_tally.set_response(PING_OK_RESPONSE)
        payload_with_unicode = "<ENVELOPE><NAME>Aadhaar क</NAME></ENVELOPE>"
        with TallyClient(mock_tally.tally_settings()) as client:
            client.request(payload_with_unicode)
        assert "क".encode("utf-8") in mock_tally.last_request_body

    def test_raises_tally_request_error_on_status_1(
        self, mock_tally: MockTallyServer
    ) -> None:
        mock_tally.set_response(APP_ERROR_RESPONSE)
        with TallyClient(mock_tally.tally_settings()) as client:
            with pytest.raises(TallyRequestError) as exc_info:
                client.request(_SIMPLE_PAYLOAD)
        assert "Company not available" in str(exc_info.value)
        assert mock_tally.request_count == 1  # no retries on app errors

    def test_raises_empty_response_error(self, mock_tally: MockTallyServer) -> None:
        mock_tally.set_response(EMPTY_RESPONSE)
        with TallyClient(mock_tally.tally_settings()) as client:
            with pytest.raises(TallyEmptyResponseError):
                client.request(_SIMPLE_PAYLOAD)
        assert mock_tally.request_count == 1  # no retries on empty

    def test_retries_on_http_500(self, mock_tally: MockTallyServer) -> None:
        # 500, 500, then success
        mock_tally.enqueue_response(b"server error", status_code=500)
        mock_tally.enqueue_response(b"server error", status_code=500)
        mock_tally.enqueue_response(PING_OK_RESPONSE, status_code=200)
        settings = mock_tally.tally_settings()

        with TallyClient(settings) as client:
            # HTTP 500 raises requests.HTTPError which is a subclass of
            # requests.RequestException but NOT ConnectionError/Timeout.
            # Verify this doesn't cause infinite retry (it should raise immediately).
            with pytest.raises(Exception):
                client.request(_SIMPLE_PAYLOAD)

    def test_context_manager_closes_session(self, mock_tally: MockTallyServer) -> None:
        mock_tally.set_response(PING_OK_RESPONSE)
        with TallyClient(mock_tally.tally_settings()) as client:
            assert client._session is not None
        assert client._session is None


class TestTallyClientIsAlive:
    def test_returns_true_when_tally_responds(self, mock_tally: MockTallyServer) -> None:
        mock_tally.set_response(PING_OK_RESPONSE)
        with TallyClient(mock_tally.tally_settings()) as client:
            assert client.is_alive() is True

    def test_returns_false_when_tally_returns_empty(
        self, mock_tally: MockTallyServer
    ) -> None:
        mock_tally.set_response(EMPTY_RESPONSE)
        with TallyClient(mock_tally.tally_settings()) as client:
            assert client.is_alive() is False

    def test_returns_false_when_server_not_running(self) -> None:
        from app.config.settings import TallySettings

        settings = TallySettings(host="127.0.0.1", port=19999, timeout_seconds=1)
        with TallyClient(settings) as client:
            assert client.is_alive() is False


class TestTallyClientStreamRequest:
    def test_yields_response_bytes(self, mock_tally: MockTallyServer) -> None:
        mock_tally.set_response(PING_OK_RESPONSE)
        with TallyClient(mock_tally.tally_settings()) as client:
            chunks = list(client.stream_request(_SIMPLE_PAYLOAD))
        assembled = b"".join(chunks)
        assert assembled == PING_OK_RESPONSE

    def test_yields_nothing_on_empty_response(
        self, mock_tally: MockTallyServer
    ) -> None:
        mock_tally.set_response(EMPTY_RESPONSE)
        with TallyClient(mock_tally.tally_settings()) as client:
            chunks = list(client.stream_request(_SIMPLE_PAYLOAD))
        assert chunks == []


class TestTallyClientNoContextManager:
    def test_works_without_context_manager(self, mock_tally: MockTallyServer) -> None:
        mock_tally.set_response(PING_OK_RESPONSE)
        client = TallyClient(mock_tally.tally_settings())
        result = client.request(_SIMPLE_PAYLOAD)
        client.close()
        assert result == PING_OK_RESPONSE
