"""
File Processing Flow

Background task flow for processing uploaded files:
- PDF OCR using pytesseract
- Document text extraction (PDF, DOCX)
- Image processing
"""

import os
import io
from pathlib import Path
from typing import Optional, Dict, Any, List
from enum import Enum

from prefect import flow, task, get_run_logger
from prefect.artifacts import create_markdown_artifact


class FileType(Enum):
    PDF = "pdf"
    DOCX = "docx"
    IMAGE = "image"
    TEXT = "text"
    UNKNOWN = "unknown"


@task(name="Detect File Type", retries=1)
def detect_file_type(file_path: str) -> FileType:
    """Detect the type of file based on extension"""
    logger = get_run_logger()
    
    ext = Path(file_path).suffix.lower()
    logger.info(f"Detecting file type for: {file_path} (extension: {ext})")
    
    if ext == ".pdf":
        return FileType.PDF
    elif ext in [".docx", ".doc"]:
        return FileType.DOCX
    elif ext in [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".gif"]:
        return FileType.IMAGE
    elif ext in [".txt", ".md", ".csv"]:
        return FileType.TEXT
    else:
        return FileType.UNKNOWN


@task(name="Extract PDF Text", retries=2, retry_delay_seconds=3)
def extract_pdf_text(file_path: str) -> str:
    """Extract text from PDF file"""
    logger = get_run_logger()
    logger.info(f"Extracting text from PDF: {file_path}")
    
    try:
        import PyPDF2
        
        text_content = []
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            num_pages = len(reader.pages)
            logger.info(f"PDF has {num_pages} pages")
            
            for page_num in range(num_pages):
                page = reader.pages[page_num]
                text = page.extract_text()
                if text:
                    text_content.append(text)
        
        full_text = "\n\n".join(text_content)
        logger.info(f"Extracted {len(full_text)} characters from PDF")
        
        if not full_text.strip():
            logger.warning("PDF appears to have no extractable text")
            return ""
        
        return full_text
        
    except ImportError:
        logger.error("PyPDF2 not installed")
        raise ImportError("PyPDF2 is required for PDF processing")
    except Exception as e:
        logger.error(f"Failed to extract PDF text: {str(e)}")
        raise


@task(name="Extract DOCX Text", retries=2, retry_delay_seconds=3)
def extract_docx_text(file_path: str) -> str:
    """Extract text from DOCX file"""
    logger = get_run_logger()
    logger.info(f"Extracting text from DOCX: {file_path}")
    
    try:
        import docx
        
        doc = docx.Document(file_path)
        paragraphs = [para.text for para in doc.paragraphs]
        
        full_text = "\n\n".join(paragraphs)
        logger.info(f"Extracted {len(full_text)} characters from DOCX")
        
        return full_text
        
    except ImportError:
        logger.error("python-docx not installed")
        raise ImportError("python-docx is required for DOCX processing")
    except Exception as e:
        logger.error(f"Failed to extract DOCX text: {str(e)}")
        raise


@task(name="Perform OCR on Image", retries=2, retry_delay_seconds=5)
def perform_ocr(
    file_path: str, 
    lang: str = "eng",
    enhance: bool = True
) -> Dict[str, Any]:
    """
    Perform OCR on image using pytesseract with optional preprocessing.
    
    Args:
        file_path: Path to the image file
        lang: Language code for OCR (e.g., 'eng', 'hin', 'spa+fra')
        enhance: Whether to apply image preprocessing for better results
    
    Returns:
        Dictionary with extracted text and confidence score
    """
    logger = get_run_logger()
    logger.info(f"Performing OCR on: {file_path} with lang={lang}, enhance={enhance}")
    
    result = {
        "text": "",
        "confidence": 0.0,
        "success": False,
        "error": None
    }
    
    try:
        from PIL import Image
        import pytesseract
        import numpy as np
        
        # Try to import OpenCV for preprocessing (optional)
        cv2 = None
        try:
            import cv2
        except ImportError:
            logger.warning("OpenCV not available, using PIL-only preprocessing")
        
        # Preprocess image if enabled
        if enhance:
            image = preprocess_image_for_ocr(file_path, cv2=cv2)
        else:
            image = Image.open(file_path)
        
        # Get detailed OCR data with confidence scores
        ocr_data = pytesseract.image_to_data(image, lang=lang, output_type=pytesseract.Output.DICT)
        
        # Extract text
        result["text"] = pytesseract.image_to_string(image, lang=lang)
        
        # Calculate average confidence
        confidences = [c for c in ocr_data['conf'] if c != -1]
        if confidences:
            result["confidence"] = sum(confidences) / len(confidences)
        
        result["success"] = True
        logger.info(f"OCR extracted {len(result['text'])} characters with {result['confidence']:.1f}% confidence")
        
        if not result["text"].strip():
            logger.warning("OCR produced no text - image may be empty or not readable")
        
        return result
        
    except ImportError as e:
        logger.error(f"Missing required library: {str(e)}")
        result["error"] = f"Missing required library: {str(e)}"
        return result
    except Exception as e:
        logger.error(f"OCR failed: {str(e)}")
        result["error"] = str(e)
        return result


