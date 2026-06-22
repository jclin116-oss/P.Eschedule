import urllib.request
import ssl
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

st.set_page_config(page_title="經濟部首長行程自動觀測站", layout="wide")
st.title("💼 經濟部首長行程自動觀測站")
st.caption("究極完整版：完美分流部長、次長、單位記者會，100% 完整打包內文與說明")

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
        raw_lines = [line.strip() for line in soup.text.split('\n') if line.strip()]
        
        data = []
        current_date = "未定日期"
        current_leader = None
        current_buffer = []
        
        def save_current_entry():
            """將目前緩衝區累積的所有文字，打包存成一筆行程"""
            if current_buffer and current_leader:
                full_content = "\n".join(current_buffer)
                
                # 排除頁首頁尾選單雜訊
                if any(noise in full_content for noise in ["首長類別", "關鍵字", "主視覺", "RSS"]):
                    return
                
                # 獨立抽取地點欄位
                location = "無" if "本日無公開行程" in full_content else "未標註"
                if "地點" in full_content:
                    loc_parts = full_content.split("地點")
                    if len(loc_parts) > 1:
                        location_raw = loc_parts[1].replace("：", "").replace(":", "").strip()
                        if "※說明" in location_raw:
                            location = location_raw.split("※說明")[0].strip()
                        else:
                            location = location_raw.split("\n")[0].strip()
                
                data.append({
                    "日期": current_date,
                    "首長類別": current_leader,
                    "行程內容": full_content,
                    "地點": location,
                    "all_text": f"{current_date} {current_leader} {full_content}"
                })

        # 定義核心標籤清單
        LEADER_TAGS = ["部長", "次長", "所屬單位記者會"]

        for line in raw_lines:
            # 1. 偵測到新日期 (例如 6月18日)
            if '月' in line and '日' in line and len(line) < 15:
                if not any(tag in line for tag in LEADER_TAGS):
                    save_current_entry() # 換日前先存檔上一筆
                    current_date = line.replace("2026", "").strip()
                    current_leader = None
                    current_buffer = []
                    continue
            
            # 2. 偵測到核心分類標籤（部長、次長、所屬單位記者會獨立一行）
            if line in LEADER_TAGS:
                save_current_entry() # 換分類前先存檔
                current_leader = line
                current_buffer = []
                continue
                
            # 3. 偵測到系統尾端斷點，則結束存檔
            if "網站安全政策" in line or "隱私權保護宣告" in line:
                save_current_entry()
                current_leader = None
                current_buffer = []
                continue
            
            # 4. 貪婪累積：只要確認過分類，後續每一行字通通塞進去！
            if current_leader:
                if line not in current_buffer:
                    current_buffer.append(line)
                    
                # 防禦機制：如果是「本日無公開行程」，立刻單獨打包
                if "本日無公開行程" in line:
                    save_current_entry()
                    current_buffer = []
                    
        # 結尾保底存檔
        save_current_entry()

        if data:
            df = pd.DataFrame(data)
            # 濾除無公開行程的閒置行
            df = df[~df['行程內容'].str.contains("無公開行程", na=False)].reset_index(drop=True)
            # 移除重複項
            df = df.drop_duplicates(subset=['日期', '首長類別', '行程內容'])
            
            st.session_state.schedule_df = df
            st.success(f"🎉 終極通關！已無損收攏 {len(df)} 筆完整行程內文（含單位記者會）。")
        else:
            st.error("未能成功解析網頁內文，請點擊按鈕重新整理。")
            
    except Exception as e:
        st.error(f"抓取失敗: {e}")

# 3. 資料呈現與過濾
if 'schedule_df' in st.session_state and not st.session_state.schedule_df.empty:
    df = st.session_state.schedule_df
    
    tab1, tab2 = st.tabs(["🎯 明日/今日焦點", "📊 當週完整行程表"])
    
    with tab1:
        st.subheader("📌 快速篩選觀測")
        search_query = st.text_input("請輸入欲查詢的日期（例如 `6月18日` 或 `6月23日`）", value="6月18日")
        
        if search_query:
            filtered_df = df[df['all_text'].str.contains(search_query, na=False)]
            if not filtered_df.empty:
                st.dataframe(filtered_df.drop(columns=['all_text']), use_container_width=True)
            else:
                st.info(f"💡 目前無「{search_query}」的公開行程。")
                
    with tab2:
        st.subheader("📋 官網目前公告之所有行程")
        st.dataframe(df.drop(columns=['all_text']), use_container_width=True)
