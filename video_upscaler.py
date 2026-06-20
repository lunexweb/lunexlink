#!/usr/bin/env python3
"""
Video Upscaler
Upscale videos to 1080p, 2K, 4K with quality enhancement
"""

import subprocess
import os
from pathlib import Path


class VideoUpscaler:
    def __init__(self):
        self.supported_formats = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
    
    def upscale(self, video_path, target_resolution='1080p', enhance=True):
        """
        Upscale video to target resolution using FFmpeg
        
        Args:
            video_path: Path to input video
            target_resolution: '1080p', '2k', '4k'
            enhance: Apply quality enhancements
        
        Returns:
            Path to upscaled video
        """
        video_path = Path(video_path)
        
        # Get target dimensions
        width, height = self._get_target_dimensions(target_resolution)
        
        print(f"🎬 Upscaling video to {width}x{height}")
        
        # Output path
        output_path = video_path.parent / f"{video_path.stem}_{target_resolution}{video_path.suffix}"
        
        # Build FFmpeg command
        cmd = [
            'ffmpeg',
            '-i', str(video_path),
            '-vf', f'scale={width}:{height}:flags=lanczos',
            '-c:v', 'libx264',
            '-preset', 'slow',  # Better quality
            '-crf', '18',  # High quality (0-51, lower = better)
            '-c:a', 'copy',  # Copy audio without re-encoding
            '-y',
            str(output_path)
        ]
        
        # Add enhancement filters
        if enhance:
            filters = f'scale={width}:{height}:flags=lanczos,unsharp=5:5:1.0:5:5:0.0'
            cmd[cmd.index('-vf') + 1] = filters
        
        try:
            print("⚙️ Processing with FFmpeg...")
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"✅ Upscaled video saved: {output_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            raise Exception(f"FFmpeg error: {e.stderr.decode()[:200]}")
        except FileNotFoundError:
            raise Exception("FFmpeg not installed. Please install FFmpeg.")
    
    def _get_target_dimensions(self, resolution):
        """Get width and height for target resolution"""
        resolutions = {
            '720p': (1280, 720),
            '1080p': (1920, 1080),
            '2k': (2560, 1440),
            '4k': (3840, 2160),
        }
        return resolutions.get(resolution.lower(), (1920, 1080))


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("""
╔═══════════════════════════════════════════════════════════╗
║          Video Upscaler                                   ║
╚═══════════════════════════════════════════════════════════╝

Usage:
  python video_upscaler.py <video_file> [resolution]

Resolutions:
  720p    - 1280x720
  1080p   - 1920x1080 (default)
  2k      - 2560x1440
  4k      - 3840x2160

Examples:
  python video_upscaler.py video.mp4 1080p
  python video_upscaler.py video.mp4 4k

Features:
  ✓ High-quality upscaling
  ✓ Sharpening filter
  ✓ Audio preservation
""")
        sys.exit(1)
    
    video_path = sys.argv[1]
    resolution = sys.argv[2] if len(sys.argv) > 2 else '1080p'
    
    upscaler = VideoUpscaler()
    output = upscaler.upscale(video_path, resolution, enhance=True)
    
    print(f"\n✅ Done! Output: {output}")


if __name__ == "__main__":
    main()
