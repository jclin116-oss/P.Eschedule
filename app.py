import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import ssl
from datetime import datetime

# 設定 SSL 忽略憑證問題
ssl._create_default_https_context = ssl._create_unverified_context
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

# 定義官階 (數字越小越高)
RANK_MAP = {
    "總統": 1,
    "副總統": 2,
    "行政院院長": 3,
    "行政院副院長": 4,
    "經濟部部長": 5,
    "經濟部次長": 6
}

st.set_page_config(layout="wide", page_title="高層行程監測")
st.title("政府高層公開行程彙整")

# --- 側邊欄配置 ---
st.sidebar.header("搜尋設定")
target_date = st.sidebar.date_input("選擇日期", value=datetime.now().date())
is_searching = st.sidebar.button("搜尋行程")

# --- 資料爬取邏輯 ---
@st.cache_data(ttl=3600)
def fetch_all_schedules():
    all_data = []
    
    # 1. 總統府
    try:
        res = requests.get("https://www.president.gov.tw/Page/37", headers=HEADERS, timeout=10, verify=False)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        for unit in soup.select(".unitList"):
            name = unit.select_one(".unitTitle").get_text(strip=True) if unit.select_one(".unitTitle") else "總統"
            # 簡化名稱以匹配 RANK_MAP
            role = "總統" if "總統" in name and "副" not in name else ("副總統" if "副總統" in name else "總統")
            for item in soup.select(".timeIB"):
                all_data.append({"人物": role, "行程": item.get_text(strip=True), "日期": datetime.now().date()}) # 需調整日期邏輯
    except: pass

    # 2. 行政院與經濟部 (依據網站結構抓取)
    # 實際運作時，這裡需要針對各個網頁的 CSS Class 進行具體解析
    # 若該日無資料，需回傳空資料
    
    return pd.DataFrame(all_data)

# --- 顯示邏輯 ---
if is_searching:
    df = fetch_all_schedules()
    
    if not df.empty:
        # 加入排序權重
        df['rank'] = df['人物'].map(RANK_MAP).fillna(99)
        df = df.sort_values('rank')
        
        # 移除排序暫存欄位並顯示
        display_df = df.drop(columns=['rank'])
        st.subheader(f"{target_date} 行程總覽")
        st.table(display_df) # 使用 table 呈現整潔格式
    else:
        st.warning(f"{target_date} 目前無公開行程資料。")
else:
    st.info("請在左側選擇日期後，按下「搜尋行程」按鈕。")
