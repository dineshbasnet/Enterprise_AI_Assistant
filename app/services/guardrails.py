from __future__ import annotations
import re
from pydantic import BaseModel
import logfire


class GuardrailResult(BaseModel):
    passed: bool
    reason: str = ""
    modified_input: str = ""


_PII_PATTERNS = [
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "<SSN>"),
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"), "<EMAIL>"),
    (re.compile(r"\b\d{10,13}\b"), "<PHONE>"),
    (re.compile(r"\b4[0-9]{12}(?:[0-9]{3})?\b"), "<CARD>"),
]

_INJECTION_PATTERNS = [
    re.compile(r"ignore (all |previous |prior )?instructions", re.I),
    re.compile(r"you are now", re.I),
    re.compile(r"disregard (your |all )?", re.I),
    re.compile(r"system prompt", re.I),
    re.compile(r"jailbreak", re.I),
]


