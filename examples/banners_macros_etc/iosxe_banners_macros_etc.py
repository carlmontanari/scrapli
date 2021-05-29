"""examples.banners_macros_etc.iosxe_banners_macros_etc"""
from scrapli.driver.core import IOSXEDriver

MY_DEVICE = {
    "host": "172.31.254.1",
    "auth_username": "scrapli",
    "auth_password": "scrapli",
    "auth_strict_key": False,
}


def main():
    """Simple example of configuring banners and macros on an IOSXEDevice"""
    conn = IOSXEDriver(**MY_DEVICE)
    conn.open()

    my_banner = """banner motd ^
This is my router, get outa here!
I'm serious, you can't be in here!
Go away!
^
"""
    # Because the banner "input mode" is basically like a text editor where we dont get the prompt
    # printed out between sending lines of banner config we need to use the `eager` mode to force
    # scrapli to blindly send the banner/macro lines without looking for the prompt in between each
    # line. You should *not* use eager unless you need to and know what you are doing as it
    # basically disables one of the core features that makes scrapli reliable!
    result = conn.send_config(config=my_banner, eager=True)
    print(result.result)


if __name__ == "__main__":
    main()
