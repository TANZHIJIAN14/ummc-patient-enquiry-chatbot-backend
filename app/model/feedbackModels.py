from datetime import datetime

from pydantic import BaseModel


class CreateFeedbackReq(BaseModel):
    message: str

class CreateFeedbackResp(BaseModel):
    user_id: str
    message: str
    created_at: datetime