import streamlit as st
import pandas as pd
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# --- 爬蟲核心函式 ---

@st.cache_data(ttl=3600)
def fetch_rss_data(url):
    """通用 RSS 爬蟲"""
    feed = feedparser.parse(url)
    data = []
    for entry in feed.entries:
        # 強制轉換日期格式
        pub_date = pd.to_datetime(entry.published, errors='coerce')
        date_val = pub_date.date() if pd.notnull(pub_date) else datetime.now().date()
        
        data.append({
            "標題": entry.title,
            "連結": entry.link,
            "日期": date_val
        })
    return pd.DataFrame(data)

@st.cache_data(ttl=3600)
def get_president_schedule():
    """總統府行程爬蟲 (針對官網結構優化)"""
    url = "https://www.president.gov.tw/Page/37"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        schedule_data = []
        
        # 根據官網結構：尋找 unitList 區塊
        for unit in soup.select(".unitList"):
            title = unit.select_one(".unitTitle").get_text(strip=True) if unit.select_one(".unitTitle") else "總統/副總統"
            items = unit.select(".timeIB")
            
            # 若無特定行程列表，檢查是否有文字顯示無公開行程
            if not items:
                text_content = unit.get_text(strip=True)
                if "無公開行程" in text_content:
                    schedule_data.append({"人物": title, "行程": "無公開行程", "日期": datetime.now().date()})
            else:
                for item in items:
                    schedule_data.append({"人物": title, "行程": item.get_text(strip=True), "日期": datetime.now().date()})
        
        return pd.DataFrame(schedule_data)
    except:
        return pd.DataFrame(columns=["人物", "行程", "日期"])

# --- UI 介面 ---

st.set_page_config(page_title="政府政要行程監測", layout="wide")
st.title("政要行程與公告監測儀表板")

# 側邊欄篩選
st.sidebar.header("篩選條件")
search_keyword = st.sidebar.text_input("輸入關鍵字 (如：會議、參訪)", "")
selected_date = st.sidebar.date_input("選擇日期", datetime.now())

# 獲取資料
df_moea = fetch_rss_data("https://www.moea.gov.tw/Mns/populace/news/NewsRSSdetail.aspx?Kind=10")
df_ey = fetch_rss_data("https://www.ey.gov.tw/RSS_Content2.aspx?PID=c98e07e2-66b4-4c90-a68d-2ef8ef8cf550")
df_po = get_president_schedule()

# --- 資料顯示邏輯 ---

def apply_and_display(df, title, is_rss=True):
    st.subheader(title)
    
    if df.empty:
        st.info("目前無資料載入。")
        return

    # 1. 日期篩選 (RSS 來源篩選日期，總統府資料則視為當日)
    filtered_df = df.copy()
    if is_rss:
        filtered_df = filtered_df[filtered_df["日期"] == selected_date]
    
    # 2. 關鍵字篩選
    if search_keyword:
        target_col = "標題" if "標題" in filtered_df.columns else "行程"
        filtered_df = filtered_df[filtered_df[target_col].str.contains(search_keyword, case=False, na=False)]

    # 3. 顯示結果
    if not filtered_df.empty:
        st.dataframe(filtered_df, use_container_width=True)
    else:
        st.warning(f"在 {selected_date} 找不到符合條件的資料。")

# 佈局顯示
col1, col2 = st.columns(2)

with col1:
    apply_and_display(df_moea, "經濟部公告", is_rss=True)
    apply_and_display(df_ey, "行政院公告", is_rss=True)

with col2:
    apply_and_display(df_po, "總統/副總統行程", is_rss=False)
