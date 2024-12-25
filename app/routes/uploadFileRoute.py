import os
from datetime import datetime
from http import HTTPStatus
from typing import List

from bson import ObjectId
from fastapi import APIRouter, UploadFile, File, HTTPException
from starlette.responses import JSONResponse

from app.database import uploaded_file_collection, db
from bson.binary import Binary
import gridfs

from app.eventhandler.deleteFileEventHandler import DELETED_FILE_TOPIC_NAME
from app.eventhandler.kafkaConfig import produce_message
from app.eventhandler.uploadedFileEventHandler import UPLOADED_FILE_TOPIC_NAME
from app.model import ProblemDetail
from app.pinecone import get_assistant_file
from util import serialize_mongo_document

fs = gridfs.GridFS(db)

upload_file_router = APIRouter()
@upload_file_router.get("/file")
async def get_file():
    try:
        all_uploaded_files = uploaded_file_collection.find().sort("uploaded_at", -1)
        return [serialize_mongo_document(doc) for doc in all_uploaded_files]
    except Exception as e:
        return JSONResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value,
            content=ProblemDetail(
                type="chat/file",
                title="Internal server error",
                details=f"An error occurred: {e}",
                status=HTTPStatus.INTERNAL_SERVER_ERROR.value
            ).model_dump()
        )

@upload_file_router.get("/file/gradio_file_path")
async def get_file_by_gradio_file_path(gradio_file_path: str):
    try:
        query = {"gradio_file_path": gradio_file_path}
        file = uploaded_file_collection.find_one(query)
        return serialize_mongo_document(file)
    except Exception as e:
        return JSONResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value,
            content=ProblemDetail(
                type="chat/file/{gradio_file_path}",
                title="Internal server error",
                details=f"An error occurred: {e}",
                status=HTTPStatus.INTERNAL_SERVER_ERROR.value
            ).model_dump()
        )

@upload_file_router.post("/file/pdf")
async def upload_file(files: List[UploadFile] = File(...)):
    responses = []

    for file in files:
        if file.content_type != "application/pdf":
            return JSONResponse(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY.value,
                content=ProblemDetail(
                    type="chat/file/pdf",
                    title="Invalid file format",
                    details="Only PDF files are allowed.",
                    status=HTTPStatus.UNPROCESSABLE_ENTITY.value
                ).model_dump()
            )

        try:
            # Read file content
            file_content = await file.read()

            # Create a document for the file
            file_document = {
                "gradio_file_path": file.filename,
                "filename": os.path.basename(file.filename),
                "content_type": file.content_type,
                "size": len(file_content),
                "status": "Processing",
                "uploaded_at": datetime.now(),
                "file_data": Binary(file_content)
            }

            # Insert the document into MongoDB
            result = uploaded_file_collection.insert_one(file_document)

            if result.inserted_id is None:
                return JSONResponse(
                    status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value,
                    content=ProblemDetail(
                        type="chat/file/pdf",
                        title="Unexpected error",
                        details="Object id from mongo db is not found",
                        status=HTTPStatus.INTERNAL_SERVER_ERROR.value
                    ).model_dump()
                )

            produce_message(UPLOADED_FILE_TOPIC_NAME, "file-id", result.inserted_id)

            responses.append({
                "filename": file.filename,
                "status": "processing",
                "file_id": str(result.inserted_id)
            })

        except Exception as e:
            print(f"An error occurred while processing {file.filename}: {e}")
            return JSONResponse(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value,
                content=ProblemDetail(
                    type="chat/file/pdf",
                    title="Internal server error",
                    details=f"An error occurred: {e}",
                    status=HTTPStatus.INTERNAL_SERVER_ERROR.value
                ).model_dump()
            )

    return {
        "message": "File upload process completed",
        "details": responses
    }

@upload_file_router.delete("/file/pdf")
async def delete_file(file_id: str):
    """
    Delete a file record from MongoDB based on the provided file_id.
    """
    try:
        # Convert file_id to ObjectId
        object_id = ObjectId(file_id)
    except Exception:
        return JSONResponse(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY.value,
            content=ProblemDetail(
                type="chat/file/pdf",
                title="Invalid object id",
                details="Invalid file_id format. Must be a valid ObjectId.",
                status=HTTPStatus.UNPROCESSABLE_ENTITY.value
            ).model_dump()
        )

    # Query to find the record
    query = {"_id": object_id}

    file = uploaded_file_collection.find_one(query)

    produce_message(DELETED_FILE_TOPIC_NAME, "file-id", file["uploaded_file_id"])

    # Attempt to delete the record
    result = uploaded_file_collection.delete_one(query)

    if result.deleted_count == 1:
        return {"message": f"File with ID {file_id} successfully deleted."}
    else:
        return JSONResponse(
            status_code=HTTPStatus.NOT_FOUND.value,
            content=ProblemDetail(
                type="chat/file/pdf",
                title="Not found",
                details=f"File with ID {file_id} not found.",
                status=HTTPStatus.NOT_FOUND.value
            ).model_dump()
        )