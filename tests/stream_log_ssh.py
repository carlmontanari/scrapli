import logging
from io import StringIO

from scrapli.driver.core import IOSXEDriver

logstream = StringIO()
logging.basicConfig(stream=logstream, level=logging.DEBUG)
logger = logging.getLogger("scrapli")


conn1 = IOSXEDriver(
    host="localhost",
    auth_username="scrapli",
    auth_private_key='tests/test_data/files/vrnetlab_key',
    transport="system",
    port=2211,
    auth_strict_key=False
)


def run_conn1():
    conn1.open()
    result = conn1.get_prompt()
    print(f"Conn1 prompt: {result}")
    result = conn1.send_command("show version")
    print(result.result)
    conn1.close()


run_conn1()
