import feedparser
import requests
from bs4 import BeautifulSoup
import pandas as pd

def fetch_rss_data(url):
    """抓取 RSS 並轉換為 DataFrame"""
    try:
        feed = feedparser.parse(url)
        data = []
        for entry in feed.entries:
            data.append({
                "標題": entry.title,
                "連結": entry.link,
                "日期": entry.published
            })
        return pd.DataFrame(data)
    except Exception as e:
        return pd.DataFrame([{"標題": "資料讀取失敗", "連結": "#", "日期": str(e)}])

def get_president_schedule():
    """抓取總統府行程"""
    url = "https://www.president.gov.tw/Page/37"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        schedule_data = []
        unit_lists = soup.select(".unitList")
        
        for unit in unit_lists:
            title = unit.select_one(".unitTitle").get_text(strip=True) if unit.select_one(".unitTitle") else "未知"
            items = unit.select(".timeIB")
            for item in items:
                content = item.get_text(strip=True)
                schedule_data.append({"人物": title, "行程": content})
        
        return pd.DataFrame(schedule_data) if schedule_data else pd.DataFrame(columns=["人物", "行程"])
    except Exception as e:
        return pd.DataFrame([{"人物": "錯誤", "行程": f"無法載入: {e}"}])
