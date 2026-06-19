# High-Quality Video Downloader 🎬

Download videos from any website in high quality with a beautiful web interface!

**Live Demo:** [Deploy to Vercel](#deployment)

![Video Downloader](https://img.shields.io/badge/Python-3.11-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Features ✨

- ✅ Download in **best quality** (4K, 1080p, 720p, etc.)
- ✅ Supports **1000+ websites** (YouTube, Vimeo, Twitter, TikTok, etc.)
- ✅ **Playlist downloads**
- ✅ **Progress tracking** with speed and ETA
- ✅ **Auto-merge** best video + audio streams
- ✅ Get video info before downloading
- ✅ Simple command-line interface

## 🌟 Features

- ✅ **Web Interface** - Beautiful, modern UI
- ✅ **High Quality** - Preserves original video quality
- ✅ **1000+ Sites** - Works with YouTube, Vimeo, TikTok, and more
- ✅ **Fast Downloads** - Optimized download speeds
- ✅ **No Registration** - Start downloading immediately
- ✅ **Free & Open Source**

## 🚀 Quick Start (Local)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Web App

```bash
python app.py
```

### 3. Open Browser

Visit: **http://localhost:5000**

That's it! Paste a video URL and click download.

## 🌐 Deploy to Vercel

### One-Click Deploy

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/YOUR_USERNAME/YOUR_REPO)

### Manual Deployment

1. **Install Vercel CLI**
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel**
   ```bash
   vercel login
   ```

3. **Deploy**
   ```bash
   vercel
   ```

4. **Production Deploy**
   ```bash
   vercel --prod
   ```

Your app will be live at: `https://your-app.vercel.app`

## 📱 How to Use

1. Open the web interface
2. Paste your video URL
3. Click "Download Video"
4. Wait for processing
5. Click the download link to save

## � Command Line Usage (Alternative)

### Basic Download (Best Quality)

```bash
python video_downloader.py "https://youtube.com/watch?v=VIDEO_ID"
```

### Specify Quality

```bash
# Download in 4K
python video_downloader.py "https://youtube.com/watch?v=VIDEO_ID" 4k

# Download in 1080p
python video_downloader.py "https://youtube.com/watch?v=VIDEO_ID" 1080p

# Download in 720p
python video_downloader.py "https://youtube.com/watch?v=VIDEO_ID" 720p
```

### Custom Output Directory

```bash
python video_downloader.py "https://youtube.com/watch?v=VIDEO_ID" best my_videos
```

### Download Playlists

```bash
python video_downloader.py "https://youtube.com/playlist?list=PLAYLIST_ID"
```

### Get Video Info (Without Downloading)

```bash
python video_downloader.py info "https://youtube.com/watch?v=VIDEO_ID"
```

## Python API Usage 🐍

You can also use it as a library in your Python code:

```python
from video_downloader import VideoDownloader

# Create downloader
downloader = VideoDownloader(output_dir="my_videos")

# Download single video
downloader.download("https://youtube.com/watch?v=...", quality="1080p")

# Download playlist
downloader.download_playlist("https://youtube.com/playlist?list=...")

# Get video info
info = downloader.get_video_info("https://youtube.com/watch?v=...")
```

## Quality Options 🎯

- **best** (default) - Downloads highest quality video + audio and merges them
- **4k** - Up to 4K (2160p) resolution
- **1080p** - Full HD resolution
- **720p** - HD resolution

The tool automatically selects the best video and audio streams and merges them using ffmpeg for maximum quality.

## Supported Sites 🌐

Works with 1000+ sites including:

- YouTube
- Vimeo
- Dailymotion
- Facebook
- Twitter/X
- Instagram
- TikTok
- Reddit
- Twitch
- And many more!

Full list: [yt-dlp supported sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)

## Troubleshooting 🔧

### "ERROR: ffmpeg not found"
Install ffmpeg (see installation section above)

### "ERROR: Unable to download"
- Check if the URL is correct
- Some sites may require authentication
- Try updating yt-dlp: `pip install --upgrade yt-dlp`

### Quality not as expected
- Some videos may not have 4K available
- Use `python video_downloader.py info <URL>` to see available formats

## Advanced Usage 💡

### Download specific format

```python
from video_downloader import VideoDownloader

downloader = VideoDownloader()
downloader.download(
    "https://youtube.com/watch?v=...",
    quality="best",
    format_preference="webm"  # or "mp4"
)
```

## Tips for Best Quality 📝

1. **Always use "best" quality** - This downloads the highest quality streams available
2. **Install ffmpeg** - Required for merging separate video/audio streams
3. **Check available formats** - Use the `info` command to see what's available
4. **Stable internet** - Large files require stable connections

## License 📄

This tool uses [yt-dlp](https://github.com/yt-dlp/yt-dlp) which is unlicense/public domain.

## Credits 🙏

Built with:
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - The best video downloader
- [ffmpeg](https://ffmpeg.org/) - For video/audio processing
