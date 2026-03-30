import easyocr
import ssl
from flask import Flask, request, render_template, jsonify
import os

# Initialize SSL context to bypass certificate verification
ssl._create_default_https_context = ssl._create_unverified_context

# Initialize EasyOCR reader with Hindi and English
reader = easyocr.Reader(['hi', 'en'])

# Initialize Flask app
app = Flask(__name__)

# Create a folder to store uploaded images (if it doesn't exist)
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    # Render the index.html template
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    file = request.files['image']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Save the uploaded file to the 'uploads' folder
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    # Perform OCR using EasyOCR
    result = reader.readtext(file_path)
    
    # Create a list of dictionaries for each detected text and its confidence score
    extracted_text_data = []
    for idx, (bbox, text, score) in enumerate(result):
        extracted_text_data.append({
            "no": idx,
            "text": text,
            "confidence_score": round(score, 4)
        })

    # Return the result as JSON so that the frontend can display it in the table
    return jsonify(extracted_text_data)

if __name__ == '__main__':
    app.run(debug=True)