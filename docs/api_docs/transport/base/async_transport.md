<link rel="preload stylesheet" as="style" href="https://cdnjs.cloudflare.com/ajax/libs/10up-sanitize.css/11.0.1/sanitize.min.css" integrity="sha256-PK9q560IAAa6WVRRh76LtCaI8pjTJ2z11v0miyNNjrs=" crossorigin>
<link rel="preload stylesheet" as="style" href="https://cdnjs.cloudflare.com/ajax/libs/10up-sanitize.css/11.0.1/typography.min.css" integrity="sha256-7l/o7C8jubJiy74VsKTidCy1yBkRtiUGbVkYBylBqUg=" crossorigin>
<link rel="stylesheet preload" as="style" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/10.1.1/styles/github.min.css" crossorigin>
<script defer src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/10.1.1/highlight.min.js" integrity="sha256-Uv3H6lx7dJmRfRvH8TH6kJD1TSK1aFcwgx+mdg3epi8=" crossorigin></script>
<script>window.addEventListener('DOMContentLoaded', () => hljs.initHighlighting())</script>















#Module scrapli.transport.base.async_transport

scrapli.transport.async_transport

<details class="source">
    <summary>
        <span>Expand source code</span>
    </summary>
    <pre>
        <code class="python">
"""scrapli.transport.async_transport"""
from abc import ABC, abstractmethod

from scrapli.transport.base.base_transport import BaseTransport


class AsyncTransport(BaseTransport, ABC):
    @abstractmethod
    async def open(self) -> None:
        """
        Open the transport session

        Args:
            N/A

        Returns:
            None

        Raises:
            N/A

        """

    @abstractmethod
    async def read(self) -> bytes:
        """
        Read data from the transport session

        Args:
            N/A

        Returns:
            None

        Raises:
            N/A

        """
        </code>
    </pre>
</details>




## Classes

### AsyncTransport


```text
Helper class that provides a standard way to create an ABC using
inheritance.

Scrapli's transport base class

Args:
    base_transport_args: base transport args dataclass

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
class AsyncTransport(BaseTransport, ABC):
    @abstractmethod
    async def open(self) -> None:
        """
        Open the transport session

        Args:
            N/A

        Returns:
            None

        Raises:
            N/A

        """

    @abstractmethod
    async def read(self) -> bytes:
        """
        Read data from the transport session

        Args:
            N/A

        Returns:
            None

        Raises:
            N/A

        """
        </code>
    </pre>
</details>


#### Ancestors (in MRO)
- scrapli.transport.base.base_transport.BaseTransport
- abc.ABC
#### Descendants
- scrapli.transport.plugins.asyncssh.transport.AsyncsshTransport
- scrapli.transport.plugins.asynctelnet.transport.AsynctelnetTransport
#### Methods

    

##### open
`open(self) ‑> None`

```text
Open the transport session

Args:
    N/A

Returns:
    None

Raises:
    N/A
```



    

##### read
`read(self) ‑> bytes`

```text
Read data from the transport session

Args:
    N/A

Returns:
    None

Raises:
    N/A
```