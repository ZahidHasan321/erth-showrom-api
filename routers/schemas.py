from pydantic import BaseModel
from typing import Any, Optional


# --- Request Schema ---
class RecordSchema(BaseModel):
    id: str | None = None
    fields: dict


# --- Response Schema ---
class ApiResponse(BaseModel):
    status: str
    message: Optional[str] = None
    data: Optional[Any] = None
    count: Optional[int] = None


# --- Order Filter Schema ---
class OrderFilterSchema(BaseModel):
    """Schema for filtering orders with optional parameters"""
    OrderID: Optional[str] = None
    Status: Optional[str] = None
    CustomerID: Optional[list[str]] = None
    # Add more filter fields as needed
    # You can add date ranges, price ranges, etc.
