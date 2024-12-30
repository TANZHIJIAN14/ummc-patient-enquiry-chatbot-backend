from io import BytesIO

import pytest
from unittest.mock import patch, MagicMock
from httpx import AsyncClient

from app.main import app  # Replace with your app's main module
from http import HTTPStatus

#------------------------ GET /upload/file ------------------------

@pytest.mark.asyncio
async def test_get_file_success():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/upload/file")
    assert response.status_code == HTTPStatus.OK.value

#------------------------ GET /upload/file/gradio_file_path ------------------------

@pytest.mark.asyncio
async def test_get_file_by_gradio_file_path_success():
    # Simulate a successful file retrieval
    mock_gradio_file_path = "some_file_path"
    mock_file_data = {
        "_id": "some_id",
        "gradio_file_path": mock_gradio_file_path,
        "filename": "test_file.pdf",
        "size": 1234,
        "status": "uploaded",
        "uploaded_at": "2024-12-30T12:34:56",
        "metadata": {"key": "value"},
        "uploaded_file_id": "uploaded_file_id_example"
    }

    # Patch the database call to return mock data
    with patch("app.routes.uploadFileRoute.uploaded_file_collection.find_one", return_value=mock_file_data):
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/upload/file/gradio_file_path",
                                        params={"gradio_file_path": mock_gradio_file_path})

        assert response.status_code == HTTPStatus.OK
        assert response.json() == mock_file_data

@pytest.mark.asyncio
async def test_get_file_by_gradio_file_path_not_found():
    # Simulate a file not found scenario
    mock_gradio_file_path = "non_existent_file_path"

    # Patch the database call to return None (file not found)
    with patch("app.routes.uploadFileRoute.uploaded_file_collection.find_one",
               side_effect=Exception(f"{mock_gradio_file_path} not found")):
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/upload/file/gradio_file_path",
                                        params={"gradio_file_path": mock_gradio_file_path})

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR.value
    assert response.json() == {
        "type": "chat/file/non_existent_file_path",
        "title": "Internal server error",
        "details": f"An error occurred: {mock_gradio_file_path} not found",
        "status": HTTPStatus.INTERNAL_SERVER_ERROR.value
    }

#------------------------ POST /upload/file/gradio_file_path ------------------------

@pytest.mark.asyncio
async def test_upload_pdf_file_success():
    # Simulate a valid PDF file
    mock_pdf_content = b'%PDF-1.4 mock PDF content'
    mock_pdf_file = BytesIO(mock_pdf_content)
    mock_pdf_file.name = "test_file.pdf"

    # Patch the database call to return a mock insert result
    mock_insert_result = MagicMock()
    mock_insert_result.inserted_id = "some_id"
    with patch("app.routes.uploadFileRoute.uploaded_file_collection.insert_one", return_value=mock_insert_result):
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/upload/file/pdf",
                files={"files": ("test_file.pdf", mock_pdf_file, "application/pdf")}
            )

    assert response.status_code == HTTPStatus.OK.value
    assert response.json() == {
        "message": "File upload process completed",
        "details": [{
            "filename": "test_file.pdf",
            "status": "processing",
            "file_id": "some_id"
        }]
    }

@pytest.mark.asyncio
async def test_upload_invalid_file_format():
    # Simulate an invalid file format (e.g., a text file)
    mock_txt_content = b"Hello, this is a text file."
    mock_txt_file = BytesIO(mock_txt_content)
    mock_txt_file.name = "test_file.txt"

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/upload/file/pdf",
            files={"files": ("test_file.txt", mock_txt_file, "text/plain")}
        )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY.value
    assert response.json() == {
        "type": "chat/file/pdf",
        "title": "Invalid file format",
        "details": "Only PDF files are allowed.",
        "status": HTTPStatus.UNPROCESSABLE_ENTITY.value
    }

@pytest.mark.asyncio
async def test_upload_file_internal_error():
    # Simulate an internal error during the file processing (e.g., unexpected exception)
    mock_pdf_content = b'%PDF-1.4 mock PDF content'
    mock_pdf_file = BytesIO(mock_pdf_content)
    mock_pdf_file.name = "test_file.pdf"

    with patch("app.routes.uploadFileRoute.uploaded_file_collection.insert_one",
               side_effect=Exception("Database error")):
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/upload/file/pdf",
                files={"files": ("test_file.pdf", mock_pdf_file, "application/pdf")}
            )

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR.value
    assert response.json() == {
        "type": "chat/file/pdf",
        "title": "Internal server error",
        "details": "An error occurred: Database error",
        "status": HTTPStatus.INTERNAL_SERVER_ERROR.value
    }

@pytest.mark.asyncio
async def test_upload_file_mongo_insert_failure():
    # Simulate a MongoDB insertion failure (inserted_id is None)
    mock_pdf_content = b'%PDF-1.4 mock PDF content'
    mock_pdf_file = BytesIO(mock_pdf_content)
    mock_pdf_file.name = "test_file.pdf"

    mock_insert_result = MagicMock()
    mock_insert_result.inserted_id = None
    with patch("app.routes.uploadFileRoute.uploaded_file_collection.insert_one",
               return_value=mock_insert_result):
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/upload/file/pdf",
                files={"files": ("test_file.pdf", mock_pdf_file, "application/pdf")}
            )

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR.value
    assert response.json() == {
        "type": "chat/file/pdf",
        "title": "Unexpected error",
        "details": "Object id from mongo db is not found",
        "status": HTTPStatus.INTERNAL_SERVER_ERROR.value
    }



