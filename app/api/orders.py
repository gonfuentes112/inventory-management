from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import CurrentUser, get_order_service
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


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


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
