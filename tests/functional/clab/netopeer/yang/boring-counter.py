#!/build/venv/bin/python
import signal
import sys
import threading
import time

import sysrepo

counter_value = 0


def main():
    try:
        with sysrepo.SysrepoConnection() as conn:
            with conn.start_session() as sess:
                threading.Thread(
                    target=update_counter_periodically, args=(sess,), daemon=True
                ).start()

                signal.sigwait({signal.SIGINT, signal.SIGTERM})
        return 0
    except sysrepo.SysrepoError:
        return 1


def boring_counter_change_cb(event, req_id, changes, private_data):
    _, _, _ = event, req_id, private_data

    print(changes)

    return 0


def update_counter_periodically(sess):
    global counter_value  # noqa: PLW0603

    while True:
        counter_value += 1
        xpath = "/boring-counter:system/counter"
        sess.set_item(xpath, counter_value)
        sess.apply_changes()

        notif_xpath = "/boring-counter:counter-update"
        sess.notification_send(
            notif_xpath, {"/boring-counter:counter-update/counter-value": counter_value}
        )

        time.sleep(3)


if __name__ == "__main__":
    sys.exit(main())
