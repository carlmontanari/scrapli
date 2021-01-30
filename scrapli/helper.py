"""scrapli.helper"""
import importlib
from io import TextIOWrapper
from pathlib import Path
from shutil import get_terminal_size
from typing import Any, Dict, List, Optional, TextIO, Union
from warnings import warn

import pkg_resources  # pylint: disable=C0411

from scrapli.exceptions import ScrapliValueError
from scrapli.logging import logger


def _textfsm_get_template(platform: str, command: str) -> Optional[TextIO]:
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
        importlib.import_module(name=".templates", package="ntc_templates")
        CliTable = getattr(importlib.import_module(name=".clitable", package="textfsm"), "CliTable")
    except ModuleNotFoundError as exc:
        title = "Optional Extra Not Installed!"
        message = (
            "Optional extra 'textfsm' is not installed!\n"
            f"To resolve this issue, install '{exc.name}'. You can do this in one of the following"
            " ways:\n"
            "1: 'pip install -r requirements-textfsm.txt'\n"
            "2: 'pip install scrapli[textfsm]'"
        )
        user_warning(title=title, message=message)
        return None
    template_dir = pkg_resources.resource_filename("ntc_templates", "templates")
    cli_table = CliTable("index", template_dir)
    template_index = cli_table.index.GetRowMatch({"Platform": platform, "Command": command})
    if not template_index:
        logger.warning(
            f"No match in ntc_templates index for platform `{platform}` and command `{command}`"
        )
        return None
    template_name = cli_table.index.index[template_index]["Template"]
    template = open(f"{template_dir}/{template_name}")
    return template


def _textfsm_to_dict(
    structured_output: Union[List[Any], Dict[str, Any]], header: List[str]
) -> Union[List[Any], Dict[str, Any]]:
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
    template: Union[str, TextIOWrapper], output: str, to_dict: bool = True
) -> Union[List[Any], Dict[str, Any]]:
    """
    Parse output with TextFSM and ntc-templates, try to return structured output

    Args:
        template: TextIOWrapper or string path to template to use to parse data
        output: unstructured output from device to parse
        to_dict: convert textfsm output from list of lists to list of dicts -- basically create dict
            from header and row data so it is easier to read/parse the output

    Returns:
        output: structured data

    Raises:
        N/A

    """
    import textfsm  # pylint: disable=C0415

    if not isinstance(template, TextIOWrapper):
        template_file = open(template)
    else:
        template_file = template
    re_table = textfsm.TextFSM(template_file)
    try:
        structured_output: Union[List[Any], Dict[str, Any]] = re_table.ParseText(output)
        if to_dict:
            structured_output = _textfsm_to_dict(
                structured_output=structured_output, header=re_table.header
            )
        return structured_output
    except textfsm.parser.TextFSMError:
        logger.warning("failed to parse data with textfsm")
    return []


def genie_parse(platform: str, command: str, output: str) -> Union[List[Any], Dict[str, Any]]:
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
        Device = getattr(importlib.import_module(name=".conf.base", package="genie"), "Device")
        get_parser = getattr(
            importlib.import_module(name=".libs.parser.utils", package="genie"), "get_parser"
        )
    except ModuleNotFoundError as exc:
        title = "Optional Extra Not Installed!"
        message = (
            "Optional extra 'genie' is not installed!\n"
            f"To resolve this issue, install '{exc.name}'. You can do this in one of the following"
            " ways:\n"
            "1: 'pip install -r requirements-genie.txt'\n"
            "2: 'pip install scrapli[genie]'"
        )
        user_warning(title=title, message=message)
        return []

    genie_device = Device("scrapli_device", custom={"abstraction": {"order": ["os"]}}, os=platform)

    try:
        get_parser(command, genie_device)
        genie_parsed_result = genie_device.parse(command, output=output)
        if isinstance(genie_parsed_result, (list, dict)):
            return genie_parsed_result
    except Exception as exc:  # pylint: disable=W0703
        logger.warning(f"failed to parse data with genie, genie raised exception: `{exc}`")
    return []


def ttp_parse(template: Union[str, TextIOWrapper], output: str) -> Union[List[Any], Dict[str, Any]]:
    """
    Parse output with TTP, try to return structured output

    Args:
        template: TextIOWrapper or string path to template to use to parse data
        output: unstructured output from device to parse

    Returns:
        output: structured data

    Raises:
        N/A

    """
    try:
        ttp = getattr(importlib.import_module(name="ttp"), "ttp")
    except ModuleNotFoundError as exc:
        title = "Optional Extra Not Installed!"
        message = (
            "Optional extra 'ttp' is not installed!\n"
            f"To resolve this issue, install '{exc.name}'. You can do this in one of the following"
            " ways:\n"
            "1: 'pip install -r requirements-ttp.txt'\n"
            "2: 'pip install scrapli[ttp]'"
        )
        user_warning(title=title, message=message)
        return []

    if not isinstance(template, (str, TextIOWrapper)):
        logger.info(f"invalid template `{template}`; template should be string or TextIOWrapper")
        return []

    ttp_parser_template_name = "scrapli_ttp_parse"
    ttp_parser = ttp()
    ttp_parser.add_template(template=template, template_name=ttp_parser_template_name)
    ttp_parser.add_input(data=output, template_name=ttp_parser_template_name)
    ttp_parser.parse()
    ttp_result: Dict[str, List[Any]] = ttp_parser.result(structure="dictionary")
    return ttp_result[ttp_parser_template_name]


def resolve_file(file: str) -> str:
    """
    Resolve file from provided string

    Args:
        file: string path to file

    Returns:
        str: string path to file

    Raises:
        ScrapliValueError: if file cannot be resolved

    """
    if Path(file).is_file():
        return str(Path(file))
    if Path(file).expanduser().is_file():
        return str(Path(file).expanduser())
    raise ScrapliValueError(f"File path `{file}` could not be resolved")


def format_user_warning(title: str, message: str) -> str:
    """
    Nicely format a warning message for users

    Args:
        title: title of the warning message
        message: actual message body

    Returns:
        str: nicely formatted warning

    Raises:
        N/A

    """
    terminal_width = get_terminal_size().columns
    warning_banner_char = "*"

    if len(title) > (terminal_width - 4):
        warning_header = warning_banner_char * terminal_width
    else:
        banner_char_count = terminal_width - len(title) - 2
        left_banner_char_count = banner_char_count // 2
        right_banner_char_count = (
            banner_char_count / 2 if banner_char_count % 2 == 0 else (banner_char_count // 2) + 1
        )
        warning_header = (
            f"{warning_banner_char:{warning_banner_char}>{left_banner_char_count}}"
            f" {title} "
            f"{warning_banner_char:{warning_banner_char}<{right_banner_char_count}}"
        )

    warning_footer = warning_banner_char * terminal_width

    warning_message = (
        "\n\n"
        + warning_header
        + "\n"
        + message.center(terminal_width)
        + "\n"
        + warning_footer
        + "\n"
    )

    return warning_message


def user_warning(title: str, message: str) -> None:
    """
    Nicely raise warning messages for users

    Args:
        title: title of the warning message
        message: actual message body

    Returns:
        None

    Raises:
        N/A

    """
    warning_message = format_user_warning(title=title, message=message)
    logger.warning(warning_message)
    warn(warning_message)
