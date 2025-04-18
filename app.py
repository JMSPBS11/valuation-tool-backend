import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service_account.json"

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import vision
import fitz  # PyMuPDF
import io

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://valuation-tool-frontend.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    contents = await file.read()

    # Save the uploaded PDF temporarily
    with open("temp_upload.pdf", "wb") as f:
        f.write(contents)

    # Crop Page 4 bottom-right (Nissan Line 63)
    doc = fitz.open("temp_upload.pdf")
    page = doc.load_page(3)  # Page 4
    rect = fitz.Rect(420, 500, 595, 792)  # Bottom-right crop
    pix = page.get_pixmap(clip=rect, dpi=300)
    img_bytes = pix.tobytes("png")

    # Run Google OCR
    client = vision.ImageAnnotatorClient()
    image = vision.Image(content=img_bytes)
    response = client.document_text_detection(image=image)

    extracted_text = response.full_text_annotation.text

    return {
        "status": "success",
        "data": {
            "H29": 123,
            "H30": 456,
            "H31": 789,
            "raw": extracted_text
        }
    }

