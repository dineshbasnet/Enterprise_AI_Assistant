from typing import Literal
from pydantic import BaseModel


class SupportDecision(BaseModel):

    action: Literal[
        "answer",
        "ticket"
    ]

    reasoning: str