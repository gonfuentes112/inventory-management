from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import AdminUser, CurrentUser, get_user_service
from app.schemas.user import UserCreate, UserResponse, UserLogin, TokenResponse
from app.services.user import UserService

from app.core.rate_limit import login_rate_limit

router = APIRouter(prefix="/users", tags=["users"])


UserServiceDependency = Annotated[
    UserService,
    Depends(get_user_service),
]


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(login_rate_limit)],
)
def create_user(
    data: UserCreate,
    service: UserServiceDependency,
):
    try:
        return service.create_user(data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.get(
    "",
    response_model=list[UserResponse],
)
def get_users(service: UserServiceDependency, current_user: AdminUser):
    return service.get_users()


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    data: UserLogin,
    service: UserServiceDependency,
):
    token = service.authenticate_user(
        username=data.username,
        password=data.password,
    )

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    return {
        "access_token": token,
        "token_type": "bearer",
    }


@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
def get_user(user_id: int, service: UserServiceDependency, current_user: CurrentUser):
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user = service.get_user(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user
