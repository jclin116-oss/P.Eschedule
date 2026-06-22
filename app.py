import urllib.request
import ssl
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

st.set_page_config(page_title="經濟部首長行程自動觀測站", layout="wide")
st.title("💼 經濟部首長行程自動觀測站")
st.caption("直接同步官網 HTML 行程表，一鍵轉為結構化資料")

# 1. 設計「一鍵抓取」按鈕
if st.button("🔄 一鍵抓取最新行程（並整理成表格）") or 'schedule_df' not in st.session_state:
    
    url = "https://www.moea.gov.tw/Mns/populace/news/MinisterSchedule.aspx?menu_id=42225"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        # 解決政府網站阻擋與 SSL 問題
        context = ssl._create_unverified_context()
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, context=context) as response:
            html = response.read()
            
        soup = BeautifulSoup(html, 'html.parser')
        
        # 尋找經濟部網頁的行程表格 (通常為 table)
        table = soup.find('table')
        
        if table:
            data = []
            rows = table.find_all('tr')
            
            # 遍歷表格行（跳過第一行表頭）
            for row in rows[1:]:
                cols = [td.text.strip() for td in row.find_all('td')]
                if len(cols) >= 4:
                    # 依據官網結構抓取：日期時間、首長、行程、地點
                    data.append({
                        "時間/日期": cols[0],
                        "首長": cols[1],
                        "行程內容": cols[2],
                        "地點": cols[3]
                    })
            
            # 轉換為 Pandas DataFrame
            df = pd.DataFrame(data)
            st.session_state.schedule_df = df
            st.success("🎉 資料抓取且整理成功！")
        else:
            st.error("未能找到行程表格，請檢查官網是否改版。")
            
    except Exception as e:
        st.error(f"抓取失敗，原因: {e}")

# 2. 呈現與整理資料
if 'schedule_df' in st.session_state:
    df = st.session_state.schedule_df
    
    # 建立頁籤分流：方便你專注看明日，也能看全部
    tab1, tab2 = st.tabs(["🎯 明日/今日焦點", "📊 當週完整行程表"])
    
    with tab1:
        st.subheader("📌 快速篩選觀測")
        
        # 獲取明天與今天的日期字串（格式可能需依經濟部官網呈現調整，例如：115/06/23 或 2026/06/23）
        # 這裡提供一個關鍵字搜尋輸入框，讓你最彈性地過濾特定日期
        tomorrow_str = (datetime.now() + timedelta(days=1)).strftime("%m/%d")
        
        search_query = st.text_input(
            "請輸入欲查詢的日期關鍵字（例如輸入 `06/23` 查看明日，或輸入 `部長`）", 
            value=tomorrow_str
        )
        
        if search_query:
            # 模糊搜尋包含該日期的行
            filtered_df = df[
                df['時間/日期'].str.contains(search_query, na=False) | 
                df['首長'].str.contains(search_query, na=False) |
                df['行程內容'].str.contains(search_query, na=False)
            ]
            
            if not filtered_df.empty:
                st.dataframe(filtered_df, use_container_width=True)
            else:
                st.info(f"查無關鍵字「{search_query}」相關的行程，可能官方尚未公布。")
                
    with tab2:
        st.subheader("📋 官網目前公告之所有行程")
        # 讓 Streamlit 直接渲染出超漂亮的互動式表格，支援排序與搜尋
        st.dataframe(
            df,
            use_container_width=True,
            column_config={
                "行程內容": st.column_config.TextColumn("行程內容", width="large"),
                "時間/日期": st.column_config.TextColumn("時間/日期", width="medium")
            }
        )
        
        # 提供下載成 CSV 功能
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 下載此表格為 CSV 檔",
            data=csv,
            file_name=f"moea_schedule_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )
