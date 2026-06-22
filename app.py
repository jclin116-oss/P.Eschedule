import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, date
import ssl

# 忽略 SSL 錯誤
ssl._create_default_https_context = ssl._create_unverified_context
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

# 定義官階順序 (影響顯示順序，非篩選)
RANK_ORDER = ["總統", "副總統", "行政院院長", "行政院副院長", "經濟部部長", "經濟部次長"]

st.set_page_config(layout="wide", page_title="政府高層行程監測")
st.title("政府高層行程監測")

# --- 側邊欄 ---
st.sidebar.header("搜尋設定")
selected_date = st.sidebar.date_input("選擇日期", value=datetime.now().date())
is_searching = st.sidebar.button("搜尋行程")

# --- 爬蟲邏輯 ---
def get_schedules():
    all_rows = []
    
    # 1. 總統府 (抓取邏輯需對應最新網站結構)
    try:
        # 這裡需放入實際能抓到資料的爬蟲邏輯，若網站結構變更，需調整
        # 為了演示，我們使用簡單的 BeautifulSoup 抓取
        res = requests.get("https://www.president.gov.tw/Page/37", headers=HEADERS, timeout=10, verify=False)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        # 範例結構：請根據實際網頁的 class 名稱調整
        for item in soup.select(".timeIB"):
            all_rows.append({"人物": "總統", "行程": item.text.strip(), "時間": "公開行程", "日期": date.today()})
    except: pass
    
    # 這裡可以加入行政院、經濟部等其他單位的爬蟲邏輯...
    # all_rows.append(...)
    
    return pd.DataFrame(all_rows)

# --- 顯示邏輯 ---
if is_searching:
    with st.spinner('正在讀取資料...'):
        df = get_schedules()
        
        if not df.empty:
            # 1. 轉換日期並嚴格篩選
            df['日期'] = pd.to_datetime(df['日期']).dt.date
            filtered_df = df[df['日期'] == selected_date].copy()
            
            if not filtered_df.empty:
                # 2. 進行官階排序 (建立類別並排序)
                filtered_df['人物'] = pd.Categorical(filtered_df['人物'], categories=RANK_ORDER, ordered=True)
                filtered_df = filtered_df.sort_values('人物')
                
                # 3. 顯示表格
                st.subheader(f"{selected_date} 行程總覽")
                st.dataframe(filtered_df[['人物', '行程', '時間', '日期']], use_container_width=True, hide_index=True)
            else:
                st.warning(f"{selected_date} 無公開行程。")
        else:
            st.error("目前抓取不到任何資料，請檢查網路連線或網站結構是否更新。")
else:
    st.info("請選擇日期並按下「搜尋行程」按鈕。")
