from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_product_service
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.services.product import ProductService

from app.api.dependencies import CurrentUser, get_product_service, AdminUser

from app.schemas.inventory import StockUpdate

router = APIRouter(prefix="/products", tags=["products"])

ProductServiceDependency = Annotated[
    ProductService,
    Depends(get_product_service),
]


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_product(
    data: ProductCreate,
    service: ProductServiceDependency,
    current_user: CurrentUser,
):
    try:
        return service.create_product(data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.get(
    "",
    response_model=list[ProductResponse],
)
def get_products(
    service: ProductServiceDependency,
):
    return service.get_products()


@router.post(
    "/{product_id}/stock/add",
    response_model=ProductResponse,
)
def add_stock(
    product_id: int,
    data: StockUpdate,
    service: ProductServiceDependency,
    current_user: CurrentUser,
):
    try:
        product = service.add_stock(
            product_id=product_id,
            quantity=data.quantity,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return product


@router.post(
    "/{product_id}/stock/remove",
    response_model=ProductResponse,
)
def remove_stock(
    product_id: int,
    data: StockUpdate,
    service: ProductServiceDependency,
    current_user: CurrentUser,
):
    try:
        product = service.remove_stock(
            product_id=product_id,
            quantity=data.quantity,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return product


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
)
def get_product(
    product_id: int,
    service: ProductServiceDependency,
):
    product = service.get_product(product_id)

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return product


@router.patch(
    "/{product_id}",
    response_model=ProductResponse,
)
def update_product(
    product_id: int,
    data: ProductUpdate,
    service: ProductServiceDependency,
    current_user: CurrentUser,
):
    try:
        product = service.update_product(product_id, data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return product


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_product(
    product_id: int, service: ProductServiceDependency, current_user: AdminUser
):
    deleted = service.delete_product(product_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
