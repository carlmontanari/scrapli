"""examples.commandeer.commandeer_generic_connection"""
from scrapli import Scrapli
from scrapli.driver.generic import GenericDriver

GENERIC_DEVICE = {
    "host": "172.18.0.11",
    "auth_username": "scrapli",
    "auth_password": "scrapli",
    "auth_strict_key": False,
}
TARGET_DEVICE = {"host": "172.18.0.11", "platform": "cisco_iosxe"}


def main():
    """
    Connect to a generic device and then commandeer that connection

    Generally this would be used for connecting to a terminal server, then doing *something* to
    connect to one of its downstream devices (i.e. access terminal server port 123 or whatever).
    Once on the console of the downstream device, we can "commandeer" this terminal server
    connection object and basically transform it into a connection object of the type (i.e. IOSXE)
    that we ultimately want.
    """
    # firstly we create the "outer"/"parent" connection -- this would be the connection to the
    # terminal server or similar device. generally this will be the `GenericDriver`, but there is
    # nothing stopping you from using any other driver type!
    term_server_conn = GenericDriver(**GENERIC_DEVICE)
    # open this connection
    term_server_conn.open()

    # here you would normally need to add some logic to get connected to the terminal server port or
    # to ssh from this "outer" device to the target device, in this example we're just ssh'ing to a
    # device using the generic driver then transforming that to the IOSXE driver so we dont need to
    # do anything

    # next create, but dont open, a connection for the target device type
    target_device_conn = Scrapli(**TARGET_DEVICE)

    # we can then call `commandeer` from the "inner"/"child" connection, passing it the connection
    # object of the "outer"/"parent"
    target_device_conn.commandeer(conn=term_server_conn)

    # we can confirm the "target_device_conn" is of course of type IOSXE (in this example), and that
    # we see the send_config methods of the *network* driver (rather than the parent connection not
    # having those config methods as it is *generic* driver type).
    print(type(target_device_conn), dir(target_device_conn))

    # we can acquire the config mode (which only the IOSXE driver would know how to do) to confirm
    # things are working as expected
    target_device_conn.acquire_priv("configuration")
    print(target_device_conn.get_prompt())
    target_device_conn.acquire_priv("privilege_exec")
    print(target_device_conn.get_prompt())

    # closing the "inner"/"child" connection will close the "outer"/"parent" connection, so if you
    # wish to keep using the outer connection.... dont close this one :)
    # target_device_conn.close()

    # if you dont close the inner connection, you can keep using the outer connection to do whatever
    # it is you need to do with it!
    print(term_server_conn.get_prompt())


if __name__ == "__main__":
    main()
