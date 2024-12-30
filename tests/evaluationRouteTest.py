from http import HTTPStatus

import pytest
from unittest.mock import patch
from httpx import AsyncClient
from app.main import app  # Replace with your app's main module

@pytest.mark.asyncio
async def test_get_evaluation_metrics_success():
    # Mock response data to simulate database response
    mock_evaluation_metrics = [
        {
            "_id":"6772c4da6de83bfef7e82d19",
            "chat_room_id":"Chat 1",
            "user_id":"6771520ca08037a1443eec7a",
            "chat_room_object_id":"67715980971e45fff2dafa34",
            "created_at":"2024-12-29T22:16:18.284",
            "metrics":
                {
                    "relevancy_metric_score":0.25,
                    "relevancy_metric_reason":
                        "The score is <0.25> because quote message 2 where the LLL responded \
                        asking for more details, however the last output skipped explaining specific signs of psychological \
                        abusive actions and instead focused on overall characteristics, then in quote message 4 the response \
                        didn't address the request due to a previous irrelevant output.",
                    "completeness_metric_score":0.0,
                    "completeness_metric_reason":
                        "The score is 0.0 because the LLM's response consistently \
                         failed to meet the user's intentions to report and investigate domestic abuse or seek detailed \
                         information on its characteristics. The LLM provided partial information, seemed unconcerned with \
                         the user's subsequent queries about psychological abuse, and even changed the topic instead of clarifying \
                         its limitations or offering alternative resources.",
                    "role_adherence_metric_score":0.75,
                    "role_adherence_metric_reason":
                        "The score is 0.75 because the LLM chatbot responses included \
                        informative content about abusive relationships, including signs \
                        of sexual abuse (LLM chatbot response in turn #1, citing specific \
                        characteristics like \"being forced into sexual acts without consent\" and \
                        \"being treated in a sexually demeaning manner\"). This type of \
                        information may not be directly related to patient enquiry, \
                        which is the primary focus of our role. While it may be tangential to \
                        patient health or well-being, it veers off from the core knowledge base \
                        we are expected to draw upon for patient-centric responses.",
                    "updated_at":"2024-12-29T22:16:18.284"
                }
        }
    ]

    with patch("app.database.evaluation_collection.find") as mock_find:
        mock_find.return_value = mock_evaluation_metrics

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/evaluation/", params={"user_id": "user123"})

    assert response.status_code == HTTPStatus.OK.value
    assert response.json() == mock_evaluation_metrics

@pytest.mark.asyncio
async def test_get_evaluation_metrics_missing_user_id():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/evaluation/")

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY.value  # Validation error for missing user_id
    assert "user_id" in response.json()["detail"][0]["loc"]

@pytest.mark.asyncio
async def test_get_evaluation_metrics_error_during_retrieval():
    # Simulating an exception during database query
    with patch("app.database.evaluation_collection.find") as mock_find:
        mock_find.side_effect = Exception("Database error occurred")

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/evaluation/", params={"user_id": "user123"})

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR.value  # Internal server error
    assert response.json() == {
        "type": "feedback/unexpected-error",
        "title": "Unexpected error",
        "details": "Failed to get evaluation metrics of user ID: user123",
        "status": HTTPStatus.INTERNAL_SERVER_ERROR.value
    }
