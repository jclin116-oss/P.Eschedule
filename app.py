import urllib.request
import ssl
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

st.set_page_config(page_title="經濟部首長行程自動觀測站", layout="wide")
st.title("💼 經濟部首長行程自動觀測站")
st.caption("終極除錯版：精準分流部次長行程，絕不重複疊加")

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
        
        # 1. 深度拆解：先找出時間軸上所有獨立的「單日行程大區塊」
        # 觀察經濟部的 HTML 結構，通常是用帶有年份或日期特徵的區塊包裝
        day_blocks = soup.find_all(lambda tag: tag.name in ['div', 'li'] and tag.find(text=lambda t: t and '月' in t and '日' in t))
        
        if not day_blocks:
            day_blocks = soup.find_all(['div', 'li'])

        for day in day_blocks:
            # 抓取該大區塊對應的日期 (例如: 6月23日)
            date_node = day.find(text=lambda t: t and '月' in t and '日' in t)
            if not date_node:
                continue
            current_date = date_node.strip().replace('\n', '').replace(' ', '')
            
            # --- 關鍵修正：從大區塊中，往下挖出每位首長獨立的「行程小卡片」 ---
            # 官網中，部長、次長的卡片是完全拆開的。我們尋找包含「部長」或「次長」的獨立下層元素
            cards = day.find_all(lambda tag: tag.name in ['div', 'p', 'li'] and ('部長' in tag.text or '次長' in tag.text) and len(tag.text.strip()) > 10)
            
            # 如果下層找不到，再把大區塊自己當作單一卡片處理
            if not cards:
                cards = [day] if ("部長" in day.text or "次長" in day.text) else []
                
            for card in cards:
                card_text = card.text.strip()
                if "首長類別" in card_text or "關鍵字" in card_text:
                    continue
                
                # 判定本卡片到底是誰的行程
                leader = "部長" if "部長" in card_text else "次長"
                
                # 清洗文字：把行與行之間的雜亂空白扭緊，還原成一整段通順網頁
                clean_lines = [l.strip() for l in card_text.split('\n') if l.strip()]
                
                # 排除完全是重複日期或年份的短行雜訊
                final_lines = []
                for l in clean_lines:
                    if l == current_date or ("2026" in l and len(l) < 10):
                        continue
                    if l not in final_lines:
                        final_lines.append(l)
                
                event_content = " ".join(final_lines)
                
                # 精準切出地點
                location = "未標註"
                if "地點" in event_content:
                    loc_parts = event_content.split("地點")
                    if len(loc_parts) > 1:
                        location = loc_parts[1].replace("：", "").replace(":", "").strip()
                        if "※說明" in location:
                            location = location.split("※說明")[0].strip()
                
                if len(event_content) > 15:
                    data.append({
                        "日期": current_date,
                        "首長": leader,
                        "行程內容": event_content,
                        "地點": location,
                        "all_text": f"{current_date} {leader} {event_content}"
                    })

        if data:
            # 轉換為 DataFrame，並透過「行程內容」去除外層容器重複抓取造成的疊加列
            df = pd.DataFrame(data).drop_duplicates(subset=['行程內容', '首長'])
            st.session_state.schedule_df = df
            st.success(f"🎉 徹底修復！成功同步 {len(df)} 筆乾淨、不重疊的首長行程。")
        else:
            st.error("未能精準切分卡片內容。")
            
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
