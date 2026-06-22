import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import ssl

# 基礎設定
ssl._create_default_https_context = ssl._create_unverified_context
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

st.set_page_config(layout="wide", page_title="高層官員行程監測")
st.title("政府高層公開行程彙整")

# --- 爬蟲邏輯 ---

@st.cache_data(ttl=3600)
def get_all_schedules():
    data = []
    
    # 1. 總統府 (總統/副總統)
    try:
        url = "https://www.president.gov.tw/Page/37"
        res = requests.get(url, headers=HEADERS, timeout=10, verify=False)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        for unit in soup.select(".unitList"):
            person = unit.select_one(".unitTitle").get_text(strip=True) if unit.select_one(".unitTitle") else "總統/副總統"
            for item in unit.select(".timeIB"):
                data.append({"人物": person, "行程": item.get_text(strip=True), "時間": "公開行程", "日期": datetime.now().date()})
    except: pass

    # 2. 行政院 (院長/副院長) - 假設結構，若網站改版需調整選擇器
    try:
        urls = {"院長": "https://www.ey.gov.tw/Page/278197D37F0FCDA", "副院長": "https://www.ey.gov.tw/Page/EE0A18CCA0C9BC4"}
        for role, url in urls.items():
            res = requests.get(url, headers=HEADERS, timeout=10, verify=False)
            soup = BeautifulSoup(res.text, 'html.parser')
            # 依據行政院頁面常見結構抓取
            for item in soup.select(".table, .list_style"): 
                data.append({"人物": role, "行程": item.get_text(strip=True), "時間": "參照連結", "日期": datetime.now().date()})
    except: pass

    # 3. 經濟部 (部長/次長)
    try:
        url = "https://www.moea.gov.tw/MNS/populace/news/MinisterSchedule.aspx?menu_id=42225"
        res = requests.get(url, headers=HEADERS, timeout=10, verify=False)
        soup = BeautifulSoup(res.text, 'html.parser')
        # 經濟部表格抓取
        for row in soup.select("table tr"):
            cols = row.find_all("td")
            if len(cols) >= 3:
                data.append({"人物": "經濟部首長", "時間": cols[0].text, "行程": cols[1].text, "日期": datetime.now().date()})
    except: pass

    return pd.DataFrame(data)

# --- UI 呈現 ---

df = get_all_schedules()

# 側邊欄篩選
selected_date = st.sidebar.date_input("選擇日期", value=datetime.now().date())
filter_role = st.sidebar.multiselect("篩選官員", options=df['人物'].unique() if not df.empty else [])

# 顯示區塊
if not df.empty:
    # 進行篩選
    filtered_df = df.copy()
    if filter_role:
        filtered_df = filtered_df[filtered_df['人物'].isin(filter_role)]
    
    st.subheader("行程總覽")
    st.dataframe(filtered_df, use_container_width=True)
else:
    st.warning("目前無法取得行程資料，請檢查網路或官方網站結構是否變更。")
