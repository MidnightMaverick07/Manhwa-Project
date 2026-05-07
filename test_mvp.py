import yaml
import logging
from pathlib import Path
from core.ocr_engine import OCREngine
from core.scene_segmenter import SceneSegmenter
from core.pdf_extractor import PDFExtractor
import os

def test_pipeline():
    logging.basicConfig(level=logging.INFO)
    
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
        
    input_dir = config['paths']['input_dir']
    
    # Phase 0: PDF Extraction
    pdf_files = [str(Path(input_dir) / f) for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
    extracted_images = []
    if pdf_files:
        logging.info(f"[0/7] Running PDF Extraction on {len(pdf_files)} files...")
        pdf_extractor = PDFExtractor(config)
        for pdf in pdf_files:
            extracted_images.extend(pdf_extractor.extract_pdf(pdf))
            
    image_files = [str(Path(input_dir) / f) for f in os.listdir(input_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
    image_files.extend(extracted_images)
    image_files.sort()
    
    if not image_files:
        logging.error(f"No images or PDFs found in {input_dir}.")
        return

    logging.info(f"Found {len(image_files)} images to process in total.")
    
    # Phase 1: OCR Extraction
    logging.info("[1/7] Running OCR Extraction...")
    ocr_engine = OCREngine(config)
    ocr_results = ocr_engine.process_directory(image_files)
    
    # Phase 2: Scene Segmentation
    logging.info("[2/7] Running Scene Segmentation...")
    segmenter = SceneSegmenter(config)
    scenes = segmenter.process_directory(image_files, ocr_results)
    
    logging.info(f"Test complete. Extracted {len(scenes)} scenes.")
    
if __name__ == "__main__":
    test_pipeline()
