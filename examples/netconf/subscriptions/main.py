"""examples.netconf.subscriptions.main"""

import os
import sys
from time import sleep

from scrapli import AuthOptions, Netconf
from scrapli.exceptions import NoMessagesException

IS_DARWIN = sys.platform == "darwin"
HOST = os.getenv("SCRAPLI_HOST", "localhost" if IS_DARWIN else "172.20.20.18")
PORT = int(os.getenv("SCRAPLI_PORT") or 23830 if IS_DARWIN else 830)
USERNAME = os.getenv("SCRAPLI_USERNAME", "root")
PASSWORD = os.getenv("SCRAPLI_USERNAME", "password")

IOSXE_HOST = None
IOSXE_PORT = 830
IOSXE_USERNAME = ""
IOSXE_PASSWORD = ""


def main() -> None:
    """A program to using raw_rpc to create a subscription and fetch its messages"""
    netconf = Netconf(
        host=HOST,
        port=PORT,
        auth_options=AuthOptions(
            username=USERNAME,
            password=PASSWORD,
        ),
    )

    with netconf as nc:
        # because there are a zillion variants to how to setup subscriptions -- i.e. create vs
        # establish then differing ways to setup the payload based on the rfc that is followed
        # scrapli decided... nope. you can just send what you need to create your subscription
        # however makes sense for your server. here we'll just do a very simple example.
        result = nc.raw_rpc(
            payload="""
            <create-subscription xmlns="urn:ietf:params:xml:ns:netconf:notification:1.0">
            </create-subscription>
        """
        )

        print(result.result)

        try:
            notif = nc.get_next_notification()
            print(notif)
        except NoMessagesException:
            # expected as the netopeer server churns out a notification every 3s or something for
            # the "boring counter" object
            print("sad panda, no notifications... *yet*")

        # enough to ensure we can fetch a notification
        sleep(10)

        try:
            notif = nc.get_next_notification()
            print(notif)
        except NoMessagesException:
            print("womp womp, no notifications to snag sadly...")

    if IOSXE_HOST is None:
        return

    # the following assumes some standard iosxe device (with netconf running ofc) like iosxe
    # cat8k always on sandbox. it shows using *establish-subscription* and then fetching
    # subscription messages by the subscription id returned in the establish rpc.
    netconf = Netconf(
        host=IOSXE_HOST,
        port=IOSXE_PORT,
        auth_options=AuthOptions(
            username=IOSXE_USERNAME,
            password=IOSXE_PASSWORD,
        ),
    )

    with netconf as nc:
        result = nc.raw_rpc(
            payload="""
            <establish-subscription xmlns="urn:ietf:params:xml:ns:yang:ietf-event-notifications" xmlns:yp="urn:ietf:params:xml:ns:yang:ietf-yang-push">
                <stream>yp:yang-push</stream>
                <yp:xpath-filter>/mdt-oper:mdt-oper-data/mdt-subscriptions</yp:xpath-filter>
                <yp:period>1000</yp:period>
            </establish-subscription>
            """  # noqa: E501
        )

        print(result.result)

        subscription_id = nc.get_subscription_id(payload=result.result)

        print(f"subscription id > {subscription_id}")

        while True:
            sleep(3)

            try:
                notif = nc.get_next_subscription(subscription_id=subscription_id)

                print(notif)

                return
            except NoMessagesException:
                print("sad panda, no subscription messages... *yet*")


if __name__ == "__main__":
    main()
