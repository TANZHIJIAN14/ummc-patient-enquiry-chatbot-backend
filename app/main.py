import threading

from fastapi import FastAPI

from app.bootstrap.kafkaInit import run_startup_script
from app.eventhandler.uploadedFileEventHandler import init_event_listener
from app.routes.chatRoutes import chat_router
from app.routes.uploadFileRoute import upload_file_router
from app.pinecone import create_assistance


async def lifespan(app):
    run_startup_script()
    create_assistance()
    listener_thread = threading.Thread(target=init_event_listener, daemon=True)
    listener_thread.start()
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(chat_router, prefix="/chat", tags=["Chat"])
app.include_router(upload_file_router, prefix="/upload", tags=["Upload file"])
