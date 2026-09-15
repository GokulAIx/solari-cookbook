"""Small result types shared by the agent and later reliability layers."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentResult:
    claimed_success: bool
    message: str
    actions: int
    status: str = "unknown"


@dataclass(frozen=True)
class VerificationResult:
    passed: bool
    product: str
    quantity: int
    reason: str