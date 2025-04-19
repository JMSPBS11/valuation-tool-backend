import os
import re
import io
from flask import Flask, request, jsonify
from google.cloud import vision

app = Flask(__name__)

def extract_nissan_h29_h31_google(pdf_path):
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

        text = response.full_text_annotation.text
        pattern = re.compile(r"TOTAL\s+NISSAN\s+RETAIL\s+&\s+LEASE", re.IGNORECASE)

        lines = text.split("\n")
        for line in lines:
            if pattern.search(line):
                # Look ahead to the next line as values may be broken across lines
                idx = lines.index(line)
                combined_line = line
                if idx + 1 < len(lines):
                    combined_line += " " + lines[idx + 1]

                numbers = re.findall(r"\d{1,3}(?:,\d{3})*", combined_line)
                if len(numbers) >= 3:
                    result["H29"] = int(numbers[0].replace(",", ""))
                    result["H30"] = int(numbers[1].replace(",", ""))
                    result["H31"] = int(numbers[2].replace(",", ""))
                    break

        return result

    except Exception as e:
        print(f"Error in extraction: {e}")
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

    data = extract_nissan_h29_h31_google(file_path)
    return jsonify(data)

if __name__ == '__main__':
    app.run()