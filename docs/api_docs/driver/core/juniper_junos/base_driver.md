<link rel="preload stylesheet" as="style" href="https://cdnjs.cloudflare.com/ajax/libs/10up-sanitize.css/11.0.1/sanitize.min.css" integrity="sha256-PK9q560IAAa6WVRRh76LtCaI8pjTJ2z11v0miyNNjrs=" crossorigin>
<link rel="preload stylesheet" as="style" href="https://cdnjs.cloudflare.com/ajax/libs/10up-sanitize.css/11.0.1/typography.min.css" integrity="sha256-7l/o7C8jubJiy74VsKTidCy1yBkRtiUGbVkYBylBqUg=" crossorigin>
<link rel="stylesheet preload" as="style" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/10.1.1/styles/github.min.css" crossorigin>
<script defer src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/10.1.1/highlight.min.js" integrity="sha256-Uv3H6lx7dJmRfRvH8TH6kJD1TSK1aFcwgx+mdg3epi8=" crossorigin></script>
<script>window.addEventListener('DOMContentLoaded', () => hljs.initHighlighting())</script>















#Module scrapli.driver.core.juniper_junos.base_driver

scrapli.driver.core.juniper_junos.base_driver

<details class="source">
    <summary>
        <span>Expand source code</span>
    </summary>
    <pre>
        <code class="python">
"""scrapli.driver.core.juniper_junos.base_driver"""
from scrapli.driver.network.base_driver import PrivilegeLevel

PRIVS = {
    "exec": (
        PrivilegeLevel(
            pattern=r"^({\w+:\d}\n){0,1}[\w\-@()/:\.]{1,63}>\s?$",
            name="exec",
            previous_priv="",
            deescalate="",
            escalate="",
            escalate_auth=False,
            escalate_prompt="",
        )
    ),
    "configuration": (
        PrivilegeLevel(
            pattern=r"^({\w+:\d}\[edit\]\n){0,1}[\w\-@()/:\.]{1,63}#\s?$",
            name="configuration",
            previous_priv="exec",
            deescalate="exit configuration-mode",
            escalate="configure",
            escalate_auth=False,
            escalate_prompt="",
        )
    ),
    "configuration_exclusive": (
        PrivilegeLevel(
            pattern=r"^({\w+:\d}\[edit\]\n){0,1}[\w\-@()/:\.]{1,63}#\s?$",
            name="configuration_exclusive",
            previous_priv="exec",
            deescalate="exit configuration-mode",
            escalate="configure exclusive",
            escalate_auth=False,
            escalate_prompt="",
        )
    ),
    "configuration_private": (
        PrivilegeLevel(
            pattern=r"^({\w+:\d}\[edit\]\n){0,1}[\w\-@()/:\.]{1,63}#\s?$",
            name="configuration_private",
            previous_priv="exec",
            deescalate="exit configuration-mode",
            escalate="configure private",
            escalate_auth=False,
            escalate_prompt="",
        )
    ),
    "shell": (
        PrivilegeLevel(
            pattern=r"^.*[%\$]\s?$",
            not_contains=["root"],
            name="shell",
            previous_priv="exec",
            deescalate="exit",
            escalate="start shell",
            escalate_auth=False,
            escalate_prompt="",
        )
    ),
    "root_shell": (
        PrivilegeLevel(
            pattern=r"^.*root@(?:\S*:\S*\s?)?[%\#]\s?$",
            name="root_shell",
            previous_priv="exec",
            deescalate="exit",
            escalate="start shell user root",
            escalate_auth=True,
            escalate_prompt=r"^[pP]assword:\s?$",
        )
    ),
}

FAILED_WHEN_CONTAINS = [
    "is ambiguous",
    "No valid completions",
    "unknown command",
    "syntax error",
]
        </code>
    </pre>
</details>