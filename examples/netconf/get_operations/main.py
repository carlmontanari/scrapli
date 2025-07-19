"""examples.netconf.get_operations.main"""

import os
import sys

from scrapli import AuthOptions, Netconf

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
        # the simplest thing to do of course is just a "get_config"
        result = nc.get_config()

        # the srl config is *enormous* so just print a little of it...
        print(result.result[0:250])

        # we can also do "get" rpcs of course... here we'll just provide some simple filter for
        # snagging acl info; you can provide a filter to get_config in the same fashion.
        # default filter type is subtree, srlinux doesnt support xpath, so cant check that here,
        # but you can go head over to the functional tests to see that... but... basically just set
        # the filter_type and then pass a valid xpath filter
        result = nc.get(filter_="""<acl xmlns="urn:nokia.com:srlinux:acl:acl"></acl>""")

        print(result.result[0:250])


if __name__ == "__main__":
    main()
