from typing import Annotated, Literal
from decimal import Decimal

from math import ceil

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query

from app.schemas.inventory import StockUpdate
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.schemas.pagination import PaginatedResponse

from app.services.product import ProductService

from app.api.dependencies import CurrentUser, get_product_service, AdminUser


from app.tasks.product import log_product_created

router = APIRouter(prefix="/products", tags=["products"])

ProductServiceDependency = Annotated[
    ProductService,
    Depends(get_product_service),
]

SortBy = Literal["id", "name", "price", "quantity"]
SortOrder = Literal["asc", "desc"]


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_product(
    data: ProductCreate,
    service: ProductServiceDependency,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
):
    try:
        product = service.create_product(data, current_user_id=current_user.id)

        background_tasks.add_task(
            log_product_created,
            product.id,
        )
        return product

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.get(
    "",
    response_model=PaginatedResponse[ProductResponse],
)
def get_products(
    service: ProductServiceDependency,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category_id: int | None = Query(None, ge=1),
    min_price: Decimal | None = Query(None, ge=0),
    max_price: Decimal | None = Query(None, ge=0),
    sort_by: SortBy = Query("id"),
    sort_order: SortOrder = Query("asc"),
):
    products, total = service.get_products_paginated(
        page=page,
        page_size=page_size,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    pages = ceil(total / page_size) if total > 0 else 0

    return PaginatedResponse(
        items=products,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


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
            current_user_id=current_user.id,
            is_admin=current_user.role == "admin",
        )
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
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
            current_user_id=current_user.id,
            is_admin=current_user.role == "admin",
        )
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
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
        product = service.update_product(
            product_id,
            data,
            current_user_id=current_user.id,
            is_admin=current_user.role == "admin",
        )
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

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
