"""examples.configuration_modes.iosxr_configure_exclusive"""
from scrapli.driver.core import IOSXRDriver

MY_DEVICE = {
    "host": "172.18.0.13",
    "auth_username": "scrapli",
    "auth_password": "scrapli",
    "auth_strict_key": False,
}


def main():
    """Connect to an IOSXRDevice and acquiring/validating an exclusive configuration session"""
    configs = ["do show configuration sessions"]
    with IOSXRDriver(**MY_DEVICE) as conn:
        # make sure you check the names of the privilege levels to know which one to use, in the
        # case of IOSXR we want "configuration_exclusive" for this example
        result = conn.send_configs(configs=configs, privilege_level="configuration_exclusive")

    # note the "*" in the "Lock" column indicates we acquired the exclusive config session
    print(result[0].result)


if __name__ == "__main__":
    main()
