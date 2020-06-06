import asyncssh

SHOW_VERSION_PAGING_ENABLED = """Cisco IOS XE Software, Version 16.04.01
Cisco IOS Software [Everest], CSR1000V Software (X86_64_LINUX_IOSD-UNIVERSALK9-M), Version 16.4.1, RELEASE SOFTWARE (fc2)
Technical Support: http://www.cisco.com/techsupport
Copyright (c) 1986-2016 by Cisco Systems, Inc.
Compiled Sun 27-Nov-16 13:02 by mcpre


Cisco IOS-XE software, Copyright (c) 2005-2016 by cisco Systems, Inc.
All rights reserved.  Certain components of Cisco IOS-XE software are
licensed under the GNU General Public License ("GPL") Version 2.0.  The
software code licensed under GPL Version 2.0 is free software that comes
with ABSOLUTELY NO WARRANTY.  You can redistribute and/or modify such
GPL code under the terms of GPL Version 2.0.  For more details, see the
documentation or "License Notice" file accompanying the IOS-XE software,
or the applicable URL provided on the flyer accompanying the IOS-XE
software.


ROM: IOS-XE ROMMON

csr1000v uptime is 4 hours, 55 minutes
Uptime for this control processor is 4 hours, 57 minutes
System returned to ROM by reload
System image file is "bootflash:packages.conf"
Last reload reason: reload



This product contains cryptographic features and is subject to United
States and local country laws governing import, export, transfer and
 --More--
"""

SHOW_VERSION_PAGING_DISABLED = """Cisco IOS XE Software, Version 16.04.01
Cisco IOS Software [Everest], CSR1000V Software (X86_64_LINUX_IOSD-UNIVERSALK9-M), Version 16.4.1, RELEASE SOFTWARE (fc2)
Technical Support: http://www.cisco.com/techsupport
Copyright (c) 1986-2016 by Cisco Systems, Inc.
Compiled Sun 27-Nov-16 13:02 by mcpre


Cisco IOS-XE software, Copyright (c) 2005-2016 by cisco Systems, Inc.
All rights reserved.  Certain components of Cisco IOS-XE software are
licensed under the GNU General Public License ("GPL") Version 2.0.  The
software code licensed under GPL Version 2.0 is free software that comes
with ABSOLUTELY NO WARRANTY.  You can redistribute and/or modify such
GPL code under the terms of GPL Version 2.0.  For more details, see the
documentation or "License Notice" file accompanying the IOS-XE software,
or the applicable URL provided on the flyer accompanying the IOS-XE
software.


ROM: IOS-XE ROMMON

csr1000v uptime is 4 hours, 55 minutes
Uptime for this control processor is 4 hours, 56 minutes
System returned to ROM by reload
System image file is "bootflash:packages.conf"
Last reload reason: reload



This product contains cryptographic features and is subject to United
States and local country laws governing import, export, transfer and
use. Delivery of Cisco cryptographic products does not imply
third-party authority to import, export, distribute or use encryption.
Importers, exporters, distributors and users are responsible for
compliance with U.S. and local country laws. By using this product you
agree to comply with applicable laws and regulations. If you are unable
to comply with U.S. and local laws, return this product immediately.

A summary of U.S. laws governing Cisco cryptographic products may be found at:
http://www.cisco.com/wwl/export/crypto/tool/stqrg.html

If you require further assistance please contact us by sending email to
export@cisco.com.

License Level: ax
License Type: Default. No valid license found.
Next reload license Level: ax

cisco CSR1000V (VXE) processor (revision VXE) with 2052375K/3075K bytes of memory.
Processor board ID 9FKLJWM5EB0
10 Gigabit Ethernet interfaces
32768K bytes of non-volatile configuration memory.
3985132K bytes of physical memory.
7774207K bytes of virtual hard disk at bootflash:.
0K bytes of  at webui:.

Configuration register is 0x2102

"""

SPECIAL_COMMANDS = {
    "enable": "handle_enable",
    "disable": "handle_disable",
    "configure terminal": "handle_configure_terminal",
    "end": "handle_end",
    "exit": "handle_exit",
    "terminal length 0": "handle_disable_paging",
    "clear logging": "handle_clear_logging",
}

PRIVILEGE_LEVELS = {"exec": "csr1000v>", "priv_exec": "csr1000v#", "config": "csr1000v(config)#"}

COMMANDS_PAGING_ENABLED = {
    "show version": SHOW_VERSION_PAGING_ENABLED,
    "terminal width 512": "",
    "show run | i hostname": "hostname csr1000v",
}
COMMANDS_PAGING_DISABLED = {
    "show version": SHOW_VERSION_PAGING_DISABLED,
    "terminal width 512": "",
    "show run | i hostname": "hostname csr1000v",
}

INVALID_INPUT = "% Invalid input detected at '^' marker.\n"


