# Subscriptions

Netconf subscriptions... are wild. There are several differnet ways to set them up depending on the
RFC the server supports. As such, scrapli said: NOPE. You can instead setup subscriptions yourself
using the `raw_rpc` method. This example shows using the Netopeer server for a basic
`create-subscription` setup and a bring your own IOSXE device to show an `establish-subscription`
setup. Note that in the former case you use the `get_next_notification` method to fetch
notification messages, while in the latter you use `get_next_subscription` as the subscription
style will have an associated subscription id.
