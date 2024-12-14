from pydantic import BaseModel, Field, EmailStr
from typing import List, Literal, Optional
from datetime import datetime
from app.model.pineconeModel import Reference

# User Schema
class User(BaseModel):
    id: str = Field(..., description="Unique identifier for the user")
    name: str = Field(None, max_length=255, description="Name of the user")
    email: EmailStr = Field(..., description="Email of the user")
    created_at: datetime = Field(default_factory=datetime.now, description="Timestamp of user creation")

# Message req schema
class MessageReq(BaseModel):
    user_id: str
    chat_room_id: str = Field(..., description="Unique identifier for the chat room")
    prompt: str = Field(..., description="The content of the message")

# Message resp schema
class MessageResp(BaseModel):
    sender_type: Literal["user", "assistant"] = Field(..., description="Sender type: 'user' or 'chatbot'")
    message: str = Field(..., description="The content of the message")
    reference: Optional[Reference] = Field(..., description="The reference of the message")
    created_at: datetime = Field(default_factory=datetime.now, description="Timestamp of the message creation")

# Chat Room Schema
class ChatRoom(BaseModel):
    id: str = Field(..., description="Unique identifier for the chat room")
    chat_room_id: str
    user_id: str = Field(..., description="Unique identifier of the associated user")
    created_at: datetime = Field(default_factory=datetime.now, description="Timestamp of chat room creation")
    status: Literal["active", "closed"] = Field(default="active", description="Status of the chat room")
    messages: List[MessageResp] = Field(default_factory=list, description="List of messages in the chat room")

# Helper Function to Transform MongoDB `_id` to `id`
def transform_mongo_document(document):
    """
    Transform MongoDB document (_id -> id).
    """
    if "_id" in document:
        document["id"] = str(document["_id"])  # Convert ObjectId to string
        del document["_id"]  # Remove _id from the response
    return document