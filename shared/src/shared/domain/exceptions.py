class DomainError(Exception):
    def __init__(
        self,
        message: str,
        code: str | None = None,
        details: dict | None = None,
    ) -> None:
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}
        super().__init__(message)


class EntityNotFoundError(DomainError): ...


class BusinessRuleViolationError(DomainError): ...


class AuthorizationError(DomainError): ...


class ConflictError(DomainError): ...


class ValidationError(DomainError): ...


class InfrastructureError(DomainError): ...
