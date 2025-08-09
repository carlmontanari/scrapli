"""scrapli.definition_options.mikrotik_routeros"""

from scrapli import Cli


def mikrotik_routeros_post_init(c: Cli) -> None:
    """
    Apply mikrotik routeros specific options after Cli init

    Args:
        c: the Cli object to update

    Returns:
        None

    Raises:
        N/A

    """
    c.auth_options.username = f"{c.auth_options.username}+tc"
    c.session_options.return_char = "\r\n"
