<link rel="preload stylesheet" as="style" href="https://cdnjs.cloudflare.com/ajax/libs/10up-sanitize.css/11.0.1/sanitize.min.css" integrity="sha256-PK9q560IAAa6WVRRh76LtCaI8pjTJ2z11v0miyNNjrs=" crossorigin>
<link rel="preload stylesheet" as="style" href="https://cdnjs.cloudflare.com/ajax/libs/10up-sanitize.css/11.0.1/typography.min.css" integrity="sha256-7l/o7C8jubJiy74VsKTidCy1yBkRtiUGbVkYBylBqUg=" crossorigin>
<link rel="stylesheet preload" as="style" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/10.1.1/styles/github.min.css" crossorigin>
<script defer src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/10.1.1/highlight.min.js" integrity="sha256-Uv3H6lx7dJmRfRvH8TH6kJD1TSK1aFcwgx+mdg3epi8=" crossorigin></script>
<script>window.addEventListener('DOMContentLoaded', () => hljs.initHighlighting())</script>















#Module scrapli.exceptions

scrapli.exceptions

<details class="source">
    <summary>
        <span>Expand source code</span>
    </summary>
    <pre>
        <code class="python">
"""scrapli.exceptions"""
from typing import Optional


class ScrapliException(Exception):
    """Base Exception for all scrapli exceptions"""


class ScrapliModuleNotFound(ScrapliException):
    """ModuleNotFound but for scrapli related issues"""


class ScrapliTypeError(ScrapliException):
    """TypeError but for scrapli related typing issues"""


class ScrapliValueError(ScrapliException):
    """ValueError but for scrapli related value issues"""


class ScrapliUnsupportedPlatform(ScrapliException):
    """Exception for unsupported platform; i.e. using system transport on windows"""


class ScrapliTransportPluginError(ScrapliException):
    """Exception for transport plugin issues"""


class ScrapliConnectionNotOpened(ScrapliException):
    """Exception for trying to operate on a transport which has not been opened"""

    def __init__(
        self,
        message: Optional[str] = None,
    ) -> None:
        """
        Scrapli connection not opened exception

        Args:
            message: optional message

        Returns:
            None

        Raises:
            N/A

        """
        if not message:
            self.message = (
                "connection not opened, but attempting to call a method that requires an open "
                "connection, do you need to call 'open()'?"
            )
        else:
            self.message = message
        super().__init__(self.message)


class ScrapliAuthenticationFailed(ScrapliException):
    """Exception for scrapli authentication issues"""


class ScrapliConnectionError(ScrapliException):
    """Exception for underlying connection issues"""


class ScrapliTimeout(ScrapliException):
    """Exception for any scrapli timeouts"""


class ScrapliCommandFailure(ScrapliException):
    """Exception for scrapli command/config failures"""


class ScrapliPrivilegeError(ScrapliException):
    """Exception for all privilege related scrapli issues"""
        </code>
    </pre>
</details>




## Classes

### ScrapliAuthenticationFailed


```text
Exception for scrapli authentication issues
```

<details class="source">
    <summary>
        <span>Expand source code</span>
    </summary>
    <pre>
        <code class="python">
class ScrapliAuthenticationFailed(ScrapliException):
    """Exception for scrapli authentication issues"""
        </code>
    </pre>
</details>


#### Ancestors (in MRO)
- scrapli.exceptions.ScrapliException
- builtins.Exception
- builtins.BaseException



### ScrapliCommandFailure


```text
Exception for scrapli command/config failures
```

<details class="source">
    <summary>
        <span>Expand source code</span>
    </summary>
    <pre>
        <code class="python">
class ScrapliCommandFailure(ScrapliException):
    """Exception for scrapli command/config failures"""
        </code>
    </pre>
</details>


#### Ancestors (in MRO)
- scrapli.exceptions.ScrapliException
- builtins.Exception
- builtins.BaseException



### ScrapliConnectionError


```text
Exception for underlying connection issues
```

<details class="source">
    <summary>
        <span>Expand source code</span>
    </summary>
    <pre>
        <code class="python">
class ScrapliConnectionError(ScrapliException):
    """Exception for underlying connection issues"""
        </code>
    </pre>
</details>


#### Ancestors (in MRO)
- scrapli.exceptions.ScrapliException
- builtins.Exception
- builtins.BaseException



### ScrapliConnectionNotOpened


```text
Exception for trying to operate on a transport which has not been opened

Scrapli connection not opened exception

Args:
    message: optional message

Returns:
    None

Raises:
    N/A
```

<details class="source">
    <summary>
        <span>Expand source code</span>
    </summary>
    <pre>
        <code class="python">
