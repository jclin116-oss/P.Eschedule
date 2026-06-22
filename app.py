import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import ssl

ssl._create_default_https_context = ssl._create_unverified_context
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

# 定義標準排序 (官階高到低)
RANK_ORDER = ["總統", "副總統", "行政院院長", "行政院副院長", "經濟部部長", "經濟部次長"]

st.set_page_config(layout="wide", page_title="政府高層行程監測")
st.title("政府高層公開行程彙整")

# --- 側邊欄 ---
st.sidebar.header("搜尋設定")
selected_date = st.sidebar.date_input("選擇日期", value=datetime.now().date())
is_searching = st.sidebar.button("搜尋行程")

# --- 爬蟲核心 (區塊掃描) ---
def get_president_schedule():
    """專門處理總統府區塊，確保不把參觀資訊誤認為總統行程"""
    data = []
    try:
        res = requests.get("https://www.president.gov.tw/Page/37", headers=HEADERS, timeout=10, verify=False)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 尋找每一個區塊 (UnitList)
        for unit in soup.select(".unitList"):
            title_el = unit.select_one(".unitTitle")
            if not title_el: continue
            
            title = title_el.get_text(strip=True)
            
            # 判斷是哪位官員
            person = "總統" if "總統" in title and "副" not in title else ("副總統" if "副總統" in title else "其他")
            
            if person in ["總統", "副總統"]:
                # 檢查行程內容
                items = unit.select(".timeIB")
                if items:
                    for item in items:
                        data.append({"人物": person, "行程": item.get_text(strip=True), "時間": "公開行程"})
                else:
                    # 若為空，寫入「無公開行程」
                    data.append({"人物": person, "行程": "無公開行程", "時間": "-"})
                    
    except Exception as e:
        st.error(f"總統府資料抓取失敗: {e}")
    return pd.DataFrame(data)

# --- 顯示邏輯 ---
if is_searching:
    with st.spinner('正在分析行程...'):
        df = get_president_schedule()
        
        if not df.empty:
            # 依照定義的官階排序
            df['人物'] = pd.Categorical(df['人物'], categories=RANK_ORDER, ordered=True)
            df = df.sort_values('人物')
            
            st.subheader(f"{selected_date} 行程總覽")
            st.table(df) # 使用 table 顯示完整列表
        else:
            st.warning("查無行程資料或無法連線。")
else:
    st.info("請選擇日期並按下「搜尋行程」按鈕。")
