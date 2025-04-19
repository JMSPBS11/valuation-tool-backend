from flask import Flask, request, jsonify
import os
import fitz  # PyMuPDF
import re
from google.cloud import vision
import io

app = Flask(__name__)

def extract_nissan_new_vehicle_data_google(pdf_path):
    try:
        client = vision.ImageAnnotatorClient()

        with io.open(pdf_path, 'rb') as f:
            content = f.read()

        image = vision.Image(content=content)
        response = client.document_text_detection(image=image)

        if response.error.message:
            print("Google OCR error:", response.error.message)
            return {"H29": None, "H30": None, "H31": None}

        full_text = response.full_text_annotation.text

        # Print full text for debug purposes
        print("-------- OCR DEBUG START (Page 4) --------")
        print(full_text)
        print("-------- OCR DEBUG END --------")

        result = {"H29": None, "H30": None, "H31": None}

        # Locate the correct line and extract numbers
        pattern = r"TOTAL\s+NISSAN\s+RETAIL\s+&\s+LEASE\s+VEH.*?([\d,]+)\s+([\d,]+)\s+([\d,]+)"
        match = re.search(pattern, full_text, re.IGNORECASE)

        if match:
            result["H29"] = int(match.group(1).replace(",", ""))
            result["H30"] = int(match.group(2).replace(",", ""))
            result["H31"] = int(match.group(3).replace(",", ""))

        return result

    except Exception as e:
        print(f"OCR processing failed: {e}")
        return {"H29": None, "H30": None, "H31": None}

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

    extracted_data = extract_nissan_new_vehicle_data_google(file_path)
    return jsonify(extracted_data)

if __name__ == '__main__':
    app.run(debug=True)
