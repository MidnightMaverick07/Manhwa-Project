import os
from pathlib import Path
import logging
import wave
import contextlib

try:
    from TTS.api import TTS
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    logging.warning("TTS package not installed. Audio generation will create dummy WAV files.")

class AudioEngine:
    def __init__(self, config: dict):
        self.config = config.get('tts', {})
        self.model_name = self.config.get('model_name', 'tts_models/multilingual/multi-dataset/xtts_v2')
        self.speaker_wav = self.config.get('speaker_wav', 'reference_voice.wav')
        self.language = self.config.get('language', 'en')
        self.outputs_dir = Path(config.get('paths', {}).get('output_dir', 'outputs/'))
        self.audio_dir = self.outputs_dir / "narration_chunks"
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        
        self.tts = None
        if TTS_AVAILABLE:
            logging.info(f"Loading TTS model: {self.model_name}")
            try:
                # To avoid downloading massive models during development if not wanted,
                # we could add a flag, but for now we just initialize it.
                # gpu=False to be safe, change to True if user has CUDA
                self.tts = TTS(self.model_name, gpu=False)
            except Exception as e:
                logging.error(f"Failed to load TTS model: {e}")
                self.tts = None

    def _create_dummy_wav(self, output_path: str, duration_sec: int = 5):
        """Creates a silent WAV file for testing if TTS fails."""
        with contextlib.closing(wave.open(output_path, 'wb')) as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(22050)
            f.writeframes(b'\x00' * 22050 * duration_sec)

    def generate_chunk(self, scene_id: str, script: str) -> dict:
        """
        Generate audio for a single script chunk.
        """
        output_filename = f"chunk_{scene_id}.wav"
        output_path = self.audio_dir / output_filename
        
        logging.info(f"Generating audio for scene {scene_id}")
        
        if self.tts and os.path.exists(self.speaker_wav):
            try:
                self.tts.tts_to_file(
                    text=script, 
                    speaker_wav=self.speaker_wav, 
                    language=self.language, 
                    file_path=str(output_path)
                )
            except Exception as e:
                logging.error(f"TTS generation failed for {scene_id}: {e}. Creating dummy audio.")
                self._create_dummy_wav(str(output_path))
        else:
            if not os.path.exists(self.speaker_wav):
                logging.warning(f"Speaker reference {self.speaker_wav} not found.")
            logging.warning(f"Creating dummy audio for {scene_id} due to missing TTS/Speaker.")
            self._create_dummy_wav(str(output_path))
            
        # Get duration
        duration = 5.0
        try:
            with contextlib.closing(wave.open(str(output_path), 'rb')) as f:
                frames = f.getnframes()
                rate = f.getframerate()
                duration = frames / float(rate)
        except Exception:
            pass
            
        return {
            "scene_id": scene_id,
            "audio_path": str(output_path),
            "duration": duration
        }

    def process_scripts(self, scripts: dict) -> list:
        audio_metadata = []
        for scene_id, data in scripts.items():
            script_text = data['script']
            audio_info = self.generate_chunk(scene_id, script_text)
            audio_info['scene_path'] = data['scene_path']
            audio_info['script'] = script_text
            audio_metadata.append(audio_info)
            
        return audio_metadata
