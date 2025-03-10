import json
from datetime import datetime
from http import HTTPStatus

from fastapi import APIRouter, Header
from app.database import chat_room_collection, evaluation_collection
from app.eventhandler.evaluation.evaluationEventHandler import EVALUATION_TOPIC_NAME
from app.eventhandler.kafkaConfig import produce_message
from app.model import ProblemDetail
from app.model.chatModels import MessageResp, MessageReq, ChatRoom, transform_mongo_document
from app.model.pineconeModel import Reference
from app.pinecone import assistant_chat
from starlette.responses import JSONResponse

chat_router = APIRouter()
@chat_router.get("/chat-room", response_model=list[ChatRoom])
async def get_chat_rooms(user_id = Header()):
    # Validate user_id header
    if not user_id:
        return JSONResponse(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY.value,
            content=ProblemDetail(
                type="GET /chat-room",
                title="Unprocessable entity",
                details="User ID header is required.",
                status=HTTPStatus.UNPROCESSABLE_ENTITY.value
            ).model_dump()
        )

    try:
        query = {"user_id": user_id}
        cursor = chat_room_collection.find(query)
        chat_rooms = [transform_mongo_document(doc) for doc in cursor]

        if not chat_rooms:
            return []

        return chat_rooms

    except Exception as e:
        # Catch any unexpected errors and return a 500 status
        return JSONResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value,
            content=ProblemDetail(
                type="GET /chat-room",
                title="Internal server error",
                details=f"An error occurred: {e}",
                status=HTTPStatus.INTERNAL_SERVER_ERROR.value
            ).model_dump()
        )

@chat_router.get("/chat-room/{chat_room_id}", response_model=ChatRoom)
async def get_chat_room(chat_room_id, user_id = Header()):
    # Validate user_id header
    if not user_id:
        return JSONResponse(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY.value,
            content=ProblemDetail(
                type="GET /chat-room/{chat-room-id}",
                title="Unprocessable entity",
                details=f"User ID header is required.",
                status=HTTPStatus.UNPROCESSABLE_ENTITY.value
            ).model_dump()
        )

    if not chat_room_id:
        return JSONResponse(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY.value,
            content=ProblemDetail(
                type="GET /chat-room/{chat-room-id}",
                title="Unprocessable entity",
                details="Chat room id is required.",
                status=HTTPStatus.UNPROCESSABLE_ENTITY.value
            ).model_dump()
        )

    query = {
        "$and": [
            {"chat_room_id": {"$eq": chat_room_id}},
            {"user_id": {"$eq": user_id}}
        ]
    }
    chat_room = chat_room_collection.find_one(query)

    if chat_room is None:
        return JSONResponse(
            status_code=HTTPStatus.NOT_FOUND.value,
            content=ProblemDetail(
                type="GET /chat-room/{chat-room-id}",
                title="Chat not found",
                details=f"Chat room with ID: {chat_room_id} is not found",
                status=HTTPStatus.NOT_FOUND.value
            ).model_dump()
        )

    # Extract and validate the fields
    object_id = str(chat_room.get("_id"))
    user_id = str(chat_room.get("user_id"))
    status = str(chat_room.get("status"))
    messages = chat_room.get("messages")
    created_at = chat_room.get("created_at")

    # Return the ChatRoom object
    return ChatRoom(
        id=object_id,
        user_id=user_id,
        created_at=created_at,
        status=status,
        messages=messages
    )

@chat_router.delete("/{chat_room_id}")
async def delete_chat_room(chat_room_id, user_id = Header()):
    if not user_id:
        return JSONResponse(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY.value,
            content=ProblemDetail(
                type="DELETE /chat",
                title="Unprocessable entity",
                details=f"User ID header is required.",
                status=HTTPStatus.UNPROCESSABLE_ENTITY.value
            ).model_dump()
        )

    if not chat_room_id:
        return JSONResponse(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY.value,
            content=ProblemDetail(
                type="DELETE /chat",
                title="Unprocessable entity",
                details="Chat room id is required.",
                status=HTTPStatus.UNPROCESSABLE_ENTITY.value
            ).model_dump()
        )

    query = {
        "$and": [
            {"chat_room_id": {"$eq": chat_room_id}},
            {"user_id": {"$eq": user_id}}
        ]
    }
    chat_room = chat_room_collection.find_one(query)

    if chat_room is None:
        return JSONResponse(
            status_code=HTTPStatus.NOT_FOUND.value,
            content=ProblemDetail(
                type="DELETE /chat",
                title="Chat not found",
                details=f"Chat room with ID: {chat_room_id} is not found",
                status=HTTPStatus.NOT_FOUND.value
            ).model_dump()
        )

    deleted_evaluation = evaluation_collection.find_one(query)

    if deleted_evaluation is None:
        return JSONResponse(
            status_code=HTTPStatus.NOT_FOUND.value,
            content=ProblemDetail(
                type="DELETE /chat",
                title="Chat evaluation not found",
                details=f"Chat room with ID: {chat_room_id} is not found",
                status=HTTPStatus.NOT_FOUND.value
            ).model_dump()
        )

    result_delete_chat_room = chat_room_collection.delete_one(query)

    result_delete_metrics = evaluation_collection.delete_one(query)

    if result_delete_chat_room.deleted_count == 0:
        return JSONResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value,
            content=ProblemDetail(
                type="DELETE /chat",
                title="Internal server error",
                details=f"Failed to delete the chat room with ID: {chat_room_id} of user ID: {user_id}",
                status=HTTPStatus.INTERNAL_SERVER_ERROR.value
            ).model_dump()
        )

    if result_delete_metrics.deleted_count == 0:
        return JSONResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value,
            content=ProblemDetail(
                type="DELETE /chat",
                title="Internal server error",
                details=f"Failed to delete evaluation metrics of chat room with ID: {chat_room_id} of user ID: {user_id}",
                status=HTTPStatus.INTERNAL_SERVER_ERROR.value
            ).model_dump()
        )

    return {"message": f"Chat room: {chat_room_id} of user ID: {user_id} has been successfully deleted."}

