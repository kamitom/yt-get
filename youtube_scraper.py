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
        """
        print(f"正在抓取頻道: {channel_url}")
        print(f"獲取影片數量: {count}")
        
        # Use yt-dlp to get basic video info
        videos_url = f"{channel_url}/videos"
        cmd = [self.ytdlp_path, '--flat-playlist', '--print-json', videos_url]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                print(f"yt-dlp 錯誤: {result.stderr}")
                return []
                
            lines = result.stdout.strip().split('\n')
            videos = []
            
            for line in lines[:count]:
                if line.strip():
                    try:
                        video_data = json.loads(line)
                        videos.append(video_data)
                    except json.JSONDecodeError:
                        continue
                        
            print(f"成功獲取 {len(videos)} 部影片基本資訊")
            return videos
            
        except subprocess.TimeoutExpired:
            print("yt-dlp 執行超時")
            return []
        except Exception as e:
            print(f"執行 yt-dlp 時發生錯誤: {e}")
            return []
    
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
        """
        # Get basic video info
        videos = self.get_channel_videos(channel_url, count)
        
        if not videos:
            print("無法獲取影片資訊")
            return []
        
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
  %(prog)s https://www.youtube.com/@airnekao --count 20 --output airnekao.csv
  %(prog)s https://www.youtube.com/@CHIENYU我在路上 --count 10
  %(prog)s "https://www.youtube.com/@laosong_channel" -c 15 -o laosong.csv

注意事項:
  - 需要安裝 yt-dlp 工具
  - 頻道 URL 需要包含 @ 符號 (例如: @channelname)
  - 輸出的 CSV 檔案使用 UTF-8 編碼
  - 腳本會自動處理標題中的逗號問題
        """
    )
    
    parser.add_argument(
        'channel_url',
        help='YouTube 頻道 URL (例如: https://www.youtube.com/@channelname)'
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
    
    # Validate channel URL
    if '@' not in args.channel_url or 'youtube.com' not in args.channel_url:
        print("錯誤: 請提供有效的 YouTube 頻道 URL (包含 @ 符號)")
        print("範例: https://www.youtube.com/@channelname")
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
            channel_url=args.channel_url,
            count=args.count,
            output_file=args.output
        )
        
        if videos:
            print(f"\n成功處理 {len(videos)} 部影片")
            if args.output:
                print(f"CSV 檔案已儲存到 yt-csv 目錄")
            else:
                print("如需儲存到檔案，請使用 --output 參數")
        else:
            print("未能獲取任何影片資訊")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n使用者中斷執行")
        sys.exit(1)
    except Exception as e:
        print(f"執行時發生錯誤: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()