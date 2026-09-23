from pydantic import BaseModel, Field


class StockUpdate(BaseModel):
    quantity: int = Field(gt=0)
