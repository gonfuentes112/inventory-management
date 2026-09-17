from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    price: float = Field(ge=0)
    owner_id: int
    category_id: int


class ProductResponse(BaseModel):
    id: int
    name: str
    description: str | None
    price: float
    owner_id: int
    category_id: int

    model_config = {"from_attributes": True}
