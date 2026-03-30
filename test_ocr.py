# import easyocr
# import ssl
# ssl._create_default_https_context = ssl._create_unverified_context
# reader = easyocr.Reader(['en','mr']) # this needs to run only once to load the model into memory
# result = reader.readtext('/Users/neelakshabhardwaj/Desktop/marathi.png')
# print(result)







# from docling.document_converter import DocumentConverter, PdfFormatOption
# from docling.datamodel.pipeline_options import PdfPipelineOptions, TesseractCliOcrOptions
# from docling.datamodel.base_models import InputFormat

# source = "/Users/neelakshabhardwaj/Desktop/hindi.png"

# # Configure Tesseract with a custom binary or data path
# ocr_options = TesseractCliOcrOptions(
#     lang=["hin"],  # Hindi
#     path="/usr/local/bin/tesseract"  # or your custom Tesseract binary
# )

# pipeline_options = PdfPipelineOptions(
#     do_ocr=True,
#     do_table_structure=False,
#     ocr_options=ocr_options
# )

# converter = DocumentConverter(
#     format_options={
#         InputFormat.PDF: PdfFormatOption(
#             pipeline_options=pipeline_options
#         )
#     }
# )

# result = converter.convert(source)

# print(result.document.export_to_markdown())










from paddleocr import PaddleOCR

# Initialize OCR for Hindi
ocr = PaddleOCR(lang='hi')  # 'hi' = Hindi

# Run OCR prediction
result = ocr.predict('/Users/neelakshabhardwaj/Desktop/hindi.png')

# result is a list of dicts: [{'box': [...], 'text': '...', 'score': ...}, ...]
for item in result:
    print(item['text'])