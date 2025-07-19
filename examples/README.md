# Example Lab

Unless otherwise noted in the specific example repository, all examples target the srlinux device
in the "scrapli_clab" containerlab testbed topology, specifically the "ci" variant of the topology.
This topology should be able to be ran on any linux or darwin device and uses only publicly available images.

If you've cloned this repository and are working in the repository root, you can run the
`make run-clab-ci` make target -- this will spin up the test topology in docker, obviously you will
need to have docker for this.

The topology will spin up a launcher pod with the docker sock bound to it, this way we can run
containerlab sort of natively even on darwin hosts.

The "ci" variant of the topology includes a srlinux device, a netopeer netconf server, as well as a
dummy linux container that can be used to test proxy-jump ssh behavior.

You can check out the "scrapli_clab" bits [here](https://github.com/scrapli/scrapli_clab).

Specifically the amd64 or arm "ci" variants live
[here](https://github.com/scrapli/scrapli_clab/blob/main/launcher/topos/topo.ci.amd64.yaml) and
[here](https://github.com/scrapli/scrapli_clab/blob/main/launcher/topos/topo.ci.arm64.yaml)
respectively.

The srlinux device exposes (among others) SSH, Telnet and Netconf ports normally (22, 23, 830) and
also exposes them NAT'd for darwin users on 21022, 21023, and 21830. Credentials are `admin` /
`NokiaSrl1!`.

Each example will connect to the appropriate port based on the system the example is being ran on
(i.e. check if darwin, if so SSH to 21022).

The examples allow for overrding of the platform (srlinux), host, port, username, and password via
environment variables. Obviously changing the target platform type may cause the examples to not
work as expected or at all.
