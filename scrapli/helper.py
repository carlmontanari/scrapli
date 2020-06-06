"""scrapli.helper"""
import importlib
import os
import re
import warnings
from functools import lru_cache
from io import TextIOWrapper
from pathlib import Path
from typing import Any, Dict, List, Optional, Pattern, TextIO, Tuple, Union

import pkg_resources  # pylint: disable=C0411

from scrapli.exceptions import TransportPluginError


def _find_transport_plugin(transport: str) -> Tuple[Any, Tuple[str, ...]]:
    """
    Find non-core transport plugins and required plugin arguments

    Args:
        transport: string name of the desired transport, i.e.: paramiko or ssh2

    Returns:
        transport_class: class representing the given transport
        required_transport_args: tuple of required arguments for given transport

    Raises:
        ModuleNotFoundError: if unable to  find scrapli transport module
        TransportPluginError: if unable to load `Transport` and `TRANSPORT_ARGS` from given
            transport module

    """
    try:
        transport_plugin_lib = importlib.import_module(f"scrapli_{transport}.transport")
    except ModuleNotFoundError as exc:
        err = f"Module '{exc.name}' not found!"
        msg = f"***** {err} {'*' * (80 - len(err))}"
        fix = (
            "To resolve this issue, ensure you are referencing a valid transport plugin. Transport"
            " plugins should be named similar to `scrapli_paramiko` or `scrapli_ssh2`, and can be "
            "selected by passing simply `paramiko` or `ssh2` into the scrapli driver."
        )
        warning = "\n" + msg + "\n" + fix + "\n" + msg
        raise ModuleNotFoundError(warning)
    transport_class = getattr(transport_plugin_lib, "Transport", None)
    required_transport_args = getattr(transport_plugin_lib, "TRANSPORT_ARGS", None)
    if not all([transport_class, required_transport_args]):
        msg = f"Failed to load transport plugin `{transport}` transport class or required arguments"
        raise TransportPluginError(msg)
    return transport_class, required_transport_args


@lru_cache()
def get_prompt_pattern(prompt: str, class_prompt: str) -> Pattern[bytes]:
    """
    Return compiled prompt pattern

    Given a potential prompt and the Channel class' prompt, return compiled prompt pattern

    Args:
        prompt: bytes string to process
        class_prompt: Channel class prompt pattern; never re.escape class prompt pattern

    Returns:
        output: bytes string each line right stripped

    Raises:
        N/A

    """
    check_prompt = prompt or class_prompt
    if isinstance(check_prompt, str):
        bytes_check_prompt = check_prompt.encode()
    else:
        bytes_check_prompt = check_prompt

    if bytes_check_prompt.startswith(b"^") and bytes_check_prompt.endswith(b"$"):
        return re.compile(bytes_check_prompt, flags=re.M | re.I)
    if check_prompt == class_prompt:
        return re.compile(bytes_check_prompt, flags=re.M | re.I)
    return re.compile(re.escape(bytes_check_prompt))


def normalize_lines(output: bytes) -> bytes:
    r"""
    Normalize lines

    Split output lines to remove \r\n, rstrip each line and rejoin

    Args:
        output: bytes string to process

    Returns:
        bytes: bytes string each line right stripped

    Raises:
        N/A

    """
    return b"\n".join([line.rstrip() for line in output.splitlines()])


