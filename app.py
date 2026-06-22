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
    try:
        url = "https://www.president.gov.tw/Page/37"
        response = requests.get(url, timeout=10, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.select(".timeIB")
        data = [{"行程": item.text} for item in items]
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"總統府爬蟲錯誤: {e}")
        return pd.DataFrame()

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
