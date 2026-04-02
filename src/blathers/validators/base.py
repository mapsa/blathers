"""Base types for validators."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationResult:
    validator: str
    severity: Severity
    message: str
    term: str | None = None


class Validator(Protocol):
    """Protocol that all validators implement."""

    def validate(self) -> list[ValidationResult]: ...
