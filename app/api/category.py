from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.services.category import CategoryService
from app.schemas.category import CategoryCreate, CategoryResponse
from app.api.dependencies import get_category_service

router = APIRouter(prefix="/categories", tags=["categories"])

CategoryServiceDependency = Annotated[
    CategoryService,
    Depends(get_category_service),
]


@router.post(
    "",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_category(data: CategoryCreate, service: CategoryServiceDependency):
    return service.create_category(data.name)


@router.get(
    "",
    response_model=list[CategoryResponse],
)
def get_categories(
    service: CategoryServiceDependency,
):
    return service.get_categories()


@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
)
def get_category(
    category_id: int,
    service: CategoryServiceDependency,
):
    category = service.get_category(category_id)

    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, service: CategoryServiceDependency):
    deleted = service.delete_category(category_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )
