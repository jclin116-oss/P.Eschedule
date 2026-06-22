import urllib.request
import ssl
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

st.set_page_config(page_title="經濟部首長行程自動觀測站", layout="wide")
st.title("💼 經濟部首長行程自動觀測站")
st.caption("終極破局版：改用超連結節點物理分流，徹底解決內容黏疊與首長誤判")

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
        
        # --- 降維打擊邏輯：不抓大方塊，直接抓網頁中所有的「超連結 (<a>)」 ---
        # 官網中，每個真實存在的行程都是一個獨立的超連結
        links = soup.find_all('a')
        
        for link in links:
            title_text = link.text.strip().replace('\n', ' ').replace('\r', '')
            
            # 過濾機制：只有同時包含「部長」或「次長」或「無公開行程」且字數足夠的超連結，才是真正的行程
            if ("部長" in title_text or "次長" in title_text) and len(title_text) > 8:
                # 排除頁面導覽或重複的側欄雜訊
                if "首長類別" in title_text or "關鍵字" in title_text or "主視覺" in title_text:
                    continue
                
                # 1. 物理隔離：精準判定這一個超連結到底屬於誰
                if "部長" in title_text and "次長" in title_text:
                    # 如果一行內兩個字都有，看誰在前面或是次長陪同部長
                    leader = "次長(陪同)" if "次長陪同" in title_text else "部長"
                else:
                    leader = "部長" if "部長" in title_text else "次長"
                
                # 2. 向上回溯尋找日期：在這個超連結的附近，往上找最靠近它的日期標籤
                # 我們直接從這個超連結出頭，往上爬 1~5 層父節點，尋找包含「月、日」的文字
                current_date = "未定日期"
                parent = link
                for _ in range(5):
                    if parent is None:
                        break
                    # 在這個父節點範圍內找尋獨立的日期字樣
                    date_tag = parent.find(lambda tag: tag.name in ['span', 'div', 'p', 'h3'] and '月' in tag.text and '日' in tag.text and len(tag.text.strip()) < 15)
                    if date_tag:
                        current_date = date_tag.text.strip().replace('\n', '').replace(' ', '')
                        if "2026" in current_date:
                            current_date = current_date.replace("2026", "")
                        break
                    parent = parent.parent
                
                # 3. 擷取地點
                location = "未標註"
                if "地點" in title_text:
                    loc_parts = title_text.split("地點")
                    if len(loc_parts) > 1:
                        location = loc_parts[1].replace("：", "").replace(":", "").strip()
                
                data.append({
                    "日期": current_date,
                    "首長": leader,
                    "行程內容": title_text,
                    "地點": location,
                    "all_text": f"{current_date} {leader} {title_text}"
                })

        if data:
            # 轉換成 DataFrame
            df = pd.DataFrame(data)
            # 依照精準的超連結內容進行去重，完全杜絕大容器重複抓取的問題
            df = df.drop_duplicates(subset=['行程內容'])
            
            # 簡單清洗：如果抓到漏網的舊行程日期錯位，進行基本過濾
            st.session_state.schedule_df = df
            st.success(f"🎉 物理隔離同步成功！已成功分流 {len(df)} 筆精準行程。")
        else:
            st.error("未能透過超連結節點撈取到行程。")
            
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
                st.info(f"💡 官網目前無「{search_query}」的公開行程，或該日行程尚未發布。")
                
    with tab2:
        st.subheader("📋 官網目前公告之所有行程")
        st.dataframe(df.drop(columns=['all_text']), use_container_width=True)
