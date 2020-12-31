import os
import sys

import jinja2
from napalm import get_network_driver
from test_data.devices import DEVICES

VROUTER_MODE = bool(os.environ.get("SCRAPLI_VROUTER", False))

NAPALM_DEVICE_TYPE_MAP = {
    "cisco_iosxe": "ios",
    "cisco_nxos": "nxos_ssh",
    "cisco_iosxr": "iosxr",
    "arista_eos": "eos",
    "juniper_junos": "junos",
}

# we can just search at / because the "base_config" is already fully qualified
JINJA_LOADER = jinja2.FileSystemLoader(searchpath="/")
JINJA_ENV = jinja2.Environment(
    loader=JINJA_LOADER, trim_blocks=True, undefined=jinja2.StrictUndefined
)


def prepare_device(test_devices):
    # push base config via napalm to ensure consistent testing experience
    for device in test_devices:
        base_config = DEVICES[device]["base_config"]

        napalm_device_type = NAPALM_DEVICE_TYPE_MAP.get(device)
        napalm_driver = get_network_driver(napalm_device_type)
        napalm_args = {
            "hostname": DEVICES[device]["host"],
            "username": DEVICES[device]["auth_username"],
            "password": DEVICES[device]["auth_password"],
            "optional_args": {"port": DEVICES[device]["port"], "global_delay_factor": 4},
        }
        if device == "arista_eos":
            napalm_args["optional_args"] = {}
            napalm_args["optional_args"]["enable_password"] = DEVICES[device]["auth_password"]
            # if port is not 22 we are in "vrouter mode" so we set https port -> 24443
            napalm_args["optional_args"]["port"] = 443 if DEVICES[device]["port"] == 22 else 24443
        elif device == "juniper_junos":
            # if port is not 22 we are in "vrouter mode" so we set netconf port -> 25830
            napalm_args["optional_args"]["port"] = 830 if DEVICES[device]["port"] == 22 else 25830

        napalm_conn = napalm_driver(**napalm_args)
        napalm_conn.open()

        if device == "cisco_iosxe":
            # getting existing crypto "stuff" from the device to stuff it into config template to
            # avoid netconf complaints -- replacing crypto was strings caused things to not get
            # registered in the keychain and netconf-yang connections would get denied
            crypto_pki = napalm_conn._netmiko_device.send_command("show run | section crypto")
            template = JINJA_ENV.get_template(f"{base_config}.j2")
            loaded_base_config = template.render(crypto_pki=crypto_pki)
        else:
            with open(base_config, "r") as f:
                loaded_base_config = f.read()

        napalm_conn.load_replace_candidate(config=loaded_base_config)
        napalm_conn.commit_config()
        napalm_conn.close()


def main():
    test_devices = sys.argv[1].split(",")
    prepare_device(test_devices)


if __name__ == "__main__":
    main()
