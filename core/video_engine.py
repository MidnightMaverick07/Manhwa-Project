import ffmpeg
import os
from pathlib import Path
import logging

class VideoEngine:
    def __init__(self, config: dict):
        self.config = config.get('video', {})
        self.resolution = self.config.get('resolution', [1920, 1080])
        self.fps = self.config.get('fps', 30)
        self.outputs_dir = Path(config.get('paths', {}).get('output_dir', 'outputs/'))
        self.temp_dir = Path(config.get('paths', {}).get('temp_dir', 'temp/'))
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
    def _create_scene_clip(self, scene_item: dict) -> str:
        """Create a video clip for a single scene with static or simple motion."""
        scene_path = scene_item['scene_path']
        audio_path = scene_item['audio_path']
        duration = scene_item['duration']
        scene_id = scene_item['scene_id']
        
        output_clip_path = self.temp_dir / f"clip_{scene_id}.mp4"
        
        # Build FFmpeg input for image (looping)
        video_input = ffmpeg.input(scene_path, loop=1, t=duration)
        
        # Scale and pad to fit resolution
        w, h = self.resolution
        # A simple scale and pad to keep aspect ratio and fit into 1920x1080
        video_stream = (
            video_input
            .filter('scale', w, h, force_original_aspect_ratio='decrease')
            .filter('pad', w, h, '(ow-iw)/2', '(oh-ih)/2')
            .filter('setsar', '1')
        )
        
        # Audio input
        audio_input = ffmpeg.input(audio_path)
        
        # Combine
        try:
            logging.info(f"Rendering clip for scene {scene_id}")
            (
                ffmpeg
                .output(video_stream, audio_input, str(output_clip_path), 
                        vcodec='libx264', pix_fmt='yuv420p', r=self.fps, 
                        acodec='aac', shortest=None)
                .overwrite_output()
                .run(quiet=True)
            )
            return str(output_clip_path)
        except ffmpeg.Error as e:
            logging.error(f"FFmpeg error rendering {scene_id}: {e.stderr.decode() if e.stderr else e}")
            return None

    def render_video(self, timeline: list, srt_path: str):
        """Render the final video from timeline."""
        clip_paths = []
        for item in timeline:
            clip = self._create_scene_clip(item)
            if clip:
                clip_paths.append(clip)
                
        if not clip_paths:
            logging.error("No clips were generated. Aborting final render.")
            return
            
        # Create a concat demuxer file
        concat_file_path = self.temp_dir / "concat_list.txt"
        with open(concat_file_path, 'w', encoding='utf-8') as f:
            for clip_path in clip_paths:
                # FFmpeg requires forward slashes or escaped backslashes for paths
                safe_path = Path(clip_path).absolute().as_posix()
                f.write(f"file '{safe_path}'\n")
                
        final_output = self.outputs_dir / "output_video.mp4"
        
        # Concat all clips
        logging.info("Concatenating clips and burning subtitles...")
        
        try:
            # We use subprocess to run ffmpeg directly for the concat + subtitle filter 
            # because ffmpeg-python concat can be tricky with complex subtitle filters.
            # Using concat demuxer:
            # ffmpeg -f concat -safe 0 -i concat_list.txt -vf subtitles=subtitles.srt final.mp4
            
            safe_srt = Path(srt_path).absolute().as_posix()
            # subtitle filter needs escaped colons and slashes if it's Windows absolute path, 
            # but as_posix usually works if we escape the drive letter colon
            safe_srt_escaped = safe_srt.replace(':', r'\:')
            
            concat_stream = ffmpeg.input(str(concat_file_path), format='concat', safe=0)
            
            (
                ffmpeg
                .output(concat_stream, str(final_output), 
                        vf=f"subtitles={safe_srt_escaped}", 
                        c='copy', # We can't copy if we apply video filters (subtitles)
                        vcodec='libx264', acodec='aac')
                .overwrite_output()
                .run(quiet=True)
            )
            logging.info(f"Final video rendered successfully at {final_output}")
        except ffmpeg.Error as e:
            logging.error(f"FFmpeg concat error: {e.stderr.decode() if e.stderr else e}")
            
        return str(final_output)
