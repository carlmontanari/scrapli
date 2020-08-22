import sys

from napalm import get_network_driver
from test_data.devices import DEVICES

NAPALM_DEVICE_TYPE_MAP = {
    "cisco_iosxe": "ios",
    "cisco_nxos": "nxos",
    "cisco_iosxr": "iosxr",
    "arista_eos": "eos",
    "juniper_junos": "junos",
}


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
        }
        if device == "arista_eos":
            napalm_args["optional_args"] = {}
            napalm_args["optional_args"]["enable_password"] = DEVICES[device]["auth_password"]
        napalm_conn = napalm_driver(**napalm_args)
        napalm_conn.open()
        napalm_conn.load_replace_candidate(filename=base_config)
        napalm_conn.commit_config()
        napalm_conn.close()


def main():
    test_devices = sys.argv[1].split(",")
    prepare_device(test_devices)


if __name__ == "__main__":
    main()
