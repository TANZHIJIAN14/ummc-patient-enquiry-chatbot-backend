from pydantic import BaseModel

class ProblemDetail(BaseModel):
    type: str
    title: str
    details: str
    status: int