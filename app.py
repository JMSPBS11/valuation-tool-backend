from flask import Flask, request, jsonify
import os
import io
import fitz  # PyMuPDF
from google.cloud import vision
import re

app = Flask(__name__)
vision_client = vision.ImageAnnotatorClient()

def extract_nissan_debug_google(pdf_path):
    result = {
        "H29": None,
        "H30": None,
        "H31": None,
        "matched_line": None,
        "all_lines": []
    }

    try:
        doc = fitz.open(pdf_path)
        page = doc.load_page(3)  # Page 4

        pix = page.get_pixmap(dpi=300)
        img_bytes = pix.tobytes("png")
        image = vision.Image(content=img_bytes)

        response = vision_client.document_text_detection(image=image)
        if response.error.message:
            raise Exception(response.error.message)

        # Collect all lines and look for matches
        pattern = re.compile(r"TOTAL\s+NISSAN\s+RETAIL\s+&\s+LEASE\s+VEH", re.IGNORECASE)

        lines = []
        for page in response.full_text_annotation.pages:
            for block in page.blocks:
                for para in block.paragraphs:
                    line_text = " ".join([symbol.text for word in para.words for symbol in word.symbols])
                    lines.append(line_text)
                    if pattern.search(line_text):
                        result["matched_line"] = line_text
                        numbers = re.findall(r"\d{1,3}(?:,\d{3})+", line_text)
                        if len(numbers) >= 3:
                            result["H29"] = int(numbers[0].replace(",", ""))
                            result["H30"] = int(numbers[1].replace(",", ""))
                            result["H31"] = int(numbers[2].replace(",", ""))

        result["all_lines"] = lines
        return result

    except Exception as e:
        print(f"Debug OCR extraction error: {e}")
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

    data = extract_nissan_debug_google(file_path)
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)