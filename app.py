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
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7'
    }
    
    try:
        context = ssl._create_unverified_context()
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, context=context) as response:
            html = response.read()
            
        soup = BeautifulSoup(html, 'html.parser')
        
        # --- 核心邏輯升級：精準鎖定經濟部的主要內文區塊 ---
        # 經濟部官網的主要內容區塊通常在 class 包含 "content" 或 id 為 "news_box" 的地方
        # 我們直接找出網頁中「所有」的 tr，再過濾出真正有 4 個欄位以上的行程資料
        all_rows = soup.find_all('tr')
        
        data = []
        for row in all_rows:
            cols = [td.text.strip().replace('\n', ' ').replace('\r', '') for td in row.find_all('td')]
            
            # 只有當欄位數量大於等於 3 或 4，且不是表頭時，才判定為行程資料
            if len(cols) >= 3 and "首長" not in cols[0] and "行程" not in cols[0]:
                row_data = {}
                for idx, text in enumerate(cols):
                    row_data[f"欄位_{idx+1}"] = text
                
                row_data["all_text"] = " ".join(cols)
                data.append(row_data)
        
        if data:
            df = pd.DataFrame(data)
            
            # 動態重新命名欄位
            rename_dict = {
                "欄位_1": "時間/日期",
                "欄位_2": "首長",
                "欄位_3": "行程內容",
                "欄位_4": "地點"
            }
            df.rename(columns=rename_dict, inplace=True)
            st.session_state.schedule_df = df
            st.success(f"🎉 資料抓取且整理成功！共抓到 {len(df)} 筆行程。")
        else:
            # 如果還是空的，列印出網頁部分的文字以利除錯
            st.error("未能解析到行程資料。")
            with st.expander("查看網頁原始文字摘要（偵錯用）"):
                st.text(soup.text[:1000])
            
    except Exception as e:
        st.error(f"抓取失敗，原因: {e}")

# 2. 呈現與整理資料
if 'schedule_df' in st.session_state and not st.session_state.schedule_df.empty:
    df = st.session_state.schedule_df
    
    tab1, tab2 = st.tabs(["🎯 明日/今日焦點", "📊 當週完整行程表"])
    
    with tab1:
        st.subheader("📌 快速篩選觀測")
        
        # 配合網站顯示格式，自動生成今天的「6月23日」或「6/23」格式
        now = datetime.now() + timedelta(days=1)
        tomorrow_str_1 = now.strftime("%m/%d")         # 06/23
        tomorrow_str_2 = f"{now.month}月{now.day}日"    # 6月23日
        
        search_query = st.text_input(
            "請輸入欲查詢的日期關鍵字（支援 6月23日 或 06/23 格式）", 
            value=tomorrow_str_2
        )
        
        if search_query:
            if "all_text" in df.columns:
                filtered_df = df[df['all_text'].str.contains(search_query, na=False)]
                
                if not filtered_df.empty:
                    display_df = filtered_df.drop(columns=['all_text'], errors='ignore')
                    st.dataframe(display_df, use_container_width=True)
                else:
                    st.info(f"查無關鍵字「{search_query}」相關的行程。官網可能尚未排定或更新。")
            else:
                st.dataframe(df, use_container_width=True)
                
    with tab2:
        st.subheader("📋 官網目前公告之所有行程")
        final_all_df = df.drop(columns=['all_text'], errors='ignore')
        st.dataframe(final_all_df, use_container_width=True)
        
        csv = final_all_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 下載此表格為 CSV 檔",
            data=csv,
            file_name=f"moea_schedule_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )
