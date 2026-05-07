import os
import logging
from pathlib import Path
from core.ocr_engine import OCREngine
from core.scene_segmenter import SceneSegmenter
from core.pdf_extractor import PDFExtractor
from core.script_engine import ScriptEngine
from core.audio_engine import AudioEngine
from core.timeline_engine import TimelineEngine
from core.subtitle_engine import SubtitleEngine
from core.video_engine import VideoEngine

def setup_logging(config):
    log_dir = Path(config.get('paths', {}).get('logs_dir', 'logs/'))
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "pipeline.log"),
            logging.StreamHandler()
        ]
    )

def run_pipeline(config: dict):
    setup_logging(config)
    logging.info("Initializing Manhwa-to-YouTube-Recap Pipeline (Phase 1)...")
    
    input_dir = config['paths']['input_dir']
    
    if not os.path.exists(input_dir):
        logging.error(f"Input directory {input_dir} does not exist.")
        return

    # Phase 0: PDF Extraction (if any)
    pdf_files = [str(Path(input_dir) / f) for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
    extracted_images = []
    if pdf_files:
        logging.info(f"[0/7] Running PDF Extraction on {len(pdf_files)} files...")
        pdf_extractor = PDFExtractor(config)
        for pdf in pdf_files:
            extracted_images.extend(pdf_extractor.extract_pdf(pdf))
            
    # Combine directly provided images with PDF extracted images
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
    
    if not scenes:
        logging.error("No scenes generated. Aborting.")
        return
    
    # Phase 3: Script Generation
    logging.info("[3/7] Generating Narrative Script...")
    script_engine = ScriptEngine(config)
    scripts = script_engine.process_scenes(scenes)
    
    # Phase 4: Audio Generation
    logging.info("[4/7] Generating Semantic Audio Chunks...")
    audio_engine = AudioEngine(config)
    audio_metadata = audio_engine.process_scripts(scripts)
    
    # Phase 5: Timeline
    logging.info("[5/7] Building Timeline...")
    timeline_engine = TimelineEngine(config)
    timeline = timeline_engine.build_timeline(audio_metadata)
    
    # Phase 6: Subtitles
    logging.info("[6/7] Generating Subtitles...")
    subtitle_engine = SubtitleEngine(config)
    srt_path = subtitle_engine.generate_srt(timeline)
    
    # Phase 7: Video Rendering
    logging.info("[7/7] Rendering Final Video...")
    video_engine = VideoEngine(config)
    final_video = video_engine.render_video(timeline, srt_path)
    
    if final_video:
        logging.info(f"Pipeline finished successfully! Video saved to {final_video}")
    else:
        logging.error("Pipeline failed during video rendering.")
