import urllib.request
import ssl
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

st.set_page_config(page_title="經濟部首長行程自動觀測站", layout="wide")
st.title("💼 經濟部首長行程自動觀測站")
st.caption("結構收攏優化版：依據官網視覺層級解析，行程完整不切斷")

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
        
        # 讀取全網頁純文字，切成一行一行
        raw_lines = [line.strip() for line in soup.text.split('\n') if line.strip()]
        
        data = []
        current_date = "未定日期"
        current_leader = None
        current_buffer = []
        
        def commit_current_entry():
            """將目前累積的緩衝行程打包寫入資料庫"""
            if current_buffer and current_leader:
                full_content = " ".join(current_buffer)
                
                # 排除系統選單雜訊
                if any(noise in full_content for noise in ["首長類別", "關鍵字", "主視覺", "RSS"]):
                    return
                
                # 擷取地點
                location = "未標註"
                if "地點" in full_content:
                    loc_parts = full_content.split("地點")
                    if len(loc_parts) > 1:
                        location = loc_parts[1].replace("：", "").replace(":", "").strip()
                        if "※說明" in location:
                            location = location.split("※說明")[0].strip()
                
                data.append({
                    "日期": current_date,
                    "首長": current_leader,
                    "行程內容": full_content,
                    "地點": location,
                    "all_text": f"{current_date} {current_leader} {full_content}"
                })

        for line in raw_lines:
            # 1. 識別日期標籤 (例如 "6月23日")
            if '月' in line and '日' in line and len(line) < 15:
                # 遇到新日期，先把上一個首長的行程存起來
                commit_current_entry()
                current_date = line.replace("2026", "").strip()
                current_leader = None
                current_buffer = []
                continue
            
            # 2. 識別首長短標籤 (官網上獨立的「部長」或「次長」小方塊)
            if line in ["部長", "次長"]:
                # 如果同天內已經有別的首長行程在緩衝，先存檔
                commit_current_entry()
                current_leader = line
                current_buffer = []
                continue
                
            # 3. 累積行程內容與說明內容 (不切斷)
            if current_leader and len(line) > 2:
                # 避免重複塞入相同的行
                if line not in current_buffer:
                    current_buffer.append(line)
                    
        # 結尾保底存檔
        commit_current_entry()

        if data:
            df = pd.DataFrame(data)
            # 濾除無公開行程的列
            df = df[~df['行程內容'].str.contains("無公開行程", na=False)].reset_index(drop=True)
            # 去除完全相同的重複列
            df = df.drop_duplicates(subset=['日期', '首長', '行程內容'])
            
            st.session_state.schedule_df = df
            st.success(f"🎉 同步成功！已完美收攏 {len(df)} 筆完整行程內容。")
        else:
            st.error("未能成功解析網頁內文，請點擊按鈕重試。")
            
    except Exception as e:
        st.error(f"抓取失敗: {e}")

# 3. 資料呈現與過濾 (修正欄位名稱，統一使用「日期」)
if 'schedule_df' in st.session_state and not st.session_state.schedule_df.empty:
    df = st.session_state.schedule_df
    
    tab1, tab2 = st.tabs(["🎯 明日/今日焦點", "📊 當週完整行程表"])
    
    with tab1:
        st.subheader("📌 快速篩選觀測")
        search_query = st.text_input("請輸入欲查詢的日期（例如 `6月23日`）", value="6月23日")
        
        if search_query:
            filtered_df = df[df['all_text'].str.contains(search_query, na=False)]
            if not filtered_df.empty:
                st.dataframe(filtered_df.drop(columns=['all_text']), use_container_width=True)
            else:
                st.info(f"💡 目前無「{search_query}」的公開行程。")
                
    with tab2:
        st.subheader("📋 官網目前公告之所有行程")
        st.dataframe(df.drop(columns=['all_text']), use_container_width=True)
