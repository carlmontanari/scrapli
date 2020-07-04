"""examples.banners_macros_etc.iosxe_banners_macros_etc"""
from scrapli.driver.core import IOSXEDriver

MY_DEVICE = {
    "host": "172.18.0.11",
    "auth_username": "vrnetlab",
    "auth_password": "VR-netlab9",
    "auth_strict_key": False,
}


def main():
    """Simple example of configuring banners and macros on an IOSXEDevice"""
    conn = IOSXEDriver(**MY_DEVICE)
    conn.open()

    my_banner = """This is my router, get outa here!
I'm serious, you can't be in here!
Go away!
"""

    # the overall pattern/process is that we must use send_interactive as this is an "interactive"
    # style command/input because the prompt changes and relies on a human to understand what is
    # going on. this whole operation is completed by the `send_interactive` method, but we break it
    # up here so its easier to understand what is going on. first we have a "start" point -- where
    # we send the actual command that kicks things off -- in this case "banner motd ^" -- we need to
    # tell scrapli what to expect so it knows there is success; "Enter TEXT message." in this
    # exmaple. We set the "hidden input" to `True` because this forces scrapli to not try to read
    # the inputs back off the channel -- we can't read the inputs because they are interrupted by
    # the prompt of enter your text blah blah.
    banner_start = ("banner motd ^", "Enter TEXT message.", True)
    # next we can simply create an "event" for each line of the banner we want to send, we dont
    # need to set the "hidden_prompt" value to `True` here because scrapli can simply read the
    # inputs off the channel normally as there is no prompts/inputs from the device
    banner_lines = [(line, "\n") for line in my_banner.splitlines()]
    # then we need to "end" our interactive event and ensure scrapli knows how to find the prompt
    # that we'll be left at at the end of this operation. note that you could just capture the
    # config mode prompt via `get_prompt` if you wanted and pass that value here, but we'll set it
    # manually for this example
    banner_end = ("^", "csr1000v(config)#", True)
    # finally we need to add all these sections up into a single list of tuples so that we can pass
    # this to the `send_interactive` method -- note the `*` in front of the `banner_lines` argument
    # we "unpack" the tuples from the list into this final list object
    banner_events = [banner_start, *banner_lines, banner_end]
    result = conn.send_interactive(interact_events=banner_events, privilege_level="configuration")
    print(result.result)

    # Note: csr1000v (at least the version scrapli is regularly tested with does not support macros
    # the following has been tested and works on a 3560 switch
    my_macro = """# description
desc this_is_a_neat_macro

# do a thing
power inline never
"""

    macro_start = ("macro name my_macro", "Enter macro commands one per line.", True)
    macro_lines = [(line, "\n", True) for line in my_macro.splitlines()]
    macro_end = ("@", "csr1000v(config)#", True)
    macro_events = [macro_start, *macro_lines, macro_end]
    result = conn.send_interactive(interact_events=macro_events, privilege_level="configuration")
    print(result.result)


if __name__ == "__main__":
    main()
