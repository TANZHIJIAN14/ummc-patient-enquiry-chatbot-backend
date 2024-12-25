import requests
from fastapi import APIRouter
from app.config import config

convert_url_router = APIRouter()

PDF_STORAGE_DIR = "pdf"
BASE_URL = "https://api.pdf.co/v1"

@convert_url_router.post("/pdf-from-url")
async def convert_url_to_pdf(url: str, file_name: str):
    # Generate a safe filename based on the URL
    pdf_convertor_url = "{}/pdf/convert/from/url".format(BASE_URL)
    parameters = {
        "name": file_name,
        "url": url
    }
    response = requests.post(
        pdf_convertor_url,
        data=parameters,
        headers={"x-api-key": config("PDF_CONVERTOR_API_KEY")})

    return response.json()