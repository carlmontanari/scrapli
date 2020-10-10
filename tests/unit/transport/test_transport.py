from typing import Optional

from scrapli.transport import Transport


class MockTransport(Transport):
    def __init__(self, host):
        super().__init__()
        self.host = host

    def open(self) -> None:
        return

    def close(self) -> None:
        return

    def isalive(self) -> bool:
        return True

    def read(self) -> bytes:
        return b""

    def write(self, channel_input: str) -> None:
        return

    def flush(self) -> None:
        return

    def set_timeout(self, timeout: Optional[int] = None) -> None:
        return


def test_transport_abc_init():
    transport = MockTransport("racecar")
    assert transport.host == "racecar"
