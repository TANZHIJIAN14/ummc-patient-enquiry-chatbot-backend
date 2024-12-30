from http import HTTPStatus

import pytest
from unittest.mock import patch

from bson import ObjectId
from httpx import AsyncClient
from app.main import app  # Replace with your app's main module
from app.model.feedbackModels import CreateFeedbackReq

#------------------------ GET /feedback ------------------------

@pytest.mark.asyncio
async def test_get_feedback_success():
    # Mock feedback data to simulate database response
    mock_feedbacks = [
        {
            "_id": "6771686bafc2ac0add464176",
            "user_id": "6771520ca08037a1443eec7a",
            "message": "Not bad",
            "label": "POSITIVE",
            "created_at": "2024-12-29T23:19:07.880000"
        },
        {
            "_id":"67715a50cfe5a835c3298811",
            "user_id":"6771520ca08037a1443eec7a",
            "message":"I think the response of the chatbot is accurate",
            "label":"POSITIVE",
            "created_at":"2024-12-29T22:18:56.953000"
        }
    ]

    with patch("app.database.feedback_collection.sort") as mock_find:
        # Simulate the sorted feedbacks
        mock_find.return_value = mock_feedbacks

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/feedback/")

    assert response.status_code == HTTPStatus.OK.value
    assert response.json() == mock_feedbacks

@pytest.mark.asyncio
async def test_get_feedback_error_during_retrieval():
    # Simulating an exception during database query
    with patch("app.database.feedback_collection.find") as mock_find:
        mock_find.side_effect = Exception("Database error occurred")

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/feedback/")

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR.value  # Internal server error
    assert response.json() == {
        "type": "GET /feedback",
        "title": "Internal server error",
        "details": "An error occurred: Database error occurred",
        "status": HTTPStatus.INTERNAL_SERVER_ERROR.value
    }

#------------------------ POST /feedback ------------------------

@pytest.mark.asyncio
async def test_send_feedback_success():
    # Mock valid request and user data
    mock_request = CreateFeedbackReq(message="Great service!")
    user_id = "605c72ef153207a2d3d98f35"
    mock_user = {"_id": ObjectId(user_id), "name": "John Doe"}

    # Mock the database call to find the user and insert feedback
    with patch("app.database.users_collection.find_one") as mock_find_user, \
            patch("app.database.feedback_collection.insert_one") as mock_insert_feedback:
        mock_find_user.return_value = mock_user
        mock_insert_feedback.return_value.inserted_id = ObjectId(user_id)

        # Simulate sending feedback
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/feedback/", json=mock_request.model_dump(),
                                         headers={"user-id": user_id})

        assert response.status_code == HTTPStatus.OK.value
        assert response.json()["user_id"] == user_id

@pytest.mark.asyncio
async def test_send_feedback_missing_user_id():
    # Simulate a missing user ID in the header
    mock_request = CreateFeedbackReq(message="Great service!")
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/feedback/", json=mock_request.model_dump())

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY.value
    assert "user-id" in response.json()["detail"][0]["loc"]

@pytest.mark.asyncio
async def test_send_feedback_missing_message():
    # Simulate a missing message in the feedback request
    mock_request = CreateFeedbackReq(message="")

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/feedback/", json=mock_request.model_dump(),
                                     headers={"user-id": "605c72ef153207a2d3d98f35"})

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY.value
    assert response.json() == {
        "type": "feedback/invalid-argument",
        "title": "Invalid argument",
        "details": "Invalid argument",
        "status": HTTPStatus.UNPROCESSABLE_ENTITY.value
    }

@pytest.mark.asyncio
async def test_send_feedback_user_not_found():
    # Simulate a user not found scenario
    mock_request = CreateFeedbackReq(message="Great service!")

    with patch("app.routes.feedbackRoutes.users_collection.find_one") as mock_find_user:
        mock_find_user.return_value = None

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/feedback/", json=mock_request.model_dump(),
                                         headers={"user-id": "605c72ef153207a2d3d98f35"})

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY.value
    assert response.json() == {
        "type": "feedback/user-not-found",
        "title": "User not found",
        "details": "User with ID: 605c72ef153207a2d3d98f35 not found.",
        "status": HTTPStatus.UNPROCESSABLE_ENTITY.value
    }

@pytest.mark.asyncio
async def test_send_feedback_internal_error():
    # Simulate an error during feedback insertion
    mock_request = CreateFeedbackReq(message="Great service!")

    with patch("app.routes.feedbackRoutes.users_collection.find_one") as mock_find_user, \
            patch("app.routes.feedbackRoutes.feedback_collection.insert_one") as mock_insert_feedback:
        mock_find_user.return_value = {"_id": ObjectId("605c72ef153207a2d3d98f35"), "name": "John Doe"}
        mock_insert_feedback.side_effect = Exception("Failed to insert feedback")

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/feedback/", json=mock_request.model_dump(),
                                         headers={"user-id": "605c72ef153207a2d3d98f35"})

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR.value
    assert response.json() == {
        "type": "feedback/unexpected-error",
        "title": "Unexpected error",
        "details": "Failed to insert feedback",
        "status": HTTPStatus.INTERNAL_SERVER_ERROR.value
    }

