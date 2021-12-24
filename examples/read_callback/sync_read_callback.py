"""examples.read_callback.sync_read_callback"""
from scrapli.driver.core import IOSXEDriver
from scrapli.driver.generic.base_driver import ReadCallback
from scrapli.driver.generic.sync_driver import GenericDriver

device = {
    "host": "c3560",
    "auth_strict_key": False,
    "ssh_config_file": True,
}


def callback_one(cls: GenericDriver, read_output: str):
    """Callback that enters config mode (as a silly example)"""
    _ = read_output

    # note that because cls is typed `GenericDriver` mypy/IDE will not like this, but it does work
    # because yay python :) (assuming the driver you use is a NetworkDriver of course)
    cls.acquire_priv("configuration")
    cls.channel.send_return()


def callback_two(cls: GenericDriver, read_output: str):
    """Callback that enters runs a silly command"""
    print(f"previous read output : {read_output}")

    r = cls.send_command("do show run | i hostname")
    print(f"result: {r.result}")


if __name__ == "__main__":
    with IOSXEDriver(**device) as conn:
        callbacks = [
            ReadCallback(
                contains="rtr1#",
                callback=callback_one,
                name="enter config mode callback",
                case_insensitive=False,
            ),
            ReadCallback(
                contains_re=r"^rtr1\(config\)#",
                callback=callback_two,
                complete=True,
            ),
        ]
        conn.read_callback(callbacks=callbacks, initial_input="show run | i hostname")
