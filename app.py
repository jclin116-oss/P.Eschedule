import streamlit as st
import pandas as pd
import requests
import urllib3
from datetime import datetime

# 強制關閉 SSL 驗證，並抑制警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.title("除錯模式：檢查是否啟動")
st.write("程式已順利執行到這裡。")

# 檢查套件匯入
try:
    import feedparser
    from bs4 import BeautifulSoup
    st.write("套件匯入成功")
except Exception as e:
    st.error(f"套件匯入失敗: {e}")

# 測試連線
try:
    url = "https://www.president.gov.tw/Page/37"
    response = requests.get(url, timeout=5, verify=False)
    st.write(f"連線狀態碼: {response.status_code}")
except Exception as e:
    st.error(f"連線失敗: {e}")

st.write("--- 測試結束 ---")
