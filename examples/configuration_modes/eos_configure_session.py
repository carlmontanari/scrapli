"""examples.configuration_modes.eos_configure_session"""
from scrapli.driver.core import EOSDriver

MY_DEVICE = {
    "host": "172.18.0.14",
    "auth_username": "scrapli",
    "auth_password": "scrapli",
    "auth_secondary": "VR-netlab9",
    "auth_strict_key": False,
}


def main():
    """Connect to an EOS Device and create and acquire a configuration session"""
    configs = ["show configuration sessions"]
    with EOSDriver(**MY_DEVICE) as conn:
        conn.register_configuration_session(session_name="my-config-session")
        # for configuration sessions we have to first "register" the session with scrapli:
        result = conn.send_configs(configs=configs, privilege_level="my-config-session")

    # we should see our session name with an "*" indicating that is the active config session
    print(result[0].result)


if __name__ == "__main__":
    main()
