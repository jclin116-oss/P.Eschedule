import urllib.request
import ssl
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st

st.set_page_config(page_title="經濟部首長行程自動觀測站", layout="wide")
st.title("💼 經濟部首長行程自動觀測站")
st.caption("智慧選單版：自動提取官網現存日期，防止無效查詢")

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
            """將目前緩衝區累積的所有內文原封不動打包"""
            if current_buffer and current_leader:
                full_content = "\n".join(current_buffer)
                
                # 排除頁首頁尾選單雜訊
                if any(noise in full_content for noise in ["首長類別", "關鍵字", "主視覺", "RSS"]):
                    return
                
                data.append({
                    "日期": current_date,
                    "首長類別": current_leader,
                    "行程內容": full_content,
                    "all_text": f"{current_date} {current_leader} {full_content}"
                })

        # 核心分類標籤
        LEADER_TAGS = ["部長", "次長", "所屬單位記者會"]

        for line in raw_lines:
            # 1. 偵測到新日期
            if '月' in line and '日' in line and len(line) < 15:
                if not any(tag in line for tag in LEADER_TAGS):
                    save_current_entry()
                    current_date = line.replace("2026", "").strip()
                    current_leader = None
                    current_buffer = []
                    continue
            
            # 2. 偵測到核心分類標籤
            if line in LEADER_TAGS:
                save_current_entry()
                current_leader = line
                current_buffer = []
                continue
                
            # 3. 系統尾端斷點
            if "網站安全政策" in line or "隱私權保護宣告" in line:
                save_current_entry()
                current_leader = None
                current_buffer = []
                continue
            
            # 4. 貪婪累積
            if current_leader:
                if line not in current_buffer:
                    current_buffer.append(line)
                    
                if "本日無公開行程" in line:
                    save_current_entry()
                    current_buffer = []
                    
        # 結尾保底存檔
        save_current_entry()

        if data:
            df = pd.DataFrame(data)
            # 濾除無公開行程的列
            df = df[~df['行程內容'].str.contains("無公開行程", na=False)].reset_index(drop=True)
            # 移除重複項
            df = df.drop_duplicates(subset=['日期', '首長類別', '行程內容'])
            
            st.session_state.schedule_df = df
            st.success(f"🎉 同步成功！共取得 {len(df)} 筆有效行程。")
        else:
            st.error("未能成功解析網頁內文。")
            
    except Exception as e:
        st.error(f"抓取失敗: {e}")

# 3. 資料呈現
if 'schedule_df' in st.session_state and not st.session_state.schedule_df.empty:
    df = st.session_state.schedule_df
    
    tab1, tab2 = st.tabs(["🎯 焦點行程觀測", "📊 當週完整行程表"])
    
    with tab1:
        st.subheader("📌 快速日期篩選")
        
        # 💡 關鍵改動：從現有的資料庫中提取不重複的日期清單，排序後做成下拉選單
        available_dates = sorted(list(df['日期'].unique()), reverse=True)
        
        if available_dates:
            search_query = st.selectbox(
                "請選擇欲觀測的公告日期（選單範圍依官網現存日期動態調整）：", 
                options=available_dates,
                index=0  # 預設選取最新的一天
            )
            
            filtered_df = df[df['日期'] == search_query]
            if not filtered_df.empty:
                st.dataframe(filtered_df.drop(columns=['all_text']), use_container_width=True)
            else:
                st.info(f"💡 目前無「{search_query}」的公開行程。")
        else:
            st.warning("⚠️ 目前無任何可供選擇的日期資料。")
                
    with tab2:
        st.subheader("📋 官網目前公告之所有行程")
        st.dataframe(df.drop(columns=['all_text']), use_container_width=True)
