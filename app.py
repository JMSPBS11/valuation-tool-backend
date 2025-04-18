from flask import Flask, request, jsonify
import os
import fitz  # PyMuPDF
import re

app = Flask(__name__)

def extract_new_vehicle_data_nissan(pdf_path):
    result = {"H29": None, "H30": None, "H31": None}

    try:
        doc = fitz.open(pdf_path)
        page = doc.load_page(3)  # Page 4

        label_keywords = ["TOTAL", "NISSAN", "RETAIL", "LEASE"]
        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            for line in block.get("lines", []):
                line_text = " ".join(span["text"] for span in line["spans"])
                if all(word in line_text.upper() for word in label_keywords):
                    numeric_spans = [span["text"] for span in line["spans"] if re.fullmatch(r"[\d,]+", span["text"])]
                    if len(numeric_spans) >= 3:
                        try:
                            result["H29"] = int(numeric_spans[0].replace(",", ""))
                            result["H30"] = int(numeric_spans[1].replace(",", ""))
                            result["H31"] = int(numeric_spans[2].replace(",", ""))
                            return result
                        except ValueError:
                            return result
        return result
    except Exception as e:
        print(f"Error extracting new vehicle data for Nissan: {e}")
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

    # Run the Nissan extraction
    extracted_data = extract_new_vehicle_data_nissan(file_path)

    return jsonify(extracted_data)

if __name__ == '__main__':
    app.run(debug=True)