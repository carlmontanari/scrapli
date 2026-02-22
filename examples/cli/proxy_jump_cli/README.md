# Proxy Jump (Cli)

This example showcases using both the libssh2 and bin transports to accomplish proxy-jump behavior,
that is, connecting initially to a bastion host of some kind, and then to your ultimate target host
via that intermediate connection.

It is important to note that while both the libssh2 and bin transports support this, the
implementations are completely unique/isolated and as such are not, and will not, be 1:1 from a
feature parity perspective.

*Note:* assumes you are running from the repository root (for paths to ssh keys in the test fixtures).
