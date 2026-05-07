import logging
import yaml
from core.pdf_extractor import PDFExtractor
import os
from pathlib import Path

logging.basicConfig(level=logging.INFO)

with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

input_dir = config['paths']['input_dir']
pdf_files = [str(Path(input_dir) / f) for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]

if pdf_files:
    pdf_extractor = PDFExtractor(config)
    for pdf in pdf_files:
        print(f"Extracting {pdf}...")
        extracted = pdf_extractor.extract_pdf(pdf)
        print(f"Extracted {len(extracted)} pages.")
else:
    print("No PDFs found.")
