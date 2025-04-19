import os
from flask import Flask, request, jsonify
from google.cloud import vision
import fitz  # PyMuPDF
import io
import re

app = Flask(__name__)

# Initialize Google Vision client using environment variable
vision_client = vision.ImageAnnotatorClient()

def extract_nissan_new_vehicle_data_google(pdf_path):
    result = {"H29": None, "H30": None, "H31": None, "raw": []}
    try:
        doc = fitz.open(pdf_path)
        page = doc.load_page(3)  # Page 4 (index 3)

        pix = page.get_pixmap(dpi=300)
        img_bytes = pix.tobytes("png")
        image = vision.Image(content=img_bytes)

        response = vision_client.document_text_detection(image=image)
        if response.error.message:
            raise Exception(response.error.message)

        text = response.full_text_annotation.text
        result["raw"] = re.findall(r"\d{1,3}(?:,\d{3})+", text)

        pattern = re.compile(r"TOTAL\s+NISSAN\s+RETAIL\s+&\s+LEASE\s+VEHS.*", re.IGNORECASE)
        for block in response.full_text_annotation.pages[0].blocks:
            for para in block.paragraphs:
                line_text = " ".join([
                    word.symbols[0].text for word in para.words if word.symbols
                ])
                if pattern.search(line_text):
                    numbers = re.findall(r"\d{1,3}(?:,\d{3})+", line_text)
                    if len(numbers) >= 3:
                        result["H29"] = int(numbers[0].replace(",", ""))
                        result["H30"] = int(numbers[1].replace(",", ""))
                        result["H31"] = int(numbers[2].replace(",", ""))
                    return result
        return result
    except Exception as e:
        print(f"Extraction error: {e}")
        return result

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    upload_folder = 'uploads'
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, file.filename)
    file.save(file_path)

    data = extract_nissan_new_vehicle_data_google(file_path)
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)