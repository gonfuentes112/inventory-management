class DomainError(ValueError):
    """Base class for expected business-rule violations."""


class NotFoundError(DomainError):
    """The requested resource does not exist (HTTP 404)."""


class ConflictError(DomainError):
    """The request is valid but conflicts with the current state (HTTP 409)."""


class ProductNotFoundError(NotFoundError):
    pass


class OrderNotFoundError(NotFoundError):
    pass


class InsufficientStockError(ConflictError):
    pass


class InvalidOrderStateError(ConflictError):
    pass


class DuplicateProductError(DomainError):
    """The same product appears twice in one order (HTTP 400)."""
