"""TallyPrime HTTP/XML client.

Responsibilities
----------------
* Send XML payloads to TallyPrime's HTTP endpoint.
* Retry transient network failures with exponential-backoff + jitter.
* Detect Tally application-level errors in the response body (HTTP 200 != success).
* Provide a chunked streaming mode for large exports.

Thread safety
-------------
requests.Session is NOT thread-safe.  One TallyClient instance per thread.
For concurrent sync workers, create one client per worker.

Usage
-----
    with TallyClient(settings.tally) as client:
        raw_bytes = client.request(xml_payload)
"""

from __future__ import annotations

import random
import time
from collections.abc import Iterator

import lxml.etree as etree
import requests
import requests.adapters
from loguru import logger

from app.config.settings import TallySettings

# ── Exceptions ────────────────────────────────────────────────────────────────


class TallyError(Exception):
    """Base for all Tally client errors."""


class TallyConnectionError(TallyError):
    """Could not reach TallyPrime (connection refused, timeout, unreachable)."""


class TallyEmptyResponseError(TallyError):
    """Tally returned an empty body — usually means it is busy or overloaded."""


class TallyRequestError(TallyError):
    """Tally returned an application-level error (STATUS=1 or LINEERROR in XML)."""

    def __init__(self, message: str, *, status_code: str = "", error_desc: str = "") -> None:
        super().__init__(message)
        self.status_code = status_code
        self.error_desc = error_desc


# ── Ping XML ──────────────────────────────────────────────────────────────────

_PING_XML = """<ENVELOPE>
  <HEADER>
    <TALLYREQUEST>Export Data</TALLYREQUEST>
  </HEADER>
  <BODY>
    <EXPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>List of Companies</REPORTNAME>
        <STATICVARIABLES>
          <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
        </STATICVARIABLES>
      </REQUESTDESC>
    </EXPORTDATA>
  </BODY>
</ENVELOPE>"""

_HTTP_HEADERS: dict[str, str] = {
    "Content-Type": "text/xml;charset=utf-8",
    "Accept": "text/xml",
}

_STREAM_CHUNK_SIZE = 65_536  # 64 KB per iteration_content() call


# ── Client ────────────────────────────────────────────────────────────────────


