"""
SECUROXI AI Intelligence 2.0 — Orchestrator Error Taxonomy
Defines structured, strongly-typed errors with error codes, details, and retryability flags.
"""

from typing import Optional, Dict, Any


class OrchestratorError(Exception):
    """Base exception for all orchestrator errors."""
    def __init__(
        self,
        message: str,
        code: str = "ORCHESTRATION_ERROR",
        details: Optional[Dict[str, Any]] = None,
        retryable: bool = False
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
        self.retryable = retryable

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_code": self.code,
            "message": self.message,
            "details": self.details,
            "retryable": self.retryable,
        }


class AuthorizationError(OrchestratorError):
    """Raised when an actor or node attempts an unauthorized operation."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="AUTHORIZATION_ERROR", details=details, retryable=False)


class TenantAccessError(OrchestratorError):
    """Raised when an operation attempts to cross tenant isolation boundaries."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="TENANT_ACCESS_ERROR", details=details, retryable=False)


class ToolNotFoundError(OrchestratorError):
    """Raised when an unregistered tool is requested."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="TOOL_NOT_FOUND", details=details, retryable=False)


class ToolExecutionError(OrchestratorError):
    """Raised when a registered tool fails during execution."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, retryable: bool = True):
        super().__init__(message, code="TOOL_EXECUTION_ERROR", details=details, retryable=retryable)


class ToolTimeoutError(OrchestratorError):
    """Raised when a tool call exceeds its allocated timeout."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="TOOL_TIMEOUT", details=details, retryable=True)


class ToolValidationError(OrchestratorError):
    """Raised when tool inputs or outputs fail schema validation."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="VALIDATION_ERROR", details=details, retryable=False)


class PolicyDeniedError(OrchestratorError):
    """Raised when a high-impact operation is rejected by the Policy Engine."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="POLICY_DENIED", details=details, retryable=False)


class DependencyFailedError(OrchestratorError):
    """Raised when an upstream DAG dependency fails, blocking downstream execution."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="DEPENDENCY_FAILED", details=details, retryable=False)


class BudgetExhaustedError(OrchestratorError):
    """Raised when execution limits (steps, tool calls, tokens, cost) are exceeded."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="RESOURCE_EXHAUSTED", details=details, retryable=False)


class DeadlineExceededError(OrchestratorError):
    """Raised when total run wall-clock time exceeds deadline."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="DEADLINE_EXCEEDED", details=details, retryable=False)


class CancelledError(OrchestratorError):
    """Raised when an active run or node is cancelled by user or system."""
    def __init__(self, message: str = "Execution was cancelled.", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="CANCELLED", details=details, retryable=False)


class ConcurrencyLimitExceededError(OrchestratorError):
    """Raised when backpressure triggers or concurrency ceiling is reached."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="CONCURRENCY_LIMIT_EXCEEDED", details=details, retryable=True)


class ApprovalRejectedError(OrchestratorError):
    """Raised when a required human approval gate is rejected."""
    def __init__(self, message: str = "Human approval was rejected.", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="APPROVAL_REJECTED", details=details, retryable=False)


class InvalidStateTransitionError(OrchestratorError):
    """Raised when an illegal lifecycle state transition is attempted."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="INVALID_STATE_TRANSITION", details=details, retryable=False)
