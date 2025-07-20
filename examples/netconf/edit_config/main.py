"""examples.netconf.edit_config.main"""

import os
import sys

from scrapli import AuthOptions, Netconf
from scrapli.netconf import DatastoreType

IS_DARWIN = sys.platform == "darwin"
HOST = os.getenv("SCRAPLI_HOST", "localhost" if IS_DARWIN else "172.20.20.16")
PORT = int(os.getenv("SCRAPLI_PORT") or 21830 if IS_DARWIN else 830)
USERNAME = os.getenv("SCRAPLI_USERNAME", "admin")
PASSWORD = os.getenv("SCRAPLI_USERNAME", "NokiaSrl1!")


def main() -> None:
    """A program to demonstrate *get* operations (of all kinds!) with netconf."""
    netconf = Netconf(
        host=HOST,
        port=PORT,
        auth_options=AuthOptions(
            username=USERNAME,
            password=PASSWORD,
        ),
    )

    with netconf as nc:
        # we can lock the config before doing things if we want
        result = nc.lock(target=DatastoreType.CANDIDATE)

        print(result.result)

        # and push a valid config of course
        result = nc.edit_config(
            config="""
            <system xmlns="urn:nokia.com:srlinux:general:system">
                <name xmlns="urn:nokia.com:srlinux:chassis:system-name">
                    <host-name>foozzzBaaaaAR</host-name>
                </name>
            </system>
            """,
            target=DatastoreType.CANDIDATE,
        )

        print(result.result)

        # then commit it
        result = nc.commit()

        print(result.result)

        # annnnd unlock
        result = nc.unlock(target=DatastoreType.CANDIDATE)

        print(result.result)

        # well put it back just in case using this w/ testing so we didnt make any change
        nc.edit_config(
            config="""
            <system xmlns="urn:nokia.com:srlinux:general:system">
                <name xmlns="urn:nokia.com:srlinux:chassis:system-name">
                    <host-name>srl</host-name>
                </name>
            </system>
            """,
            target=DatastoreType.CANDIDATE,
        )
        nc.commit()


if __name__ == "__main__":
    main()
