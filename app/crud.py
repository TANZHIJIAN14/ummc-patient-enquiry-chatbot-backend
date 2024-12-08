from fastcrud import FastCRUD
from app.model.chatModels import User, MessageResp, ChatRoom

crud_user = FastCRUD(User)
crud_message = FastCRUD(MessageResp)
crud_chat_room = FastCRUD(ChatRoom)
