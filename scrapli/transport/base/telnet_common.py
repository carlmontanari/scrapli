"""scrapli.transport.base.telnet_common"""

IAC = bytes([255])
DONT = bytes([254])
DO = bytes([253])
WONT = bytes([252])
WILL = bytes([251])
TERM_TYPE = bytes([24])
SUPPRESS_GO_AHEAD = bytes([3])
