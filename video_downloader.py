#!/usr/bin/env python3
"""
High-Quality Video Downloader
Downloads videos from YouTube and 1000+ sites while preserving quality
"""

import sys
import os
from pathlib import Path
try:
    import yt_dlp
except ImportError:
    print("Error: yt-dlp not installed. Run: pip install yt-dlp")
    sys.exit(1)


class VideoDownloader:
    def __init__(self, output_dir="downloads"):
        """Initialize downloader with output directory"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def download(self, url, quality="best", format_preference=None):
        """
        Download video in highest quality
        
        Args:
            url: Video URL to download
            quality: 'best' (default), '4k', '1080p', '720p', or custom
            format_preference: Specific format like 'mp4', 'webm', or None for best
        """
        # Configure download options
        ydl_opts = {
            'outtmpl': str(self.output_dir / '%(title)s.%(ext)s'),
            'progress_hooks': [self._progress_hook],
            'nocheckcertificate': True,
        }
        
        # Quality selection
        if quality == 'best':
            # Download best video + best audio and merge
            ydl_opts['format'] = 'bestvideo+bestaudio/best'
        elif quality == '4k':
            ydl_opts['format'] = 'bestvideo[height<=2160]+bestaudio/best'
        elif quality == '1080p':
            ydl_opts['format'] = 'bestvideo[height<=1080]+bestaudio/best'
        elif quality == '720p':
            ydl_opts['format'] = 'bestvideo[height<=720]+bestaudio/best'
        else:
            ydl_opts['format'] = quality
        
        # Format preference (mp4, webm, etc.)
        if format_preference:
            ydl_opts['format'] += f'[ext={format_preference}]'
            ydl_opts['merge_output_format'] = format_preference
        else:
            ydl_opts['merge_output_format'] = 'mp4'  # Default to MP4
        
        # Ensure ffmpeg is used for merging best quality
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': format_preference or 'mp4',
        }]
        
        print(f"\n📥 Downloading from: {url}")
        print(f"📁 Output directory: {self.output_dir.absolute()}")
        print(f"🎬 Quality: {quality}")
        print("-" * 60)
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Get video info first
                info = ydl.extract_info(url, download=False)
                print(f"\n📺 Title: {info.get('title', 'Unknown')}")
                print(f"⏱️  Duration: {info.get('duration', 0) // 60}:{info.get('duration', 0) % 60:02d}")
                
                # Available formats info
                if info.get('formats'):
                    print(f"📊 Available formats: {len(info['formats'])}")
                
                print("\n🚀 Starting download...\n")
                
                # Download the video
                ydl.download([url])
                
            print("\n✅ Download completed successfully!")
            return True
            
        except yt_dlp.utils.DownloadError as e:
            print(f"\n❌ Download error: {e}")
            return False
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            return False
    
    def _progress_hook(self, d):
        """Display download progress"""
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', 'N/A')
            speed = d.get('_speed_str', 'N/A')
            eta = d.get('_eta_str', 'N/A')
            print(f"\r⬇️  Progress: {percent} | Speed: {speed} | ETA: {eta}", end='', flush=True)
        elif d['status'] == 'finished':
            print(f"\n✓ Download finished, processing...")
    
    def download_playlist(self, url, quality="best"):
        """Download entire playlist"""
        ydl_opts = {
            'outtmpl': str(self.output_dir / '%(playlist_title)s/%(title)s.%(ext)s'),
            'format': 'bestvideo+bestaudio/best' if quality == 'best' else quality,
            'merge_output_format': 'mp4',
            'progress_hooks': [self._progress_hook],
            'nocheckcertificate': True,
        }
        
        print(f"\n📥 Downloading playlist from: {url}")
        print(f"📁 Output directory: {self.output_dir.absolute()}")
        print("-" * 60)
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                playlist_title = info.get('title', 'Unknown Playlist')
                entries = info.get('entries', [])
                
                print(f"\n📺 Playlist: {playlist_title}")
                print(f"🎬 Videos: {len(entries)}")
                print("\n🚀 Starting playlist download...\n")
                
                ydl.download([url])
                
            print("\n✅ Playlist download completed!")
            return True
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            return False
    
    def get_video_info(self, url):
        """Get video information without downloading"""
        ydl_opts = {'quiet': True, 'no_warnings': True}
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                print(f"\n📺 Video Information")
                print("=" * 60)
                print(f"Title: {info.get('title', 'N/A')}")
                print(f"Uploader: {info.get('uploader', 'N/A')}")
                print(f"Duration: {info.get('duration', 0) // 60}:{info.get('duration', 0) % 60:02d}")
                print(f"Views: {info.get('view_count', 'N/A'):,}" if info.get('view_count') else "Views: N/A")
                print(f"Upload Date: {info.get('upload_date', 'N/A')}")
                print(f"\nDescription:\n{info.get('description', 'N/A')[:200]}...")
                
                # Available formats
                if info.get('formats'):
                    print(f"\n📊 Available Quality Options:")
                    formats_seen = set()
                    for fmt in info['formats']:
                        height = fmt.get('height')
                        ext = fmt.get('ext')
                        if height and f"{height}p-{ext}" not in formats_seen:
                            print(f"  • {height}p ({ext})")
                            formats_seen.add(f"{height}p-{ext}")
                
                return info
                
        except Exception as e:
            print(f"\n❌ Error getting video info: {e}")
            return None


def main():
    """Command-line interface"""
    if len(sys.argv) < 2:
        print("""
╔══════════════════════════════════════════════════════════════╗
║           High-Quality Video Downloader                      ║
║              Powered by yt-dlp                               ║
╚══════════════════════════════════════════════════════════════╝

Usage:
  python video_downloader.py <URL> [quality] [output_dir]

Examples:
  python video_downloader.py "https://youtube.com/watch?v=..."
  python video_downloader.py "https://youtube.com/watch?v=..." 4k
  python video_downloader.py "https://youtube.com/watch?v=..." 1080p my_videos

Quality Options:
  best   - Best available quality (default)
  4k     - Up to 4K resolution
  1080p  - Up to 1080p resolution
  720p   - Up to 720p resolution

Supported Sites:
  YouTube, Vimeo, Dailymotion, Facebook, Twitter, Instagram,
  TikTok, Reddit, Twitch, and 1000+ more sites!

Options:
  info   - Get video information without downloading
           python video_downloader.py info <URL>

Note: Requires ffmpeg installed for best quality merging
""")
        sys.exit(1)
    
    # Check for info command
    if sys.argv[1] == 'info' and len(sys.argv) >= 3:
        url = sys.argv[2]
        downloader = VideoDownloader()
        downloader.get_video_info(url)
        sys.exit(0)
    
    # Parse arguments
    url = sys.argv[1]
    quality = sys.argv[2] if len(sys.argv) > 2 else "best"
    output_dir = sys.argv[3] if len(sys.argv) > 3 else "downloads"
    
    # Create downloader and download
    downloader = VideoDownloader(output_dir)
    
    # Check if it's a playlist
    if 'playlist' in url or 'list=' in url:
        downloader.download_playlist(url, quality)
    else:
        downloader.download(url, quality)


if __name__ == "__main__":
    main()
