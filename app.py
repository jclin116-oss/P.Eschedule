import streamlit as st
import pandas as pd
import requests
import feedparser
from bs4 import BeautifulSoup
import ssl

# 1. 解決 SSL 憑證驗證失敗問題
ssl._create_default_https_context = ssl._create_unverified_context

# 設定瀏覽器標頭，避免被網站封鎖
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

st.set_page_config(layout="wide", page_title="政府行程監測")
st.title("政要行程與公告監測儀表板")

# --- 爬蟲函式區 ---

@st.cache_data(ttl=3600)
def fetch_rss(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10, verify=False)
        if response.status_code == 200:
            feed = feedparser.parse(response.content)
            data = [{"標題": e.title, "連結": e.link, "日期": e.published} for e in feed.entries]
            return pd.DataFrame(data)
    except Exception as e:
        st.error(f"RSS 抓取失敗: {e}")
    return pd.DataFrame()

@st.cache_data(ttl=3600)
def fetch_president_schedule():
    url = "https://www.president.gov.tw/Page/37"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10, verify=False)
        # 2. 強制設定編碼為 utf-8 解決亂碼問題
        response.encoding = 'utf-8' 
        
        soup = BeautifulSoup(response.text, 'html.parser')
        data = []
        for unit in soup.select(".unitList"):
            title = unit.select_one(".unitTitle").get_text(strip=True) if unit.select_one(".unitTitle") else "總統/副總統"
            for item in unit.select(".timeIB"):
                data.append({"人物": title, "行程": item.get_text(strip=True)})
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"總統府資料抓取失敗: {e}")
    return pd.DataFrame()

# --- 介面呈現區 ---

# 執行爬蟲
df_moea = fetch_rss("https://www.moea.gov.tw/Mns/populace/news/NewsRSSdetail.aspx?Kind=10")
df_ey = fetch_rss("https://www.ey.gov.tw/RSS_Content2.aspx?PID=c98e07e2-66b4-4c90-a68d-2ef8ef8cf550")
df_po = fetch_president_schedule()

col1, col2 = st.columns(2)

with col1:
    st.subheader("經濟部公告")
    # 3. 安全判斷：確保 DataFrame 存在且不為空
    if df_moea is not None and not df_moea.empty:
        st.dataframe(df_moea, use_container_width=True)
    else:
        st.info("目前無資料。")

    st.subheader("行政院公告")
    if df_ey is not None and not df_ey.empty:
        st.dataframe(df_ey, use_container_width=True)
    else:
        st.info("目前無資料。")

with col2:
    st.subheader("總統/副總統行程")
    if df_po is not None and not df_po.empty:
        st.dataframe(df_po, use_container_width=True)
    else:
        st.info("目前無資料。")
