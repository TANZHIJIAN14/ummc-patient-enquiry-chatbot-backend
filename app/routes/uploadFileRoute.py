from datetime import datetime

from bson import ObjectId
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.database import uploaded_file_collection, db
from bson.binary import Binary
import gridfs

from app.eventhandler.deleteFileEventHandler import DELETED_FILE_TOPIC_NAME
from app.eventhandler.kafkaConfig import produce_message
from app.eventhandler.uploadedFileEventHandler import UPLOADED_FILE_TOPIC_NAME

fs = gridfs.GridFS(db)

upload_file_router = APIRouter()
@upload_file_router.post("/file/pdf")
async def upload_file(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    try:
        # Read file content
        file_content = await file.read()

        # Create a document for the file
        file_document = {
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(file_content),
            "uploaded_at": datetime.now(),
            "file_data": Binary(file_content)
        }

        # Insert the document into MongoDB
        result = uploaded_file_collection.insert_one(file_document)

        if result.inserted_id is None:
            print("Insertion of file failed or the document was not inserted.")

        produce_message(UPLOADED_FILE_TOPIC_NAME, "file-id", result.inserted_id)

        return {
            "message": "File uploaded successfully",
            "file_id": str(result.inserted_id)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

@upload_file_router.delete("/file/pdf")
async def delete_file(file_id: str):
    """
    Delete a file record from MongoDB based on the provided file_id.
    """
    try:
        # Convert file_id to ObjectId
        object_id = ObjectId(file_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid file_id format. Must be a valid ObjectId.")

    # Query to find the record
    query = {"_id": object_id}

    file = uploaded_file_collection.find_one(query)

    produce_message(DELETED_FILE_TOPIC_NAME, "file-id", file["uploaded_file_id"])

    # Attempt to delete the record
    result = uploaded_file_collection.delete_one(query)

    if result.deleted_count == 1:
        return {"message": f"File with ID {file_id} successfully deleted."}
    else:
        raise HTTPException(status_code=404, detail=f"File with ID {file_id} not found.")