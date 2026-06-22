import streamlit as st
import pandas as pd
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# --- 爬蟲核心 ---

@st.cache_data(ttl=3600)
def fetch_rss_data(url):
    feed = feedparser.parse(url)
    data = []
    for entry in feed.entries:
        # 轉換日期
        pub_date = pd.to_datetime(entry.published, errors='coerce')
        data.append({
            "標題": entry.title,
            "連結": entry.link,
            "日期": pub_date.date() if pd.notnull(pub_date) else None
        })
    return pd.DataFrame(data)

@st.cache_data(ttl=3600)
def get_president_schedule():
    url = "https://www.president.gov.tw/Page/37"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        schedule_data = []
        for unit in soup.select(".unitList"):
            title = unit.select_one(".unitTitle").get_text(strip=True) if unit.select_one(".unitTitle") else "未知"
            for item in unit.select(".timeIB"):
                schedule_data.append({"人物": title, "行程": item.get_text(strip=True), "日期": datetime.now().date()})
        return pd.DataFrame(schedule_data)
    except:
        return pd.DataFrame(columns=["人物", "行程", "日期"])

# --- UI 介面 ---

st.set_page_config(page_title="政府政要行程監測", layout="wide")
st.title("政要行程與公告監測儀表板")

# 側邊欄：搜尋與篩選功能
st.sidebar.header("篩選條件")
search_keyword = st.sidebar.text_input("關鍵字搜尋 (例如: 部長、會議)", "")
selected_date = st.sidebar.date_input("選擇特定日期", datetime.now())

# 獲取原始資料
df_moea = fetch_rss_data("https://www.moea.gov.tw/Mns/populace/news/NewsRSSdetail.aspx?Kind=10")
df_ey = fetch_rss_data("https://www.ey.gov.tw/RSS_Content2.aspx?PID=c98e07e2-66b4-4c90-a68d-2ef8ef8cf550")
df_po = get_president_schedule()

# 資料過濾函數
def apply_filters(df, col_name):
    filtered_df = df.copy()
    # 1. 根據日期過濾 (若 RSS 資料有日期欄位)
    if "日期" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["日期"] == selected_date]
    # 2. 根據關鍵字過濾
    if search_keyword:
        filtered_df = filtered_df[filtered_df[col_name].str.contains(search_keyword, case=False, na=False)]
    return filtered_df

# 顯示版面
col1, col2 = st.columns(2)

with col1:
    st.subheader("經濟部公告")
    df_moea_filtered = apply_filters(df_moea, "標題")
    st.dataframe(df_moea_filtered, use_container_width=True)

    st.subheader("行政院公告")
    df_ey_filtered = apply_filters(df_ey, "標題")
    st.dataframe(df_ey_filtered, use_container_width=True)

with col2:
    st.subheader("總統/副總統行程")
    df_po_filtered = apply_filters(df_po, "行程")
    st.dataframe(df_po_filtered, use_container_width=True)