@task(name="Preprocess Image for OCR", retries=1)
def preprocess_image_for_ocr(file_path: str, cv2=None) -> Image.Image:
    """
    Preprocess image using OpenCV for better OCR results.
    
    Args:
        file_path: Path to the image file
        cv2: OpenCV module (optional)
    
    Returns:
        Preprocessed PIL Image
    """
    logger = get_run_logger()
    logger.info(f"Preprocessing image: {file_path}")
    
    from PIL import Image, ImageEnhance, ImageFilter
    
    try:
        # Try OpenCV-based preprocessing first
        if cv2 is not None:
            # Read image with OpenCV
            img = cv2.imread(file_path)
            
            if img is None:
                # Fallback to PIL if OpenCV can't read
                return Image.open(file_path)
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Apply median blur to remove noise
            gray = cv2.medianBlur(gray, 3)
            
            # Apply adaptive thresholding for better OCR
            thresh = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            # Convert back to PIL Image
            img = Image.fromarray(thresh)
        else:
            # Fallback to PIL-only preprocessing
            img = Image.open(file_path)
            
            # Convert to grayscale
            if img.mode != 'L':
                img = img.convert('L')
            
            # Increase contrast
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.5)
            
            # Sharpen
            img = img.filter(ImageFilter.SHARPEN)
        
        logger.info("Image preprocessing completed")
        return img
        
    except Exception as e:
        logger.warning(f"Preprocessing failed, using original: {str(e)}")
        return Image.open(file_path)


@task(name="Perform Multilingual OCR", retries=2, retry_delay_seconds=5)
def perform_multilingual_ocr(
    file_path: str, 
    languages: str = "hin",
    enhance: bool = True
) -> Dict[str, Any]:
    """
    Perform OCR with multilingual support and preprocessing.
    
    Args:
        file_path: Path to the image file
        languages: Language code(s) - e.g., 'eng', 'hin+eng', 'spa fra'
        enhance: Whether to apply image preprocessing
    
    Returns:
        Dictionary with extracted text, confidence, and metadata
    """
    logger = get_run_logger()
    logger.info(f"Performing multilingual OCR: {file_path}")
    
    # Supported languages mapping
    supported_languages = {
        "eng": "English",
        "hin": "Hindi",
        "spa": "Spanish",
        "fra": "French",
        "deu": "German",
        "chi_sim": "Chinese (Simplified)",
        "chi_tra": "Chinese (Traditional)",
        "jpn": "Japanese",
        "kor": "Korean",
        "ara": "Arabic",
        "por": "Portuguese",
        "ita": "Italian",
        "rus": "Russian",
        "nld": "Dutch",
        "pol": "Polish",
        "tur": "Turkish",
        "vie": "Vietnamese",
        "tha": "Thai",
        "ind": "Indonesian",
        "msa": "Malay"
    }
    
    result = {
        "text": "",
        "confidence": 0.0,
        "languages_used": languages,
        "languages_detected": [],
        "success": False,
        "error": None
    }
    
    try:
        from PIL import Image
        import pytesseract
        import numpy as np
        
        # Try to import OpenCV for preprocessing
        cv2 = None
        try:
            import cv2
        except ImportError:
            pass
        
        # Preprocess image
        if enhance:
            image = preprocess_image_for_ocr(file_path, cv2=cv2)
        else:
            image = Image.open(file_path)
        
        # Get detailed OCR data with confidence
        ocr_data = pytesseract.image_to_data(image, lang=languages, output_type=pytesseract.Output.DICT)
        
        # Extract all text
        result["text"] = pytesseract.image_to_string(image, lang=languages)
        
        # Calculate confidence
        confidences = [c for c in ocr_data['conf'] if c != -1]
        if confidences:
            result["confidence"] = sum(confidences) / len(confidences)
        
        # Try to detect which languages were used based on confidence
        for lang_code, lang_name in supported_languages.items():
            if lang_code in languages or languages == "eng+hin":
                result["languages_detected"].append(lang_name)
        
        result["success"] = True
        logger.info(f"Multilingual OCR completed: {len(result['text'])} chars, {result['confidence']:.1f}% confidence")
        
    except Exception as e:
        logger.error(f"Multilingual OCR failed: {str(e)}")
        result["error"] = str(e)
    
    return result


