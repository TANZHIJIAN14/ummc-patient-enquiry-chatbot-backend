from datetime import datetime
from http import HTTPStatus

import pymongo
from bson import ObjectId
from fastapi import APIRouter, Header, HTTPException
from starlette.responses import JSONResponse

from app.database import feedback_collection, users_collection
from app.eventhandler.feedbackAnalysisEventHandler import FEEDBACK_ANALYSIS_TOPIC_NAME
from app.eventhandler.kafkaConfig import produce_message
from app.model import ProblemDetail
from app.model.feedbackModels import CreateFeedbackReq, CreateFeedbackResp
from util import serialize_mongo_document

feedback_router = APIRouter()
@feedback_router.get("/")
async def get_feedback():
    try:
        feedbacks = feedback_collection.find().sort("created_at", pymongo.DESCENDING)
        return [serialize_mongo_document(feedback) for feedback in feedbacks]
    except Exception as e:
        return JSONResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value,
            content=ProblemDetail(
                type="GET /feedback",
                title="Internal server error",
                details=f"An error occurred: {e}",
                status=HTTPStatus.INTERNAL_SERVER_ERROR.value
            ).model_dump()
        )

@feedback_router.post("/")
async def send_feedback(request: CreateFeedbackReq, user_id = Header()):
    if not user_id:
        return JSONResponse(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY.value,
            content=ProblemDetail(
                type="feedback/invalid-user-id",
                title="Invalid user id",
                details=f"Invalid user id: {user_id}",
                status=HTTPStatus.UNPROCESSABLE_ENTITY.value
            ).model_dump()
        )

    if not request or not request.message:
        return JSONResponse(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY.value,
            content=ProblemDetail(
                type="feedback/invalid-argument",
                title="Invalid argument",
                details=f"Invalid argument",
                status=HTTPStatus.UNPROCESSABLE_ENTITY.value
            ).model_dump()
        )

    # Check user is existed
    query = {"_id": ObjectId(user_id)}
    user = users_collection.find_one(query)

    if not user:
        return JSONResponse(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY.value,
            content=ProblemDetail(
                type="feedback/user-not-found",
                title="User not found",
                details=f"User with ID: {user_id} not found.",
                status=HTTPStatus.UNPROCESSABLE_ENTITY.value
            ).model_dump()
        )
    try:
        document = {
            "user_id": user_id,
            "message": request.message,
            'label': "Analysing",
            "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        }

        result = feedback_collection.insert_one(document)

        if not result.inserted_id:
            return JSONResponse(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value,
                content=ProblemDetail(
                    type="feedback/unexpected-error",
                    title="Unexpected error",
                    details=f"Failed to upload feedback of user ID: {user_id}",
                    status=HTTPStatus.INTERNAL_SERVER_ERROR.value
                ).model_dump()
            )

        # Send event to Feedback topic to sentiment analysis
        produce_message(FEEDBACK_ANALYSIS_TOPIC_NAME, "id", result.inserted_id)

        return CreateFeedbackResp(
            user_id=document["user_id"],
            message=document["message"],
            created_at=document["created_at"]
        )
    except Exception as e:
        return JSONResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value,
            content=ProblemDetail(
                type="feedback/unexpected-error",
                title="Unexpected error",
                details=str(e),
                status=HTTPStatus.INTERNAL_SERVER_ERROR.value
            ).model_dump()
        )