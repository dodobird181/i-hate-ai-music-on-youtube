from dataclasses import dataclass


@dataclass
class Channel:
    """
    A youtube channel.
    """

    id: str
    title: str
