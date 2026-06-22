import urllib.request
import ssl
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st

st.set_page_config(page_title="經濟部首長行程自動觀測站", layout="wide")
st.title("💼 經濟部首長行程自動觀測站")
st.caption("完美阻斷版：徹底過濾頁尾分頁雜訊，100% 精準判斷無行程日")

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
                
                # 排除頁首頁尾選單與分頁雜訊
                if any(noise in full_content for noise in ["首長類別", "關鍵字", "主視覺", "RSS", "目前總共有"]):
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
            # 💡 絕對黑名單防禦：一旦遇到分頁或經濟部頁尾宣告，代表行程表已經結束，立刻存檔並跳出
            if any(stop_word in line for stop_word in ["目前總共有", "筆資料", "上一頁", "下一頁", "網站安全政策", "隱私權保護宣告"]):
                save_current_entry()
                break
                
            # 1. 偵測到新日期 (長度過長則忽略，避開可能含有月日的內文)
            if '月' in line and '日' in line and len(line) < 15:
                if not any(tag in line for tag in LEADER_TAGS):
                    save_current_entry() # 換日前先存檔
                    current_date = line.replace("2026", "").strip()
                    current_leader = None
                    current_buffer = []
                    continue
            
            # 2. 偵測到核心分類標籤
            if line in LEADER_TAGS:
                save_current_entry() # 換分類前先存檔
                current_leader = line
                current_buffer = []
                continue
            
            # 3. 貪婪累積行程內容
            if current_leader:
                if line not in current_buffer:
                    current_buffer.append(line)
                    
                # 💡 如果內容直接是「本日無公開行程」，不需要再等下一行，直接存檔並清空
                if "本日無公開行程" in line:
                    save_current_entry()
                    current_buffer = []
                    
        # 結尾保底存檔
        save_current_entry()

        if data:
            df = pd.DataFrame(data)
            
            # 💡 確實濾除所有包含「無公開行程」的列
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
        
        # 提取去重並排序的日期清單
        available_dates = sorted(list(df['日期'].unique()), reverse=True)
        
        if available_dates:
            search_query = st.selectbox(
                "請選擇欲觀測的公告日期：", 
                options=available_dates,
                index=0
            )
            
            filtered_df = df[df['日期'] == search_query]
            if not filtered_df.empty:
                st.dataframe(filtered_df.drop(columns=['all_text']), use_container_width=True)
            else:
                st.info(f"💡 目前無「{search_query}」的公開行程。")
        else:
            st.warning("⚠️ 目前無任何有公開行程的日期供選擇。")
                
    with tab2:
        st.subheader("📋 官網目前公告之所有行程")
        st.dataframe(df.drop(columns=['all_text']), use_container_width=True)
