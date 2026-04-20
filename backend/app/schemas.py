from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, condecimal, constr


class ExpenseCreate(BaseModel):
    amount: condecimal(gt=Decimal("0"), max_digits=12, decimal_places=2)
    category: constr(strip_whitespace=True, min_length=1, max_length=100)
    description: constr(strip_whitespace=True, min_length=1, max_length=255)
    date: date


class ExpenseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: Decimal
    category: str
    description: str
    date: date
    created_at: datetime
