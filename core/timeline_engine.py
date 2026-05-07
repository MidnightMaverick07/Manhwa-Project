import json
from pathlib import Path

class TimelineEngine:
    def __init__(self, config: dict):
        self.outputs_dir = Path(config.get('paths', {}).get('output_dir', 'outputs/'))
        
    def build_timeline(self, audio_metadata: list) -> list:
        """
        Build a flat timeline mapping scenes to audio chunks and timings.
        """
        timeline = []
        current_time = 0.0
        
        for item in audio_metadata:
            duration = item.get('duration', 5.0)
            timeline.append({
                "scene_id": item['scene_id'],
                "scene_path": item['scene_path'],
                "audio_path": item['audio_path'],
                "script": item['script'],
                "start": current_time,
                "end": current_time + duration,
                "duration": duration
            })
            current_time += duration
            
        timeline_path = self.outputs_dir / "timeline.json"
        with open(timeline_path, 'w', encoding='utf-8') as f:
            json.dump(timeline, f, indent=2)
            
        return timeline
