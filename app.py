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
st.title("政要行程與公告監測儀表板")

# --- 側邊欄篩選 ---
st.sidebar.header("篩選條件")
selected_date = st.sidebar.date_input("選擇日期", value=datetime.now().date())
keyword = st.sidebar.text_input("輸入關鍵字 (如：會議、參訪)")

# --- 爬蟲資料獲取 ---

@st.cache_data(ttl=3600)
def get_rss_data(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10, verify=False)
        feed = feedparser.parse(response.content)
        data = []
        for e in feed.entries:
            # 嘗試解析 RSS 日期
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
        # 這裡的邏輯是假設當天行程
        for unit in soup.select(".unitList"):
            title = unit.select_one(".unitTitle").get_text(strip=True) if unit.select_one(".unitTitle") else "總統/副總統"
            for item in unit.select(".timeIB"):
                data.append({"人物": title, "行程": item.get_text(strip=True), "日期": datetime.now().date()})
        return pd.DataFrame(data)
    except:
        return pd.DataFrame()

# --- 資料處理與顯示 ---

# 1. 獲取資料
df_moea = get_rss_data("https://www.moea.gov.tw/Mns/populace/news/NewsRSSdetail.aspx?Kind=10")
df_ey = get_rss_data("https://www.ey.gov.tw/RSS_Content2.aspx?PID=c98e07e2-66b4-4c90-a68d-2ef8ef8cf550")
df_po = get_president_data()

# 2. 定義篩選函式
def filter_df(df, date, kw):
    if df.empty: return df
    # 日期篩選
    mask = df['日期'] == date
    df = df[mask]
    # 關鍵字篩選 (僅針對標題或行程欄位)
    if kw:
        search_col = '標題' if '標題' in df.columns else '行程'
        df = df[df[search_col].str.contains(kw, na=False)]
    return df

# 3. 渲染 UI
col1, col2 = st.columns(2)

with col1:
    st.subheader("經濟部公告")
    d1 = filter_df(df_moea, selected_date, keyword)
    st.dataframe(d1, use_container_width=True) if not d1.empty else st.info("無當日公告")

    st.subheader("行政院公告")
    d2 = filter_df(df_ey, selected_date, keyword)
    st.dataframe(d2, use_container_width=True) if not d2.empty else st.info("無當日公告")

with col2:
    st.subheader("總統/副總統行程")
    d3 = filter_df(df_po, selected_date, keyword)
    st.dataframe(d3, use_container_width=True) if not d3.empty else st.info("今日無公開行程或無法讀取")
