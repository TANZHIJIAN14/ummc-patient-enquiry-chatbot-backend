import pytest
from httpx import AsyncClient
from app.main import app  # Replace with your app's main module
from unittest.mock import patch

@pytest.mark.asyncio
async def test_get_chat_room_with_valid_user_id():
    # Mock data to return from the database query
    mock_chat_rooms = [
        {"_id": "1", "user_id": "123", "name": "Chat Room 1"},
        {"_id": "2", "user_id": "123", "name": "Chat Room 2"},
    ]

    # Mock the database collection's find method
    with patch("app.database.chat_room_collection.find") as mock_find:
        mock_find.return_value = iter(mock_chat_rooms)  # Simulate a cursor

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/chat-room", headers={"user_id": "123"})

        assert response.status_code == 200
        assert response.json() == mock_chat_rooms

@pytest.mark.asyncio
async def test_get_chat_room_without_user_id():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/chat-room")

    assert response.status_code == 422
    assert response.json() == {
        "type": "GET /chat-room",
        "title": "Unprocessable entity",
        "details": "User ID header is required.",
        "status": 422,
    }

@pytest.mark.asyncio
async def test_get_chat_room_with_no_chat_rooms():
    # Mock the database collection's find method to return an empty cursor
    with patch("your_application.chat_room_collection.find") as mock_find:
        mock_find.return_value = iter([])  # Simulate an empty cursor

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/chat-room", headers={"user_id": "123"})

        assert response.status_code == 200
        assert response.json() == []

@pytest.mark.asyncio
async def test_get_chat_room_with_internal_server_error():
    # Mock the database collection's find method to raise an exception
    with patch("your_application.chat_room_collection.find", side_effect=Exception("Unexpected error")):
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/chat-room", headers={"user_id": "123"})

        assert response.status_code == 500
        assert response.json() == {
            "type": "GET /chat-room",
            "title": "Internal server error",
            "details": "An error occurred: Unexpected error",
            "status": 500,
        }
