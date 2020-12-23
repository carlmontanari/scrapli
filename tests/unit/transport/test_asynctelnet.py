import asyncio
import sys
from asyncio import StreamReader, StreamWriter

import pytest

from scrapli.exceptions import ConnectionNotOpened, ScrapliTimeout
from scrapli.transport import AsyncTelnetTransport


def test_creation():
    conn = AsyncTelnetTransport("localhost")
    assert conn.host == "localhost"
    assert conn.port == 23
    assert conn._isauthenticated is False


@pytest.mark.asyncio
@pytest.mark.skipif(sys.platform.startswith("win"), reason="skipping on windows")
async def test_open_failure():
    conn = AsyncTelnetTransport("localhost", port=23)
    with pytest.raises(ConnectionNotOpened) as exc:
        await conn.open()
    assert (
        str(exc.value)
        == "Failed to open telnet session to host localhost -- do you have a bad host/port?"
    )


@pytest.mark.asyncio
async def test_requires_open():
    # probably should go back and change this in asycnssh as well.... really
    # only need to decorate the "write" method -- everything that a user should touch will call
    # write to send a return char... the read (being a coroutine) does not actually raise anything
    # for the async transports...
    conn = AsyncTelnetTransport("localhost")
    with pytest.raises(ConnectionNotOpened):
        conn.write("blah")


@pytest.mark.asyncio
async def test_handle_control_chars(transport, protocol):
    conn = AsyncTelnetTransport("localhost")
    conn._isauthenticated = True
    conn.stdout = StreamReader()
    conn.stdin = StreamWriter(transport, protocol, reader=None, loop=asyncio.get_event_loop())

    data = b"\xff\xfd\x18\xff\xfd \xff\xfd#someoutput\xff\xfd'\xff\xfb\x03\xff\xfd\x01\xff\xfd\x1f\xff\xfb\x05\xff\xfd!\xff\xfb\x03\xff\xfb\x01moreoutput"
    conn.stdout.feed_data(data)
    output = await conn._handle_control_chars()
    assert output == b"someoutputmoreoutput"
    assert (
        conn.stdin.transport.out_buf
        == b"\xff\xfc\x18\xff\xfc \xff\xfc#\xff\xfc'\xff\xfe\x03\xff\xfc\x01\xff\xfc\x1f\xff\xfe\x05\xff\xfc!\xff\xfe\x03\xff\xfe\x01"
    )


@pytest.mark.skipif(sys.version_info < (3, 7), reason="requires python3.7 or higher")
@pytest.mark.asyncio
async def test_authenticate(transport, protocol):
    conn = AsyncTelnetTransport(
        "localhost",
        auth_password="lookforthispassword",
        auth_username="lookforthisusername",
        timeout_ops=10,
        timeout_socket=5,
    )
    conn.stdout = StreamReader()
    conn.stdin = StreamWriter(transport, protocol, reader=None, loop=asyncio.get_event_loop())
    # feed data in w/ the username prompt already in it -- auth should then send the username and
    # clear the buffer... then it should read and see the password that we are inserting later
    data = b"\xff\xfd\x18\xff\xfd \xff\xfd#username:\xff\xfd'\xff\xfb\x03\xff\xfd\x01\xff\xfd\x1f\xff\xfb\x05\xff\xfd!\xff\xfb\x03\xff\xfb\x01"
    conn.stdout.feed_data(data)

    async def _put_login_data_in_reader():
        # this sleep is enough that we should *always* see a an additional return char that we send
        # when we dont get any output on telnet connections
        await asyncio.sleep(1.5)
        conn.stdout.feed_data(b"Password:")

    asyncio.create_task(_put_login_data_in_reader())
    await conn._authenticate()
    # asserting that we entered the user/pass correctly
    assert b"lookforthisusername" in conn.stdin.transport.out_buf
    assert b"lookforthispassword" in conn.stdin.transport.out_buf
    # a return for the username, one for password and one for the extra return we send when we dont
    # see the password prompt soon enough
    assert conn.stdin.transport.out_buf.count(b"\n") >= 3


@pytest.mark.asyncio
async def test_authenticate_timeout(transport, protocol):
    conn = AsyncTelnetTransport(
        "localhost", auth_password="lookforthispassword", auth_username="lookforthisusername"
    )

    # make the timeout way faster so we dont have to wait
    conn._timeout_ops_auth = 0.25

    conn.stdout = StreamReader()
    conn.stdin = StreamWriter(transport, protocol, reader=None, loop=asyncio.get_event_loop())

    # feed data in w/ the username prompt already in it -- auth should then send the username and
    # clear the buffer... then it should read and see the password that we are inserting later
    data = b"\xff\xfd\x18\xff\xfd \xff\xfd#username:\xff\xfd'\xff\xfb\x03\xff\xfd\x01\xff\xfd\x1f\xff\xfb\x05\xff\xfd!\xff\xfb\x03\xff\xfb\x01"
    conn.stdout.feed_data(data)

    with pytest.raises(ScrapliTimeout) as exc:
        await conn._authenticate()
    assert str(exc.value) == "Timed out looking for telnet login prompts"
    # asserting that we at least got the username sent
    assert b"lookforthisusername" in conn.stdin.transport.out_buf


