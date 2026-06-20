from flask import Flask, render_template, request, jsonify, send_file
import os
import re
from pathlib import Path
from urllib.parse import urlparse
from html import unescape
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import tempfile
import uuid
from io import BytesIO
from image_upscaler import ImageUpscaler

# Watermark remover only works locally, not on Vercel
WATERMARK_ENABLED = False
try:
    from watermark_remover import WatermarkRemover
    WATERMARK_ENABLED = True
except ImportError:
    print("⚠️ Watermark removal disabled (OpenCV not available on this platform)")

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = Path(tempfile.gettempdir()) / 'video_downloads'
UPLOAD_FOLDER.mkdir(exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

class VideoDownloader:
    def __init__(self, output_dir):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Setup requests session with retries
        self.session = requests.Session()
        retry = Retry(total=3, backoff_factor=0.3)
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        # Common headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': '',
        })
    
    def download(self, url, timeout=8):
        """Download video - optimized for serverless with timeout"""
        parsed = urlparse(url)
        self.session.headers['Referer'] = f"{parsed.scheme}://{parsed.netloc}/"
        
        # Try yt-dlp with strict timeout (for serverless)
        try:
            import yt_dlp
            print("🔍 Trying yt-dlp...")
            
            ydl_opts = {
                'outtmpl': str(self.output_dir / '%(title)s.%(ext)s'),
                'format': 'best',
                'quiet': True,
                'no_warnings': True,
                'socket_timeout': timeout,
                'retries': 1,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                if os.path.exists(filename):
                    print("✅ yt-dlp success!")
                    return Path(filename)
        except Exception as e:
            print(f"⚠️ yt-dlp failed: {str(e)[:100]}")
        
        # Fallback: direct extraction
        print("🔄 Direct extraction...")
        response = self.session.get(url, timeout=timeout)
        response.raise_for_status()
        html = response.text
        
        video_urls = self._extract_video_urls(html, url)
        
        if not video_urls:
            raise Exception("No video URLs found. Try YouTube, Vimeo, or TikTok links.")
        
        # Try downloading
        for video_url in video_urls[:3]:  # Limit to 3 attempts
            try:
                file_path = self._download_file(video_url, url, timeout)
                if file_path:
                    return file_path
            except Exception as e:
                print(f"Failed URL: {str(e)[:50]}")
                continue
        
        raise Exception("Failed to download. Try a different video site.")
    
    def _extract_video_urls(self, html, base_url):
        """Extract video URLs from HTML"""
        video_urls = []
        
        # Pattern 1: Direct video tags
        video_patterns = [
            r'<video[^>]+src=["\']([^"\']+)["\']',
            r'<source[^>]+src=["\']([^"\']+)["\']',
        ]
        
        for pattern in video_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            video_urls.extend(matches)
        
        # Pattern 2: JavaScript patterns (enhanced)
        js_patterns = [
            r'["\'](https?://[^"\']*\.(?:mp4|webm|m3u8|mpd|mov)[^"\']*)["\']',
            r'src["\']\s*[:=]\s*["\']([^"\']+\.(?:mp4|webm|m3u8))["\']',
            r'url["\']\s*[:=]\s*["\']([^"\']+\.(?:mp4|webm|m3u8))["\']',
            r'video["\']\s*[:=]\s*["\']([^"\']+)["\']',
            r'videoUrl["\']\s*[:=]\s*["\']([^"\']+)["\']',
            r'videoSrc["\']\s*[:=]\s*["\']([^"\']+)["\']',
            r'file["\']\s*[:=]\s*["\']([^"\']+)["\']',
            # AWS/CDN patterns
            r'(https?://[^"\']*\.(?:cloudfront|amazonaws|s3)[^"\']*\.(?:mp4|webm)[^"\']*)',
            # JSON patterns
            r'"videoUrl"\s*:\s*"([^"]+)"',
            r'"video"\s*:\s*"([^"]+\.(?:mp4|webm))"',
            r'"url"\s*:\s*"([^"]+\.(?:mp4|webm))"',
            r'"src"\s*:\s*"([^"]+\.(?:mp4|webm))"',
        ]
        
        for pattern in js_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            video_urls.extend(matches)
        
        # Make URLs absolute and decode
        absolute_urls = []
        for url in video_urls:
            url = unescape(url)
            try:
                url = url.rstrip('\\')
                url = url.replace('\\u0026', '&')
                url = url.replace('\\u003d', '=')
                url = url.replace('\\u003f', '?')
                url = url.replace('\\/', '/')
            except:
                pass
            
            if url.startswith('http'):
                absolute_urls.append(url)
            elif url.startswith('//'):
                absolute_urls.append('https:' + url)
        
        # Remove duplicates and filter
        seen = set()
        unique_urls = []
        for url in absolute_urls:
            # Also check for CDN patterns
            if url not in seen and (self._is_valid_video_url(url) or 'cloudfront' in url or 's3.amazonaws' in url):
                seen.add(url)
                unique_urls.append(url)
        
        return unique_urls
    
    def _is_valid_video_url(self, url):
        """Check if URL looks like a video file"""
        video_extensions = ['.mp4', '.webm', '.m3u8', '.mpd', '.mov', '.avi', '.mkv']
        url_lower = url.lower()
        return any(ext in url_lower for ext in video_extensions)
    
    def _download_file(self, url, referer, timeout=8):
        """Download file with timeout"""
        self.session.headers['Referer'] = referer
        
        # Generate unique filename
        filename = self._get_filename(url)
        output_path = self.output_dir / filename
        
        # Download with timeout
        response = self.session.get(url, stream=True, timeout=timeout)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        return output_path
    
    def _get_filename(self, url):
        """Extract filename from URL"""
        parsed = urlparse(url)
        path = parsed.path
        filename = os.path.basename(path)
        
        if '.' not in filename or filename.split('.')[-1] not in ['mp4', 'webm', 'mov', 'avi', 'mkv']:
            filename = f"video_{uuid.uuid4().hex[:8]}.mp4"
        
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        return filename


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/download', methods=['POST'])
def download_video():
    try:
        data = request.get_json()
        url = data.get('url')
        remove_watermark = data.get('remove_watermark', False)
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Validate URL
        if not url.startswith('http'):
            return jsonify({'error': 'Invalid URL format'}), 400
        
        # Download video with serverless timeout
        downloader = VideoDownloader(app.config['UPLOAD_FOLDER'])
        file_path = downloader.download(url, timeout=8)
        
        # Remove watermark if requested and available
        if remove_watermark and WATERMARK_ENABLED:
            try:
                print("🔧 Removing watermark...")
                remover = WatermarkRemover()
                file_path = remover.remove_watermark(file_path)
                print("✅ Watermark removed!")
            except Exception as e:
                print(f"⚠️ Watermark removal failed: {e}")
                # Continue with original file if watermark removal fails
        elif remove_watermark and not WATERMARK_ENABLED:
            print("⚠️ Watermark removal not available on this platform")
        
        return jsonify({
            'success': True,
            'filename': os.path.basename(file_path),
            'download_url': f'/api/file/{os.path.basename(file_path)}',
            'message': 'Video processed successfully!' + (' (watermark removal not available on serverless)' if remove_watermark and not WATERMARK_ENABLED else '')
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/file/<filename>')
def download_file(filename):
    try:
        file_path = app.config['UPLOAD_FOLDER'] / filename
        if not file_path.exists():
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/info', methods=['POST'])
def get_info():
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Get page info
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        return jsonify({
            'success': True,
            'status': 'URL is accessible',
            'size': len(response.content)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/upscale', methods=['POST'])
def upscale_image():
    try:
        # Check if file was uploaded
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Get resolution parameter
        resolution = request.form.get('resolution', '4k')
        enhance = request.form.get('enhance', 'true').lower() == 'true'
        
        # Read image bytes
        image_bytes = file.read()
        
        # Upscale image
        upscaler = ImageUpscaler()
        output_bytes, filename = upscaler.upscale_from_bytes(image_bytes, resolution, enhance)
        
        # Save to temp directory
        output_path = app.config['UPLOAD_FOLDER'] / filename
        with open(output_path, 'wb') as f:
            f.write(output_bytes)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'download_url': f'/api/file/{filename}',
            'message': f'Image upscaled to {resolution}!'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
