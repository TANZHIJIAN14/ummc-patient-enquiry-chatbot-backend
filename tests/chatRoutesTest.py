from datetime import datetime
from http import HTTPStatus

import pytest
from httpx import AsyncClient
from app.main import app  # Replace with your app's main module
from unittest.mock import patch

#------------------------ GET /chat/chat-room ------------------------

@pytest.mark.asyncio
async def test_get_chat_room_with_valid_user_id():
    # Mock data to return from the database query
    user_id = "6771520ca08037a1443eec7a"
    mock_chat_rooms = [
        {
            "_id":"6772aff6bfdc44e562806086",
            "chat_room_id":"Chat 2",
            "status":"active",
            "user_id":user_id,
            "created_at":"2024-12-29T22:15:27.388000Z",
            "messages":[
                {"sender_type":"user","message":"hihi","reference":None,"created_at":"2024-12-29T23:01:10.388000Z"},
                {"sender_type":"assistant","message":"Hello! How can I assist you today?","reference":None,"created_at":"2024-12-29T23:01:10.388000Z"}
            ]}
    ]

    # Mock the database collection's find method
    with patch("app.database.chat_room_collection.find") as mock_find:
        mock_find.return_value = iter(mock_chat_rooms)  # Simulate a cursor

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/chat/chat-room", headers={"user-id": user_id})

        print(response.json())
        assert response.status_code == HTTPStatus.OK.value
        assert response.json() == mock_chat_rooms

@pytest.mark.asyncio
async def test_get_chat_room_without_user_id():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/chat/chat-room", headers={"user-id": ""})

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY.value
    assert response.json() == {
        "type": "GET /chat-room",
        "title": "Unprocessable entity",
        "details": "User ID header is required.",
        "status": HTTPStatus.UNPROCESSABLE_ENTITY.value,
    }

@pytest.mark.asyncio
async def test_get_chat_room_with_no_chat_rooms():
    # Mock the database collection's find method to return an empty cursor
    user_id = "6771520ca08037a1443eec7a"
    with patch("app.database.chat_room_collection.find") as mock_find:
        mock_find.return_value = iter([])  # Simulate an empty cursor

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/chat/chat-room", headers={"user-id": user_id})

        assert response.status_code == HTTPStatus.OK.value
        assert response.json() == []

@pytest.mark.asyncio
async def test_get_chat_room_with_internal_server_error():
    # Mock the database collection's find method to raise an exception
    user_id = "6771520ca08037a1443eec7a"
    with patch("app.database.chat_room_collection.find", side_effect=Exception("Unexpected error")):
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/chat/chat-room", headers={"user-id": user_id})

        assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR.value
        assert response.json() == {
            "type": "GET /chat-room",
            "title": "Internal server error",
            "details": "An error occurred: Unexpected error",
            "status": HTTPStatus.INTERNAL_SERVER_ERROR.value,
        }

#------------------------ DELETE /chat/chat-room ------------------------

@pytest.mark.asyncio
async def test_delete_chat_room_missing_user_id():
    async with AsyncClient(app=app, base_url="http://test", headers={"user-id": ""}) as client:
        response = await client.delete("/chat/123")

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY.value
    assert response.json() == {
        "type": "DELETE /chat",
        "title": "Unprocessable entity",
        "details": "User ID header is required.",
        "status": HTTPStatus.UNPROCESSABLE_ENTITY.value,
    }

@pytest.mark.asyncio
async def test_delete_chat_room_not_found():
    with patch("app.database.chat_room_collection.find_one", return_value=None):
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.delete("/chat/123", headers={"user-id": "456"})

    assert response.status_code == HTTPStatus.NOT_FOUND.value
    assert response.json() == {
        "type": "DELETE /chat",
        "title": "Chat not found",
        "details": "Chat room with ID: 123 is not found",
        "status": HTTPStatus.NOT_FOUND.value,
    }

@pytest.mark.asyncio
async def test_delete_chat_room_successful():
    # Mock the database methods
    with patch("app.database.chat_room_collection.find_one",
               return_value={"_id": "1", "chat_room_id": "123", "user_id": "456"}), \
            patch("app.database.chat_room_collection.delete_one",
                  return_value=type("MockResult", (object,), {"deleted_count": 1})), \
            patch("app.database.evaluation_collection.delete_one",
                  return_value=type("MockResult", (object,), {"deleted_count": 1})):
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.delete("/chat/123", headers={"user-id": "456"})

    assert response.status_code == HTTPStatus.OK.value
    assert response.json() == {
        "message": "Chat room: 123 of user ID: 456 has been successfully deleted."
    }


