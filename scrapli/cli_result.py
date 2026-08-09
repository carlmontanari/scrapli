"""scrapli.result"""

from ctypes import c_size_t, pointer
from typing import Any, TextIO

from scrapli.cli_parse import genie_parse, textfsm_get_template, textfsm_parse
from scrapli.exceptions import ParsingException
from scrapli.ffi_types import ZigSlice
from scrapli.helper import bulid_result_preview, unix_nano_timestmap_to_iso


def _split_packed(data: bytes, lens: list[int]) -> list[bytes]:
    """
    Split a packed (back-to-back, no delimiters) buffer apart using the given lens.

    Args:
        data: the packed buffer
        lens: the length of each entry in the packed buffer

    Returns:
        list[bytes]: the entries

    Raises:
        N/A

    """
    out = []

    cur = 0

    for length in lens:
        out.append(data[cur : cur + length])

        cur += length

    return out


class Result:
    """
    Result represents a set of results from some Cli operation(s).

    Args:
        N/A

    Returns:
        None

    Raises:
        N/A

    """

    def __init__(  # noqa: PLR0913
        self,
        *,
        host: str,
        port: int,
        inputs: bytes,
        input_lens: list[int],
        start_time: int,
        splits: list[int],
        result_raw_journals: bytes,
        result_raw_journal_lens: list[int],
        results: bytes,
        result_lens: list[int],
        results_failed_indicator: str,
        textfsm_platform: str,
        genie_platform: str,
    ) -> None:
        self.host = host
        self.port = port
        self.inputs = [i.decode() for i in _split_packed(inputs, input_lens)]
        self.start_time = start_time
        self.splits = splits
        self.results = [r.decode() for r in _split_packed(results, result_lens)]
        self.results_failed_indicator = results_failed_indicator
        self.textfsm_platform = textfsm_platform
        self.genie_platform = genie_platform

        # each entry's *journal* of the content that was cleaned out of the corresponding
        # result -- raw is never stored, its reconstructed (lazily, see results_raw) from the
        # (result, journal) pair on demand
        self._result_raw_journals = _split_packed(result_raw_journals, result_raw_journal_lens)
        self._results_raw: list[bytes] | None = None

    def __repr__(self) -> str:
        """
        Magic repr method for Result class

        Args:
            N/A

        Returns:
            str: repr for class object

        Raises:
            N/A

        """
        return (
            f"{self.__class__.__name__}("
            f"host={self.host!r}, "
            f"port={self.port!r}, "
            f"failed={self.failed!r})"
        )

    def __str__(self) -> str:
        """
        Magic str method for Result class

        Args:
            N/A

        Returns:
            str: str for class object

        Raises:
            N/A

        """
        return (
            "<-----\n"
            f"\tInput(s)         : {self.inputs}\n"
            f"\tStart Time       : {unix_nano_timestmap_to_iso(timestamp=self.start_time)}\n"
            f"\tEnd Time         : {unix_nano_timestmap_to_iso(timestamp=self.end_time)}\n"
            f"\tElapsed Time (s) : {self.elapsed_time_seconds:.2f}s\n"
            f"\tResult           : {bulid_result_preview(result=self.result)}\n"
            "----->"
        )

    def extend(self, result: "Result") -> None:
        """
        Extends this Result object with another Result object.

        Args:
            result: the result object with which to extend this result object

        Returns:
            N/A

        Raises:
            N/A

        """
        self.inputs.extend(result.inputs)
        self.results.extend(result.results)
        self.splits.extend(result.splits)

        self._result_raw_journals.extend(result._result_raw_journals)
        # drop any cached reconstruction, itll rebuild (now including the extended entries)
        # on next access
        self._results_raw = None

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
        return bool(self.results_failed_indicator)

    @property
    def end_time(self) -> int:
        """
        Returns the end time of the operations in unix nano.

        Args:
            N/A

        Returns:
            int: end time in unix nano

        Raises:
            N/A

        """
        if not self.splits:
            # if we had no splits it was a "noop" type op (like enter mode when
            # you are already in the requested mode), so we'll lie and say it
            # was a 1ns op time
            return self.start_time + 1

        return self.splits[-1]

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
        Returns the results joined on newline chars. Note this does *not* include inputs sent.

        Args:
            N/A

        Returns:
            str: joined results

        Raises:
            N/A

        """
        return "\n".join(self.results)

    @property
    def results_raw(self) -> list[bytes]:
        """
        Returns the raw (as in wire-exact) bytes of each result.

        Raw is never shipped over the ffi boundary or stored -- each entry is reconstructed
        (then cached) from its (result, journal) pair on first access.

        Args:
            N/A

        Returns:
            list[bytes]: the raw result entries

        Raises:
            N/A

        """
        if self._results_raw is None:
            self._results_raw = [
                self._reconstruct_result_raw(index=index) for index in range(len(self.results))
            ]

        return self._results_raw

    def _reconstruct_result_raw(self, index: int) -> bytes:
        """
        Reconstructs a single entry's raw output from its (result, journal) pair.

        Args:
            index: the index of the result to reconstruct

        Returns:
            bytes: the reconstructed raw entry

        Raises:
            N/A

        """
        # deferred to avoid circular imports (and to only pay for it when raw is fetched)
        from scrapli.ffi_mapping import LibScrapliMapping  # noqa: PLC0415

        result = self.results[index].encode()
        journal = self._result_raw_journals[index]

        if not journal:
            # empty journal means nothing was ever cleaned out of this entry, raw == result
            return result

        result_slice = pointer(ZigSlice.from_bytes(result))
        journal_slice = pointer(ZigSlice.from_bytes(journal))

        raw_size = pointer(c_size_t())

        mapping = LibScrapliMapping()

        mapping.cli_mapping.get_reconstructed_result_raw_size(
            result_slice=result_slice,
            result_raw_journal_slice=journal_slice,
            raw_size=raw_size,
        )

        result_raw_slice = pointer(ZigSlice(size=raw_size.contents))

        mapping.cli_mapping.get_reconstructed_result_raw(
            result_slice=result_slice,
            result_raw_journal_slice=journal_slice,
            result_raw_slice=result_raw_slice,
        )

        return result_raw_slice.contents.get_contents()

    @property
    def result_raw(self) -> bytes:
        """
        Returns the results (raw) joined on newline chars. Note this does *not* include inputs sent.

        Args:
            N/A

        Returns:
            bytes: joined results

        Raises:
            N/A

        """
        return b"\n".join(self.results_raw)

    def textfsm_parse(
        self,
        index: int = 0,
        template: str | TextIO | None = None,
        to_dict: bool = True,
    ) -> list[Any] | dict[str, Any]:
        """
        Parse results with textfsm, always return structured data

        Returns an empty list if parsing fails!

        Args:
            index: the index of the result to parse, assumes first/zeroith if not provided
            template: string path to textfsm template or opened textfsm template file
            to_dict: convert textfsm output from list of lists to list of dicts -- basically create
                dict from header and row data so it is easier to read/parse the output

        Returns:
            structured_result: empty list or parsed data from textfsm

        Raises:
            N/A

        """
        if template is None:
            template = textfsm_get_template(
                platform=self.textfsm_platform, command=self.inputs[index]
            )

        if template is None:
            raise ParsingException("no template provided or available for input")

        return textfsm_parse(template=template, output=self.results[index], to_dict=to_dict)

    def genie_parse(
        self,
        index: int = 0,
    ) -> dict[str, Any] | list[Any]:
        """
        Parse results with genie, always return structured data

        Returns an empty list if parsing fails!

        Args:
            index: the index of the result to parse, assumes first/zeroith if not provided

        Returns:
            structured_result: empty list or parsed data from genie

        Raises:
            N/A

        """
        return genie_parse(self.genie_platform, self.inputs[index], self.results[index])
