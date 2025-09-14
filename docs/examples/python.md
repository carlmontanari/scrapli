# Python

This page contains a very simple example for using scrapli to connect to a CLI device (telnet/ssh) as well as a NETCONF server -- there are many more examples [here](https://github.com/carlmontanari/scrapli/tree/main/examples), so check those out too.


## CLI


```python
from scrapli import AuthOptions, Cli # (1)


def main(name):
    cli = Cli( # (2)
        definition_file_or_name="cisco_iosxe",
        host="myrouter",
        auth_options=AuthOptions(
            username="scrapli",
            password="verysecurepassword",
        ),
    )

    with cli as c: # (3)
        result = c.send_input(input_="show version") # (4)
        print(result.result) # (5)

if __name__ == "__main__":
    main()
```

1. Import the `Cli` and `AuthOptions` objects from scrapli, the `Cli` object is the class that represents our connection to some device via telnet/SSH, and `AuthOptions` is just a class that holds various authentication related things.
2. Here we create our instance `cli` of the `Cli` class -- the only *required* argument is `host` -- as of course we must tell scrapli what host to connect to, but here we also provide a few other common things. `definition_file_or_name` refers to either a [platform name](../details.md#platform-definitions) or a local YAML file defining a platform. `auth_options` is of course options related to authentication.
3. The `Cli` implements the context manager protocol, so you can use it like this in a `with` block, or simply call `open` and then `close` when you are done.
4. Once we've got an opened connection we can use methods like `send_input` to interact with the device.
5. All operations return a `Result` object, in this case we are printing the `result` field of that object which of course contains the output from our input.


## NETCONF


```python
from scrapli import AuthOptions, Netconf # (1)


def main(name):
    netconf = Netconf( # (2)
        host="myrouter",
        auth_options=AuthOptions(
            username="scrapli",
            password="verysecurepassword",
        ),
    )

    with cli as c: # (3)
        result = c.get_config() # (4)
        print(result.result) # (5)

if __name__ == "__main__":
    main()
```

1. Similar to the cli example we'll import `Netconf` here with our `AuthOptions`.
2. When creating a `Netconf` connection we only need to provide the host and probably auth information.
3. Again, using the context manager is a good idea, but not strictly required.
4. Once we've got an opened connection we can use methods like `send_input` to interact with the device.
5. All methods also return a `Result`, though this time it is a NETCONF flavor result, but the look and feel is pretty much the same!
