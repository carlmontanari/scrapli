# BaseDriver Object

BaseDriver is the root for all Scrapli driver classes.

The synchronous and asyncio driver base driver classes can be used to provide a semi-pexpect like experience over top of
whatever transport a user prefers. Generally, however, the base driver classes should not be used directly. It is 
best to use the GenericDriver \(or AsyncGenericDriver\) or NetworkDriver \(or AsyncNetworkDriver\) sub-classes of 
the base drivers.


## Args

- __host__: host ip/name to connect to
- __port__: port to connect to
- __auth_username__: username for authentication
- __auth_private_key__: path to private key for authentication
- __auth_private_key_passphrase__: passphrase for decrypting ssh key if necessary
- __auth_password__: password for authentication
- __auth_strict_key__: strict host checking or not
- __auth_bypass__: bypass "in channel" authentication -- only supported with telnet, asynctelnet, and system transport 
  __plugins__
- __timeout_socket__: timeout for establishing socket/initial connection in seconds
- __timeout_transport__: timeout for ssh|telnet transport in seconds
- __timeout_ops__: timeout for ssh channel operations
- __comms_prompt_pattern__: raw string regex pattern -- preferably use `^` and `$` anchors!
    this is the single most important attribute here! if this does not match a prompt,
    scrapli will not work!
    __IMPORTANT__: regex search uses multi-line + case-insensitive flags. multi-line allows
    for highly reliably matching for prompts however we do NOT strip trailing whitespace
    for each line, so be sure to add '\\s?' or similar if your device needs that. This
    should be mostly sorted for you if using network drivers (i.e. `IOSXEDriver`).
- __comms_return_char__: character to used to send returns to host
- __ssh_config_file__: string to path for ssh config file, True to use default ssh config file or False to ignore 
  default ssh config file
- __ssh_known_hosts_file__: string to path for ssh known hosts file, True to use default known file locations. Only 
  applicable/needed if `auth_strict_key` is set to True
- __on_init__: callable that accepts the class instance as its only argument. this callable, if provided, is 
  executed as 
  the last step of object instantiation -- its purpose is primarily to provide a mechanism for scrapli community 
  platforms to have an easy way to modify initialization arguments/object attributes without needing to create a 
  class that extends the driver, instead allowing the community platforms to simply build from the GenericDriver or 
  NetworkDriver classes, and pass this callable to do things such as appending to a username (looking at you 
  RouterOS!!). Note that this is *always* a synchronous function (even for asyncio drivers)!
- __on_open__: callable that accepts the class instance as its only argument. this callable, if provided, is executed 
  immediately after authentication is completed. Common use cases for this callable would be to disable paging or 
  accept any kind of banner message that prompts a user upon connection
- __on_close__: callable that accepts the class instance as its only argument. this callable, if provided, is executed 
  immediately prior to closing the underlying transport. Common use cases for this callable would be to save 
  configurations prior to exiting, or to logout properly to free up vtys or similar
- __transport__: name of the transport plugin to use for the actual telnet/ssh/netconf connection. Available "core" transports are:

    - system
    - telnet
    - asynctelnet
    - ssh2
    - paramiko
    - asyncssh
    
    Please see relevant transport plugin section for details. Additionally, third party transport plugins may be 
    available.

- __transport_options__: dictionary of options to pass to selected transport class; see docs for given transport class 
  for details of what to pass here 
- __channel_lock__: True/False to lock the channel (threading.Lock/asyncio.Lock) during any channel operations, defaults 
  to False
- __channel_log__: True/False, a string path to a file of where to write out channel logs, or a BytesIO object to 
  write to -- these are not "logs" in the normal logging module sense, but only the output that is read from the 
  channel. In other words, the output of the channel log should look similar to what you would see as a human 
  connecting to a device 
- __channel_log_mode__: "write"|"append", all other values will raise ValueError, does what it sounds like it should 
  by setting the channel log to the provided mode
- __logging_uid__: unique identifier (string) to associate to log messages; useful if you have multiple connections 
  to the same device (i.e. one console, one ssh, or one to each supervisor module, etc.)


## Returns

- None


## Raises

- N/A
