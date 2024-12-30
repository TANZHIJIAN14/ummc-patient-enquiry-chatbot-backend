from http import HTTPStatus

import pytest
from unittest.mock import patch
from httpx import AsyncClient
from app.main import app  # Replace with your app's main module

@pytest.mark.asyncio
async def test_convert_url_to_pdf_success():
    mock_response = {
        "url": "https://example.com/generated.pdf",
        "name": "example.pdf",
        "size": 12345,
        "status": "success"
    }

    with patch("app.routes.convertUrlRoute.requests.post") as mock_post:
        mock_post.return_value.json.return_value = mock_response
        mock_post.return_value.status_code = HTTPStatus.OK.value

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/convert/pdf-from-url",
                params={"url": "https://example.com", "file_name": "example.pdf"}
            )

    print(response.json())
    assert response.status_code == HTTPStatus.OK.value
    assert response.json() == mock_response

@pytest.mark.asyncio
async def test_convert_url_to_pdf_missing_parameters():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/convert/pdf-from-url",
            json={"url": ""}  # Missing file_name
        )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY.value  # Validation error
    assert "detail" in response.json()

@pytest.mark.asyncio
async def test_convert_url_to_pdf_external_api_failure():
    with patch("app.routes.convertUrlRoute.requests.post") as mock_post:
        mock_post.return_value.json.return_value = {
            "status": "error",
            "message": "API key invalid or request failed."
        }
        mock_post.return_value.status_code = HTTPStatus.UNPROCESSABLE_ENTITY.value

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/convert/pdf-from-url",
                params={"url": "https://example.com", "file_name": "example.pdf"}
            )

    assert response.status_code == HTTPStatus.OK.value  # Your endpoint doesn't handle external API failure directly
    assert response.json() == {
        "status": "error",
        "message": "API key invalid or request failed."
    }
