import urllib.request
import ssl
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

st.set_page_config(page_title="經濟部首長行程自動觀測站", layout="wide")
st.title("💼 經濟部首長行程自動觀測站")
st.caption("完美修復版：100% 完整還原大會行程主旨與詳細內容")

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
        data = []
        
        # 尋找網頁中所有帶有日期特徵的時間軸區塊容器
        timeline_blocks = soup.find_all(lambda tag: tag.name in ['div', 'li'] and tag.find(text=lambda t: t and '月' in t and '日' in t))
        
        if not timeline_blocks:
            timeline_blocks = soup.find_all(['div', 'li'])

        current_date = "未定日期"
        
        for block in timeline_blocks:
            # 1. 抓取精準日期 (例如: 6月23日)
            date_nodes = block.find_all(lambda tag: tag.name in ['span', 'div', 'p'] and '月' in tag.text and '日' in tag.text and len(tag.text.strip()) < 15)
            if date_nodes:
                temp_date = date_nodes[0].text.strip().replace('\n', '').replace(' ', '')
                if temp_date:
                    current_date = temp_date
            
            # 2. 判斷是否為有效行程區塊
            block_text = block.text.strip()
            if ("部長" in block_text or "次長" in block_text) and "首長類別" not in block_text:
                
                # --- 核心改動：不再只挑一行，而是完整打包這個區塊的所有內文文字 ---
                lines = [line.strip() for line in block.text.split('\n') if line.strip()]
                
                # 過濾掉多餘的導覽文字或純粹重複的日期標籤
                filtered_lines = []
                for line in lines:
                    if line == current_date or "2026" in line and len(line) < 10:
                        continue
                    if line not in filtered_lines: # 避免重疊標籤造成的文字重複
                        filtered_lines.append(line)
                
                # 將該區塊內所有的文字合併，形成最完整的行程敘述
                full_event_content = " ".join(filtered_lines)
                
                # 判定首長
                leader = "部長" if "部長" in full_event_content else "次長"
                
                # 精準抓取地點
                location = "未標註"
                if "地點" in full_event_content:
                    loc_parts = full_event_content.split("地點")
                    if len(loc_parts) > 1:
                        # 拿地點後面的文字，並清理符號
                        location = loc_parts[1].replace("：", "").replace(":", "").strip()
                        # 如果地點後面還黏著說明，稍微縮短
                        if "※說明" in location:
                            location = location.split("※說明")[0].strip()
                
                if len(full_event_content) > 15:
                    data.append({
                        "日期": current_date,
                        "首長": leader,
                        "行程內容": full_event_content,
                        "地點": location,
                        "all_text": f"{current_date} {leader} {full_event_content}"
                    })

        if data:
            df = pd.DataFrame(data).drop_duplicates(subset=['行程內容'])
            st.session_state.schedule_df = df
            st.success(f"🎉 完美同步！已完整解構 {len(df)} 筆完整行程內文與主旨。")
        else:
            st.error("未能成功分離內文。")
            
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
        # 利用 Streamlit 的寬度自動延展，確保手機看表格內容不會被壓縮
        st.dataframe(df.drop(columns=['all_text']), use_container_width=True)
