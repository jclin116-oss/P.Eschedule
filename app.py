import streamlit as st
import pandas as pd
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# 設定頁面寬度
st.set_page_config(layout="wide")

# --- 爬蟲邏輯 (加入 User-Agent 以免被封鎖) ---
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

@st.cache_data(ttl=3600)
def fetch_rss_data(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            return None, f"HTTP Error {response.status_code}"
        
        feed = feedparser.parse(response.content)
        data = []
        for entry in feed.entries:
            # 轉換日期格式為 YYYY-MM-DD
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
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        schedule_data = []
        
        # 根據總統府結構
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

# --- UI 介面 ---
st.title("政要行程與公告監測儀表板")

st.sidebar.header("篩選條件")
search_keyword = st.sidebar.text_input("輸入關鍵字", "")
selected_date = st.sidebar.date_input("選擇日期", datetime.now())

# 獲取資料
df_moea, err1 = fetch_rss_data("https://www.moea.gov.tw/Mns/populace/news/NewsRSSdetail.aspx?Kind=10")
df_ey, err2 = fetch_rss_data("https://www.ey.gov.tw/RSS_Content2.aspx?PID=c98e07e2-66b4-4c90-a68d-2ef8ef8cf550")
df_po, err3 = get_president_schedule()

# --- 顯示函數 ---
def display_table(df, error, title, filter_date=True):
    st.subheader(title)
    if error:
        st.error(f"抓取失敗: {error}")
        return
    if df.empty:
        st.info("今日無資料。")
        return

    # 過濾
    filtered_df = df.copy()
    if filter_date:
        filtered_df = filtered_df[filtered_df["日期"] == selected_date]
    if search_keyword:
        target_col = "標題" if "標題" in filtered_df.columns else "行程"
        filtered_df = filtered_df[filtered_df[target_col].str.contains(search_keyword, case=False, na=False)]

    if not filtered_df.empty:
        st.dataframe(filtered_df, use_container_width=True)
    else:
        st.warning("無符合條件的資料。")
        with st.expander("查看原始資料 (除錯用)"):
            st.write(df.head())

col1, col2 = st.columns(2)
with col1:
    display_table(df_moea, err1, "經濟部公告")
    display_table(df_ey, err2, "行政院公告")
with col2:
    display_table(df_po, err3, "總統/副總統行程", filter_date=False)
