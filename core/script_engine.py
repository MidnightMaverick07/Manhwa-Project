import requests
import json
import logging
import yaml
from pathlib import Path

class ScriptEngine:
    def __init__(self, config: dict):
        self.config = config.get('llm', {})
        self.endpoint = self.config.get('endpoint', 'http://localhost:11434/api/generate')
        self.model = self.config.get('model', 'qwen2.5:14b')
        self.temperature = self.config.get('temperature', 0.7)
        self.outputs_dir = Path(config.get('paths', {}).get('output_dir', 'outputs/'))
        
        # Load style profile
        self.style_profile = {}
        style_path = Path("style_profile.yaml")
        if style_path.exists():
            with open(style_path, 'r', encoding='utf-8') as f:
                self.style_profile = yaml.safe_load(f)

    def _build_prompt(self, scene_data: dict, ocr_text: str) -> str:
        style_desc = self.style_profile.get('narrator_personality', 'dramatic')
        intensity = self.style_profile.get('emotional_intensity', 'high')
        rules = "\n".join([f"- {r}" for r in self.style_profile.get('rules', [])])
        
        prompt = f"""
        You are a YouTube recap narrator for a manhwa/webtoon. 
        Style: {style_desc}
        Emotional Intensity: {intensity}
        Rules:
        {rules}
        
        Here is the text extracted from a scene (dialogue, sound effects, etc):
        "{ocr_text}"
        
        Write a short narration script for this scene. It should be 1-3 sentences.
        DO NOT include sound effects or visual descriptions that aren't implied. 
        JUST output the spoken narration script.
        """
        return prompt.strip()

    def generate_scene_script(self, scene_data: dict) -> str:
        """
        Generate narration for a single scene based on its OCR text.
        """
        scene_text = ""
        text_blocks = scene_data.get('text_blocks', [])
        
        for block in text_blocks:
            scene_text += f"{block['text']} "
                        
        scene_text = scene_text.strip()
        
        if not scene_text:
            logging.warning(f"No OCR text found for scene {scene_data.get('scene_id')}. Skipping generation.")
            return ""

        prompt = self._build_prompt(scene_data, scene_text)
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature
            }
        }
        
        logging.info(f"Generating script for scene {scene_data['scene_id']} using {self.model}")
        try:
            response = requests.post(self.endpoint, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            script = result.get('response', '').strip()
            return script
        except Exception as e:
            logging.error(f"Failed to generate script for {scene_data['scene_id']}: {e}")
            return ""

    def process_scenes(self, scenes: list) -> dict:
        """
        Generate scripts for all scenes and structure them.
        """
        structured_scripts = {}
        for scene in scenes:
            script = self.generate_scene_script(scene)
            if script:
                structured_scripts[scene['scene_id']] = {
                    "scene_path": scene['scene_path'],
                    "script": script
                }
                
        # Save to file
        output_file = self.outputs_dir / "narration.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(structured_scripts, f, indent=2, ensure_ascii=False)
            
        # Also save raw text
        text_file = self.outputs_dir / "narration.txt"
        with open(text_file, 'w', encoding='utf-8') as f:
            for scene_id, data in structured_scripts.items():
                f.write(f"{data['script']}\n\n")
                
        return structured_scripts