def strip_ansi(output: bytes) -> bytes:
    """
    Strip ansi characters from output

    Args:
        output: bytes from previous reads if needed

    Returns:
        bytes: bytes output read from channel with ansi characters removed

    Raises:
        N/A

    """
    ansi_escape_pattern = re.compile(rb"\x1b(\[.*?[@-~]|\].*?(\x07|\x1b\\))")
    output = re.sub(pattern=ansi_escape_pattern, repl=b"", string=output)
    return output


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
        from textfsm.clitable import CliTable  # pylint: disable=C0415
        from ntc_templates import templates  # pylint: disable=C0415,W0611
    except ModuleNotFoundError as exc:
        err = f"Module '{exc.name}' not installed!"
        msg = f"***** {err} {'*' * (80 - len(err))}"
        fix = (
            f"To resolve this issue, install '{exc.name}'. You can do this in one of the following"
            " ways:\n"
            "1: 'pip install -r requirements-textfsm.txt'\n"
            "2: 'pip install scrapli[textfsm]'"
        )
        warning = "\n" + msg + "\n" + fix + "\n" + msg
        warnings.warn(warning)
        return None
    template_dir = pkg_resources.resource_filename("ntc_templates", "templates")
    cli_table = CliTable("index", template_dir)
    template_index = cli_table.index.GetRowMatch({"Platform": platform, "Command": command})
    if not template_index:
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
        pass
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
        from genie.conf.base import Device  # pylint: disable=C0415
        from genie.libs.parser.utils import get_parser  # pylint: disable=C0415
    except ModuleNotFoundError as exc:
        err = f"Module '{exc.name}' not installed!"
        msg = f"***** {err} {'*' * (80 - len(err))}"
        fix = (
            f"To resolve this issue, install '{exc.name}'. You can do this in one of the following"
            " ways:\n"
            "1: 'pip install -r requirements-genie.txt'\n"
            "2: 'pip install scrapli[genie]'"
        )
        warning = "\n" + msg + "\n" + fix + "\n" + msg
        warnings.warn(warning)
        return []

    genie_device = Device("scrapli_device", custom={"abstraction": {"order": ["os"]}}, os=platform)

    try:
        get_parser(command, genie_device)
        genie_parsed_result = genie_device.parse(command, output=output)
        if not genie_parsed_result:
            return []
        if isinstance(genie_parsed_result, (list, dict)):
            return genie_parsed_result
    # have to catch base exception because that is all genie raises for some reason :(
    except Exception:  # pylint: disable=E0012,W0703
        pass
    return []


def resolve_ssh_config(ssh_config_file: str) -> str:
    """
    Resolve ssh configuration file from provided string

    If provided string is empty (`""`) try to resolve system ssh config files located at
    `~/.ssh/config` or `/etc/ssh/ssh_config`.

    Args:
        ssh_config_file: string representation of ssh config file to try to use

    Returns:
        str: string path to ssh config file or an empty string

    Raises:
        N/A

    """
    if Path(ssh_config_file).is_file():
        return str(Path(ssh_config_file))
    if Path(os.path.expanduser("~/.ssh/config")).is_file():
        return str(Path(os.path.expanduser("~/.ssh/config")))
    if Path("/etc/ssh/ssh_config").is_file():
        return str(Path("/etc/ssh/ssh_config"))
    return ""


def resolve_ssh_known_hosts(ssh_known_hosts: str) -> str:
    """
    Resolve ssh known hosts file from provided string

    If provided string is empty (`""`) try to resolve system known hosts files located at
    `~/.ssh/known_hosts` or `/etc/ssh/ssh_known_hosts`.

    Args:
        ssh_known_hosts: string representation of ssh config file to try to use

    Returns:
        str: string path to ssh known hosts file or an empty string

    Raises:
        N/A

    """
    if Path(ssh_known_hosts).is_file():
        return str(Path(ssh_known_hosts))
    if Path(os.path.expanduser("~/.ssh/known_hosts")).is_file():
        return str(Path(os.path.expanduser("~/.ssh/known_hosts")))
    if Path("/etc/ssh/ssh_known_hosts").is_file():
        return str(Path("/etc/ssh/ssh_known_hosts"))
    return ""


def resolve_file(file: str) -> str:
    """
    Resolve file from provided string

    Args:
        file: string path to file

    Returns:
        str: string path to file

    Raises:
        ValueError: if file cannot be resolved

    """
    if Path(file).is_file():
        return str(Path(file))
    if Path(os.path.expanduser(file)).is_file():
        return str(Path(os.path.expanduser(file)))
    raise ValueError(f"File path `{file}` could not be resolved")
