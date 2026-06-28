from __future__ import annotations

import io
from collections.abc import Iterator


class IteratorIO(io.RawIOBase):
    """Wrap an Iterator[bytes] as a readable file-like object for lxml.iterparse.

    Bytes are pulled from the iterator on demand so the HTTP response is never
    fully buffered in memory — important for large voucher exports.
    """

    def __init__(self, chunks: Iterator[bytes]) -> None:
        self._chunks = chunks
        self._buf = b""

    def readinto(self, b: bytearray | memoryview) -> int:  # type: ignore[override]
        while not self._buf:
            try:
                chunk = next(self._chunks)
                if chunk:
                    self._buf = chunk
            except StopIteration:
                return 0
        n = min(len(b), len(self._buf))
        b[:n] = self._buf[:n]
        self._buf = self._buf[n:]
        return n

    def readable(self) -> bool:
        return True
