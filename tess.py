# backend/ocr_script.py

import cv2        # OpenCV for preprocessing
import pytesseract
from PIL import Image  # Pillow, optional if using Image.open

# If pytesseract cannot find tesseract, set the path manually:
# pytesseract.pytesseract.tesseract_cmd = "/usr/local/bin/tesseract"

# 1️⃣ Load image with OpenCV
img = cv2.imread("/Users/neelakshabhardwaj/Desktop/hin.png")

# 2️⃣ Preprocess the image for better OCR
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)          # Convert to grayscale
gray = cv2.medianBlur(gray, 1)                        # Remove small noise
_, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)  # Binarize

# Optional: save preprocessed image to check
cv2.imwrite("/Users/neelakshabhardwaj/Desktop/hin_preprocessed.png", thresh)

# 3️⃣ Run OCR with pytesseract
# For Hindi text; add '+eng' if image has English as well
text = pytesseract.image_to_string(thresh, lang="hin")

# 4️⃣ Print result
print("=== OCR Output ===")
print(text)