@pytest.mark.asyncio
async def test_delete_chat_room_failed_chat_room_deletion():
    with patch("app.database.chat_room_collection.find_one",
               return_value={"_id": "1", "chat_room_id": "123", "user_id": "456"}), \
            patch("app.database.chat_room_collection.delete_one",
                  return_value=type("MockResult", (object,), {"deleted_count": 0})):
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.delete("/chat/123", headers={"user-id": "456"})

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR.value
    assert response.json() == {
        "type": "DELETE /chat",
        "title": "Internal server error",
        "details": "Failed to delete the chat room with ID: 123 of user ID: 456",
        "status": HTTPStatus.INTERNAL_SERVER_ERROR.value,
    }

@pytest.mark.asyncio
async def test_delete_chat_room_failed_metrics_deletion():
    with patch("app.database.chat_room_collection.find_one",
               return_value={"_id": "1", "chat_room_id": "123", "user_id": "456"}), \
            patch("app.database.chat_room_collection.delete_one",
                  return_value=type("MockResult", (object,), {"deleted_count": 1})), \
            patch("app.database.evaluation_collection.delete_one",
                  return_value=type("MockResult", (object,), {"deleted_count": 0})):
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.delete("/chat/123", headers={"user-id": "456"})

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR.value
    assert response.json() == {
        "type": "DELETE /chat",
        "title": "Internal server error",
        "details": "Failed to delete evaluation metrics of chat room with ID: 123 of user ID: 456",
        "status": HTTPStatus.INTERNAL_SERVER_ERROR.value,
    }


#------------------------ POST /chat ------------------------

@pytest.mark.asyncio
async def test_chat_success():
    # Mock input and output
    mock_request = {
        "chat_room_id": "room123",
        "user_id": "user456",
        "prompt": "What is the weather today?"
    }

    mock_response = {
        "message": {"content": "The weather today is sunny."},
        "citations": []
    }

    with patch("app.routes.chatRoutes.get_history_chat", return_value=("room123", "")), \
         patch("app.routes.chatRoutes.assistant_chat", return_value=type("MockResponse", (object,), {"json": lambda: mock_response})), \
         patch("app.routes.chatRoutes.persist_prompt", return_value=None), \
         patch("app.eventhandler.kafkaConfig.produce_message", return_value=None):

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/chat/", json=mock_request)

    assert response.status_code == HTTPStatus.OK.value
    assert response.json() == {
        "sender_type": "assistant",
        "message": "The weather today is sunny.",
        "reference": None,
        "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    }

@pytest.mark.asyncio
async def test_chat_missing_chat_room_id():
    mock_request = {
        "user_id": "user456",
        "prompt": "What is the weather today?"
    }

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/chat/", json=mock_request)

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY.value
    assert "chat_room_id" in response.json()["detail"][0]["loc"]

@pytest.mark.asyncio
async def test_chat_missing_user_id():
    mock_request = {
        "chat_room_id": "room123",
        "prompt": "What is the weather today?"
    }

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/chat/", json=mock_request)

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY.value
    assert "user_id" in response.json()["detail"][0]["loc"]


@pytest.mark.asyncio
async def test_chat_assistant_chat_failure():
    # Mock input and assistant chat failure
    mock_request = {
        "chat_room_id": "room123",
        "user_id": "user456",
        "prompt": "What is the weather today?"
    }

    with patch("app.routes.chatRoutes.get_history_chat", return_value=("room123", "")), \
         patch("app.routes.chatRoutes.assistant_chat", side_effect=Exception("Assistant chat failed")):

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/chat/", json=mock_request)

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR.value
    assert response.json() == {
        "type": "POST /chat",
        "title": "Internal server error",
        "details": "Failed to upload chat: Assistant chat failed",
        "status": HTTPStatus.INTERNAL_SERVER_ERROR.value
    }

@pytest.mark.asyncio
async def test_chat_unexpected_error():
    # Mock input and unexpected error
    mock_request = {
        "chat_room_id": "room123",
        "user_id": "user456",
        "prompt": "What is the weather today?"
    }

    with patch("app.routes.chatRoutes.get_history_chat", side_effect=Exception("Unexpected error")):

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/chat/", json=mock_request)

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR.value
    assert response.json() == {
        "type": "POST /chat",
        "title": "Internal server error",
        "details": "Failed to upload chat: Unexpected error",
        "status": HTTPStatus.INTERNAL_SERVER_ERROR.value
    }