@pytest.mark.asyncio
async def test_telnet_isauthenticated_success(transport, protocol):
    conn = AsyncTelnetTransport("localhost")
    assert conn._isauthenticated is False

    conn.stdout = StreamReader()
    conn.stdin = StreamWriter(transport, protocol, reader=None, loop=asyncio.get_event_loop())

    # feed data in w/ the username prompt already in it -- auth should then send the username and
    # clear the buffer... then it should read and see the password that we are inserting later
    data = b"averyniceswitch#"
    conn.stdout.feed_data(data)
    await conn._telnet_isauthenticated()
    assert conn._isauthenticated is True


@pytest.mark.asyncio
async def test_telnet_isauthenticated_success_set_binary_transmission(transport, protocol):
    conn = AsyncTelnetTransport("localhost")
    assert conn._isauthenticated is False
    assert conn._stdout_binary_transmission is False

    conn.stdout = StreamReader()
    conn.stdin = StreamWriter(transport, protocol, reader=None, loop=asyncio.get_event_loop())

    data = b"\x00averyniceswitch#"
    conn.stdout.feed_data(data)
    await conn._telnet_isauthenticated()
    assert conn._isauthenticated is True
    assert conn._stdout_binary_transmission is True


@pytest.mark.asyncio
async def test_telnet_isauthenticated_failed_username(transport, protocol):
    conn = AsyncTelnetTransport("localhost")

    conn.stdout = StreamReader()
    conn.stdin = StreamWriter(transport, protocol, reader=None, loop=asyncio.get_event_loop())

    data = b"username:"
    conn.stdout.feed_data(data)

    _isauthenticated = await conn._telnet_isauthenticated()
    assert _isauthenticated is False


@pytest.mark.asyncio
async def test_telnet_isauthenticated_failed_password(transport, protocol):
    conn = AsyncTelnetTransport("localhost")

    conn.stdout = StreamReader()
    conn.stdin = StreamWriter(transport, protocol, reader=None, loop=asyncio.get_event_loop())

    data = b"password:"
    conn.stdout.feed_data(data)

    _isauthenticated = await conn._telnet_isauthenticated()
    assert _isauthenticated is False


@pytest.mark.asyncio
async def test_isalive_true():
    conn = AsyncTelnetTransport("localhost")
    conn._isauthenticated = True
    conn.stdout = StreamReader()
    data = b"somethingtoread"
    conn.stdout.feed_data(data)
    assert conn.isalive() is True


@pytest.mark.asyncio
async def test_isalive_false_not_auth():
    conn = AsyncTelnetTransport("localhost")
    conn._isauthenticated = False
    conn.stdout = StreamReader()
    data = b"somethingtoread"
    conn.stdout.feed_data(data)
    assert conn.isalive() is False


@pytest.mark.asyncio
async def test_isalive_false_eof():
    conn = AsyncTelnetTransport("localhost")
    conn._isauthenticated = True
    conn.stdout = StreamReader()
    conn.stdout.feed_eof()
    assert conn.isalive() is False


@pytest.mark.asyncio
async def test_read_success():
    conn = AsyncTelnetTransport("localhost")

    # load up the conn's stdout obj w/ a little faked out streamreader
    conn.stdout = StreamReader()
    data = b"somethingtoread"
    conn.stdout.feed_data(data)
    out = await conn.read()
    assert out == data


@pytest.mark.asyncio
async def test_read_success_stdout_binary():
    conn = AsyncTelnetTransport("localhost")
    conn.stdout = StreamReader()
    conn._stdout_binary_transmission = True
    data = b"\x00somethingtoread"
    conn.stdout.feed_data(data)
    out = await conn.read()
    assert out == b"somethingtoread"


@pytest.mark.asyncio
async def test_read_timeout():
    conn = AsyncTelnetTransport("localhost")
    conn.stdout = StreamReader()
    conn._stdout_binary_transmission = True
    conn.set_timeout(0.01)
    with pytest.raises(ScrapliTimeout):
        await conn.read()


def test_set_timeout():
    conn = AsyncTelnetTransport("localhost")
    assert conn.timeout_transport == 30
    conn.set_timeout(999)
    assert conn.timeout_transport == 999
