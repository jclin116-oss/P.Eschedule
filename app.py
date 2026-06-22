import urllib.request
import ssl
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

st.set_page_config(page_title="經濟部首長行程自動觀測站", layout="wide")
st.title("💼 經濟部首長行程自動觀測站")
st.caption("特製版：專門拆解官網時間軸（Timeline）排版結構")

# 1. 一鍵抓取按鈕
if st.button("🔄 一鍵抓取最新行程（並整理成表格）") or 'schedule_df' not in st.session_state:
    
    url = "https://www.moea.gov.tw/Mns/populace/news/MinisterSchedule.aspx?menu_id=42225"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        context = ssl._create_unverified_context()
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, context=context) as response:
            html = response.read()
            
        soup = BeautifulSoup(html, 'html.parser')
        
        # 尋找時間軸的大容器 (通常在 class 包含 schedule 或內容區)
        # 由於政府網站內部常有動態包裝，我們直接抓取最關鍵的「日期標籤」與「行程內容方塊」
        # 經濟部常見的標籤特性：日期通常會包含在特定的 class 或帶有日期的文字中
        
        timeline_items = soup.find_all(['div', 'span', 'li', 'td'])
        
        data = []
        current_date = "未定日期"
        
        # 遍歷網頁所有元素，用邏輯「重新綁定」日期與行程
        for item in timeline_items:
            text = item.text.strip().replace('\n', ' ').replace('\r', '')
            if not text:
                continue
                
            # 判斷是不是日期標籤（例如：包含 "6月23日" 或像截圖中的黃色黃底日期）
            # 這裡用正則或關鍵字特徵來辨識
            if ("月" in text and "日" in text and len(text) < 20) or ("2026" in text and len(text) < 25):
                current_date = text
                continue
                
            # 判斷是不是行程方塊（包含 部長、次長 關鍵字，且有一定字數）
            if ("部長" in text or "次長" in text) and len(text) > 10:
                # 嘗試切分首長、行程與地點
                leader = "部長" if "部長" in text else "次長"
                
                # 抽取地點（通常寫在 地點：後面）
                location = "未標註"
                if "地點" in text:
                    parts = text.split("地點")
                    if len(parts) > 1:
                        location = parts[1].replace("：", "").strip()
                
                data.append({
                    "時間/日期": current_date,
                    "首長": leader,
                    "行程內容": text,
                    "地點": location,
                    "all_text": f"{current_date} {text}"
                })
                
        # 如果精準抓取沒撈到，啟動暴力保底方案：直接把含有首長關鍵字的區塊全抓出來
        if not data:
            cards = soup.find_all(lambda tag: tag.name in ['div', 'li'] and ('部長' in tag.text or '次長' in tag.text))
            for card in cards:
                t = card.text.strip().replace('\n', ' ')
                if len(t) > 15 and "首長類別" not in t:
                    data.append({
                        "時間/日期": "請對照當週",
                        "首長": "部次長",
                        "行程內容": t,
                        "地點": "見內容說明",
                        "all_text": t
                    })

        if data:
            # 去除重複抓取的雜訊行
            df = pd.DataFrame(data).drop_duplicates(subset=['行程內容'])
            st.session_state.schedule_df = df
            st.success(f"🎉 成功解構時間軸！共抓到 {len(df)} 筆即時行程。")
        else:
            st.error("未能成功解析時間軸，請展開下方查看官網目前實際的文字結構。")
            with st.expander("官網文字結構"):
                st.write(soup.text[:2000])
                
    except Exception as e:
        st.error(f"抓取失敗: {e}")

# 2. 呈現與整理資料
if 'schedule_df' in st.session_state and not st.session_state.schedule_df.empty:
    df = st.session_state.schedule_df
    
    tab1, tab2 = st.tabs(["🎯 明日/今日焦點", "📊 當週完整行程表"])
    
    with tab1:
        st.subheader("📌 快速篩選觀測")
        
        now = datetime.now() + timedelta(days=1)
        tomorrow_str = f"{now.month}月{now.day}日" 
        
        search_query = st.text_input("請輸入欲查詢的日期或關鍵字", value=tomorrow_str)
        
        if search_query:
            filtered_df = df[df['all_text'].str.contains(search_query, na=False)]
            if not filtered_df.empty:
                st.dataframe(filtered_df.drop(columns=['all_text']), use_container_width=True)
            else:
                st.info(f"查無「{search_query}」的行程。可能官方尚未上架或當日無公開行程。")
                
    with tab2:
        st.subheader("📋 官網目前公告之所有行程")
        st.dataframe(df.drop(columns=['all_text']), use_container_width=True)
