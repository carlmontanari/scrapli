from unittest import mock

import pytest


@pytest.fixture
def transport():
    # creating a mock transport to use in a "dummy" StreamWriter -- we set the "out_buf" attribute
    # so we can assert what has been written into the writer easily
    transport = mock.Mock()
    transport.out_buf = bytearray()

    def write(chunk):
        transport.out_buf.extend(chunk)

    transport.write.side_effect = write
    transport.is_closing.return_value = False
    return transport


@pytest.fixture
def protocol(transport):
    protocol = mock.Mock(transport=transport)
    return protocol
