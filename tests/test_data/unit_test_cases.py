IOSXE_SHOW_VERSION_RAW = """\nCisco IOS XE Software, Version 16.04.01\nCisco IOS Software [Everest], CSR1000V Software (X86_64_LINUX_IOSD-UNIVERSALK9-M), Version 16.4.1, RELEASE SOFTWARE (fc2)\nTechnical Support: http://www.cisco.com/techsupport\nCopyright (c) 1986-2016 by Cisco Systems, Inc.\nCompiled Sun 27-Nov-16 13:02 by mcpre\n\n\nCisco IOS-XE software, Copyright (c) 2005-2016 by cisco Systems, Inc.\nAll rights reserved.  Certain components of Cisco IOS-XE software are\nlicensed under the GNU General Public License ("GPL") Version 2.0.  The\nsoftware code licensed under GPL Version 2.0 is free software that comes\nwith ABSOLUTELY NO WARRANTY.  You can redistribute and/or modify such\nGPL code under the terms of GPL Version 2.0.  For more details, see the\ndocumentation or "License Notice" file accompanying the IOS-XE software,\nor the applicable URL provided on the flyer accompanying the IOS-XE\nsoftware.\n\n\nROM: IOS-XE ROMMON\n\ncsr1000v uptime is 4 hours, 55 minutes\nUptime for this control processor is 4 hours, 56 minutes\nSystem returned to ROM by reload\nSystem image file is "bootflash:packages.conf"\nLast reload reason: reload\n\n\n\nThis product contains cryptographic features and is subject to United\nStates and local country laws governing import, export, transfer and\nuse. Delivery of Cisco cryptographic products does not imply\nthird-party authority to import, export, distribute or use encryption.\nImporters, exporters, distributors and users are responsible for\ncompliance with U.S. and local country laws. By using this product you\nagree to comply with applicable laws and regulations. If you are unable\nto comply with U.S. and local laws, return this product immediately.\n\nA summary of U.S. laws governing Cisco cryptographic products may be found at:\nhttp://www.cisco.com/wwl/export/crypto/tool/stqrg.html\n\nIf you require further assistance please contact us by sending email to\nexport@cisco.com.\n\nLicense Level: ax\nLicense Type: Default. No valid license found.\nNext reload license Level: ax\n\ncisco CSR1000V (VXE) processor (revision VXE) with 2052375K/3075K bytes of memory.\nProcessor board ID 9FKLJWM5EB0\n10 Gigabit Ethernet interfaces\n32768K bytes of non-volatile configuration memory.\n3985132K bytes of physical memory.\n7774207K bytes of virtual hard disk at bootflash:.\n0K bytes of  at webui:.\n\nConfiguration register is 0x2102\n\ncsr1000v#"""
IOSXE_SHOW_VERSION_PROCESSED_NO_STRIP = """Cisco IOS XE Software, Version 16.04.01\nCisco IOS Software [Everest], CSR1000V Software (X86_64_LINUX_IOSD-UNIVERSALK9-M), Version 16.4.1, RELEASE SOFTWARE (fc2)\nTechnical Support: http://www.cisco.com/techsupport\nCopyright (c) 1986-2016 by Cisco Systems, Inc.\nCompiled Sun 27-Nov-16 13:02 by mcpre\n\n\nCisco IOS-XE software, Copyright (c) 2005-2016 by cisco Systems, Inc.\nAll rights reserved.  Certain components of Cisco IOS-XE software are\nlicensed under the GNU General Public License ("GPL") Version 2.0.  The\nsoftware code licensed under GPL Version 2.0 is free software that comes\nwith ABSOLUTELY NO WARRANTY.  You can redistribute and/or modify such\nGPL code under the terms of GPL Version 2.0.  For more details, see the\ndocumentation or "License Notice" file accompanying the IOS-XE software,\nor the applicable URL provided on the flyer accompanying the IOS-XE\nsoftware.\n\n\nROM: IOS-XE ROMMON\n\ncsr1000v uptime is 4 hours, 55 minutes\nUptime for this control processor is 4 hours, 56 minutes\nSystem returned to ROM by reload\nSystem image file is "bootflash:packages.conf"\nLast reload reason: reload\n\n\n\nThis product contains cryptographic features and is subject to United\nStates and local country laws governing import, export, transfer and\nuse. Delivery of Cisco cryptographic products does not imply\nthird-party authority to import, export, distribute or use encryption.\nImporters, exporters, distributors and users are responsible for\ncompliance with U.S. and local country laws. By using this product you\nagree to comply with applicable laws and regulations. If you are unable\nto comply with U.S. and local laws, return this product immediately.\n\nA summary of U.S. laws governing Cisco cryptographic products may be found at:\nhttp://www.cisco.com/wwl/export/crypto/tool/stqrg.html\n\nIf you require further assistance please contact us by sending email to\nexport@cisco.com.\n\nLicense Level: ax\nLicense Type: Default. No valid license found.\nNext reload license Level: ax\n\ncisco CSR1000V (VXE) processor (revision VXE) with 2052375K/3075K bytes of memory.\nProcessor board ID 9FKLJWM5EB0\n10 Gigabit Ethernet interfaces\n32768K bytes of non-volatile configuration memory.\n3985132K bytes of physical memory.\n7774207K bytes of virtual hard disk at bootflash:.\n0K bytes of  at webui:.\n\nConfiguration register is 0x2102\n\ncsr1000v#"""
IOSXE_SHOW_VERSION_PROCESSED_STRIP = IOSXE_SHOW_VERSION_PROCESSED_NO_STRIP[:-11]
IOSXE_EXEC_PROMPT = "csr1000v>"
IOSXE_PRIV_EXEC_PROMPT = "csr1000v#"
IOSXE_CONFIG_PROMPT = "csr1000v(config)#"

IOSXE_TEST_CASES = {
    "test_read_until_prompt": {"expected_prompt": IOSXE_PRIV_EXEC_PROMPT},
    "test_get_prompt": {
        "exec": IOSXE_EXEC_PROMPT,
        "privilege_exec": IOSXE_PRIV_EXEC_PROMPT,
        "configuration": IOSXE_CONFIG_PROMPT,
    },
    "test_send_input": {
        "raw_result": IOSXE_SHOW_VERSION_RAW,
        "processed_result": {
            "strip": IOSXE_SHOW_VERSION_PROCESSED_STRIP,
            "no_strip": IOSXE_SHOW_VERSION_PROCESSED_NO_STRIP,
        },
    },
    "test_send_inputs_interact": {
        "interact_events": [
            ["clear logging", "Clear logging buffer [confirm]"],
            ["", IOSXE_PRIV_EXEC_PROMPT],
        ],
        "raw_result": "clear logging\nClear logging buffer [confirm]\ncsr1000v#",
        "processed_result": "clear logging\nClear logging buffer [confirm]\ncsr1000v#",
    },
}

TEST_CASES = {"cisco_iosxe": IOSXE_TEST_CASES}