class TallyClient:
    """HTTP client for the TallyPrime 7 XML/HTTP interface."""

    def __init__(self, settings: TallySettings) -> None:
        self._s = settings
        self._session: requests.Session | None = None

    # ── Context manager ───────────────────────────────────────────────────────

    def __enter__(self) -> TallyClient:
        self._session = _build_session()
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        if self._session is not None:
            self._session.close()
            self._session = None

    # ── Public API ────────────────────────────────────────────────────────────

    def request(self, xml_payload: str) -> bytes:
        """POST xml_payload to Tally, return response bytes.

        Retries on ConnectionError / Timeout up to settings.max_retries times
        with exponential backoff + jitter.  Application-level errors
        (STATUS=1, LINEERROR) are NOT retried — they indicate a logic problem.

        Raises:
            TallyConnectionError: all retries exhausted.
            TallyEmptyResponseError: Tally returned an empty body.
            TallyRequestError: Tally returned a business-layer error.
        """
        session = self._get_session()
        last_exc: Exception | None = None

        for attempt in range(self._s.max_retries):
            try:
                return self._post(session, xml_payload)
            except TallyRequestError:
                raise  # never retry app errors
            except TallyEmptyResponseError:
                raise  # let caller decide — empty body is unusual
            except (requests.ConnectionError, requests.Timeout) as exc:
                last_exc = exc
                remaining = self._s.max_retries - attempt - 1
                if remaining > 0:
                    wait = _backoff_wait(
                        attempt,
                        base=self._s.retry_backoff_base,
                        cap=self._s.retry_backoff_max,
                    )
                    logger.warning(
                        "Tally unreachable — retrying",
                        attempt=attempt + 1,
                        max_retries=self._s.max_retries,
                        wait_s=round(wait, 2),
                        url=self._s.base_url,
                        error=str(exc),
                    )
                    time.sleep(wait)

        raise TallyConnectionError(
            f"Could not reach Tally at {self._s.base_url} after {self._s.max_retries} attempts"
        ) from last_exc

    def stream_request(self, xml_payload: str) -> Iterator[bytes]:
        """POST xml_payload and yield raw response bytes in chunks.

        Use for large exports (vouchers, stock items) so the entire response
        is never held in memory at once.  The caller assembles chunks into a
        streaming XML parser (lxml.iterparse via a pipe or temp file).

        No retry on failure — the caller's sync engine handles recovery.

        Raises:
            TallyConnectionError: network-level failure during streaming.
        """
        session = self._get_session()
        url = self._s.base_url

        try:
            with session.post(
                url,
                data=xml_payload.encode("utf-8"),
                headers=_HTTP_HEADERS,
                timeout=self._s.timeout_seconds,
                stream=True,
            ) as response:
                response.raise_for_status()
                for chunk in response.iter_content(chunk_size=_STREAM_CHUNK_SIZE):
                    if chunk:
                        yield chunk
        except (requests.ConnectionError, requests.Timeout) as exc:
            raise TallyConnectionError(f"Streaming request to Tally failed: {exc}") from exc

    def is_alive(self, timeout: float = 5.0) -> bool:
        """Return True if Tally responds to a lightweight ping request."""
        session = self._get_session()
        try:
            response = session.post(
                self._s.base_url,
                data=_PING_XML.encode("utf-8"),
                headers=_HTTP_HEADERS,
                timeout=timeout,
            )
            return response.status_code == 200 and len(response.content) > 0
        except Exception:
            return False

    # ── Internals ─────────────────────────────────────────────────────────────

    def _post(self, session: requests.Session, xml_payload: str) -> bytes:
        t0 = time.perf_counter()
        url = self._s.base_url

        logger.debug("→ Tally POST", url=url, payload_bytes=len(xml_payload))

        response = session.post(
            url,
            data=xml_payload.encode("utf-8"),
            headers=_HTTP_HEADERS,
            timeout=self._s.timeout_seconds,
        )
        response.raise_for_status()

        elapsed_ms = (time.perf_counter() - t0) * 1000
        content = response.content

        if not content:
            raise TallyEmptyResponseError(
                f"Tally returned an empty response body for POST to {url}"
            )

        logger.debug(
            "← Tally response",
            elapsed_ms=round(elapsed_ms, 1),
            response_bytes=len(content),
        )

        _check_tally_app_error(content)
        return content

    def _get_session(self) -> requests.Session:
        # Allow use without context manager (e.g. one-shot health checks).
        if self._session is None:
            self._session = _build_session()
        return self._session


# ── Helpers ───────────────────────────────────────────────────────────────────


def _build_session() -> requests.Session:
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(
        pool_connections=2,
        pool_maxsize=4,
        max_retries=0,  # retries managed by TallyClient._post loop
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def _backoff_wait(attempt: int, *, base: float, cap: float) -> float:
    """Exponential backoff with ±1 s full jitter, capped at `cap` seconds."""
    exp = base * (2**attempt)
    jitter = random.uniform(0.0, 1.0)
    return min(exp + jitter, cap)


def _check_tally_app_error(content: bytes) -> None:
    """Raise TallyRequestError if the XML body signals an application error.

    Tally returns HTTP 200 even for errors; the error is signalled via:
    * <STATUS>1</STATUS> — in the HEADER element
    * <LINEERROR>...</LINEERROR> — in the DATA element

    We do a cheap byte scan first to avoid parsing every response.
    """
    lower = content[:4096].lower()
    if b"<status>1</status>" not in lower and b"<lineerror>" not in lower:
        return

    # Confirmed candidate — do a proper parse to extract the message.
    try:
        root = etree.fromstring(content)
        status = (root.findtext(".//STATUS") or "").strip()
        lineerror = (root.findtext(".//LINEERROR") or "").strip()
        errdesc = (root.findtext(".//ERRDESC") or lineerror or "").strip()

        if status == "1" or lineerror:
            raise TallyRequestError(
                f"Tally application error: {errdesc or '(no description)'}",
                status_code=status,
                error_desc=errdesc,
            )
    except TallyRequestError:
        raise
    except etree.XMLSyntaxError:
        pass  # malformed XML — let the parser raise a better error
