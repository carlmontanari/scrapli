from scrapli import AuthOptions, Cli, TransportOptions, TransportSsh2Options
from scrapli.auth import LookupKeyValue
from scrapli.ffi_types import StringPointer


def dummy_logger(level: int, message: StringPointer):
    # not sure why python adds the \xaa bits, if we knew the length we could slice but in the
    # callback scenario we dont know it (unless we amend the callback signature to include it)
    print(f"log :: {level} :: {message.contents.value.rstrip(b"\xaa")}")


def main():
    c = Cli(
        definition_file_or_name="/Users/carl/dev/github/scrapligo/assets/definitions/cisco_iosxe.yaml",
        logger_callback=dummy_logger,
        host="172.31.254.1",
        port=22,
        auth_options=AuthOptions(
            username="FOO",
            password="BAR",
            lookups=[LookupKeyValue(key="enable", value="BAZ")],
        ),
        transport_options=TransportOptions(ssh2=TransportSsh2Options()),
    )

    print("open >> ", c.open().result)
    print("prompt >> ", c.get_prompt().result)
    print("send input >> ", c.send_input(input_="show version | i Ver").result)
    print("enter exec >> ", c.enter_mode(requested_mode="exec"))
    print("enter tclsh >> ", c.enter_mode(requested_mode="tclsh"))
    print("close >> ", c.close())


if __name__ == "__main__":
    main()
