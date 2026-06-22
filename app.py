import streamlit as st
import pandas as pd
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import urllib3

# 關閉不安全的 HTTPS 請求警告，避免儀表板出現雜訊
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

@st.cache_data(ttl=3600)
def fetch_rss_data(url):
    try:
        # 加入 verify=False 跳過 SSL 驗證
        response = requests.get(url, headers=HEADERS, timeout=10, verify=False)
        if response.status_code != 200:
            return None, f"HTTP Error {response.status_code}"
        
        feed = feedparser.parse(response.content)
        data = []
        for entry in feed.entries:
            pub_date = pd.to_datetime(entry.published, errors='coerce').date()
            data.append({
                "標題": entry.title,
                "連結": entry.link,
                "日期": pub_date
            })
        return pd.DataFrame(data), None
    except Exception as e:
        return None, str(e)

@st.cache_data(ttl=3600)
def get_president_schedule():
    url = "https://www.president.gov.tw/Page/37"
    try:
        # 加入 verify=False 跳過 SSL 驗證
        response = requests.get(url, headers=HEADERS, timeout=10, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')
        schedule_data = []
        
        for unit in soup.select(".unitList"):
            title = unit.select_one(".unitTitle").get_text(strip=True) if unit.select_one(".unitTitle") else "總統/副總統"
            for item in soup.select(".timeIB"):
                schedule_data.append({
                    "人物": title,
                    "行程": item.get_text(strip=True),
                    "日期": datetime.now().date()
                })
        return pd.DataFrame(schedule_data), None
    except Exception as e:
        return None, str(e)
