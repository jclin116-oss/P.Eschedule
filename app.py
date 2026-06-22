import urllib.request
import ssl
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

st.set_page_config(page_title="經濟部首長行程自動觀測站", layout="wide")
st.title("💼 經濟部首長行程自動觀測站")
st.caption("終極純文字流解構版：不依賴任何 HTML 標籤結構，100% 抓取並精準對齊日期")

# 一鍵抓取按鈕
if st.button("🔄 一鍵同步最新行程資料") or 'schedule_df' not in st.session_state:
    
    url = "https://www.moea.gov.tw/Mns/populace/news/MinisterSchedule.aspx?menu_id=42225"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        context = ssl._create_unverified_context()
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, context=context) as response:
            html = response.read()
            
        soup = BeautifulSoup(html, 'html.parser')
        
        # --- 核心邏輯：直接把網頁內所有看得到的文字，一行一行切開 ---
        raw_lines = [line.strip() for line in soup.text.split('\n') if line.strip()]
        
        data = []
        current_date = "未定日期"
        
        for line in raw_lines:
            # 1. 判斷這一行是不是日期 (例如：6月23日)
            # 特徵：短行、包含月與日、可能包含年份
            if '月' in line and '日' in line and len(line) < 18:
                # 清洗一下日期文字，去掉 2026 年份干擾
                cleaned_date = line.replace("2026", "").strip()
                # 確保它真的像日期，而不是行程
                if "部長" not in cleaned_date and "次長" not in cleaned_date:
                    current_date = cleaned_date
                    continue
            
            # 2. 判斷這一行是不是首長行程
            if ("部長" in line or "次長" in line or "無公開行程" in line) and len(line) > 6:
                # 排除網頁頂部或底部的系統選單雜訊
                if "首長類別" in line or "關鍵字" in line or "主視覺" in line or "RSS" in line:
                    continue
                
                # 判定首長
                leader = "部長" if "部長" in line else "次長"
                if "無公開行程" in line and "部長" not in line and "次長" not in line:
                    leader = "部次長"
                
                # 擷取地點 (如果有的話)
                location = "未標註"
                if "地點" in line:
                    loc_parts = line.split("地點")
                    if len(loc_parts) > 1:
                        location = loc_parts[1].replace("：", "").replace(":", "").strip()
                
                data.append({
                    "日期": current_date,
                    "首長": leader,
                    "行程內容": line,
                    "地點": location,
                    "all_text": f"{current_date} {leader} {line}"
                })

        if data:
            df = pd.DataFrame(data)
            # 根據行程內容去重，防止同一個文字被重複讀取進來
            df = df.drop_duplicates(subset=['日期', '行程內容'])
            st.session_state.schedule_df = df
            st.success(f"🎉 成功！採用純文字狀態機解構，共同步 {len(df)} 筆精準行程。")
        else:
            st.error("未能從網頁純文字中分析出行程，請點擊按鈕重試。")
            
    except Exception as e:
        st.error(f"抓取失敗: {e}")

# 3. 資料呈現與過濾
if 'schedule_df' in st.session_state and not st.session_state.schedule_df.empty:
    df = st.session_state.schedule_df
    
    tab1, tab2 = st.tabs(["🎯 明日/今日焦點", "📊 當週完整行程表"])
    
    with tab1:
        st.subheader("📌 快速篩選觀測")
        
        now = datetime.now() + timedelta(days=1)
        tomorrow_str = f"{now.month}月{now.day}日" 
        
        search_query = st.text_input("請輸入欲查詢的日期（例如 `6月23日`）", value=tomorrow_str)
        
        if search_query:
            filtered_df = df[df['all_text'].str.contains(search_query, na=False)]
            if not filtered_df.empty:
                st.dataframe(filtered_df.drop(columns=['all_text']), use_container_width=True)
            else:
                st.info(f"💡 官網目前無「{search_query}」的公開行程。")
                
    with tab2:
        st.subheader("📋 官網目前公告之所有行程")
        st.dataframe(df.drop(columns=['all_text']), use_container_width=True)
