import threading
from fastapi import FastAPI
from app.bootstrap.kafkaInit import run_startup_script
from app.eventhandler.deleteFileEventHandler import init_delete_file_event_listener
from app.eventhandler.evaluation.evaluationEventHandler import init_evaluation_event_listener
from app.eventhandler.feedbackAnalysisEventHandler import init_feedback_analysis_event_listener
from app.eventhandler.uploadedFileEventHandler import init_upload_file_event_listener
from app.routes.chatRoutes import chat_router
from app.routes.convertUrlRoute import convert_url_router
from app.routes.evaluationRoute import evaluation_router
from app.routes.feedbackRoutes import feedback_router
from app.routes.uploadFileRoute import upload_file_router
from app.pinecone import create_assistance

async def lifespan(app):
    run_startup_script()
    create_assistance()
    listener_thread_1 = threading.Thread(target=init_upload_file_event_listener, daemon=True)
    listener_thread_1.start()

    listener_thread_2 = threading.Thread(target=init_delete_file_event_listener, daemon=True)
    listener_thread_2.start()

    listener_thread_3 = threading.Thread(target=init_feedback_analysis_event_listener, daemon=True)
    listener_thread_3.start()

    listener_thread_4 = threading.Thread(target=init_evaluation_event_listener, daemon=True)
    listener_thread_4.start()
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(chat_router, prefix="/chat", tags=["Chat"])
app.include_router(upload_file_router, prefix="/upload", tags=["Upload file"])
app.include_router(feedback_router, prefix="/feedback", tags=["Feedback"])
app.include_router(convert_url_router, prefix="/convert", tags=["Convert URL to PDF"])
app.include_router(evaluation_router, prefix="/evaluation", tags=["Chatbot conversation evaluation"])