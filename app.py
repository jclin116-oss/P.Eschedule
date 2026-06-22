import urllib.request
import ssl
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

st.set_page_config(page_title="經濟部首長行程自動觀測站", layout="wide")
st.title("💼 經濟部首長行程自動觀測站")
st.caption("直接解構官網時間軸元件，自動整理成明日觀測表格")

# 一鍵抓取按鈕
if st.button("🔄 一鍵同步最新行程資料") or 'schedule_df' not in st.session_state:
    
    url = "https://www.moea.gov.tw/Mns/populace/news/MinisterSchedule.aspx?menu_id=42225"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0'}
    
    try:
        context = ssl._create_unverified_context()
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, context=context) as response:
            html = response.read()
            
        soup = BeautifulSoup(html, 'html.parser')
        
        data = []
        
        # 1. 經濟部時間軸的關鍵：每一個日期與其底下的行程，通常會包在一個 class 叫 'news_box' 或類似的清單項目中
        # 我們直接抓取包含整個行程區塊的 li 元素或 div 元素
        items = soup.find_all(['li', 'div'], class_=lambda x: x and ('list' in x or 'box' in x or 'item' in x))
        
        # 如果找不到特定的 class，我們改用最穩固的：尋找網頁中所有的「日期區塊」與其相鄰的「行程區塊」
        # 觀察經濟部結構，日期通常放在 class="date" 或是特定黃底標籤裡，行程放在 class="info" 或 "text"
        timeline_blocks = soup.find_all(lambda tag: tag.name in ['div', 'li'] and tag.find(text=lambda t: t and '月' in t and '日' in t))
        
        if not timeline_blocks:
            # 備用保底：如果連區塊都抓不到，直接全網頁搜尋特定帶有日期的元素
            timeline_blocks = soup.find_all(['div', 'li', 'tr'])

        current_date = "未定日期"
        
        for block in timeline_blocks:
            # 提取當前區塊的文字
            block_text = block.text.strip().replace('\n', ' ').replace('\r', '')
            
            # 檢查這一個大區塊內部有沒有獨立的日期標籤
            # 經濟部網站的特徵：日期常包在 <span> 或 <div> 內，單獨一行
            date_nodes = block.find_all(lambda tag: tag.name in ['span', 'div', 'p'] and '月' in tag.text and '日' in tag.text and len(tag.text.strip()) < 15)
            if date_nodes:
                current_date = date_nodes[0].text.strip().replace('\n', '').replace(' ', '')
            
            # 尋找行程內容
            # 行程方塊通常會包含「部長」或「次長」關鍵字
            if "部長" in block_text or "次長" in block_text:
                # 排除無意義的導覽列或搜尋欄
                if "首長類別" in block_text or "關鍵字" in block_text:
                    continue
                    
                # 萃取首長是誰
                leader = "部長" if "部長" in block_text else "次長"
                
                # 清洗內容文字，移除重複的日期雜質
                clean_content = block_text
                if current_date in clean_content:
                    clean_content = clean_content.replace(current_date, "").strip()
                # 移除年份干擾
                clean_content = clean_content.replace("2026", "").strip()
                
                # 抓取地點
                location = "未標註"
                if "地點" in clean_content:
                    loc_parts = clean_content.split("地點")
                    if len(loc_parts) > 1:
                        location = loc_parts[1].replace("：", "").strip()
                
                data.append({
                    "日期": current_date,
                    "首長": leader,
                    "行程內容": clean_content,
                    "地點": location,
                    "all_text": f"{current_date} {clean_content}"
                })

        if data:
            df = pd.DataFrame(data).drop_duplicates(subset=['行程內容'])
            st.session_state.schedule_df = df
            st.success(f"🎉 成功解構官網時間軸！已同步最新 {len(df)} 筆首長行程。")
        else:
            st.error("暫時抓取不到結構化行程。")
            with st.expander("偵錯專用：查看官網今日純文字流"):
                st.write(soup.text[:3000])
                
    except Exception as e:
        st.error(f"抓取失敗: {e}")

# 2. 資料呈現與過濾
if 'schedule_df' in st.session_state and not st.session_state.schedule_df.empty:
    df = st.session_state.schedule_df
    
    tab1, tab2 = st.tabs(["🎯 明日/今日焦點", "📊 當週完整行程表"])
    
    with tab1:
        st.subheader("📌 快速篩選觀測")
        
        # 自動推算明天日期 (格式：6月23日)
        now = datetime.now() + timedelta(days=1)
        tomorrow_str = f"{now.month}月{now.day}日" 
        
        search_query = st.text_input("請輸入欲查詢的日期（例如 `6月23日`）或首長名稱", value=tomorrow_str)
        
        if search_query:
            filtered_df = df[df['all_text'].str.contains(search_query, na=False)]
            if not filtered_df.empty:
                st.dataframe(filtered_df.drop(columns=['all_text']), use_container_width=True)
            else:
                st.info(f"💡 官網目前無「{search_query}」的公開行程，或行程尚未更新發布。")
                
    with tab2:
        st.subheader("📋 官網目前公告之所有行程")
        st.dataframe(df.drop(columns=['all_text']), use_container_width=True)
