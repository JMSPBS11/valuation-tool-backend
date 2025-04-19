import os
import re
import io
from flask import Flask, request, jsonify
from google.cloud import vision

app = Flask(__name__)

# Google Vision OCR debug logging function
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

# Actual extraction logic for Nissan H29–H31
def extract_nissan_debug_google(pdf_path):
    result = {"H29": None, "H30": None, "H31": None}
    client = vision.ImageAnnotatorClient()

    with io.open(pdf_path, 'rb') as f:
        content = f.read()

    image = vision.Image(content=content)
    response = client.document_text_detection(image=image)

    if response.error.message:
        print("OCR error:", response.error.message)
        return result

    full_text = response.full_text_annotation.text

    # Look for the correct label line
    pattern = re.compile(r'TOTAL\s+NISSAN\s+RETAIL\s+&\s+LEASE\s+VEH', re.IGNORECASE)
    match = pattern.search(full_text)

    if match:
        after = full_text[match.end():]
        numbers = re.findall(r"\d{1,3}(?:,\d{3})*", after)

        if len(numbers) >= 3:
            try:
                result["H29"] = int(numbers[0].replace(",", ""))
                result["H30"] = int(numbers[1].replace(",", ""))
                result["H31"] = int(numbers[2].replace(",", ""))
            except ValueError:
                pass

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

    # Run debug output for logging
    debug_ocr_output(file_path)

    # Extract values
    data = extract_nissan_debug_google(file_path)
    return jsonify(data)

if __name__ == '__main__':
    app.run()
