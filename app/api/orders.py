from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import CurrentUser, get_order_service
from app.core.exceptions import ConflictError, NotFoundError
from app.schemas.order import OrderCreate, OrderResponse
from app.schemas.pagination import PaginatedResponse
from app.services.order import OrderService

router = APIRouter(
    prefix="/orders",
    tags=["orders"],
)


OrderServiceDependency = Annotated[
    OrderService,
    Depends(get_order_service),
]


def _to_http_exception(exc: ValueError) -> HTTPException:
    if isinstance(exc, NotFoundError):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, ConflictError):
        status_code = status.HTTP_409_CONFLICT
    else:
        status_code = status.HTTP_400_BAD_REQUEST

    return HTTPException(status_code=status_code, detail=str(exc))


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"description": "Invalid order (for example a duplicate product)"},
        404: {"description": "A product in the order does not exist"},
        409: {"description": "Insufficient stock"},
    },
)
def create_order(
    data: OrderCreate,
    service: OrderServiceDependency,
    current_user: CurrentUser,
):
    try:
        return service.create_order(
            data=data,
            current_user_id=current_user.id,
        )

    except ValueError as exc:
        raise _to_http_exception(exc) from exc


@router.post(
    "/{order_id}/cancel",
    response_model=OrderResponse,
    responses={
        404: {"description": "Order not found"},
        409: {"description": "Order is not pending"},
    },
)
def cancel_order(
    order_id: int,
    service: OrderServiceDependency,
    current_user: CurrentUser,
):
    try:
        return service.cancel_order(
            order_id=order_id,
            current_user_id=current_user.id,
        )

    except ValueError as exc:
        raise _to_http_exception(exc) from exc


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
)
def get_order(
    order_id: int,
    service: OrderServiceDependency,
    current_user: CurrentUser,
):
    order = service.get_order(
        order_id=order_id,
        current_user_id=current_user.id,
    )

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    return order


@router.get(
    "",
    response_model=PaginatedResponse[OrderResponse],
)
def get_orders(
    service: OrderServiceDependency,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    orders, total = service.get_orders_paginated(
        current_user_id=current_user.id,
        page=page,
        page_size=page_size,
    )

    pages = (total + page_size - 1) // page_size if total > 0 else 0

    return PaginatedResponse(
        items=orders,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )
