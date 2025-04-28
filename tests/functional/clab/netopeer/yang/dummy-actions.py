#!/build/venv/bin/python
import signal
import sys

import sysrepo


def main():
    try:
        with sysrepo.SysrepoConnection() as conn:
            with conn.start_session() as sess:
                sess.subscribe_rpc_call("/dummy-actions:system/reboot", reboot)

                signal.sigwait({signal.SIGINT, signal.SIGTERM})
        return 0
    except sysrepo.SysrepoError:
        return 1


def reboot(xpath, input_params, event, private_data):
    _, _ = event, private_data

    out = {"message": "bye bye"}

    print("========================")
    print(f"rpc: {xpath}")
    print(f"params: {input_params}")
    print(f"returning {out}")

    return out


if __name__ == "__main__":
    sys.exit(main())
