import os
from pathlib import Path
import json

class SubtitleEngine:
    def __init__(self, config: dict):
        self.outputs_dir = Path(config.get('paths', {}).get('output_dir', 'outputs/'))
        
    def _format_time(self, seconds: float) -> str:
        """Format seconds to SRT time format: HH:MM:SS,mmm"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds - int(seconds)) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def generate_srt(self, timeline: list) -> str:
        """
        Generate SRT file based on the timeline audio chunks.
        Expects timeline to be a list of dicts:
        [{'start': 0.0, 'end': 5.0, 'script': 'text'}]
        """
        srt_path = self.outputs_dir / "subtitles.srt"
        
        with open(srt_path, 'w', encoding='utf-8') as f:
            for idx, item in enumerate(timeline):
                start_time = self._format_time(item['start'])
                end_time = self._format_time(item['end'])
                text = item.get('script', '')
                
                f.write(f"{idx + 1}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{text}\n\n")
                
        return str(srt_path)
