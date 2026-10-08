from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import CurrentUser, get_order_service
from app.schemas.order import OrderCreate, OrderResponse
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
