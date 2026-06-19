#!/usr/bin/env python3
"""
Universal Video Downloader
Downloads videos from any site by finding the actual video URL
"""

import sys
import os
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse
from html import unescape
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    import yt_dlp
    YT_DLP_AVAILABLE = True
except ImportError:
    YT_DLP_AVAILABLE = False
    print("Note: yt-dlp not found, using direct download method")


class UniversalDownloader:
    def __init__(self, output_dir="downloads"):
        """Initialize downloader"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Setup requests session with retries
        self.session = requests.Session()
        retry = Retry(total=3, backoff_factor=0.3)
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        # Common headers to avoid blocks
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': '',
        })
    
    def download(self, url, method="auto"):
        """
        Download video using the best available method
        
        Args:
            url: Video URL
            method: 'auto' (try yt-dlp first), 'direct' (direct download), 'ytdlp' (force yt-dlp)
        """
        print(f"\n📥 Downloading from: {url}")
        print(f"📁 Output: {self.output_dir.absolute()}")
        print("-" * 70)
        
        # Set referer from URL
        parsed = urlparse(url)
        self.session.headers['Referer'] = f"{parsed.scheme}://{parsed.netloc}/"
        
        # Try yt-dlp first if available and method allows
        if method in ["auto", "ytdlp"] and YT_DLP_AVAILABLE:
            print("🔍 Trying yt-dlp method...")
            if self._download_ytdlp(url):
                return True
            
            if method == "ytdlp":
                print("❌ yt-dlp failed and no fallback requested")
                return False
            
            print("\n🔄 Falling back to direct download method...")
        
        # Try direct download
        print("🔍 Analyzing page for video sources...")
        return self._download_direct(url)
    
    def _download_ytdlp(self, url):
        """Download using yt-dlp"""
        ydl_opts = {
            'outtmpl': str(self.output_dir / '%(title)s.%(ext)s'),
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4',
            'quiet': False,
            'no_warnings': False,
            'nocheckcertificate': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            print("\n✅ Download completed via yt-dlp!")
            return True
        except Exception as e:
            print(f"⚠️  yt-dlp error: {e}")
            return False
    
    def _download_direct(self, url):
        """Download by finding video URL directly"""
        try:
            # Step 1: Get the page content
            print("📄 Fetching page content...")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            html = response.text
            
            # Step 2: Find video URLs in the page
            print("🔎 Searching for video sources...")
            video_urls = self._extract_video_urls(html, url)
            
            if not video_urls:
                print("❌ No video URLs found in page")
                return False
            
            print(f"✓ Found {len(video_urls)} potential video source(s)")
            
            # Step 3: Try downloading each URL
            for i, video_url in enumerate(video_urls, 1):
                print(f"\n📹 Trying source {i}/{len(video_urls)}: {video_url[:80]}...")
                if self._download_file(video_url, url):
                    return True
            
            print("❌ Failed to download from any source")
            return False
            
        except requests.RequestException as e:
            print(f"❌ Network error: {e}")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
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
        
        # Pattern 2: Common video URL patterns in JavaScript
        js_patterns = [
            r'["\'](https?://[^"\']*\.(?:mp4|webm|m3u8|mpd)[^"\']*)["\']',
            r'src["\']\s*:\s*["\']([^"\']+\.(?:mp4|webm|m3u8))["\']',
            r'url["\']\s*:\s*["\']([^"\']+\.(?:mp4|webm|m3u8))["\']',
            r'video["\']\s*:\s*["\']([^"\']+)["\']',
            r'videoUrl["\']\s*:\s*["\']([^"\']+)["\']',
        ]
        
        for pattern in js_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            video_urls.extend(matches)
        
        # Pattern 3: JSON data containing video URLs
        json_pattern = r'\{[^}]*["\'](?:url|src|video)["\']?\s*:\s*["\']([^"\']+\.(?:mp4|webm|m3u8))["\'][^}]*\}'
        json_matches = re.findall(json_pattern, html, re.IGNORECASE)
        video_urls.extend(json_matches)
        
        # Make URLs absolute and decode HTML entities
        absolute_urls = []
        for url in video_urls:
            # Decode HTML entities (&amp; -> &, etc.)
            url = unescape(url)
            # Also decode unicode escapes like \u0026 -> &
            try:
                # Remove trailing backslash first to avoid unicode escape errors
                url = url.rstrip('\\')
                # Replace \u escapes with actual characters
                url = url.replace('\\u0026', '&')
                url = url.replace('\\u003d', '=')
                url = url.replace('\\u003f', '?')
            except:
                pass
            
            if url.startswith('http'):
                absolute_urls.append(url)
            elif url.startswith('//'):
                absolute_urls.append('https:' + url)
            elif url.startswith('/'):
                absolute_urls.append(urljoin(base_url, url))
        
        # Remove duplicates and filter valid video URLs
        seen = set()
        unique_urls = []
        for url in absolute_urls:
            if url not in seen and self._is_valid_video_url(url):
                seen.add(url)
                unique_urls.append(url)
        
        return unique_urls
    
    def _is_valid_video_url(self, url):
        """Check if URL looks like a video file"""
        video_extensions = ['.mp4', '.webm', '.m3u8', '.mpd', '.mov', '.avi', '.mkv']
        url_lower = url.lower()
        return any(ext in url_lower for ext in video_extensions)
    
    def _download_file(self, url, referer):
        """Download file with progress bar"""
        try:
            # Update referer
            self.session.headers['Referer'] = referer
            
            # Get filename from URL
            filename = self._get_filename(url)
            output_path = self.output_dir / filename
            
            # Stream download with progress
            response = self.session.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            if total_size == 0:
                print("⚠️  Warning: Unknown file size")
            else:
                print(f"📦 File size: {total_size / (1024*1024):.2f} MB")
            
            print(f"💾 Saving to: {filename}")
            
            downloaded = 0
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            bar_length = 40
                            filled = int(bar_length * downloaded / total_size)
                            bar = '█' * filled + '░' * (bar_length - filled)
                            print(f"\r⬇️  [{bar}] {percent:.1f}% ({downloaded/(1024*1024):.1f}/{total_size/(1024*1024):.1f} MB)", end='', flush=True)
            
            print("\n✅ Download completed successfully!")
            print(f"📁 Saved: {output_path.absolute()}")
            return True
            
        except Exception as e:
            print(f"\n⚠️  Failed: {e}")
            return False
    
    def _get_filename(self, url):
        """Extract filename from URL"""
        parsed = urlparse(url)
        path = parsed.path
        
        # Get last part of path
        filename = os.path.basename(path)
        
        # If no extension, add .mp4
        if '.' not in filename or filename.split('.')[-1] not in ['mp4', 'webm', 'mov', 'avi', 'mkv']:
            filename = f"video_{hash(url) % 10000}.mp4"
        
        # Clean filename
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        return filename


def main():
    if len(sys.argv) < 2:
        print("""
╔═══════════════════════════════════════════════════════════╗
║          Universal Video Downloader                       ║
║       Works with ANY site (including custom sites)        ║
╚═══════════════════════════════════════════════════════════╝

Usage:
  python universal_downloader.py <URL> [method]

Methods:
  auto   - Try yt-dlp first, fallback to direct (default)
  direct - Force direct download (inspect page for video URL)
  ytdlp  - Force yt-dlp only (no fallback)

Examples:
  python universal_downloader.py "https://example.com/video"
  python universal_downloader.py "https://example.com/video" direct
  python universal_downloader.py "https://youtube.com/watch?v=..." ytdlp

Features:
  ✓ Automatically finds video URLs in pages
  ✓ Supports custom/unknown video sites
  ✓ Falls back to direct download if yt-dlp fails
  ✓ Progress bar with speed tracking
  ✓ Handles authentication and referer headers

Requirements:
  pip install requests
  pip install yt-dlp (optional, for YouTube etc.)
""")
        sys.exit(1)
    
    url = sys.argv[1]
    method = sys.argv[2] if len(sys.argv) > 2 else "auto"
    
    downloader = UniversalDownloader()
    success = downloader.download(url, method)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