class IOSXEServerSession(asyncssh.SSHServerSession):
    def connection_made(self, chan):
        self._chan = chan

    def shell_requested(self):
        return True

    def session_started(self):
        self._enable_prompting = False
        self._paging_disabled = False
        self._interacting = False
        self._priv_level = "priv_exec"
        self._chan.write(PRIVILEGE_LEVELS.get(self._priv_level))

    def handle_normal_command(self, command: str) -> None:
        if not self._paging_disabled:
            output = COMMANDS_PAGING_ENABLED.get(command, INVALID_INPUT)
            self._chan.write(output)
            if "--More--" in output:
                return
        else:
            output = COMMANDS_PAGING_DISABLED.get(command, INVALID_INPUT)
            self._chan.write(output)
        self._chan.write(PRIVILEGE_LEVELS.get(self._priv_level))

    def handle_special_command(self, command: str) -> None:
        handler_method_name = SPECIAL_COMMANDS.get(command)
        handler_method = getattr(self, handler_method_name)
        handler_method()

    def handle_disable_paging(self) -> None:
        if self._priv_level == "config":
            self._chan.write(INVALID_INPUT)
            self._chan.write(PRIVILEGE_LEVELS.get(self._priv_level))
        else:
            self._paging_disabled = True
            self._chan.write("")
            self._chan.write(PRIVILEGE_LEVELS.get(self._priv_level))

    def handle_configure_terminal(self) -> None:
        if self._priv_level != "priv_exec":
            self._chan.write(INVALID_INPUT)
            self._chan.write(PRIVILEGE_LEVELS.get(self._priv_level))
        else:
            self._chan.write("")
            self._priv_level = "config"
            self._chan.write(PRIVILEGE_LEVELS.get(self._priv_level))

    def handle_end(self) -> None:
        if self._priv_level != "config":
            self._chan.write(INVALID_INPUT)
            self._chan.write(PRIVILEGE_LEVELS.get(self._priv_level))
        else:
            self._chan.write("")
            self._priv_level = "priv_exec"
            self._chan.write(PRIVILEGE_LEVELS.get(self._priv_level))

    def handle_exit(self) -> None:
        if self._priv_level == "config":
            self._chan.write("")
            self._priv_level = "priv_exec"
            self._chan.write(PRIVILEGE_LEVELS.get(self._priv_level))
        else:
            self.eof_received()

    def handle_disable(self) -> None:
        if self._priv_level == "priv_exec":
            self._chan.write("")
            self._priv_level = "exec"
            self._chan.write(PRIVILEGE_LEVELS.get(self._priv_level))
        elif self._priv_level == "exec":
            self._chan.write("")
            self._chan.write(PRIVILEGE_LEVELS.get(self._priv_level))
        else:
            self._chan.write(INVALID_INPUT)
            self._chan.write(PRIVILEGE_LEVELS.get(self._priv_level))

    def handle_enable(self) -> None:
        if self._priv_level == "exec":
            self._chan.set_echo(False)
            self._enable_prompting = True
            self._chan.write("Password:")
        else:
            self._chan.write(INVALID_INPUT)
            self._chan.write(PRIVILEGE_LEVELS.get(self._priv_level))

    def handle_clear_logging(self) -> None:
        if self._priv_level != "priv_exec":
            self._chan.write(INVALID_INPUT)
            self._chan.write(PRIVILEGE_LEVELS.get(self._priv_level))
        else:
            self._interacting = True
            self._chan.write("Clear logging buffer [confirm]")

    def data_received(self, data, datatype):
        data = data.rstrip()

        if self._interacting is True:
            self._interacting = False
            self._chan.write("")
            self._chan.write(PRIVILEGE_LEVELS.get(self._priv_level))
            return

        if not data:
            self._chan.write("")
            self._chan.write(PRIVILEGE_LEVELS.get(self._priv_level))
            return

        if self._enable_prompting is True:
            if data == "scrapli":
                self._chan.set_echo(True)
                self._enable_prompting = False
                self._priv_level = "priv_exec"
                self._chan.write("")
                self._chan.write(PRIVILEGE_LEVELS.get(self._priv_level))
                return
            else:
                self._chan.write("Password:")
                return

        if data in SPECIAL_COMMANDS:
            self.handle_special_command(command=data)
        else:
            self.handle_normal_command(command=data)

    def eof_received(self):
        self._chan.exit(0)

    def break_received(self, msec):
        self.eof_received()


class IOSXEServer(asyncssh.SSHServer):
    def session_requested(self):
        return IOSXEServerSession()

    def begin_auth(self, username) -> bool:
        return True

    def password_auth_supported(self) -> bool:
        return True

    def public_key_auth_supported(self) -> bool:
        return True

    def validate_password(self, username, password) -> bool:
        if username == password == "scrapli":
            return True
        return False

    def validate_public_key(self, username, key) -> bool:
        if (
            username == "scrapli"
            and key.get_fingerprint() == "SHA256:rb1CVtQCkWBAzm1AxV7xR7BLBawUwFUlUVFVu+QYQBM"
        ):
            return True
        return False
