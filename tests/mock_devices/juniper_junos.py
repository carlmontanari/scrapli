"""mock_devices.juniper_junos"""
from typing import Any

from .base import BaseServer, BaseSSHServerSession

# yes this is "show version detail" but w/e it requires paging :)
SHOW_COMMAND = """Model: vsrx
Junos: 17.3R2.10
JUNOS Software Release [17.3R2.10]
KERNEL 17.3R2.10 #0 built by builder on 2018-02-08 02:19:07 UTC
MGD release 17.3R2.10 built by builder on 2018-02-08 04:40:18 UTC
CLI release 17.3R2.10 built by builder on 2018-02-08 03:45:31 UTC
IKED release 17.3R2.10 built by builder on 2018-02-08 04:03:22 UTC
RPD release 17.3R2.10 built by builder on 2018-02-08 05:08:08 UTC
CHASSISD release 17.3R2.10 built by builder on 2018-02-08 04:41:34 UTC
GKSD release 17.3R2.10 built by builder on 2018-02-08 04:05:26 UTC
GKMD release 17.3R2.10 built by builder on 2018-02-08 04:04:37 UTC
PKID release 17.3R2.10 built by builder on 2018-02-08 03:56:43 UTC
SENDD release 17.3R2.10 built by builder on 2018-02-08 03:44:42 UTC
DFWD release 17.3R2.10 built by builder on 2018-02-08 03:58:56 UTC
SNMPD release 17.3R2.10 built by builder on 2018-02-08 04:37:26 UTC
MIB2D release 17.3R2.10 built by builder on 2018-02-08 04:40:40 UTC
VRRPD release 17.3R2.10 built by builder on 2018-02-08 04:40:45 UTC
ALARMD release 17.3R2.10 built by builder on 2018-02-08 03:58:13 UTC
PFED release 17.3R2.10 built by builder on 2018-02-08 04:40:40 UTC
CRAFTD release 17.3R2.10 built by builder on 2018-02-08 03:58:51 UTC
SAMPLED release 17.3R2.10 built by builder on 2018-02-08 03:59:57 UTC
SRRD release 17.3R2.10 built by builder on 2018-02-08 03:49:41 UTC
RMOPD release 17.3R2.10 built by builder on 2018-02-08 03:58:02 UTC
COSD release 17.3R2.10 built by builder on 2018-02-08 04:02:26 UTC
IRSD release 17.3R2.10 built by builder on 2018-02-08 03:49:21 UTC
FUD release 17.3R2.10 built by builder on 2018-02-08 03:46:48 UTC
KSYNCD release 17.3R2.10 built by builder on 2018-02-08 03:47:19 UTC
HTTPD-GK release 17.3R2.10 built by builder on 2018-02-08 03:52:07 UTC
DHCPD release 17.3R2.10 built by builder on 2018-02-08 03:50:41 UTC
PPPOED release 17.3R2.10 built by builder on 2018-02-08 04:41:39 UTC
PPPD release 17.3R2.10 built by builder on 2018-02-08 04:41:16 UTC
DFCD release 17.3R2.10 built by builder on 2018-02-08 03:58:55 UTC
LACPD release 17.3R2.10 built by builder on 2018-02-08 04:40:39 UTC
USBD release 17.3R2.10 built by builder on 2018-02-08 03:21:06 UTC
LFMD release 17.3R2.10 built by builder on 2018-02-08 03:59:45 UTC
OAMD release 17.3R2.10 built by builder on 2018-02-08 04:01:15 UTC
TNETD release 17.3R2.10 built by builder on 2018-02-08 03:21:12 UTC
CFMD release 17.3R2.10 built by builder on 2018-02-08 03:58:25 UTC
JDHCPD release 17.3R2.10 built by builder on 2018-02-08 04:40:34 UTC
PSSD release 17.3R2.10 built by builder on 2018-02-08 03:49:29 UTC
AUTHD release 17.3R2.10 built by builder on 2018-02-08 04:40:24 UTC
BDBREPD release 17.3R2.10 built by builder on 2018-02-08 03:46:18 UTC
RES-CLEANUPD release 17.3R2.10 built by builder on 2018-02-08 03:47:48 UTC
APPIDD release 17.3R2.10 built by builder on 2018-02-08 03:52:03 UTC
IDPD release 17.3R2.10 built by builder on 2018-02-08 04:03:21 UTC
SHM-RTSDBD release 17.3R2.10 built by builder on 2018-02-08 03:47:50 UTC
SMID release 17.3R2.10 built by builder on 2018-02-08 04:40:42 UTC
SMIHELPERD release 17.3R2.10 built by builder on 2018-02-08 04:00:00 UTC
R2CPD release 17.3R2.10 built by builder on 2018-02-08 03:49:35 UTC
GSTATD release 17.3R2.10 built by builder on 2018-02-08 03:44:42 UTC
DOT1XD release 17.3R2.10 built by builder on 2018-02-08 04:29:39 UTC
UACD release 17.3R2.10 built by builder on 2018-02-08 03:50:38 UTC
ESSMD release 17.3R2.10 built by builder on 2018-02-08 03:49:02 UTC
TAD release 17.3R2.10 built by builder on 2018-02-08 04:01:41 UTC
DOOD release 17.3R2.10 built by builder on 2018-02-08 03:51:17 UTC
AUTOD release 17.3R2.10 built by builder on 2018-02-08 03:48:15 UTC
NSD release 17.3R2.10 built by builder on 2018-02-08 04:04:20 UTC
IPFD release 17.3R2.10 built by builder on 2018-02-08 04:03:23 UTC
AAMWD release 17.3R2.10 built by builder on 2018-02-08 04:03:17 UTC
NSTRACED release 17.3R2.10 built by builder on 2018-02-08 03:51:00 UTC
FWAUTHD release 17.3R2.10 built by builder on 2018-02-08 04:04:06 UTC
GPRSD release 17.3R2.10 built by builder on 2018-02-08 03:50:56 UTC
JSRPD release 17.3R2.10 built by builder on 2018-02-08 04:04:13 UTC
PROFILERD release 17.3R2.10 built by builder on 2018-02-08 03:51:04 UTC
OAMD release 17.3R2.10 built by builder on 2018-02-08 04:01:15 UTC
RTLOGD release 17.3R2.10 built by builder on 2018-02-08 04:04:20 UTC
UTMD release 17.3R2.10 built by builder on 2018-02-08 04:04:34 UTC
SYSHMD release 17.3R2.10 built by builder on 2018-02-08 03:51:22 UTC
SMTPD release 17.3R2.10 built by builder on 2018-02-08 03:51:07 UTC
USERIDD release 17.3R2.10 built by builder on 2018-02-08 04:03:33 UTC
SDK-VMMD release 17.3R2.10 built by builder on 2018-02-08 04:00:53 UTC
PPMD release 17.3R2.10 built by builder on 2018-02-08 03:57:48 UTC
STATICD release 17.3R2.10 built by builder on 2018-02-08 04:39:50 UTC
PGMD release 17.3R2.10 built by builder on 2018-02-08 03:45:05 UTC
BFDD release 17.3R2.10 built by builder on 2018-02-08 03:57:07 UTC
AUDITD release 17.3R2.10 built by builder on 2018-02-08 03:44:47 UTC
L2ALD release 17.3R2.10 built by builder on 2018-02-08 04:38:48 UTC
EVENTD release 17.3R2.10 built by builder on 2018-02-08 03:57:09 UTC
L2CPD release 17.3R2.10 built by builder on 2018-02-08 04:38:54 UTC
MCSNOOPD release 17.3R2.10 built by builder on 2018-02-08 04:39:04 UTC
MPLSOAMD release 17.3R2.10 built by builder on 2018-02-08 03:44:57 UTC
COMMITD release 17.3R2.10 built by builder on 2018-02-08 04:40:13 UTC
JNUD release 17.3R2.10 built by builder on 2018-02-08 04:38:47 UTC
WEB-API release 17.3R2.10 built by builder on 2018-02-08 03:20:56 UTC
JSD release 17.3R2.10 built by builder on 2018-02-08 04:40:45 UTC
UI-PUBD release 17.3R2.10 built by builder on 2018-02-08 03:48:53 UTC
MGD-API release 17.3R2.10 built by builder on 2018-02-08 04:40:18 UTC
MGD-API release 17.3R2.10 built by builder on 2018-02-08 04:40:18 UTC
NTAD release 17.3R2.10 built by builder on 2018-02-08 03:45:01 UTC
SDPD release 17.3R2.10 built by builder on 2018-02-08 03:45:22 UTC
SPMD release 17.3R2.10 built by builder on 2018-02-08 03:57:52 UTC
SCPD release 17.3R2.10 built by builder on 2018-02-08 03:45:20 UTC
SDXD release 17.3R2.10 built by builder on 2018-02-08 03:44:42 UTC
base-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:58:19 UTC
jroute-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:56:47 UTC
jkernel-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:58:39 UTC
appsecure-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:58:34 UTC
aprobe-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:58:34 UTC
authd_cmd-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:58:34 UTC
autod-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:59:06 UTC
cfm-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:58:35 UTC
chassis_cmd-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:58:35 UTC
collector-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:59:09 UTC
cos_cmd-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:58:36 UTC
cpcdd_cmd-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:58:36 UTC
dcd_cmd-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:58:37 UTC
dfcd_cmd-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:58:37 UTC
dot1xd-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:59:08 UTC
elmi-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:58:37 UTC
essmd-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:59:09 UTC
forwarding_options_cmd-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:58:37 UTC
gres-test-point-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:56:47 UTC
httpd_cmd-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:58:38 UTC
iccp_cmd-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:58:39 UTC
jappid-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:58:39 UTC
jcrypto-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:56:33 UTC
jcrypto_usp-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:59:12 UTC
jdocs-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:58:32 UTC
jidpd-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:58:39 UTC
jkernel_jseries-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:59:14 UTC
jkernel_usp-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:59:12 UTC
jpppd-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:59:09 UTC
jroute_junos-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:56:47 UTC
l2ald-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:56:48 UTC
lldp-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:56:48 UTC
lrf-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:59:09 UTC
mclag_cfgchk_cmd-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:59:08 UTC
mcsnoop-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:56:49 UTC
mo-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:58:41 UTC
pccd-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:56:49 UTC
phcd-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:59:14 UTC
pppd-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:59:09 UTC
pppoed-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:59:09 UTC
r2cpd-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:59:09 UTC
rdd-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:58:42 UTC
repd_cmd-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:58:42 UTC
scpd-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:56:50 UTC
sdpd-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:56:50 UTC
services-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:59:09 UTC
spmd-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:56:53 UTC
srd-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:59:10 UTC
stpng-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:59:07 UTC
syshmd_health_mon-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:59:14 UTC
syshmd_trackip-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:59:14 UTC
traffic-dird-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:59:10 UTC
transportd-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:59:10 UTC
url-filterd-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:59:10 UTC
vlans-ng-actions-dd release 17.3R2.10 built by builder on 2018-02-08 02:59:07 UTC

"""