@task(name="Extract Text from Image", retries=1)
def extract_image_metadata(file_path: str) -> Dict[str, Any]:
    """Extract metadata from image file"""
    logger = get_run_logger()
    logger.info(f"Extracting metadata from: {file_path}")
    
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS
        
        image = Image.open(file_path)
        
        metadata = {
            "format": image.format,
            "mode": image.mode,
            "size": image.size,
            "width": image.width,
            "height": image.height,
        }
        
        # Try to extract EXIF data
        try:
            exif_data = image._getexif()
            if exif_data:
                exif = {}
                for tag, value in exif_data.items():
                    tag_name = TAGS.get(tag, tag)
                    exif[tag_name] = str(value)
                metadata["exif"] = exif
        except Exception:
            pass  # No EXIF data available
        
        logger.info(f"Extracted metadata: {metadata}")
        return metadata
        
    except Exception as e:
        logger.error(f"Failed to extract metadata: {str(e)}")
        return {}


@task(name="Save Extracted Text")
def save_extracted_text(file_path: str, text: str, output_dir: str = "extracted_texts") -> str:
    """Save extracted text to file"""
    logger = get_run_logger()
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate output filename
    base_name = Path(file_path).stem
    output_path = os.path.join(output_dir, f"{base_name}_extracted.txt")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(text)
    
    logger.info(f"Saved extracted text to: {output_path}")
    return output_path


@flow(name="Process Uploaded File", log_prints=True)
def process_uploaded_file(
    file_path: str,
    perform_ocr: bool = False,
    ocr_lang: str = "eng",
    enhance_ocr: bool = True,
    save_text: bool = True,
    output_dir: str = "extracted_texts"
) -> Dict[str, Any]:
    """
    Main flow for processing uploaded files.
    
    Args:
        file_path: Path to the uploaded file
        perform_ocr: Whether to perform OCR on images (default: False)
        ocr_lang: Language for OCR (default: "eng")
        enhance_ocr: Whether to apply image preprocessing for better OCR (default: True)
        save_text: Whether to save extracted text to file
        output_dir: Directory to save extracted text
    
    Returns:
        Dictionary containing processing results
    """
    logger = get_run_logger()
    logger.info(f"Starting file processing for: {file_path}")
    
    results = {
        "file_path": file_path,
        "file_name": os.path.basename(file_path),
        "file_type": None,
        "text": None,
        "metadata": None,
        "saved_path": None,
        "success": False
    }
    
    try:
        # Step 1: Detect file type
        file_type = detect_file_type(file_path)
        results["file_type"] = file_type.value
        logger.info(f"Detected file type: {file_type.value}")
        
        # Step 2: Extract text based on file type
        text = ""
        
        if file_type == FileType.PDF:
            text = extract_pdf_text(file_path)
            
        elif file_type == FileType.DOCX:
            text = extract_docx_text(file_path)
            
        elif file_type == FileType.IMAGE:
            # Extract metadata
            metadata = extract_image_metadata(file_path)
            results["metadata"] = metadata
            
            # Perform OCR if requested
            if perform_ocr:
                text = perform_ocr(file_path, ocr_lang)
            else:
                logger.info("OCR not requested for image file")
                
        elif file_type == FileType.TEXT:
            # Read plain text file
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
                
        else:
            logger.warning(f"Unknown file type: {file_type}")
            results["error"] = f"Unsupported file type: {file_type}"
            return results
        
        results["text"] = text
        logger.info(f"Extracted {len(text)} characters")
        
        # Step 3: Save extracted text if requested
        if save_text and text:
            saved_path = save_extracted_text(file_path, text, output_dir)
            results["saved_path"] = saved_path
        
        results["success"] = True
        logger.info("File processing completed successfully")
        
        # Create artifact
        create_markdown_artifact(
            f"## File Processing Complete\n\n"
            f"- **File**: {results['file_name']}\n"
            f"- **Type**: {results['file_type']}\n"
            f"- **Characters extracted**: {len(text)}\n"
            f"- **Saved to**: {results.get('saved_path', 'Not saved')}"
        )
        
    except Exception as e:
        logger.error(f"File processing failed: {str(e)}")
        results["error"] = str(e)
        results["success"] = False
    
    return results


@flow(name="Process Multiple Files")
def process_multiple_files(
    file_paths: List[str],
    perform_ocr: bool = False,
    ocr_lang: str = "eng"
) -> List[Dict[str, Any]]:
    """Process multiple files"""
    results = []
    for file_path in file_paths:
        result = process_uploaded_file(
            file_path, 
            perform_ocr=perform_ocr,
            ocr_lang=ocr_lang
        )
        results.append(result)
    return results

