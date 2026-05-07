import fitz # PyMuPDF
import os
import logging
from pathlib import Path

class PDFExtractor:
    def __init__(self, config: dict):
        self.temp_dir = Path(config.get('paths', {}).get('temp_dir', 'temp/'))
        self.extracted_pages_dir = self.temp_dir / "extracted_pages"
        self.extracted_pages_dir.mkdir(parents=True, exist_ok=True)

    def extract_pdf(self, pdf_path: str) -> list:
        """
        Extracts all pages from a PDF as images.
        Returns a list of paths to the extracted image files.
        """
        logging.info(f"Extracting pages from PDF: {pdf_path}")
        image_paths = []
        try:
            doc = fitz.open(pdf_path)
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                # Render page to an image (pixmap) with 300 DPI for high quality
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                
                # Format: 001.png, 002.png
                output_filename = f"{page_num + 1:03d}.png"
                output_path = self.extracted_pages_dir / output_filename
                
                pix.save(str(output_path))
                image_paths.append(str(output_path))
                
            logging.info(f"Successfully extracted {len(image_paths)} pages.")
        except Exception as e:
            logging.error(f"Failed to extract PDF {pdf_path}: {e}")
            
        return image_paths
