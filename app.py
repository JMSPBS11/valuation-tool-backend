from flask import Flask, request, jsonify
import os
import io
from google.cloud import vision
import fitz  # PyMuPDF

app = Flask(__name__)

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

    # Debug OCR output
    debug_ocr_output(file_path)

    data = extract_nissan_debug_google(file_path)
    return jsonify(data)

def extract_nissan_debug_google(pdf_path):
    result = {"H29": None, "H30": None, "H31": None}

    try:
        client = vision.ImageAnnotatorClient()

        with io.open(pdf_path, 'rb') as f:
            content = f.read()

        image = vision.Image(content=content)
        response = client.document_text_detection(image=image)

        if response.error.message:
            print("OCR error:", response.error.message)
            return result

        full_text = response.full_text_annotation.text

        # Use basic search logic
        if "TOTAL NISSAN RETAIL & LEASE VEH" in full_text:
            lines = full_text.split("\n")
            for line in lines:
                if "TOTAL NISSAN RETAIL & LEASE VEH" in line:
                    numbers = [word.replace(",", "") for word in line.split() if word.replace(",", "").isdigit()]
                    if len(numbers) >= 3:
                        result["H29"] = int(numbers[0])
                        result["H30"] = int(numbers[1])
                        result["H31"] = int(numbers[2])
                    break

        return result

    except Exception as e:
        print(f"Google OCR extraction error: {e}")
        return result

def debug_ocr_output(pdf_path):
    client = vision.ImageAnnotatorClient()
    with io.open(pdf_path, 'rb') as f:
        content = f.read()

    image = vision.Image(content=content)
    response = client.document_text_detection(image=image)

    if response.error.message:
        print("OCR error:", response.error.message)
        return

    print("-------- GOOGLE OCR RAW TEXT (Page 4) --------")
    print(response.full_text_annotation.text)
    print("------------------------------------------------")

if __name__ == '__main__':
    app.run(debug=True)
