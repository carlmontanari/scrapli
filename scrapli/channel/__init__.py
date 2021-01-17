"""scrapli.channel"""
from scrapli.channel.async_channel import AsyncChannel
from scrapli.channel.sync_channel import Channel

__all__ = (
    "AsyncChannel",
    "Channel",
)
