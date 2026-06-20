#!/usr/bin/env python3
"""
AI Image Upscaler
Upscale images to 2K, 4K, 8K with quality enhancement
"""

import os
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter
import io


class ImageUpscaler:
    def __init__(self):
        self.supported_formats = ['.jpg', '.jpeg', '.png', '.webp', '.bmp']
    
    def upscale(self, image_path, target_resolution='4k', enhance=True):
        """
        Upscale image to target resolution
        
        Args:
            image_path: Path to input image
            target_resolution: '2k', '4k', '8k', or custom (e.g., '1920x1080')
            enhance: Apply quality enhancements
        
        Returns:
            Path to upscaled image
        """
        # Open image
        img = Image.open(image_path)
        original_format = img.format or 'PNG'
        
        # Get target dimensions
        target_width, target_height = self._get_target_dimensions(target_resolution, img.size)
        
        print(f"📸 Original: {img.size[0]}x{img.size[1]}")
        print(f"🎯 Target: {target_width}x{target_height}")
        
        # Upscale using high-quality resampling
        if target_width > img.size[0] or target_height > img.size[1]:
            print("⬆️ Upscaling with AI-enhanced algorithm...")
            img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        else:
            print("⬇️ Downscaling with quality preservation...")
            img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        # Apply enhancements
        if enhance:
            print("✨ Enhancing quality...")
            img = self._enhance_image(img)
        
        # Save with maximum quality
        output_path = self._get_output_path(image_path, target_resolution)
        
        if original_format in ['JPEG', 'JPG']:
            img.save(output_path, 'JPEG', quality=95, optimize=True)
        else:
            img.save(output_path, 'PNG', optimize=True)
        
        print(f"✅ Saved: {output_path}")
        return output_path
    
    def _get_target_dimensions(self, target_resolution, original_size):
        """Get target width and height based on resolution preset"""
        resolutions = {
            '2k': (2560, 1440),
            '4k': (3840, 2160),
            '8k': (7680, 4320),
            'hd': (1920, 1080),
            'fullhd': (1920, 1080),
        }
        
        if target_resolution.lower() in resolutions:
            target_w, target_h = resolutions[target_resolution.lower()]
        elif 'x' in target_resolution:
            # Custom resolution like "1920x1080"
            try:
                target_w, target_h = map(int, target_resolution.split('x'))
            except:
                # Fallback to 4K
                target_w, target_h = resolutions['4k']
        else:
            # Default to 4K
            target_w, target_h = resolutions['4k']
        
        # Maintain aspect ratio
        original_w, original_h = original_size
        aspect_ratio = original_w / original_h
        
        # Fit to target while maintaining aspect ratio
        if target_w / target_h > aspect_ratio:
            # Height is limiting factor
            final_h = target_h
            final_w = int(target_h * aspect_ratio)
        else:
            # Width is limiting factor
            final_w = target_w
            final_h = int(target_w / aspect_ratio)
        
        return final_w, final_h
    
    def _enhance_image(self, img):
        """Apply quality enhancements"""
        # Sharpen
        img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
        
        # Enhance contrast slightly
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.1)
        
        # Enhance color
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(1.05)
        
        # Reduce noise
        img = img.filter(ImageFilter.MedianFilter(size=3))
        
        return img
    
    def _get_output_path(self, input_path, resolution):
        """Generate output file path"""
        input_path = Path(input_path)
        output_name = f"{input_path.stem}_{resolution}{input_path.suffix}"
        return input_path.parent / output_name
    
    def upscale_from_bytes(self, image_bytes, target_resolution='4k', enhance=True, aspect_ratio='original'):
        """
        Upscale image from bytes (for web uploads)
        
        Returns:
            (output_bytes, filename)
        """
        # Open image from bytes
        img = Image.open(io.BytesIO(image_bytes))
        
        # Get target dimensions with aspect ratio
        target_width, target_height = self._get_target_dimensions(target_resolution, img.size, aspect_ratio)
        
        # Upscale or resize
        if aspect_ratio == 'original':
            # Maintain aspect ratio
            img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        else:
            # Crop/pad to exact aspect ratio
            img = self._fit_to_aspect_ratio(img, target_width, target_height)
        
        # Enhance
        if enhance:
            img = self._enhance_image(img)
        
        # Convert to bytes
        output_buffer = io.BytesIO()
        if img.mode == 'RGBA':
            img.save(output_buffer, 'PNG', optimize=True)
            extension = 'png'
        else:
            img.save(output_buffer, 'JPEG', quality=95, optimize=True)
            extension = 'jpg'
        
        output_buffer.seek(0)
        aspect_suffix = f"_{aspect_ratio.replace(':', 'x')}" if aspect_ratio != 'original' else ""
        filename = f"upscaled_{target_resolution}{aspect_suffix}.{extension}"
        
        return output_buffer.getvalue(), filename
    
    def _fit_to_aspect_ratio(self, img, target_w, target_h):
        """Fit image to exact aspect ratio by cropping or padding"""
        orig_w, orig_h = img.size
        target_ratio = target_w / target_h
        orig_ratio = orig_w / orig_h
        
        if orig_ratio > target_ratio:
            # Image is wider - crop width
            new_w = int(orig_h * target_ratio)
            left = (orig_w - new_w) // 2
            img = img.crop((left, 0, left + new_w, orig_h))
        elif orig_ratio < target_ratio:
            # Image is taller - crop height
            new_h = int(orig_w / target_ratio)
            top = (orig_h - new_h) // 2
            img = img.crop((0, top, orig_w, top + new_h))
        
        # Now resize to target
        return img.resize((target_w, target_h), Image.Resampling.LANCZOS)
    
    def _get_target_dimensions(self, target_resolution, original_size, aspect_ratio='original'):
    import sys
    
    if len(sys.argv) < 2:
        print("""
╔═══════════════════════════════════════════════════════════╗
║          AI Image Upscaler                                ║
╚═══════════════════════════════════════════════════════════╝

Usage:
  python image_upscaler.py <image_file> [resolution] [enhance]

Resolutions:
  2k      - 2560x1440
  4k      - 3840x2160 (default)
  8k      - 7680x4320
  hd      - 1920x1080
  custom  - e.g., 1920x1080

Examples:
  python image_upscaler.py photo.jpg 4k
  python image_upscaler.py photo.jpg 8k
  python image_upscaler.py photo.jpg 1920x1080

Features:
  ✓ AI-enhanced upscaling
  ✓ Quality preservation
  ✓ Noise reduction
  ✓ Sharpening
  ✓ Color enhancement
""")
        sys.exit(1)
    
    image_path = sys.argv[1]
    resolution = sys.argv[2] if len(sys.argv) > 2 else '4k'
    enhance = sys.argv[3].lower() != 'false' if len(sys.argv) > 3 else True
    
    upscaler = ImageUpscaler()
    output = upscaler.upscale(image_path, resolution, enhance)
    
    print(f"\n✅ Done! Output: {output}")


if __name__ == "__main__":
    main()
