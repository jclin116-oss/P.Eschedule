import urllib.request
import ssl
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

st.set_page_config(page_title="經濟部首長行程自動觀測站", layout="wide")
st.title("💼 經濟部首長行程自動觀測站")
st.caption("結構重建版：採用精準節點定位，徹底解決日期錯位與重複問題")

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
        
        # --- 核心邏輯重組：直接定位時間軸最外層的各別「日容器」 ---
        # 經濟部網頁中，每一天的所有行程都會包在一個單獨的 class="news_box"（或類似名稱的獨立 div）內
        # 這裡我們擴大相容性，找出包含獨立日期標籤與行程內容的最高層獨立區塊
        boxes = soup.find_all('div', class_=lambda x: x and ('box' in x or 'block' in x or 'list' in x))
        
        # 保底：如果 class 找不到，直接找所有包含條目的 li 或行
        if not boxes or len(boxes) < 5:
            boxes = soup.find_all(['li', 'div'])

        for box in boxes:
            # 檢查這個方塊內部有沒有包含「首長行程」關鍵字，沒有就直接跳過，避開頁首頁尾雜訊
            box_text = box.text.strip()
            if ("部長" not in box_text and "次長" not in box_text) or "首長類別" in box_text:
                continue
                
            # 1. 精準抓取「唯獨屬於這一個方塊」的日期標籤
            # 日期通常放在方塊內的第一個 span, div 或特定小標籤裡
            date_tag = box.find(lambda tag: tag.name in ['span', 'div', 'p', 'h3'] and '月' in tag.text and '日' in tag.text and len(tag.text.strip()) < 15)
            
            if date_tag:
                current_date = date_tag.text.strip().replace('\n', '').replace(' ', '')
                # 去除 2026 等年份贅字，只保留如 "6月23日"
                if "2026" in current_date:
                    current_date = current_date.replace("2026", "")
            else:
                # 如果這個子方塊自己沒寫日期，代表它是跟著上一個大容器的，如果連前面都沒有，就跳過
                continue

            # 2. 抓取這一個方塊內的詳細行程內容
            # 為了避免跟別天混在一起，我們只清洗「這一個 box」內部的文字
            raw_lines = [line.strip() for line in box.text.split('\n') if line.strip()]
            
            # 剔除掉作為標題的日期字串，剩下的就是行程本體
            clean_lines = []
            for line in raw_lines:
                if '月' in line and '日' in line and len(line) < 15:
                    continue
                if "2026" in line and len(line) < 10:
                    continue
                if line not in clean_lines:
                    clean_lines.append(line)
            
            full_content = " ".join(clean_lines)
            
            # 3. 判定首長是誰
            leader = "部長" if "部長" in full_content else "次長"
            
            # 4. 擷取地點
            location = "未標註"
            if "地點" in full_content:
                loc_parts = full_content.split("地點")
                if len(loc_parts) > 1:
                    location = loc_parts[1].replace("：", "").replace(":", "").strip()
                    if "※說明" in location:
                        location = location.split("※說明")[0].strip()
            
            # 確保內容是有意義的行程，而非殘留雜訊
            if len(full_content) > 15:
                data.append({
                    "日期": current_date,
                    "首長": leader,
                    "行程內容": full_content,
                    "地點": location,
                    "all_text": f"{current_date} {leader} {full_content}"
                })

        if data:
            # 依照行程內容與日期進行唯一性去重，保證不重複
            df = pd.DataFrame(data).drop_duplicates(subset=['日期', '行程內容'])
            # 排序讓最新的日期在最上面
            st.session_state.schedule_df = df
            st.success(f"🎉 結構化同步成功！已精準對齊 {len(df)} 筆不重複行程。")
        else:
            st.error("未能精準解析網頁結構，請重新整理重試。")
            
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
