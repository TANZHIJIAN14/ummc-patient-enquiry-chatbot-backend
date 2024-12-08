from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.database import uploaded_file_collection, db
from bson.binary import Binary
import gridfs
from app.eventhandler.kafkaConfig import produce_message
from app.eventhandler.uploadedFileEventHandler import TOPIC_NAME

fs = gridfs.GridFS(db)

upload_file_router = APIRouter()
@upload_file_router.post("/small-file/pdf")
async def upload_small_file(file: UploadFile = File(...)):
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

        produce_message(TOPIC_NAME, "file-id", result.inserted_id)

        return {
            "message": "File uploaded successfully",
            "file_id": str(result.inserted_id)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


@upload_file_router.post("/large-file/pdf")
async def upload_large_file(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    try:
        # Read file content
        file_content = await file.read()

        # Upload to GridFS
        file_id = fs.put(file_content, filename=file.filename, contentType=file.content_type, metadata={
            "uploaded_at": datetime.now()
        })

        return {"message": "File uploaded successfully", "file_id": str(file_id)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")