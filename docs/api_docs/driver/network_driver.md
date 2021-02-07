# NetworkDriver Object

The NetworkDriver further extends the GenericDriver objects and adds "network device" specific logic. Chiefly, the 
NetworkDrivers have the concept of "privilege levels" -- levels such as "exec", "privilege-exec", and 
"configuration" in Cisco parlance. 


## Args

- All [`BaseDriver/GenericDriver`](base_driver.md) arguments plus...
- __privilege_levels__: Dict of privilege levels for a given platform
- __default_desired_privilege_level__: string of name of default desired priv, this is the priv level that is generally 
  used to disable paging/set terminal width and things like that upon first login, and is also the priv level 
  scrapli will try to acquire for normal "command" operations (`send_command`, `send_commands`)
- __auth_secondary__: password to use for secondary authentication (enable)
- __failed_when_contains__: list of strings that indicate a command/configuration has failed
- __textfsm_platform__: string name of platform to use for textfsm parsing
- __genie_platform__: string name of platform to use for genie parsing


## Returns

- None


## Raises

- N/A
