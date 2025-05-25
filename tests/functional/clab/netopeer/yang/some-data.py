#!/build/venv/bin/python
import signal
import sys
import time

import sysrepo

START_TIME = time.time()


def main():
    try:
        with sysrepo.SysrepoConnection() as conn:
            with conn.start_session() as sess:
                sess.set_item("/some-data:system/hostname", "foo-bar-baz")
                sess.set_item("/some-data:system/interfaces[name='eth0']/enabled", True)
                sess.apply_changes()

                signal.sigwait({signal.SIGINT, signal.SIGTERM})
        return 0
    except sysrepo.SysrepoError:
        return 1


if __name__ == "__main__":
    sys.exit(main())
