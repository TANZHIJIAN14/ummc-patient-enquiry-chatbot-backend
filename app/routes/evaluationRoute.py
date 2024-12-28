from http import HTTPStatus

from fastapi import APIRouter
from starlette.responses import JSONResponse

from app.database import evaluation_collection
from app.model import ProblemDetail

evaluation_router = APIRouter()

@evaluation_router.get("/")
async def get_evaluation_metrics(user_id: str):
    if not user_id:
        return JSONResponse(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY.value,
            content=ProblemDetail(
                type="unprocessable entity",
                title="Invalid user id",
                details=f"Invalid user ID: {user_id}",
                status=HTTPStatus.UNPROCESSABLE_ENTITY.value
            ).model_dump()
        )

    try:
        evaluation_metrics = evaluation_collection.find({"user_id": user_id})
        return evaluation_metrics
    except Exception as e:
        return JSONResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value,
            content=ProblemDetail(
                type="feedback/unexpected-error",
                title="Unexpected error",
                details=f"Failed to get evaluation metrics of user ID: {user_id}",
                status=HTTPStatus.INTERNAL_SERVER_ERROR.value
            ).model_dump()
        )