class JunoSSHServerSession(BaseSSHServerSession):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Juniper Junos mock ssh server

        Args:
            args: args to pass to base class
            kwargs: keyword args to pass to base class

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        super().__init__(*args, **kwargs)

        self.terminal_length = 32

        self.priv_levels = {
            "exec": "vrnetlab>",
            "config": "vrnetlab#",
        }
        self.priv_level = "exec"
        self.invalid_input = "% Invalid command at '^' marker.\n"
        self.paging_prompt = "\n--(more)--"

        self.command_mapper = {
            self.handle_open: [
                "set cli complete-on-space off",
                "set cli screen-length 0",
                "set cli screen-width 511",
            ],
            self.handle_close: ["exit"],
            self.handle_priv: ["configure", "exit"],
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
        elif channel_input == "set cli screen-length 0":
            # in the future can actually set the value if we care?
            self.terminal_length = 0
            self._chan.write("")
            self.repaint_prompt()
        elif channel_input == "set cli screen-width 511":
            self.terminal_width = 511
            self._chan.write("")
            self.repaint_prompt()
        elif channel_input == "set cli complete-on-space off":
            # we dont care about this really, but scrapli will send it during open so have to just
            # make sure we accept it and move on
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
            self.priv_level = "exec"
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
        if self.priv_level != "exec":
            self.handle_invalid(channel_input=channel_input)
        else:
            self._chan.write("")
            self.priv_level = "config"
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
        # junos has just "exit", no "end" and no "disable/enable" so just configure to deal w/ here
        if channel_input == "configure":
            self._handle_priv_configure(channel_input=channel_input)

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


class JunosServer(BaseServer):
    pass
