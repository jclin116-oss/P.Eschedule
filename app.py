import streamlit as st
import pandas as pd
import feedparser
import requests
from bs4 import BeautifulSoup

# --- 爬蟲邏輯 (原 spiders.py 的內容) ---

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

# --- Streamlit 介面 ---

st.set_page_config(page_title="政府政要行程儀表板", layout="wide")
st.title("政府政要行程與公告監測")

@st.cache_data(ttl=3600)
def load_moea():
    return fetch_rss_data("https://www.moea.gov.tw/Mns/populace/news/NewsRSSdetail.aspx?Kind=10")

@st.cache_data(ttl=3600)
def load_ey():
    return fetch_rss_data("https://www.ey.gov.tw/RSS_Content2.aspx?PID=c98e07e2-66b4-4c90-a68d-2ef8ef8cf550")

@st.cache_data(ttl=3600)
def load_president():
    return get_president_schedule()

tab1, tab2, tab3 = st.tabs(["經濟部", "行政院", "總統府"])

with tab1:
    st.subheader("經濟部最新公告")
    st.dataframe(load_moea(), use_container_width=True)

with tab2:
    st.subheader("行政院最新公告")
    st.dataframe(load_ey(), use_container_width=True)

with tab3:
    st.subheader("總統/副總統行程")
    df_po = load_president()
    if not df_po.empty:
        st.table(df_po)
    else:
        st.info("目前無公開行程。")
