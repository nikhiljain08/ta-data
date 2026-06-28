"""Lightweight in-process mock TallyPrime HTTP server for tests.

Starts a real TCP server on a random port so integration tests exercise the
full HTTP stack (connection pooling, headers, chunked responses) without
touching the real TallyPrime instance.

Usage
-----
    with MockTallyServer() as server:
        server.set_response(b"<ENVELOPE>...</ENVELOPE>")
        client = TallyClient(server.tally_settings())
        result = client.request("<ENVELOPE>...</ENVELOPE>")

Or via pytest fixture (see conftest.py):

    def test_something(mock_tally: MockTallyServer) -> None:
        mock_tally.set_response(b"<ENVELOPE><BODY/></ENVELOPE>")
        ...
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, HTTPServer

from app.config.settings import TallySettings

# ── Canned XML responses ───────────────────────────────────────────────────────

PING_OK_RESPONSE = b"""<ENVELOPE>
  <HEADER><STATUS>0</STATUS></HEADER>
  <BODY><DATA><COLLECTION/></DATA></BODY>
</ENVELOPE>"""

APP_ERROR_RESPONSE = b"""<ENVELOPE>
  <HEADER>
    <STATUS>1</STATUS>
    <ERRDESC>Company not available</ERRDESC>
  </HEADER>
</ENVELOPE>"""

LINE_ERROR_RESPONSE = b"""<ENVELOPE>
  <BODY>
    <DATA>
      <LINEERROR>No active company open in Tally</LINEERROR>
    </DATA>
  </BODY>
</ENVELOPE>"""

EMPTY_RESPONSE = b""


# ── Request handler ───────────────────────────────────────────────────────────


class _Handler(BaseHTTPRequestHandler):
    """Minimal handler that returns whatever the MockTallyServer has queued."""

    server: MockTallyServer  # type narrowing for the shared server reference

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        self.server.last_request_body = body
        self.server.request_count += 1

        response_body, status_code = self.server.next_response()
        self.send_response(status_code)
        self.send_header("Content-Type", "text/xml;charset=utf-8")
        self.send_header("Content-Length", str(len(response_body)))
        self.end_headers()
        self.wfile.write(response_body)

    def log_message(self, *args: object) -> None:  # silence server logs in tests
        pass


# ── Server ────────────────────────────────────────────────────────────────────


class MockTallyServer:
    """In-process HTTP server that mimics TallyPrime's XML endpoint.

    Responses are queued via enqueue_response() (FIFO).  If the queue is empty
    the server returns PING_OK_RESPONSE with HTTP 200.
    """

    def __init__(self) -> None:
        self._server = HTTPServer(("127.0.0.1", 0), _Handler)
        self._server.last_request_body: bytes = b""
        self._server.request_count: int = 0
        self._server.next_response: Callable[[], tuple[bytes, int]] = self._default_response
        self._queue: list[tuple[bytes, int]] = []
        self._lock = threading.Lock()
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    # ── Context manager ───────────────────────────────────────────────────────

    def __enter__(self) -> MockTallyServer:
        self.start()
        return self

    def __exit__(self, *_: object) -> None:
        self.stop()

    def start(self) -> None:
        self._server.next_response = self._dequeue  # wire dequeue into handler
        self._thread.start()

    def stop(self) -> None:
        self._server.shutdown()
        self._thread.join(timeout=2)

    # ── Configuration helpers ─────────────────────────────────────────────────

    @property
    def port(self) -> int:
        return self._server.server_address[1]

    @property
    def last_request_body(self) -> bytes:
        return self._server.last_request_body

    @property
    def request_count(self) -> int:
        return self._server.request_count

    def tally_settings(self) -> TallySettings:
        """Return TallySettings pointing at this mock server."""
        return TallySettings(
            host="127.0.0.1",
            port=self.port,
            timeout_seconds=5,
            max_retries=3,
            retry_backoff_base=0.01,  # near-zero backoff in tests
            retry_backoff_max=0.05,
        )

    def enqueue_response(self, body: bytes, *, status_code: int = 200) -> None:
        """Queue a response to be returned for the next request."""
        with self._lock:
            self._queue.append((body, status_code))

    def set_response(self, body: bytes, *, status_code: int = 200) -> None:
        """Set a single response, clearing any previously queued responses."""
        with self._lock:
            self._queue.clear()
            self._queue.append((body, status_code))

    def reset(self) -> None:
        """Clear queue and reset counters between tests."""
        with self._lock:
            self._queue.clear()
        self._server.last_request_body = b""
        self._server.request_count = 0

    # ── Internals ─────────────────────────────────────────────────────────────

    def _dequeue(self) -> tuple[bytes, int]:
        with self._lock:
            if self._queue:
                return self._queue.pop(0)
        return PING_OK_RESPONSE, 200

    @staticmethod
    def _default_response() -> tuple[bytes, int]:
        return PING_OK_RESPONSE, 200
