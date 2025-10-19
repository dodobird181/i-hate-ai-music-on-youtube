from dataclasses import dataclass
from typing import Optional


@dataclass
class Comment:
    """
    A YouTube comment.
    """

    text: str
    is_reply: bool
    comment_id: str
    author: str = ""
    parent_id: Optional[str] = None

    @property
    def is_top_level(self) -> bool:
        return not self.is_reply

    def __str__(self) -> str:
        if self.is_reply:
            return "ID: {}. Author: {}. Reply to {}. Text: {}.".format(
                self.comment_id,
                self.author,
                self.parent_id,
                self.text,
            )
        return "ID: {}. Author: {}. Text: {}.".format(self.comment_id, self.author, self.text)
