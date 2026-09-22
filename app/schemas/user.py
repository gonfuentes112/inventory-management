from pydantic import BaseModel, Field, EmailStr


class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    email: EmailStr


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr

    model_config = {"from_attributes": True}