class ScrapliConnectionNotOpened(ScrapliException):
    """Exception for trying to operate on a transport which has not been opened"""

    def __init__(
        self,
        message: Optional[str] = None,
    ) -> None:
        """
        Scrapli connection not opened exception

        Args:
            message: optional message

        Returns:
            None

        Raises:
            N/A

        """
        if not message:
            self.message = (
                "connection not opened, but attempting to call a method that requires an open "
                "connection, do you need to call 'open()'?"
            )
        else:
            self.message = message
        super().__init__(self.message)
        </code>
    </pre>
</details>


#### Ancestors (in MRO)
- scrapli.exceptions.ScrapliException
- builtins.Exception
- builtins.BaseException



### ScrapliException


```text
Base Exception for all scrapli exceptions
```

<details class="source">
    <summary>
        <span>Expand source code</span>
    </summary>
    <pre>
        <code class="python">
class ScrapliException(Exception):
    """Base Exception for all scrapli exceptions"""
        </code>
    </pre>
</details>


#### Ancestors (in MRO)
- builtins.Exception
- builtins.BaseException
#### Descendants
- scrapli.exceptions.ScrapliAuthenticationFailed
- scrapli.exceptions.ScrapliCommandFailure
- scrapli.exceptions.ScrapliConnectionError
- scrapli.exceptions.ScrapliConnectionNotOpened
- scrapli.exceptions.ScrapliModuleNotFound
- scrapli.exceptions.ScrapliPrivilegeError
- scrapli.exceptions.ScrapliTimeout
- scrapli.exceptions.ScrapliTransportPluginError
- scrapli.exceptions.ScrapliTypeError
- scrapli.exceptions.ScrapliUnsupportedPlatform
- scrapli.exceptions.ScrapliValueError



### ScrapliModuleNotFound


```text
ModuleNotFound but for scrapli related issues
```

<details class="source">
    <summary>
        <span>Expand source code</span>
    </summary>
    <pre>
        <code class="python">
class ScrapliModuleNotFound(ScrapliException):
    """ModuleNotFound but for scrapli related issues"""
        </code>
    </pre>
</details>


#### Ancestors (in MRO)
- scrapli.exceptions.ScrapliException
- builtins.Exception
- builtins.BaseException



### ScrapliPrivilegeError


```text
Exception for all privilege related scrapli issues
```

<details class="source">
    <summary>
        <span>Expand source code</span>
    </summary>
    <pre>
        <code class="python">
class ScrapliPrivilegeError(ScrapliException):
    """Exception for all privilege related scrapli issues"""
        </code>
    </pre>
</details>


#### Ancestors (in MRO)
- scrapli.exceptions.ScrapliException
- builtins.Exception
- builtins.BaseException



### ScrapliTimeout


```text
Exception for any scrapli timeouts
```

<details class="source">
    <summary>
        <span>Expand source code</span>
    </summary>
    <pre>
        <code class="python">
class ScrapliTimeout(ScrapliException):
    """Exception for any scrapli timeouts"""
        </code>
    </pre>
</details>


#### Ancestors (in MRO)
- scrapli.exceptions.ScrapliException
- builtins.Exception
- builtins.BaseException



### ScrapliTransportPluginError


```text
Exception for transport plugin issues
```

<details class="source">
    <summary>
        <span>Expand source code</span>
    </summary>
    <pre>
        <code class="python">
class ScrapliTransportPluginError(ScrapliException):
    """Exception for transport plugin issues"""
        </code>
    </pre>
</details>


#### Ancestors (in MRO)
- scrapli.exceptions.ScrapliException
- builtins.Exception
- builtins.BaseException



### ScrapliTypeError


```text
TypeError but for scrapli related typing issues
```

<details class="source">
    <summary>
        <span>Expand source code</span>
    </summary>
    <pre>
        <code class="python">
class ScrapliTypeError(ScrapliException):
    """TypeError but for scrapli related typing issues"""
        </code>
    </pre>
</details>


#### Ancestors (in MRO)
- scrapli.exceptions.ScrapliException
- builtins.Exception
- builtins.BaseException



### ScrapliUnsupportedPlatform


```text
Exception for unsupported platform; i.e. using system transport on windows
```

<details class="source">
    <summary>
        <span>Expand source code</span>
    </summary>
    <pre>
        <code class="python">
class ScrapliUnsupportedPlatform(ScrapliException):
    """Exception for unsupported platform; i.e. using system transport on windows"""
        </code>
    </pre>
</details>


#### Ancestors (in MRO)
- scrapli.exceptions.ScrapliException
- builtins.Exception
- builtins.BaseException



### ScrapliValueError


```text
ValueError but for scrapli related value issues
```

<details class="source">
    <summary>
        <span>Expand source code</span>
    </summary>
    <pre>
        <code class="python">
class ScrapliValueError(ScrapliException):
    """ValueError but for scrapli related value issues"""
        </code>
    </pre>
</details>


#### Ancestors (in MRO)
- scrapli.exceptions.ScrapliException
- builtins.Exception
- builtins.BaseException