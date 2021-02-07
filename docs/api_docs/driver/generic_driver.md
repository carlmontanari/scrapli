# GenericDriver Object

The GenericDriver objects (sync and async versions) extend the `BaseDriver` class. The GenericDriver objects provide 
a "friendly" telnet/ssh interface with methods available to `get_prompt`, `send_input`, and `write` and `read` from 
the underlying connection.

The GenericDriver objects have no concept of "commands" or "configurations", or of "privilege levels" -- things that 
are common place in most network operating systems. As such, the GenericDriver is generally not the "right" fit to 
use when interacting with network devices, and is instead more suited to working with linux-like devices without the 
concept of privilege levels or config modes. 

The GenericDriver objects accept all the same arguments that the BaseDriver accepts and nothing else.


## Args

- All [`BaseDriver`](base_driver.md) arguments


## Returns

- None


## Raises

- N/A