@chat_router.post("/", response_model=MessageResp)
async def chat(request: MessageReq):
    try:
        chat_room_object_id, chat_history = get_history_chat(request.chat_room_id, request.user_id)

        # Combine chat history with the current prompt
        full_prompt = f"{chat_history}user: {request.prompt}"

        response = assistant_chat(full_prompt)
        if response.status_code != HTTPStatus.OK.value:
            print(f"Failed to send prompt: {response.json()}")
            raise Exception(response.reason)

        chat_response_message = response.json()["message"]["content"]

        meta_data = None
        if len(response.json()["citations"]) > 0:
            reference_from_assistant = json.loads(json.dumps(response.json()["citations"][0]["references"][0]["file"]))
            meta_data = Reference(
                status=reference_from_assistant["status"],
                id=reference_from_assistant["id"],
                name=reference_from_assistant["name"],
                size=reference_from_assistant["size"],
                created_on=reference_from_assistant["created_on"],
                updated_on=reference_from_assistant["updated_on"],
                signed_url=reference_from_assistant["signed_url"],
                pages=response.json()["citations"][0]["references"][0]["pages"])

        persist_prompt(
            request.chat_room_id,
            request.user_id,
            request.prompt,
            "user")

        persist_prompt(
            request.chat_room_id,
            request.user_id,
            chat_response_message,
            "assistant",
            meta_data)

        #TODO: Generate chat room title during first conversation

        if chat_room_object_id is None or chat_room_object_id == '':
            chat_room_object_id, chat_history = get_history_chat(request.chat_room_id, request.user_id)

        print(f"Produce message to {EVALUATION_TOPIC_NAME}: {chat_room_object_id}")
        produce_message(EVALUATION_TOPIC_NAME, 'id', chat_room_object_id)

        return MessageResp(
            sender_type="assistant",
            message=chat_response_message,
            reference=meta_data,
            created_at=datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))
    except Exception as e:
        print(f"Error: {e}")
        return JSONResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value,
            content=ProblemDetail(
                type="POST /chat",
                title="Internal server error",
                details=f"Failed to upload chat: {e}",
                status=HTTPStatus.INTERNAL_SERVER_ERROR.value
            ).model_dump()
        )

def get_history_chat(chat_room_id: str, user_id: str):
    # Query chat history from MongoDB
    chat_room = chat_room_collection.find_one(
        {"chat_room_id": chat_room_id, "user_id": user_id, "status": "active"}
    )

    chat_history = ""
    if chat_room and "messages" in chat_room:
        for message in chat_room["messages"]:
            # Format the history as "<sender_type>: <message>"
            chat_history += f'{message["sender_type"]}: {message["message"]}\n'

        return chat_room.get('_id'), chat_history

    return "", chat_history

def persist_prompt(chatroom_id: str, user_id: str, message: str, sender_type: str, meta_data: Reference = None):
    """
    Persist the user's prompt to the MongoDB chatRooms collection.
    """
    reference_dict = meta_data.model_dump() if meta_data else None
    message_entry = {
        "sender_type": sender_type,
        "message": message,
        "reference": reference_dict,
        "created_at": datetime.now()
    }

    # Update the chat room's messages array
    return chat_room_collection.update_one(
        {
            "chat_room_id": chatroom_id,
            "user_id": user_id,
            "status": "active"
        },
        {
            "$setOnInsert": {"created_at": datetime.now()},  # Set createdAt only on insert
            "$push": {"messages": message_entry}  # Append to the messages array
        },
        upsert=True
    )

