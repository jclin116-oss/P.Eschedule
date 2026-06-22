import streamlit as st
import pandas as pd
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# --- 爬蟲函式區 ---

@st.cache_data(ttl=3600)
def fetch_rss_data(url):
    """解析 RSS 資料，並確保日期格式正確"""
    feed = feedparser.parse(url)
    data = []
    for entry in feed.entries:
        # 強制轉換日期字串
        pub_date = pd.to_datetime(entry.published, errors='coerce')
        date_val = pub_date.date() if pd.notnull(pub_date) else None
        
        data.append({
            "標題": entry.title,
            "連結": entry.link,
            "日期": date_val
        })
    return pd.DataFrame(data)

@st.cache_data(ttl=3600)
def get_president_schedule():
    """爬取總統府行程"""
    url = "https://www.president.gov.tw/Page/37"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        schedule_data = []
        
        # 根據結構抓取
        for unit in soup.select(".unitList"):
            title = unit.select_one(".unitTitle").get_text(strip=True) if unit.select_one(".unitTitle") else "總統/副總統"
            # 抓取行程內容
            items = unit.select(".timeIB")
            for item in items:
                schedule_data.append({
                    "人物": title, 
                    "行程": item.get_text(strip=True), 
                    "日期": datetime.now().date() # 預設標記為今日
                })
        return pd.DataFrame(schedule_data)
    except:
        return pd.DataFrame()

# --- 網頁 UI 區 ---

st.set_page_config(page_title="政府政要行程監測", layout="wide")
st.title("政要行程與公告監測儀表板")

st.sidebar.header("篩選條件")
search_keyword = st.sidebar.text_input("輸入關鍵字 (如：會議、參訪)", "")
selected_date = st.sidebar.date_input("選擇日期", datetime.now())

# 載入資料
df_moea = fetch_rss_data("https://www.moea.gov.tw/Mns/populace/news/NewsRSSdetail.aspx?Kind=10")
df_ey = fetch_rss_data("https://www.ey.gov.tw/RSS_Content2.aspx?PID=c98e07e2-66b4-4c90-a68d-2ef8ef8cf550")
df_po = get_president_schedule()

# --- 資料顯示邏輯 ---

def display_section(df, title, filter_by_date=True):
    st.subheader(title)
    
    if df.empty:
        st.warning("目前無法取得該來源資料，請稍後再試。")
        return

    filtered_df = df.copy()

    # 1. 關鍵字篩選
    if search_keyword:
        col = "標題" if "標題" in filtered_df.columns else "行程"
        filtered_df = filtered_df[filtered_df[col].str.contains(search_keyword, case=False, na=False)]

    # 2. 日期篩選 (RSS 來源才進行日期比對)
    if filter_by_date and "日期" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["日期"] == selected_date]

    # 3. 顯示結果
    if not filtered_df.empty:
        st.dataframe(filtered_df, use_container_width=True)
    else:
        st.info(f"在 {selected_date} 無符合條件的資料。")

col1, col2 = st.columns(2)

with col1:
    display_section(df_moea, "經濟部公告")
    display_section(df_ey, "行政院公告")

with col2:
    # 總統府資料不強制日期篩選，以免因為 HTML 無明確日期而導致畫面空白
    display_section(df_po, "總統/副總統行程", filter_by_date=False)
