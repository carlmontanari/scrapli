"""mock_devices.cisco_nxos"""
from typing import Any

from .base import BaseServer, BaseSSHServerSession

SHOW_COMMAND = """Cisco Nexus Operating System (NX-OS) Software
TAC support: http://www.cisco.com/tac
Documents: http://www.cisco.com/en/US/products/ps9372/tsd_products_support_series_home.html
Copyright (c) 2002-2019, Cisco Systems, Inc. All rights reserved.
The copyrights to certain works contained herein are owned by
other third parties and are used and distributed under license.
Some parts of this software are covered under the GNU Public
License. A copy of the license is available at
http://www.gnu.org/licenses/gpl.html.

Nexus 9000v is a demo version of the Nexus Operating System

Software
  BIOS: version
 NXOS: version 9.2(4)
  BIOS compile time:
  NXOS image file is: bootflash:///nxos.9.2.4.bin
  NXOS compile time:  8/20/2019 7:00:00 [08/20/2019 15:52:22]


Hardware
  cisco Nexus9000 9000v Chassis
   with 6096432 kB of memory.
  Processor Board ID 9GXMY611NJ4

  Device name: switch
  bootflash:    3509454 kB
Kernel uptime is 0 day(s), 1 hour(s), 4 minute(s), 47 second(s)

Last reset
  Reason: Unknown
  System version:
  Service:

plugin
  Core Plugin, Ethernet Plugin

Active Package(s):

"""


class NXOSSSHServerSession(BaseSSHServerSession):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Cisco NXOS mock ssh server

        Args:
            args: args to pass to base class
            kwargs: keyword args to pass to base class

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        super().__init__(*args, **kwargs)

        self.terminal_length = 34

        self.priv_levels = {
            "privilege_exec": "switch#",
            "config": "switch(config)#",
        }
        self.priv_level = "privilege_exec"
        self.invalid_input = "% Invalid command at '^' marker.\n"
        self.paging_prompt = "\n--More--"

        self.command_mapper = {
            self.handle_open: ["terminal length 0", "terminal width 511"],
            self.handle_close: ["exit"],
            self.handle_priv: ["enable", "configure terminal", "end"],
            self.handle_show: ["show version"],
            self.handle_interactive: [],
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
            self._chan.write(self.priv_levels.get(self.priv_level))
        elif channel_input == "terminal width 511":
            self.terminal_width = 511
            self._chan.write("")
            self._chan.write(self.priv_levels.get(self.priv_level))
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
        if channel_input == "configure terminal":
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
        # TODO
        pass

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
        # in the future we can cutoff the inputs if it is over X width if disable width has not yet
        # been ran -- not needed now but could be cool; if we just send a return, we should NOT
        # strip that!
        channel_input = data if data == "\n" else data.rstrip()

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


class NXOSServer(BaseServer):
    pass
