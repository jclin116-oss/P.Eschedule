import streamlit as st
import pandas as pd
import requests
import feedparser
from bs4 import BeautifulSoup
import ssl
from datetime import datetime

# 初始化設定
ssl._create_default_https_context = ssl._create_unverified_context
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

st.set_page_config(layout="wide", page_title="政要行程監測")
st.title("政要行程與公告監測")

# --- 側邊欄 ---
selected_date = st.sidebar.date_input("選擇日期", value=datetime.now().date())
keyword = st.sidebar.text_input("輸入關鍵字")

# --- 數據抓取 ---

@st.cache_data(ttl=3600)
def get_rss_data(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10, verify=False)
        feed = feedparser.parse(response.content)
        data = []
        for e in feed.entries:
            pub_date = pd.to_datetime(e.published, errors='coerce', utc=True)
            data.append({
                "標題": e.title,
                "連結": e.link,
                "日期": pub_date.date() if pd.notnull(pub_date) else None
            })
        return pd.DataFrame(data)
    except:
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_president_data():
    url = "https://www.president.gov.tw/Page/37"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10, verify=False)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        data = []
        for unit in soup.select(".unitList"):
            title = unit.select_one(".unitTitle").get_text(strip=True) if unit.select_one(".unitTitle") else "總統/副總統"
            for item in soup.select(".timeIB"):
                data.append({"人物": title, "行程": item.get_text(strip=True), "日期": datetime.now().date()})
        return pd.DataFrame(data)
    except:
        return pd.DataFrame()

# --- 處理與顯示 ---

df_moea = get_rss_data("https://www.moea.gov.tw/Mns/populace/news/NewsRSSdetail.aspx?Kind=10")
df_ey = get_rss_data("https://www.ey.gov.tw/RSS_Content2.aspx?PID=c98e07e2-66b4-4c90-a68d-2ef8ef8cf550")
df_po = get_president_data()

def display_section(title, df, date_val, kw):
    st.subheader(title)
    if df.empty:
        st.info("無法讀取資料")
        return

    # 篩選
    mask = df['日期'] == date_val
    filtered_df = df[mask].copy()
    
    if kw:
        search_col = '標題' if '標題' in filtered_df.columns else '行程'
        filtered_df = filtered_df[filtered_df[search_col].str.contains(kw, na=False)]

    # 明確的 if/else 區塊，避免 DeltaGenerator 錯誤
    if not filtered_df.empty:
        st.dataframe(filtered_df, use_container_width=True)
    else:
        st.warning(f"{date_val} 無符合資料")

col1, col2 = st.columns(2)
with col1:
    display_section("經濟部公告", df_moea, selected_date, keyword)
    display_section("行政院公告", df_ey, selected_date, keyword)
with col2:
    display_section("總統/副總統行程", df_po, selected_date, keyword)
