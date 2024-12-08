from typing import List

from pydantic import BaseModel


class Reference(BaseModel):
    status: str
    id: str
    name: str
    size: int
    created_on: str
    updated_on: str
    signed_url: str
    pages: List[int]