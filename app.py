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
        context = ssl._create_unverified_context()
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, context=context) as response:
            html = response.read()
            
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('table')
        
        if table:
            data = []
            rows = table.find_all('tr')
            
            for row in rows[1:]:
                # 抓取該行所有的欄位文字
                cols = [td.text.strip().replace('\n', ' ').replace('\r', '') for td in row.find_all('td')]
                if cols:
                    # 動態適應欄位數量，避免欄位名稱對不上的 KeyError Bug
                    row_data = {}
                    for idx, text in enumerate(cols):
                        row_data[f"欄位_{idx+1}"] = text
                    
                    # 同時把整行文字合併成一個隱藏的搜尋欄位，方便後續模糊比對
                    row_data["all_text"] = " ".join(cols)
                    data.append(row_data)
            
            df = pd.DataFrame(data)
            
            # 嘗試重新把前幾個欄位命名為好讀的中文（如果欄位數夠的話）
            if not df.empty and len(df.columns) >= 4:
                rename_dict = {
                    "欄位_1": "時間/日期",
                    "欄位_2": "首長",
                    "欄位_3": "行程內容",
                    "欄位_4": "地點"
                }
                df.rename(columns=rename_dict, inplace=True)
                
            st.session_state.schedule_df = df
            st.success("🎉 資料抓取且整理成功！")
        else:
            st.error("未能找到行程表格，請檢查官網是否改版。")
            
    except Exception as e:
        st.error(f"抓取失敗，原因: {e}")

# 2. 呈現與整理資料
if 'schedule_df' in st.session_state:
    df = st.session_state.schedule_df
    
    tab1, tab2 = st.tabs(["🎯 明日/今日焦點", "📊 當週完整行程表"])
    
    with tab1:
        st.subheader("📌 快速篩選觀測")
        
        # 自動產生明天的日期字串 (06/23) 填入預設值
        tomorrow_str = (datetime.now() + timedelta(days=1)).strftime("%m/%d")
        
        search_query = st.text_input(
            "請輸入欲查詢的日期關鍵字（例如輸入 `06/23` 查看明日，或輸入 `部長`）", 
            value=tomorrow_str
        )
        
        if search_query:
            # 核心修正：直接從萬能的 "all_text" 欄位做模糊搜尋，絕對不會跳出 KeyError
            if "all_text" in df.columns:
                filtered_df = df[df['all_text'].str.contains(search_query, na=False)]
                
                if not filtered_df.empty:
                    # 顯示給使用者看時，把拿來搜尋用的隱藏欄位 "all_text" 濾掉，畫面才乾淨
                    display_df = filtered_df.drop(columns=['all_text'], errors='ignore')
                    st.dataframe(display_df, use_container_width=True)
                else:
                    st.info(f"查無關鍵字「{search_query}」相關的行程。")
            else:
                st.dataframe(df, use_container_width=True)
                
    with tab2:
        st.subheader("📋 官網目前公告之所有行程")
        # 顯示完整表格，同樣濾掉隱藏的搜尋欄位
        final_all_df = df.drop(columns=['all_text'], errors='ignore')
        st.dataframe(final_all_df, use_container_width=True)
        
        csv = final_all_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 下載此表格為 CSV 檔",
            data=csv,
            file_name=f"moea_schedule_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )
