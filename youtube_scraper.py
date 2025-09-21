#!/usr/bin/env python3
"""
YouTube Channel Video Scraper

This script extracts video information from YouTube channels using youtube-dl
and web scraping techniques to get accurate upload dates.

Usage:
    python youtube_scraper.py <channel_url> [options]

Example:
    python youtube_scraper.py https://www.youtube.com/@airnekao --count 20 --output videos.csv
"""

import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional


class ChannelError(Exception):
    """統一的頻道錯誤處理"""
    def __init__(self, message: str, error_type: str):
        self.message = message
        self.error_type = error_type
        super().__init__(message)


class YouTubeScraper:
    def __init__(self):
        self.user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        # Set up output directory
        self.script_dir = Path(__file__).parent
        self.csv_dir = self.script_dir / "yt-csv"
        self.csv_dir.mkdir(exist_ok=True)
        # Find yt-dlp executable
        self.ytdlp_path = self._find_ytdlp()

    def _find_ytdlp(self) -> str:
        """
        Find yt-dlp executable across different platforms

        Returns:
            Path to yt-dlp executable

        Raises:
            FileNotFoundError: If yt-dlp is not found
        """
        # Try system PATH first
        ytdlp_path = shutil.which('yt-dlp')
        if ytdlp_path:
            return ytdlp_path

        # Common installation paths
        possible_paths = [
            # User pip install
            os.path.expanduser('~/.local/bin/yt-dlp'),
            # macOS Homebrew
            '/opt/homebrew/bin/yt-dlp',  # Apple Silicon
            '/usr/local/bin/yt-dlp',     # Intel Mac
            # Windows
            os.path.expanduser('~/AppData/Local/Programs/Python/Python*/Scripts/yt-dlp.exe'),
            # Virtual environment
            './venv/bin/yt-dlp',
            './.venv/bin/yt-dlp',
        ]

        for path in possible_paths:
            if '*' in path:
                # Handle glob patterns for Windows
                import glob
                matches = glob.glob(path)
                if matches:
                    path = matches[0]

            if os.path.isfile(path) and os.access(path, os.X_OK):
                return path

        raise FileNotFoundError("找不到 yt-dlp 工具，請先安裝: pip3 install yt-dlp")
    
    def get_channel_videos(self, channel_url: str, count: int = 10) -> List[Dict]:
        """
        Get video information from a YouTube channel
        
        Args:
            channel_url: YouTube channel URL
            count: Number of videos to fetch (default: 10)
            
        Returns:
            List of video dictionaries with metadata
            
        Raises:
            ChannelError: When channel is not found or other errors occur
        """
        print(f"正在抓取頻道: {channel_url}")
        print(f"獲取影片數量: {count}")
        
        videos_url = f"{channel_url}/videos"
        cmd = [self.ytdlp_path, '--flat-playlist', '--print-json', videos_url]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                stderr = result.stderr.lower()
                
                if any(phrase in stderr for phrase in ['not found', 'does not exist', '404', 'channel not found', 'not available', 'private', 'does not have']):
                    raise ChannelError(f"頻道不存在或無法存取: {channel_url}", "not_found")
                elif any(phrase in stderr for phrase in ['network', 'timeout', 'connection', 'resolve']):
                    raise ChannelError("網路連線問題，請檢查網路設定", "network")
                else:
                    raise ChannelError(f"yt-dlp 執行失敗: {result.stderr.strip()}", "unknown")
                
            lines = result.stdout.strip().split('\n')
            if not lines or not any(line.strip() for line in lines):
                raise ChannelError(f"頻道沒有任何影片或頻道不存在: {channel_url}", "no_videos")
                
            videos = []
            for line in lines[:count]:
                if line.strip():
                    try:
                        video_data = json.loads(line)
                        videos.append(video_data)
                    except json.JSONDecodeError:
                        continue
                        
            if not videos:
                raise ChannelError(f"無法解析頻道影片資料: {channel_url}", "parse_error")
                        
            print(f"成功獲取 {len(videos)} 部影片基本資訊")
            return videos
            
        except subprocess.TimeoutExpired:
            raise ChannelError("請求超時，請檢查網路連線或稍後再試", "timeout")
        except ChannelError:
            raise
        except Exception as e:
            raise ChannelError(f"執行 yt-dlp 時發生未預期錯誤: {e}", "unknown")
    
    def get_video_upload_date(self, video_id: str) -> Optional[str]:
        """
        Get accurate upload date for a video by scraping the YouTube page
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Upload date in YYYY-MM-DD format or None if not found
        """
        url = f'https://www.youtube.com/watch?v={video_id}'
        
        try:
            req = urllib.request.Request(url, headers={'User-Agent': self.user_agent})
            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read().decode('utf-8')
            
            # Search for uploadDate in the page
            upload_match = re.search(r'"uploadDate":"([^"]+)"', html)
            if upload_match:
                full_date = upload_match.group(1)
                date_only = full_date.split('T')[0]
                return date_only
            
            # Fallback to datePublished
            date_match = re.search(r'"datePublished":"([^"]+)"', html)
            if date_match:
                full_date = date_match.group(1)
                date_only = full_date.split('T')[0]
                return date_only
                
            return None
            
        except Exception as e:
            print(f"獲取影片 {video_id} 日期時發生錯誤: {e}")
            return None
    
    def process_videos(self, videos: List[Dict]) -> List[Dict]:
        """
        Process video list to add upload dates
        
        Args:
            videos: List of video dictionaries from youtube-dl
            
        Returns:
            List of processed video dictionaries with upload dates
        """
        processed_videos = []
        
        for i, video in enumerate(videos, 1):
            video_id = video.get('id', '')
            title = video.get('title', '')
            
            print(f"處理影片 {i}/{len(videos)}: {video_id}")
            
            # Get upload date
            upload_date = self.get_video_upload_date(video_id)
            
            processed_video = {
                'title': title,
                'video_id': video_id,
                'url': f"https://www.youtube.com/watch?v={video_id}",
                'view_count': video.get('view_count', 0),
                'duration': video.get('duration', 0),
                'upload_date': upload_date or 'Unknown'
            }
            
            processed_videos.append(processed_video)
            
        return processed_videos
    
    def save_to_csv(self, videos: List[Dict], output_file: str):
        """
        Save video data to CSV file
        
        Args:
            videos: List of video dictionaries
            output_file: Output CSV file name (will be saved to yt-csv directory)
        """
        # Ensure output file is in yt-csv directory
        if not Path(output_file).is_absolute():
            output_path = self.csv_dir / output_file
        else:
            # If absolute path given, still save to yt-csv directory
            output_path = self.csv_dir / Path(output_file).name
        
        fieldnames = ['影片標題', '影片ID', '完整連結', '觀看次數', '影片長度(秒)', '首播日期']
        
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow(fieldnames)
            
            # Write data
            for video in videos:
                row = [
                    f'"{video["title"]}"',  # Quote title to handle commas
                    video['video_id'],
                    video['url'],
                    video['view_count'],
                    video['duration'],
                    video['upload_date']
                ]
                writer.writerow(row)
        
        print(f"資料已儲存到: {output_path}")
    
    def scrape_channel(self, channel_url: str, count: int = 10, output_file: str = None) -> List[Dict]:
        """
        Main scraping function
        
        Args:
            channel_url: YouTube channel URL
            count: Number of videos to fetch
            output_file: Output CSV file path (optional)
            
        Returns:
            List of processed video dictionaries
            
        Raises:
            ChannelError: When channel operations fail
        """
        # Get basic video info (may raise ChannelError)
        videos = self.get_channel_videos(channel_url, count)
        
        # Process videos to add upload dates
        processed_videos = self.process_videos(videos)
        
        # Save to CSV if output file specified
        if output_file:
            self.save_to_csv(processed_videos, output_file)
        
        return processed_videos


def main():
    parser = argparse.ArgumentParser(
        description='YouTube Channel Video Scraper - 抓取 YouTube 頻道影片資訊',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例用法:
  %(prog)s @airnekao --count 20 --output airnekao.csv
  %(prog)s airnekao -c 20 -o airnekao.csv
  %(prog)s "CHIENYU我在路上" --count 10
  %(prog)s "@laosong_channel" -c 15 -o laosong.csv
  %(prog)s https://www.youtube.com/@laosong_channel -c 15 -o laosong.csv

注意事項:
  - 需要安裝 yt-dlp 工具
  - 支援多種輸入格式: @channelname, channelname, 或完整 URL
  - 輸出的 CSV 檔案使用 UTF-8 編碼
  - 腳本會自動處理標題中的逗號問題
        """
    )
    
    parser.add_argument(
        'channel_name',
        help='YouTube 頻道名稱或完整 URL (例如: @channelname 或 https://www.youtube.com/@channelname)'
    )
    
    parser.add_argument(
        '-c', '--count',
        type=int,
        default=10,
        help='要抓取的影片數量 (預設: 10)'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='輸出 CSV 檔案路徑 (可選)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='YouTube Scraper v1.0'
    )
    
    args = parser.parse_args()
    
    # Convert channel name to full URL if needed
    channel_input = args.channel_name.strip()
    
    if channel_input.startswith('https://www.youtube.com/@'):
        # Full URL provided
        channel_url = channel_input
    elif channel_input.startswith('@'):
        # Channel name with @ provided
        channel_url = f"https://www.youtube.com/{channel_input}"
    elif channel_input.startswith('youtube.com/@'):
        # Partial URL without https
        channel_url = f"https://www.{channel_input}"
    else:
        # Assume it's just the channel name without @
        if not channel_input.startswith('@'):
            channel_input = f"@{channel_input}"
        channel_url = f"https://www.youtube.com/{channel_input}"
    
    # Validate final URL format
    if '@' not in channel_url or 'youtube.com' not in channel_url:
        print("錯誤: 無法識別的頻道格式")
        print("支援格式:")
        print("  @channelname")
        print("  channelname")
        print("  https://www.youtube.com/@channelname")
        sys.exit(1)
    
    # Create scraper and check yt-dlp availability
    try:
        scraper = YouTubeScraper()
        print(f"使用 yt-dlp: {scraper.ytdlp_path}")
    except FileNotFoundError as e:
        print(f"錯誤: {e}")
        print("\n安裝方法:")
        print("  pip3 install yt-dlp    # 推薦")
        print("  brew install yt-dlp    # macOS")
        sys.exit(1)
    
    try:
        videos = scraper.scrape_channel(
            channel_url=channel_url,
            count=args.count,
            output_file=args.output
        )
        
        print(f"\n成功處理 {len(videos)} 部影片")
        if args.output:
            print("CSV 檔案已儲存到 yt-csv 目錄")
        else:
            print("如需儲存到檔案，請使用 --output 參數")
            
    except ChannelError as e:
        print(f"\n錯誤: {e.message}")
        
        if e.error_type == "not_found":
            print("建議:")
            print("  - 確認頻道 URL 正確")
            print("  - 檢查頻道是否存在或公開可見")
            print("  - 確保 URL 格式為: https://www.youtube.com/@channelname")
        elif e.error_type == "network":
            print("建議:")
            print("  - 檢查網路連線")
            print("  - 稍後再試")
            print("  - 確認防火牆設定")
        elif e.error_type == "timeout":
            print("建議:")
            print("  - 檢查網路連線速度")
            print("  - 稍後再試")
        
        sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n使用者中斷執行")
        sys.exit(1)
    except Exception as e:
        print(f"執行時發生未預期錯誤: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()