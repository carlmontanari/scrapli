<link rel="preload stylesheet" as="style" href="https://cdnjs.cloudflare.com/ajax/libs/10up-sanitize.css/11.0.1/sanitize.min.css" integrity="sha256-PK9q560IAAa6WVRRh76LtCaI8pjTJ2z11v0miyNNjrs=" crossorigin>
<link rel="preload stylesheet" as="style" href="https://cdnjs.cloudflare.com/ajax/libs/10up-sanitize.css/11.0.1/typography.min.css" integrity="sha256-7l/o7C8jubJiy74VsKTidCy1yBkRtiUGbVkYBylBqUg=" crossorigin>
<link rel="stylesheet preload" as="style" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/10.1.1/styles/github.min.css" crossorigin>
<script defer src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/10.1.1/highlight.min.js" integrity="sha256-Uv3H6lx7dJmRfRvH8TH6kJD1TSK1aFcwgx+mdg3epi8=" crossorigin></script>
<script>window.addEventListener('DOMContentLoaded', () => hljs.initHighlighting())</script>















#Module scrapli.driver.core.arista_eos.base_driver

scrapli.driver.core.arista_eos.base_driver

<details class="source">
    <summary>
        <span>Expand source code</span>
    </summary>
    <pre>
        <code class="python">
"""scrapli.driver.core.arista_eos.base_driver"""
import re
from typing import Dict

from scrapli.driver.network.base_driver import PrivilegeLevel
from scrapli.exceptions import ScrapliValueError

PRIVS = {
    "exec": (
        PrivilegeLevel(
            pattern=r"^[\w.\-@()/: ]{1,63}>\s?$",
            name="exec",
            previous_priv="",
            deescalate="",
            escalate="",
            escalate_auth=False,
            escalate_prompt="",
        )
    ),
    "privilege_exec": (
        PrivilegeLevel(
            pattern=r"^[\w.\-@()/: ]{1,63}#\s?$",
            name="privilege_exec",
            previous_priv="exec",
            deescalate="disable",
            escalate="enable",
            escalate_auth=True,
            escalate_prompt=r"^[pP]assword:\s?$",
            not_contains=["(config"],
        )
    ),
    "configuration": (
        PrivilegeLevel(
            pattern=r"^[\w.\-@()/: ]{1,63}\(config[\w.\-@/:]{0,32}\)#\s?$",
            name="configuration",
            previous_priv="privilege_exec",
            deescalate="end",
            escalate="configure terminal",
            escalate_auth=False,
            escalate_prompt="",
            not_contains=["(config-s-"],
        )
    ),
}

FAILED_WHEN_CONTAINS = [
    "% Ambiguous command",
    "% Error",
    "% Incomplete command",
    "% Invalid input",
    "% Cannot commit",
    "% Unavailable command",
]


class EOSDriverBase:
    # EOSDriverBase Mixin values set in init of sync/async NetworkDriver classes
    privilege_levels: Dict[str, PrivilegeLevel]

    def _create_configuration_session(self, session_name: str) -> None:
        """
        Handle configuration session creation tasks for consistency between sync/async versions

        Args:
            session_name: name of session to register

        Returns:
            None

        Raises:
            ScrapliValueError: if a session of given name already exists

        """
        if session_name in self.privilege_levels.keys():
            msg = (
                f"session name `{session_name}` already registered as a privilege level, chose a "
                "unique session name"
            )
            raise ScrapliValueError(msg)
        sess_prompt = re.escape(session_name[:6])
        pattern = (
            rf"^[a-z0-9.\-@()/: ]{{1,63}}\(config\-s\-{sess_prompt}[a-z0-9_.\-@/:]{{0,32}}\)#\s?$"
        )
        name = session_name
        config_session = PrivilegeLevel(
            pattern=pattern,
            name=name,
            previous_priv="privilege_exec",
            deescalate="end",
            escalate=f"configure session {session_name}",
            escalate_auth=False,
            escalate_prompt="",
        )
        self.privilege_levels[name] = config_session
        </code>
    </pre>
</details>




## Classes

### EOSDriverBase



<details class="source">
    <summary>
        <span>Expand source code</span>
    </summary>
    <pre>
        <code class="python">
class EOSDriverBase:
    # EOSDriverBase Mixin values set in init of sync/async NetworkDriver classes
    privilege_levels: Dict[str, PrivilegeLevel]

    def _create_configuration_session(self, session_name: str) -> None:
        """
        Handle configuration session creation tasks for consistency between sync/async versions

        Args:
            session_name: name of session to register

        Returns:
            None

        Raises:
            ScrapliValueError: if a session of given name already exists

        """
        if session_name in self.privilege_levels.keys():
            msg = (
                f"session name `{session_name}` already registered as a privilege level, chose a "
                "unique session name"
            )
            raise ScrapliValueError(msg)
        sess_prompt = re.escape(session_name[:6])
        pattern = (
            rf"^[a-z0-9.\-@()/: ]{{1,63}}\(config\-s\-{sess_prompt}[a-z0-9_.\-@/:]{{0,32}}\)#\s?$"
        )
        name = session_name
        config_session = PrivilegeLevel(
            pattern=pattern,
            name=name,
            previous_priv="privilege_exec",
            deescalate="end",
            escalate=f"configure session {session_name}",
            escalate_auth=False,
            escalate_prompt="",
        )
        self.privilege_levels[name] = config_session
        </code>
    </pre>
</details>


#### Descendants
- scrapli.driver.core.arista_eos.async_driver.AsyncEOSDriver
- scrapli.driver.core.arista_eos.sync_driver.EOSDriver
#### Class variables

    
`privilege_levels: Dict[str, scrapli.driver.network.base_driver.PrivilegeLevel]`