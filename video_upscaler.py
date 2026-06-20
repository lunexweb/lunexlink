#!/usr/bin/env python3
"""
Video Upscaler
Upscale videos to 1080p, 2K, 4K with quality enhancement
"""

import subprocess
import os
import shutil
from pathlib import Path


class VideoUpscaler:
    def __init__(self):
        self.supported_formats = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
        # Try to find FFmpeg in common locations
        self.ffmpeg_path = self._find_ffmpeg()
    
    def _find_ffmpeg(self):
        """Find FFmpeg executable"""
        # First try system PATH
        ffmpeg = shutil.which('ffmpeg')
        if ffmpeg:
            return ffmpeg
        
        # Try common Windows install locations
        common_paths = [
            r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
            r"C:\ffmpeg\bin\ffmpeg.exe",
            os.path.expanduser(r"~\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-full_build\bin\ffmpeg.exe"),
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
        
        return 'ffmpeg'  # Fallback to system PATH
    
    def upscale(self, video_path, target_resolution='1080p', enhance=True, aspect_ratio='original'):
        """
        Upscale video to target resolution using FFmpeg
        
        Args:
            video_path: Path to input video
            target_resolution: '1080p', '2k', '4k'
            enhance: Apply quality enhancements
            aspect_ratio: 'original', '16:9', '9:16', '1:1', '4:3', '21:9'
        
        Returns:
            Path to upscaled video
        """
        video_path = Path(video_path)
        
        # Get target dimensions based on resolution and aspect ratio
        width, height = self._get_target_dimensions(target_resolution, aspect_ratio)
        
        print(f"🎬 Upscaling video to {width}x{height} ({aspect_ratio})")
        
        # Output path
        aspect_suffix = f"_{aspect_ratio.replace(':', 'x')}" if aspect_ratio != 'original' else ""
        output_path = video_path.parent / f"{video_path.stem}_{target_resolution}{aspect_suffix}{video_path.suffix}"
        
        # Build scale filter based on aspect ratio
        if aspect_ratio == 'original':
            # Maintain original aspect ratio
            scale_filter = f'scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:flags=lanczos'
        else:
            # Force specific aspect ratio (may crop or stretch)
            scale_filter = f'scale={width}:{height}:force_original_aspect_ratio=decrease,setsar=1,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2'
        
        # Add enhancement filters
        if enhance:
            scale_filter += ',unsharp=5:5:1.0:5:5:0.0'
        
        # Build FFmpeg command
        cmd = [
            self.ffmpeg_path,
            '-i', str(video_path),
            '-vf', scale_filter,
            '-c:v', 'libx264',
            '-preset', 'slow',  # Better quality
            '-crf', '18',  # High quality (0-51, lower = better)
            '-c:a', 'copy',  # Copy audio without re-encoding
            '-y',
            str(output_path)
        ]
        
        try:
            print(f"⚙️ Processing with FFmpeg ({self.ffmpeg_path})...")
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"✅ Upscaled video saved: {output_path}")
            return output_path
        except FileNotFoundError:
            raise Exception(f"FFmpeg not found at: {self.ffmpeg_path}. Install from: https://ffmpeg.org/download.html")
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else str(e)
            raise Exception(f"FFmpeg error: {error_msg[:300]}")
    
    def _get_target_dimensions(self, resolution, aspect_ratio='original'):
        """Get width and height for target resolution and aspect ratio"""
        # Base resolutions (height-based)
        base_heights = {
            '720p': 720,
            '1080p': 1080,
            '2k': 1440,
            '4k': 2160,
            '8k': 4320,
        }
        
        height = base_heights.get(resolution.lower(), 1080)
        
        # Calculate width based on aspect ratio
        aspect_ratios = {
            'original': None,  # Will be calculated from source
            '16:9': 16/9,
            '9:16': 9/16,
            '1:1': 1/1,
            '4:3': 4/3,
            '21:9': 21/9,
        }
        
        ratio = aspect_ratios.get(aspect_ratio, 16/9)
        
        if ratio:
            width = int(height * ratio)
            # Make sure dimensions are even (required by many codecs)
            width = width if width % 2 == 0 else width + 1
            height = height if height % 2 == 0 else height + 1
        else:
            # Original aspect ratio - use standard 16:9
            width = int(height * 16/9)
        
        return width, height


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
