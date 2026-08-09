"""scrapli.result"""

from ctypes import c_size_t, pointer
from dataclasses import dataclass, field

from scrapli.ffi_types import ZigSlice


@dataclass
class Result:
    """
    Result holds the result of an operation.

    Args:
        input_:
        host:
        port:
        start_time:
        end_time:
        result_raw_journal:
        result:
        rpc_warnings:
        rpc_errors:

    Returns:
        None

    Raises:
        N/A

    """

    input_: str
    host: str
    port: int
    start_time: int
    end_time: int
    # the *journal* of the content (framing etc.) that was cleaned out of the result -- raw is
    # never stored, its reconstructed (lazily, see result_raw) from the (result, journal) pair
    # on demand
    result_raw_journal: bytes
    _result: str
    rpc_warnings: str
    rpc_errors: str

    _result_raw: bytes | None = field(default=None, init=False, repr=False)

    @property
    def result_raw(self) -> bytes:
        """
        Returns the raw (as in wire-exact) bytes of the result.

        Raw is never shipped over the ffi boundary or stored -- its reconstructed (then cached)
        from the (result, journal) pair on first access.

        Args:
            N/A

        Returns:
            bytes: the raw result

        Raises:
            N/A

        """
        if self._result_raw is not None:
            return self._result_raw

        # note: reconstruction runs against the *verbatim* result (self._result), not the
        # xml-header-stripped result property!
        result = self._result.encode()

        if not self.result_raw_journal:
            # empty journal means nothing was cleaned out, raw == result
            self._result_raw = result

            return self._result_raw

        # deferred to avoid circular imports (and to only pay for it when raw is fetched)
        from scrapli.ffi_mapping import LibScrapliMapping  # noqa: PLC0415

        result_slice = pointer(ZigSlice.from_bytes(result))
        journal_slice = pointer(ZigSlice.from_bytes(self.result_raw_journal))

        raw_size = pointer(c_size_t())

        mapping = LibScrapliMapping()

        mapping.netconf_mapping.get_reconstructed_result_raw_size(
            result_slice=result_slice,
            result_raw_journal_slice=journal_slice,
            raw_size=raw_size,
        )

        result_raw_slice = pointer(ZigSlice(size=raw_size.contents))

        mapping.netconf_mapping.get_reconstructed_result_raw(
            result_slice=result_slice,
            result_raw_journal_slice=journal_slice,
            result_raw_slice=result_raw_slice,
        )

        self._result_raw = result_raw_slice.contents.get_contents()

        return self._result_raw

    @property
    def failed(self) -> bool:
        """
        Returns True if any failed indicators were seen, otherwise False.

        Args:
            N/A

        Returns:
            bool: True for failed, otherwise False

        Raises:
            N/A

        """
        return bool(self.rpc_errors)

    @property
    def elapsed_time_seconds(self) -> float:
        """
        Returns the number of seconds the operation took.

        Args:
            N/A

        Returns:
            float: duration in seconds

        Raises:
            N/A

        """
        return (self.end_time - self.start_time) / 1_000_000_000

    @property
    def result(self) -> str:
        """
        Returns the result, with the xml header stripped if present.

        lxml will barf on `etree.fromstring` if/when an xml header with encoding is present, so we
        will simply return the result stripping that if its there.

        Args:
            N/A

        Returns:
            str: joined results

        Raises:
            N/A

        """
        out = self._result.lstrip()

        if out.startswith("<?xml"):
            end = out.find("?>")
            if end != -1:
                return out[end + 2 :].lstrip()

        return out
