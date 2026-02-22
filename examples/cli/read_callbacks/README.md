# Read Callbacks

This example shows one of the more interesting/powerful scrapli features -- the
`read_with_callbacks` method. This method was originally designed for use with terminal servers and
connecting to device consoles during boot up, or zero-touch-provisioning type workflows. Basically,
this is a fancier way to handle device interactions and/or tailing logs or other long running
outputs that may have contents that you want to trigger some function call. Check out the comments
in the example itself for some more context.
