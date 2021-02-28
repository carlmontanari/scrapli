"""scrapli.docs.generate"""
import pdoc
from pdoc import _render_template, tpl_lookup

context = pdoc.Context()
module = pdoc.Module("scrapli", context=context)
pdoc.link_inheritance(context)
tpl_lookup.directories.insert(0, "docs/generate")

doc_map = {
    "scrapli.driver.base.base_driver": {"path": "driver/base/base_driver", "content": None},
    "scrapli.driver.base.sync_driver": {"path": "driver/base/sync_driver", "content": None},
    "scrapli.driver.base.async_driver": {"path": "driver/base/async_driver", "content": None},
    "scrapli.driver.generic.base_driver": {"path": "driver/generic/base_driver", "content": None},
    "scrapli.driver.generic.sync_driver": {"path": "driver/generic/sync_driver", "content": None},
    "scrapli.driver.generic.async_driver": {"path": "driver/generic/async_driver", "content": None},
    "scrapli.driver.network.base_driver": {"path": "driver/network/base_driver", "content": None},
    "scrapli.driver.network.sync_driver": {"path": "driver/network/sync_driver", "content": None},
    "scrapli.driver.network.async_driver": {"path": "driver/network/async_driver", "content": None},
    "scrapli.driver.core.arista_eos.base_driver": {
        "path": "driver/core/arista_eos/base_driver",
        "content": None,
    },
    "scrapli.driver.core.arista_eos.sync_driver": {
        "path": "driver/core/arista_eos/sync_driver",
        "content": None,
    },
    "scrapli.driver.core.arista_eos.async_driver": {
        "path": "driver/core/arista_eos/async_driver",
        "content": None,
    },
    "scrapli.driver.core.cisco_iosxe.base_driver": {
        "path": "driver/core/cisco_iosxe/base_driver",
        "content": None,
    },
    "scrapli.driver.core.cisco_iosxe.sync_driver": {
        "path": "driver/core/cisco_iosxe/sync_driver",
        "content": None,
    },
    "scrapli.driver.core.cisco_iosxe.async_driver": {
        "path": "driver/core/cisco_iosxe/async_driver",
        "content": None,
    },
    "scrapli.driver.core.cisco_iosxr.base_driver": {
        "path": "driver/core/cisco_iosxr/base_driver",
        "content": None,
    },
    "scrapli.driver.core.cisco_iosxr.sync_driver": {
        "path": "driver/core/cisco_iosxr/sync_driver",
        "content": None,
    },
    "scrapli.driver.core.cisco_iosxr.async_driver": {
        "path": "driver/core/cisco_iosxr/async_driver",
        "content": None,
    },
    "scrapli.driver.core.cisco_nxos.base_driver": {
        "path": "driver/core/cisco_nxos/base_driver",
        "content": None,
    },
    "scrapli.driver.core.cisco_nxos.sync_driver": {
        "path": "driver/core/cisco_nxos/sync_driver",
        "content": None,
    },
    "scrapli.driver.core.cisco_nxos.async_driver": {
        "path": "driver/core/cisco_nxos/async_driver",
        "content": None,
    },
    "scrapli.driver.core.juniper_junos.base_driver": {
        "path": "driver/core/juniper_junos/base_driver",
        "content": None,
    },
    "scrapli.driver.core.juniper_junos.sync_driver": {
        "path": "driver/core/juniper_junos/sync_driver",
        "content": None,
    },
    "scrapli.driver.core.juniper_junos.async_driver": {
        "path": "driver/core/juniper_junos/async_driver",
        "content": None,
    },
    "scrapli.channel.base_channel": {"path": "channel/base_channel", "content": None},
    "scrapli.channel.sync_channel": {"path": "channel/sync_channel", "content": None},
    "scrapli.channel.async_channel": {"path": "channel/async_channel", "content": None},
    "scrapli.transport.base.base_transport": {
        "path": "transport/base/base_transport",
        "content": None,
    },
    "scrapli.transport.base.sync_transport": {
        "path": "transport/base/sync_transport",
        "content": None,
    },
    "scrapli.transport.base.async_transport": {
        "path": "transport/base/async_transport",
        "content": None,
    },
    "scrapli.transport.base.base_socket": {"path": "transport/base/base_socket", "content": None},
    "scrapli.transport.plugins.asyncssh.transport": {
        "path": "transport/plugins/asyncssh",
        "conent": None,
    },
    "scrapli.transport.plugins.asynctelnet.transport": {
        "path": "transport/plugins/asynctelnet",
        "conent": None,
    },
    "scrapli.transport.plugins.paramiko.transport": {
        "path": "transport/plugins/paramiko",
        "conent": None,
    },
    "scrapli.transport.plugins.ssh2.transport": {"path": "transport/plugins/ssh2", "conent": None},
    "scrapli.transport.plugins.system.transport": {
        "path": "transport/plugins/system",
        "conent": None,
    },
    "scrapli.transport.plugins.telnet.transport": {
        "path": "transport/plugins/telnet",
        "conent": None,
    },
    "scrapli.decorators": {"path": "decorators", "content": None},
    "scrapli.exceptions": {"path": "exceptions", "content": None},
    "scrapli.factory": {"path": "factory", "content": None},
    "scrapli.helper": {"path": "helper", "content": None},
    "scrapli.logging": {"path": "logging", "content": None},
    "scrapli.response": {"path": "response", "content": None},
    "scrapli.ssh_config": {"path": "ssh_config", "content": None},
}


def recursive_mds(module):  # noqa
    """Recursively render mkdocs friendly markdown/html"""
    yield module.name, _render_template("/mkdocs_markdown.mako", module=module)
    for submod in module.submodules():
        yield from recursive_mds(submod)


def main():
    """Generate docs"""
    for module_name, html in recursive_mds(module=module):
        if module_name not in doc_map.keys():
            continue

        doc_map[module_name]["content"] = html

    for module_name, module_doc_data in doc_map.items():
        if not module_doc_data["content"]:
            print(f"broken module {module_name}")
            continue
        with open(f"docs/api_docs/{module_doc_data['path']}.md", "w") as f:
            f.write(module_doc_data["content"])


if __name__ == "__main__":
    main()
