# YouTube Channel Video Scraper

一個用於抓取 YouTube 頻道影片資訊的 Python 工具，可以獲取準確的首播日期和完整的影片元數據。

## 功能特色

- 抓取 YouTube 頻道最新影片資訊
- 獲取準確的首播日期（不依賴估算）
- 輸出為 CSV 格式，方便後續分析
- 自動處理標題中的逗號問題
- 支援自訂影片數量

## 安裝需求

### 系統需求
- Python 3.6+
- yt-dlp 工具 (更新的 youtube-dl 替代品)

### 安裝 yt-dlp

**推薦方法 (跨平台)**:
```bash
pip3 install yt-dlp
```

**各平台安裝方法**:
```bash
# macOS (使用 Homebrew)
brew install yt-dlp

# Ubuntu 22.04+ / Debian
pip3 install yt-dlp
# 或
sudo apt install yt-dlp  # 較舊版本

# 使用虛擬環境 (推薦)
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate     # Windows
pip install yt-dlp
```

## 使用方法

### 基本用法
```bash
python youtube_scraper.py https://www.youtube.com/@channelname
```

### 指定影片數量
```bash
python youtube_scraper.py https://www.youtube.com/@channelname --count 20
```

### 儲存到 CSV 檔案
```bash
python youtube_scraper.py https://www.youtube.com/@channelname --count 15 --output videos.csv
```

### 查看幫助
```bash
python youtube_scraper.py --help
```

## 使用範例

```bash
# 抓取旅圖奶爸頻道最新 20 部影片
python youtube_scraper.py https://www.youtube.com/@airnekao --count 20 --output airnekao.csv

# 抓取 CHIENYU 頻道最新 10 部影片
python youtube_scraper.py "https://www.youtube.com/@CHIENYU我在路上" --count 10

# 抓取老宋頻道最新 15 部影片並儲存
python youtube_scraper.py https://www.youtube.com/@laosong_channel -c 15 -o laosong.csv
```

## 使用虛擬環境

### 建立虛擬環境
```bash
cd ~/Downloads/yt-get
python3 -m venv .venv
source .venv/bin/activate
```

### 在虛擬環境中執行
```bash
source .venv/bin/activate
python youtube_scraper.py <channel_url> [options]
```

## 輸出格式

CSV 檔案會自動儲存到 `yt-csv/` 目錄內，包含以下欄位：
- 影片標題
- 影片ID
- 完整連結
- 觀看次數
- 影片長度(秒)
- 首播日期

**注意**: 無論 `--output` 參數指定什麼路徑，檔案都會儲存到專案的 `yt-csv/` 目錄內。

## 注意事項

1. **頻道 URL 格式**: 必須使用 `@` 格式的頻道 URL
   - 正確: `https://www.youtube.com/@channelname`
   - 錯誤: `https://www.youtube.com/channel/UCxxxxx`

2. **執行時間**: 獲取日期資訊需要逐一查詢影片頁面，可能需要一些時間

3. **網路依賴**: 需要穩定的網路連線來存取 YouTube

4. **編碼**: 輸出的 CSV 檔案使用 UTF-8 編碼

## 故障排除

### yt-dlp 找不到
```bash
# 確認 yt-dlp 已安裝
which yt-dlp
yt-dlp --version

# 如果沒有，請安裝
pip3 install yt-dlp

# macOS 使用 Homebrew
brew install yt-dlp
```

### 權限問題
```bash
# 確保腳本有執行權限
chmod +x youtube_scraper.py
```

### 頻道 URL 錯誤
- 確認 URL 包含 `@` 符號
- 確認頻道存在且可公開存取

## 授權

此工具僅用於學習和研究目的，請遵守 YouTube 的使用條款。