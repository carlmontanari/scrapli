import sys

import jinja2
from devices import DEVICES
from scrapli_cfg import ScrapliCfg

from scrapli import Scrapli

# we can just search at / because the "base_config" is already fully qualified
JINJA_LOADER = jinja2.FileSystemLoader(searchpath="/")
JINJA_ENV = jinja2.Environment(
    loader=JINJA_LOADER, trim_blocks=True, undefined=jinja2.StrictUndefined
)


def prepare_device(test_devices):
    # push base config via scrapli-cfg to ensure consistent testing experience
    for device in test_devices:
        base_config = DEVICES[device]["base_config"]
        conn_dict = {
            "host": DEVICES[device]["host"],
            "port": DEVICES[device]["port"],
            "auth_username": DEVICES[device]["auth_username"],
            "auth_password": DEVICES[device]["auth_password"],
            "auth_secondary": DEVICES[device]["auth_secondary"],
            "auth_strict_key": DEVICES[device]["auth_strict_key"],
            "platform": device,
            # nxos on macos w/out acceleration is... slooooooooooow
            "timeout_ops": 120,
        }

        with Scrapli(**conn_dict) as conn:

            if device == "cisco_iosxe":
                # getting existing crypto "stuff" from the device to stuff it into config template
                # to avoid netconf complaints -- replacing crypto was strings caused things to not
                # get registered in the keychain and netconf-yang connections would get denied
                crypto_pki = conn.send_command(command="show run | section crypto")
                template = JINJA_ENV.get_template(f"{base_config}.j2")
                loaded_base_config = template.render(crypto_pki=crypto_pki.result)
            else:
                with open(base_config, "r") as f:
                    loaded_base_config = f.read()

            with ScrapliCfg(conn=conn) as cfg_conn:
                cfg_conn.load_config(config=loaded_base_config, replace=True)
                cfg_conn.commit_config()

                if device == "cisco_iosxe":
                    conn.send_config(config="no file prompt quiet")


def main():
    test_devices = sys.argv[1].split(",")
    prepare_device(test_devices)


if __name__ == "__main__":
    main()
