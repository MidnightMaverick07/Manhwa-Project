import os
from pathlib import Path
from paddleocr import PaddleOCR
import json
import logging

class OCREngine:
    def __init__(self, config: dict):
        self.config = config.get('ocr', {})
        self.lang = self.config.get('language', 'en')
        self.use_angle_cls = self.config.get('use_angle_cls', True)
        self.cache_dir = Path(config.get('paths', {}).get('cache_dir', 'cache/'))
        
        logging.info(f"Initializing PaddleOCR (lang: {self.lang})")
        # Initialize PaddleOCR
        # Using show_log=True to see model download progress
        self.ocr = PaddleOCR(use_angle_cls=self.use_angle_cls, lang=self.lang)

    def extract_text(self, image_path: str) -> dict:
        """
        Extract text from an image. 
        Returns a dict containing the text and bounding boxes.
        """
        image_name = Path(image_path).name
        cache_file = self.cache_dir / f"ocr_{image_name}.json"
        
        # Check cache first
        if cache_file.exists():
            logging.info(f"Loading cached OCR for {image_name}")
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)

        logging.info(f"Running OCR on {image_name}")
        result = self.ocr.ocr(image_path)
        
        extracted_data = []
        if result and result[0]:
            for line in result[0]:
                box = line[0]
                text = line[1][0]
                confidence = float(line[1][1])
                extracted_data.append({
                    "box": box,
                    "text": text,
                    "confidence": confidence
                })

        output_data = {
            "image": image_name,
            "text_blocks": extracted_data
        }

        # Save to cache
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        return output_data

    def process_directory(self, image_paths: list) -> list:
        """
        Process a list of image paths and return their OCR results.
        """
        results = []
        for img_path in image_paths:
            res = self.extract_text(img_path)
            results.append(res)
        return results
