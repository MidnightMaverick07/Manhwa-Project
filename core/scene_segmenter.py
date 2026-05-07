import cv2
import numpy as np
import os
import json
from pathlib import Path
import logging

class SceneSegmenter:
    def __init__(self, config: dict):
        self.config = config.get('segmenter', {})
        self.min_scene_height = self.config.get('min_scene_height', 500)
        self.whitespace_threshold = self.config.get('whitespace_threshold', 240)
        self.min_gap_size = self.config.get('min_gap_size', 50)
        self.min_aspect_ratio = self.config.get('min_aspect_ratio', 0.3)
        self.max_aspect_ratio = self.config.get('max_aspect_ratio', 3.0)
        
        self.debug_dir = Path(self.config.get('debug_dir', 'debug/scene_segments/'))
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        
    def _is_whitespace_row(self, row, threshold):
        """Check if a row of pixels is mostly whitespace (very bright)."""
        return np.mean(row) > threshold

    def _intervals_overlap(self, interval_a, interval_b):
        """Check if two [start, end] intervals overlap."""
        return max(0, min(interval_a[1], interval_b[1]) - max(interval_a[0], interval_b[0])) > 0

    def segment_image(self, image_path: str, page_ocr: dict) -> list:
        """
        Segment a single vertical page into multiple scene images.
        Uses full-page OCR boxes to avoid cutting through dialogue and maps
        the OCR results to the localized scenes.
        """
        logging.info(f"Segmenting {image_path} with OCR guidance")
        img = cv2.imread(image_path)
        if img is None:
            logging.error(f"Failed to load image: {image_path}")
            return []

        height, width = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 1. Extract OCR "no-cut" zones
        no_cut_zones = []
        text_blocks = page_ocr.get("text_blocks", [])
        for tb in text_blocks:
            box = tb["box"] # [[x1,y1], [x2,y1], [x2,y2], [x1,y2]]
            y_coords = [pt[1] for pt in box]
            min_y, max_y = int(min(y_coords)), int(max(y_coords))
            # Expand the zone slightly to prevent cutting too close to text
            no_cut_zones.append([max(0, min_y - 10), min(height, max_y + 10)])

        # 2. Find horizontal gaps
        is_white = np.array([self._is_whitespace_row(gray[y, :], self.whitespace_threshold) for y in range(height)])
        
        gaps = []
        in_gap = False
        gap_start = 0
        for y in range(height):
            if is_white[y]:
                if not in_gap:
                    in_gap = True
                    gap_start = y
            else:
                if in_gap:
                    in_gap = False
                    gaps.append([gap_start, y])
        if in_gap:
            gaps.append([gap_start, height])

        # Filter gaps by min_gap_size and calculate valid cut points
        cut_points = [0] # Always start at 0
        for gap in gaps:
            gap_size = gap[1] - gap[0]
            if gap_size >= self.min_gap_size:
                # Proposed cut is the middle of the gap
                cut_y = gap[0] + (gap_size // 2)
                
                # Check if this cut intersects any no-cut zone
                valid_cut = True
                for zone in no_cut_zones:
                    if zone[0] <= cut_y <= zone[1]:
                        valid_cut = False
                        break
                
                if valid_cut:
                    cut_points.append(cut_y)
        
        cut_points.append(height) # Always end at height
        
        # 3. Create initial slices and merge them based on heuristics
        initial_slices = []
        for i in range(len(cut_points) - 1):
            initial_slices.append([cut_points[i], cut_points[i+1]])
            
        merged_slices = []
        current_slice = None
        
        for slc in initial_slices:
            if current_slice is None:
                current_slice = slc
                continue
                
            slc_height = current_slice[1] - current_slice[0]
            
            # Heuristic: If height is too small, merge with next
            if slc_height < self.min_scene_height:
                current_slice = [current_slice[0], slc[1]]
            else:
                merged_slices.append(current_slice)
                current_slice = slc
                
        if current_slice:
            # Check final slice
            slc_height = current_slice[1] - current_slice[0]
            if slc_height < self.min_scene_height and merged_slices:
                # Merge into the last existing slice
                merged_slices[-1][1] = current_slice[1]
            else:
                merged_slices.append(current_slice)

        # 4. Process segments, save images, map OCR
        base_name = Path(image_path).stem
        scene_metadata = []
        
        for idx, (start_y, end_y) in enumerate(merged_slices):
            scene_img = img[start_y:end_y, :]
            scene_id = f"{base_name}_{idx+1:03d}"
            scene_filename = f"scene_{scene_id}.jpg"
            scene_path = self.debug_dir / scene_filename
            
            # Map OCR to this segment
            mapped_text_blocks = []
            for tb in text_blocks:
                box = tb["box"]
                y_coords = [pt[1] for pt in box]
                y_center = sum(y_coords) / 4.0
                
                # If the text center falls within this segment
                if start_y <= y_center < end_y:
                    x_center = sum([pt[0] for pt in box]) / 4.0
                    
                    # Shift Y coordinates to be relative to the segment
                    shifted_box = [[pt[0], pt[1] - start_y] for pt in box]
                    
                    mapped_text_blocks.append({
                        "original_box": box,
                        "box": shifted_box,
                        "text": tb["text"],
                        "confidence": tb["confidence"],
                        "y_center": y_center - start_y,
                        "x_center": x_center
                    })
            
            # Sort dialogue by (y_center, x_center) for reading flow
            mapped_text_blocks.sort(key=lambda x: (x["y_center"], x["x_center"]))
            
            # Only save the image and add to pipeline if it has substantial content
            # (e.g. non-zero size). Even if no OCR, it might be an establishing shot.
            if scene_img.size > 0:
                cv2.imwrite(str(scene_path), scene_img)
                scene_metadata.append({
                    "source_image": Path(image_path).name,
                    "scene_id": scene_id,
                    "scene_path": str(scene_path),
                    "y_range": [start_y, end_y],
                    "height": end_y - start_y,
                    "text_blocks": mapped_text_blocks
                })
        
        # Output debug scene map
        map_path = self.debug_dir / f"{base_name}_scene_map.json"
        with open(map_path, 'w', encoding='utf-8') as f:
            json.dump({
                "source_page": Path(image_path).name,
                "segments": scene_metadata
            }, f, indent=2, ensure_ascii=False)

        return scene_metadata

    def process_directory(self, image_paths: list, ocr_results: list) -> list:
        all_scenes = []
        ocr_dict = {res["image"]: res for res in ocr_results}
        
        for img_path in image_paths:
            img_name = Path(img_path).name
            page_ocr = ocr_dict.get(img_name, {})
            scenes = self.segment_image(img_path, page_ocr)
            all_scenes.extend(scenes)
            
        return all_scenes
