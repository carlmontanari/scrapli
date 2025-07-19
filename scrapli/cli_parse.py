"""cli_parse"""

import urllib.request
from importlib import import_module, resources
from io import BytesIO, TextIOWrapper
from logging import getLogger
from typing import Any, TextIO

from scrapli.exceptions import ParsingException

logger = getLogger(__name__)


def textfsm_get_template(platform: str, command: str) -> TextIO | None:
    """
    Find correct TextFSM template based on platform and command executed

    Args:
        platform: ntc-templates device type; i.e. cisco_ios, arista_eos, etc.
        command: string of command that was executed (to find appropriate template)

    Returns:
        None or TextIO of opened template

    Raises:
        N/A

    """
    try:
        import_module(name=".templates", package="ntc_templates")
        cli_table_obj = getattr(import_module(name=".clitable", package="textfsm"), "CliTable")
    except ModuleNotFoundError as exc:
        raise ParsingException("optional extra 'textfsm' not found") from exc

    template_dir = f"{resources.files('ntc_templates')}/templates"

    cli_table = cli_table_obj("index", template_dir)
    template_index = cli_table.index.GetRowMatch({"Platform": platform, "Command": command})

    if not template_index:
        logger.warning(
            f"No match in ntc_templates index for platform `{platform}` and command `{command}`"
        )
        return None

    template_name = cli_table.index.index[template_index]["Template"]

    return open(f"{template_dir}/{template_name}", encoding="utf-8")


def _textfsm_to_dict(
    structured_output: list[Any] | dict[str, Any], header: list[str]
) -> list[Any] | dict[str, Any]:
    """
    Create list of dicts from textfsm output and header

    Args:
        structured_output: parsed textfsm output
        header: list of strings representing column headers for textfsm output

    Returns:
        output: structured data

    Raises:
        N/A

    """
    logger.debug("converting textfsm output to dictionary representation")

    header_lower = [h.lower() for h in header]
    structured_output = [dict(zip(header_lower, row)) for row in structured_output]

    return structured_output


def textfsm_parse(
    template: str | TextIO, output: str, to_dict: bool = True
) -> list[Any] | dict[str, Any]:
    """
    Parse output with TextFSM and ntc-templates, try to return structured output

    Args:
        template: TextIO or string of URL or filesystem path to template to use to parse data
        output: unstructured output from device to parse
        to_dict: convert textfsm output from list of lists to list of dicts -- basically create dict
            from header and row data so it is easier to read/parse the output

    Returns:
        output: structured data

    Raises:
        ScrapliException: If raise_err is set and a textfsm parsing error occurs, raises from the
            originating textfsm.parser.TextFSMError exception.

    """
    import textfsm  # noqa: PLC0415

    if isinstance(template, str):
        if template.startswith("http://") or template.startswith("https://"):
            with urllib.request.urlopen(template) as response:
                re_table = textfsm.TextFSM(
                    TextIOWrapper(
                        BytesIO(response.read()),
                        encoding=response.headers.get_content_charset(),
                    )
                )
        else:
            re_table = textfsm.TextFSM(open(template, mode="rb"))
    else:
        re_table = textfsm.TextFSM(template)

    try:
        structured_output: list[Any] | dict[str, Any] = re_table.ParseText(output)

        if to_dict:
            structured_output = _textfsm_to_dict(
                structured_output=structured_output, header=re_table.header
            )

        return structured_output
    except textfsm.parser.TextFSMError as exc:
        raise ParsingException("failed parsing output with 'textfsm'") from exc

    return []


def genie_parse(platform: str, command: str, output: str) -> list[Any] | dict[str, Any]:
    """
    Parse output with Cisco genie parsers, try to return structured output

    Args:
        platform: genie device type; i.e. iosxe, iosxr, etc.
        command: string of command that was executed (to find appropriate parser)
        output: unstructured output from device to parse

    Returns:
        output: structured data

    Raises:
        N/A

    """
    try:
        device = getattr(import_module(name=".conf.base", package="genie"), "Device")
        get_parser = getattr(
            import_module(name=".libs.parser.utils", package="genie"), "get_parser"
        )
    except ModuleNotFoundError as exc:
        raise ParsingException("optional extra 'genie' not found") from exc

    genie_device = device("scrapli_device", custom={"abstraction": {"order": ["os"]}}, os=platform)

    try:
        get_parser(command, genie_device)
        genie_parsed_result = genie_device.parse(command, output=output)
        if isinstance(genie_parsed_result, list | dict):
            return genie_parsed_result
    except Exception as exc:
        raise ParsingException("failed parsing output with 'genie'") from exc

    return []
