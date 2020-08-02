"""mock_devices.cisco_iosxe"""
from typing import Any

from .base import BaseServer, BaseSSHServerSession

SHOW_COMMAND = """Cisco IOS XE Software, Version 16.04.01
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
"""  # noqa: E0501


class IOSXESSHServerSession(BaseSSHServerSession):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Cisco IOSXE mock ssh server

        Args:
            args: args to pass to base class
            kwargs: keyword args to pass to base class

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        super().__init__(*args, **kwargs)
        self.priv_levels = {
            "exec": "csr1000v>",
            "privilege_exec": "csr1000v#",
            "config": "csr1000v(config)#",
        }
        self.priv_level = "privilege_exec"
        self.invalid_input = "% Invalid input detected at '^' marker.\n"
        self.paging_prompt = "\n--More--"

        self.command_mapper = {
            self.handle_open: ["terminal length 0", "terminal width 0"],
            self.handle_close: ["exit"],
            self.handle_priv: ["disable", "enable", "configure terminal", "end"],
            self.handle_show: ["show version"],
            self.handle_interactive: ["clear logging"],
        }

        self.show_command_output = SHOW_COMMAND

    def handle_open(self, channel_input: str) -> None:
        """
        Handle "open" commands sent to the ssh channel

        Args:
            channel_input: command sent to the ssh channel

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        if self.priv_level == "config":
            self.handle_invalid(channel_input=channel_input)
        elif channel_input == "terminal length 0":
            # in the future can actually set the value if we care?
            self.terminal_length = 0
            self._chan.write("")
            self.repaint_prompt()
        elif channel_input == "terminal width 0":
            self.terminal_width = 0
            self._chan.write("")
            self.repaint_prompt()
        else:
            self.handle_invalid(channel_input=channel_input)

    def handle_close(self, channel_input: str) -> None:
        """
        Handle "close" commands sent to the ssh channel

        Args:
            channel_input: command sent to the ssh channel

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        _ = channel_input
        if self.priv_level == "config":
            # exit is a weird situation since it can be used to exit config mode or exit the device
            # so this lives here instead of handle_priv
            self._chan.write("")
            self.priv_level = "privilege_exec"
            self.repaint_prompt()
        else:
            self.eof_received()

    def _handle_priv_password_input(self, channel_input: str) -> None:
        """
        Handle the enable password input

        Args:
            channel_input: command sent to the ssh channel

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        if channel_input == "scrapli":
            self._chan.set_echo(True)
            self._hide_input = False
            self.priv_level = "privilege_exec"
            self._chan.write("")
            self._chan.write(self.priv_levels.get(self.priv_level))
            self._redirect_to_handler = None
        else:
            self._chan.write("Password:")
            return

    def _handle_priv_disable(self, channel_input: str) -> None:
        """
        Handle the "disable" command

        Args:
            channel_input: command sent to the ssh channel

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        if self.priv_level == "privilege_exec":
            self._chan.write("")
            self.priv_level = "exec"
            self.repaint_prompt()
        elif self.priv_level == "exec":
            self._chan.write("")
            self.repaint_prompt()
        else:
            self.handle_invalid(channel_input=channel_input)

    def _handle_priv_enable(self, channel_input: str) -> None:
        """
        Handle the "enable" command

        Args:
            channel_input: command sent to the ssh channel

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        if self.priv_level == "exec":
            if self._redirect_to_handler is None:
                self._chan.set_echo(False)
                self._hide_input = True
                self._chan.write("Password:")
                self._redirect_to_handler = self._handle_priv_password_input
        else:
            self.handle_invalid(channel_input=channel_input)

    def _handle_priv_configure(self, channel_input: str) -> None:
        """
        Handle the "configure terminal" command

        Args:
            channel_input: command sent to the ssh channel

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        if self.priv_level != "privilege_exec":
            self.handle_invalid(channel_input=channel_input)
        else:
            self._chan.write("")
            self.priv_level = "config"
            self.repaint_prompt()

    def _handle_priv_end(self, channel_input: str) -> None:
        """
        Handle the "end" command

        Args:
            channel_input: command sent to the ssh channel

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        if self.priv_level != "config":
            self.handle_invalid(channel_input=channel_input)
        else:
            self._chan.write("")
            self.priv_level = "privilege_exec"
            self.repaint_prompt()

    def handle_priv(self, channel_input: str) -> None:
        """
        Handle "privilege" commands sent to the ssh channel

        Args:
            channel_input: command sent to the ssh channel

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        if channel_input == "disable":
            self._handle_priv_disable(channel_input=channel_input)
        elif channel_input == "enable":
            self._handle_priv_enable(channel_input=channel_input)
        elif channel_input == "configure terminal":
            self._handle_priv_configure(channel_input=channel_input)
        elif channel_input == "end":
            self._handle_priv_end(channel_input=channel_input)

    def handle_interactive(self, channel_input: str) -> None:
        """
        Handle the "interactive" (clear logging) command

        Args:
            channel_input: command sent to the ssh channel

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        if self.priv_level == "privilege_exec":
            if self._redirect_to_handler is None:
                self._chan.write("Clear logging buffer [confirm]")
        else:
            self.handle_invalid(channel_input=channel_input)

    def data_received(self, data: str, datatype: None) -> None:
        """
        Handle data received on ssh channel

        Args:
            data: string of data sent to channel
            datatype: dunno! in base class though :)

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        _ = datatype
        # in the future we can cutoff the inputs if it is over X width if disable width has not yet
        # been ran -- not needed now but could be cool; if we just send a return, we should NOT
        # strip that!
        channel_input = data if data == "\n" else data.rstrip()

        if self._redirect_to_handler is not None:
            # "redirect" to a function that needs continued inputs such as priv escalation
            self._redirect_to_handler(channel_input=channel_input)
            return

        if data == "\n":
            self.repaint_prompt()
            return

        for handler, channel_inputs in self.command_mapper.items():
            if channel_input in channel_inputs:
                # as soon as we find a match for the channel input ship it to the handler; handler
                # can figure out if command is valid for the given priv and such
                handler(channel_input=channel_input)
                return

        self.handle_invalid(channel_input=channel_input)


class IOSXEServer(BaseServer):
    pass
