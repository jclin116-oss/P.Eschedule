import urllib.request
import ssl
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

st.set_page_config(page_title="經濟部首長行程自動觀測站", layout="wide")
st.title("💼 經濟部首長行程自動觀測站")
st.caption("終極修復版：成功對齊日期，並完整還原首長詳細行程")

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
        
        # 1. 直接鎖定時間軸上的每一個「大項目方塊」
        # 經濟部的結構中，每個行程通常包在一個 class 帶有 item 或 box 的元素內
        timeline_blocks = soup.find_all(lambda tag: tag.name in ['div', 'li'] and tag.find(text=lambda t: t and '月' in t and '日' in t))
        
        if not timeline_blocks:
            timeline_blocks = soup.find_all(['div', 'li'])

        current_date = "未定日期"
        
        for block in timeline_blocks:
            # 優先提取這個區塊內的獨立日期
            date_nodes = block.find_all(lambda tag: tag.name in ['span', 'div', 'p'] and '月' in tag.text and '日' in tag.text and len(tag.text.strip()) < 15)
            if date_nodes:
                # 確保拿到純淨日期，如 "6月23日"
                temp_date = date_nodes[0].text.strip().replace('\n', '').replace(' ', '')
                if temp_date:
                    current_date = temp_date
            
            # 檢查是否包含首長行程
            block_text = block.text.strip()
            if ("部長" in block_text or "次長" in block_text) and "首長類別" not in block_text:
                
                # --- 關鍵修復：不要粗暴 replace 導致文字不見，改用精準內容清洗 ---
                # 我們把網頁行與行之間的空白整理乾淨即可，不刻意刪除關鍵字
                clean_lines = [line.strip() for line in block.text.split('\n') if line.strip()]
                
                # 行程內文通常是所有行中，字數最長的那一串（避開選單與單獨的日期標籤）
                longest_line = ""
                for line in clean_lines:
                    if ("部長" in line or "次長" in line) and len(line) > len(longest_line):
                        longest_line = line
                
                # 如果沒找到最長行，則用整段文字
                event_content = longest_line if longest_line else " ".join(clean_lines)
                
                # 抓取首長頭銜
                leader = "部長" if "部長" in event_content else "次長"
                
                # 抓取地點
                location = "未標註"
                if "地點" in event_content:
                    loc_parts = event_content.split("地點")
                    if len(loc_parts) > 1:
                        location = loc_parts[1].replace("：", "").strip()
                
                # 防止抓到過短的殘缺雜訊
                if len(event_content) > 10:
                    data.append({
                        "日期": current_date,
                        "首長": leader,
                        "行程內容": event_content,
                        "地點": location,
                        "all_text": f"{current_date} {leader} {event_content}"
                    })

        if data:
            df = pd.DataFrame(data).drop_duplicates(subset=['行程內容'])
            st.session_state.schedule_df = df
            st.success(f"🎉 成功同步！已找回完整內容，共 {len(df)} 筆行程。")
        else:
            st.error("未能成功分離內文，請查看下方網頁原始文字。")
            with st.expander("偵錯文字"):
                st.write(soup.text[:2000])
                
    except Exception as e:
        st.error(f"抓取失敗: {e}")

# 2. 資料呈現與過濾
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
