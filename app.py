import streamlit as st
import pandas as pd
import requests
import feedparser
from bs4 import BeautifulSoup
import ssl

# 強制跳過 SSL 驗證
ssl._create_default_https_context = ssl._create_unverified_context

st.title("政要行程與公告監測")

# 除錯訊息：若網頁白屏，此訊息會顯示
st.write("系統初始化中...")

def get_rss(url):
    try:
        response = requests.get(url, timeout=10, verify=False)
        if response.status_code == 200:
            feed = feedparser.parse(response.content)
            data = [{"標題": e.title, "日期": e.published} for e in feed.entries]
            return pd.DataFrame(data)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"RSS 錯誤: {e}")
        return pd.DataFrame()

def get_president():
    url = "https://www.president.gov.tw/Page/37"
    try:
        # 1. 進行請求
        response = requests.get(url, timeout=10, verify=False)
        
        # 2. 【關鍵修正】強制指定編碼為 utf-8，避免亂碼
        response.encoding = 'utf-8'
        
        # 3. 解析內容
        soup = BeautifulSoup(response.text, 'html.parser')
        
        schedule_data = []
        for unit in soup.select(".unitList"):
            title = unit.select_one(".unitTitle").get_text(strip=True) if unit.select_one(".unitTitle") else "總統/副總統"
            # 抓取行程內容
            for item in unit.select(".timeIB"):
                schedule_data.append({
                    "人物": title,
                    "行程": item.get_text(strip=True),
                    "日期": datetime.now().date()
                })
        return pd.DataFrame(schedule_data), None
    except Exception as e:
        return None, str(e)

# 執行爬蟲
with st.spinner("載入中..."):
    df_moea = get_rss("https://www.moea.gov.tw/Mns/populace/news/NewsRSSdetail.aspx?Kind=10")
    df_po = get_president()

# 顯示結果
st.subheader("經濟部公告")
if not df_moea.empty:
    st.table(df_moea.head())
else:
    st.write("無資料")

st.subheader("總統行程")
if not df_po.empty:
    st.table(df_po.head())
else:
    st.write("無資料")
