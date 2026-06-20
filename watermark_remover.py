#!/usr/bin/env python3
"""
AI-Based Watermark Remover
Automatically detects and removes watermarks from videos
"""

import cv2
import numpy as np
from pathlib import Path
import tempfile
import os


class WatermarkRemover:
    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / 'watermark_processing'
        self.temp_dir.mkdir(exist_ok=True)
    
    def remove_watermark(self, video_path, output_path=None):
        """
        Remove watermark from video using AI detection
        
        Args:
            video_path: Path to input video
            output_path: Path to output video (optional)
        
        Returns:
            Path to processed video
        """
        video_path = Path(video_path)
        
        if output_path is None:
            output_path = video_path.parent / f"{video_path.stem}_no_watermark{video_path.suffix}"
        else:
            output_path = Path(output_path)
        
        print(f"🔍 Analyzing video for watermarks...")
        
        # Open video
        cap = cv2.VideoCapture(str(video_path))
        
        if not cap.isOpened():
            raise Exception("Failed to open video file")
        
        # Get video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        print(f"📹 Video: {width}x{height} @ {fps}fps, {total_frames} frames")
        
        # Detect watermark location from sample frames
        watermark_mask = self._detect_watermark(cap, width, height)
        
        if watermark_mask is None:
            print("⚠️ No watermark detected! Trying corner removal fallback...")
            cap.release()
            # Fallback: remove common corner watermarks
            return self._remove_corners(video_path, output_path)
        
        print(f"✓ Watermark detected! Removing...")
        
        # Reset video to beginning
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
        
        # Process each frame
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Remove watermark from frame
            cleaned_frame = self._remove_watermark_from_frame(frame, watermark_mask)
            
            # Write frame
            out.write(cleaned_frame)
            
            frame_count += 1
            if frame_count % 30 == 0:
                progress = (frame_count / total_frames) * 100
                print(f"\r⚙️  Processing: {progress:.1f}% ({frame_count}/{total_frames} frames)", end='', flush=True)
        
        print("\n✅ Watermark removed successfully!")
        
        # Release resources
        cap.release()
        out.release()
        
        return output_path
    
    def _detect_watermark(self, cap, width, height, sample_frames=30):
        """
        Detect watermark location by analyzing multiple frames
        """
        # Sample frames from different parts of the video
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        sample_indices = np.linspace(0, total_frames - 1, min(sample_frames, total_frames), dtype=int)
        
        frames = []
        for idx in sample_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                frames.append(frame)
        
        if len(frames) == 0:
            return None
        
        # Convert frames to grayscale
        gray_frames = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in frames]
        
        # Calculate standard deviation across frames
        # Watermarks have low variance (static), content has high variance
        frame_stack = np.stack(gray_frames, axis=0)
        std_dev = np.std(frame_stack, axis=0)
        
        # Watermark detection: areas with low variance
        # More aggressive threshold: areas with std < 20 are likely watermarks
        watermark_candidate = (std_dev < 20).astype(np.uint8) * 255
        
        # Clean up the mask with morphological operations
        kernel = np.ones((5, 5), np.uint8)
        watermark_candidate = cv2.morphologyEx(watermark_candidate, cv2.MORPH_CLOSE, kernel)
        watermark_candidate = cv2.morphologyEx(watermark_candidate, cv2.MORPH_OPEN, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(watermark_candidate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if len(contours) == 0:
            return None
        
        # Filter contours by size (remove noise, keep watermarks)
        min_area = (width * height) * 0.0005  # At least 0.05% of frame (more sensitive)
        max_area = (width * height) * 0.25    # At most 25% of frame
        
        valid_contours = [c for c in contours if min_area < cv2.contourArea(c) < max_area]
        
        if len(valid_contours) == 0:
            return None
        
        # Create final watermark mask
        watermark_mask = np.zeros((height, width), dtype=np.uint8)
        cv2.drawContours(watermark_mask, valid_contours, -1, 255, -1)
        
        # Expand mask slightly for better coverage
        kernel = np.ones((7, 7), np.uint8)
        watermark_mask = cv2.dilate(watermark_mask, kernel, iterations=2)
        
        return watermark_mask
    
    def _remove_watermark_from_frame(self, frame, watermark_mask):
        """
        Remove watermark from a single frame using inpainting
        """
        # Use OpenCV's inpainting to fill watermark area
        # Method: INPAINT_TELEA (Fast marching method)
        cleaned = cv2.inpaint(frame, watermark_mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)
        
        return cleaned
    
    def _remove_corners(self, video_path, output_path):
        """
        Fallback: Remove all corners where watermarks typically appear (OPTIMIZED)
        """
        cap = cv2.VideoCapture(str(video_path))
        
        if not cap.isOpened():
            return video_path
        
        # Get video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # OPTIMIZATION: Use ffmpeg for faster processing
        # Instead of processing frame-by-frame, use ffmpeg's delogo filter
        import subprocess
        
        print(f"🚀 Using fast corner removal (ffmpeg optimization)...")
        
        # Create a simple crop to remove corners
        # This is much faster than inpainting
        crop_pixels = 50  # Remove 50 pixels from each edge
        
        ffmpeg_cmd = [
            'ffmpeg',
            '-i', str(video_path),
            '-vf', f'crop={width-crop_pixels*2}:{height-crop_pixels*2}:{crop_pixels}:{crop_pixels}',
            '-c:a', 'copy',  # Copy audio without re-encoding
            '-y',  # Overwrite output
            str(output_path)
        ]
        
        try:
            # Try ffmpeg first (much faster)
            subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
            print("\n✅ Fast corner removal completed!")
            return output_path
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback to OpenCV if ffmpeg not available
            print("⚠️ ffmpeg not found, using slower method...")
            return self._remove_corners_opencv(video_path, output_path, width, height, fps, total_frames)
    
    def _remove_corners_opencv(self, video_path, output_path, width, height, fps, total_frames):
        """
        Fallback: Remove all corners where watermarks typically appear
        """
        cap = cv2.VideoCapture(str(video_path))
        
        if not cap.isOpened():
            return video_path
        
        # Get video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Create mask for all corners (common watermark locations)
        mask = np.zeros((height, width), dtype=np.uint8)
        margin_w = int(width * 0.20)  # 20% width margin
        margin_h = int(height * 0.20)  # 20% height margin
        
        # Mark all four corners
        corners = [
            (0, margin_h, 0, margin_w),  # top-left
            (0, margin_h, width - margin_w, width),  # top-right
            (height - margin_h, height, 0, margin_w),  # bottom-left
            (height - margin_h, height, width - margin_w, width),  # bottom-right
        ]
        
        for y1, y2, x1, x2 in corners:
            mask[y1:y2, x1:x2] = 255
        
        print(f"🔧 Removing corners where watermarks typically appear...")
        
        # Process video
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
        
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Inpaint corner areas
            cleaned = cv2.inpaint(frame, mask, inpaintRadius=5, flags=cv2.INPAINT_TELEA)
            out.write(cleaned)
            
            frame_count += 1
            if frame_count % 30 == 0:
                progress = (frame_count / total_frames) * 100
                print(f"\r⚙️  Processing: {progress:.1f}% ({frame_count}/{total_frames} frames)", end='', flush=True)
        
        print("\n✅ Corner watermarks removed!")
        
        cap.release()
        out.release()
        
        return output_path
    
        return output_path
    
    def quick_remove(self, video_path, corner='auto'):
        """
        Quick watermark removal for common locations (corners)
        
        Args:
            video_path: Path to video
            corner: 'auto', 'top-left', 'top-right', 'bottom-left', 'bottom-right'
        """
        video_path = Path(video_path)
        output_path = video_path.parent / f"{video_path.stem}_cleaned{video_path.suffix}"
        
        cap = cv2.VideoCapture(str(video_path))
        
        if not cap.isOpened():
            raise Exception("Failed to open video file")
        
        # Get video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Create mask for corner watermarks (typical 15% of width/height)
        mask = np.zeros((height, width), dtype=np.uint8)
        margin_w = int(width * 0.15)
        margin_h = int(height * 0.15)
        
        if corner == 'auto':
            # Check all corners
            corners = [
                (0, margin_h, 0, margin_w),  # top-left
                (0, margin_h, width - margin_w, width),  # top-right
                (height - margin_h, height, 0, margin_w),  # bottom-left
                (height - margin_h, height, width - margin_w, width),  # bottom-right
            ]
            # Mark all corners
            for y1, y2, x1, x2 in corners:
                mask[y1:y2, x1:x2] = 255
        elif corner == 'top-left':
            mask[0:margin_h, 0:margin_w] = 255
        elif corner == 'top-right':
            mask[0:margin_h, width - margin_w:width] = 255
        elif corner == 'bottom-left':
            mask[height - margin_h:height, 0:margin_w] = 255
        elif corner == 'bottom-right':
            mask[height - margin_h:height, width - margin_w:width] = 255
        
        # Process video
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
        
        print(f"🔧 Removing watermarks from {corner} position...")
        
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Inpaint watermark area
            cleaned = cv2.inpaint(frame, mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)
            out.write(cleaned)
            
            frame_count += 1
            if frame_count % 30 == 0:
                print(f"\r⚙️  Processing frame {frame_count}...", end='', flush=True)
        
        print("\n✅ Done!")
        
        cap.release()
        out.release()
        
        return output_path


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("""
╔═══════════════════════════════════════════════════════════╗
║          AI Watermark Remover                             ║
╚═══════════════════════════════════════════════════════════╝

Usage:
  python watermark_remover.py <video_file> [method]

Methods:
  auto   - Automatic watermark detection (default)
  quick  - Quick removal from corners

Examples:
  python watermark_remover.py video.mp4
  python watermark_remover.py video.mp4 quick

Note: This tool is for videos you own or have permission to modify.
""")
        sys.exit(1)
    
    video_path = sys.argv[1]
    method = sys.argv[2] if len(sys.argv) > 2 else 'auto'
    
    remover = WatermarkRemover()
    
    if method == 'quick':
        output = remover.quick_remove(video_path, corner='auto')
    else:
        output = remover.remove_watermark(video_path)
    
    print(f"\n📁 Output: {output}")


if __name__ == "__main__":
    main()
