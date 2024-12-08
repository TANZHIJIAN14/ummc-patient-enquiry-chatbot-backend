import requests
from app.config import config

PINECONE_ASSISTANCE_NAME = "demo-assistance"

def get_assistant():
    url = "https://api.pinecone.io/assistant/assistants"
    headers = {
        "Api-Key": config("PINECONE_API_KEY")
    }
    return requests.get(url, headers=headers).json()

def create_assistance():
    # Get the assistants
    assistants = get_assistant()["assistants"]

    url = "https://api.pinecone.io/assistant/assistants"
    headers = {
        "Api-Key": config("PINECONE_API_KEY")
    }
    json = {
        "names": PINECONE_ASSISTANCE_NAME,
        "instructions": "You are UMMC patient enquiry chatbot. You are capable to answer patient enquiry with your knowledge base",
    }
    if len(assistants) == 0:
        resp = requests.post(url, headers=headers, json=json)
        if resp is None:
            raise Exception("Failed to create pinecone assistant")

def upload_file(file_name, file_data):
    # Upload a file.
    url = f"https://prod-1-data.ke.pinecone.io/assistant/files/{PINECONE_ASSISTANCE_NAME}"
    headers = {
        "Api-Key": config("PINECONE_API_KEY")
    }
    files = {"file": (file_name, file_data)}
    return requests.post(url, files=files, headers=headers)

def assistant_chat(messages):
    url = f"https://prod-1-data.ke.pinecone.io/assistant/chat/{PINECONE_ASSISTANCE_NAME}"
    headers = {
        "Api-Key": config("PINECONE_API_KEY")
    }
    json = {
        "messages": [
            {
                "role": "user",
                "content": messages
            }
        ]
    }
    return requests.post(url, headers=headers, json=json)