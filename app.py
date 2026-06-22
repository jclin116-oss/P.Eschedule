import urllib.request
import ssl
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st

st.set_page_config(page_title="經濟部首長行程自動觀測站", layout="wide")
st.title("💼 經濟部首長行程自動觀測站")
st.caption("全景觀測版：包含「無公開行程」在內的所有公告日期皆完整呈現")

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
            """將目前緩衝區累積的所有內文打包"""
            if current_buffer and current_leader:
                # 💡 雙重清洗：把所有可能黏在結尾的頁尾、分頁、歷史查詢雜訊彻底剔除
                clean_lines = []
                for b_line in current_buffer:
                    if any(noise in b_line for noise in ["目前總共有", "筆資料", "上一頁", "下一頁", "網站安全政策", "隱私權保護宣告", "如欲查詢歷史資訊", "首長行程(歷史資料)"]):
                        continue
                    clean_lines.append(b_line)
                
                if not clean_lines:
                    return
                    
                full_content = "\n".join(clean_lines)
                
                # 排除頁首頁尾主選單雜訊
                if any(noise in full_content for noise in ["首長類別", "關鍵字", "主視覺", "RSS"]):
                    return
                
                # 如果被剔除到只剩下空字串，就不儲存
                if not full_content.strip():
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
            # 💡 頁尾絕對防禦線：一看到這些歷史資訊與頁尾文字，立刻存檔並結束整個迴圈
            if any(stop_word in line for stop_word in ["如欲查詢歷史資訊", "首長行程(歷史資料)", "目前總共有", "網站安全政策"]):
                save_current_entry()
                current_leader = None
                current_buffer = []
                break

            # 1. 偵測到新日期
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
                    
                # 💡 終極修正：如果內容是「本日無公開行程」，存檔後除了清空緩衝區，必須立刻切斷當前首長狀態！
                if "本日無公開行程" in line:
                    save_current_entry()
                    current_leader = None  # 確保狀態歸零，後續雜音絕對找不到首長可以黏！
                    current_buffer = []
                    
        # 結尾保底存檔
        save_current_entry()

        if data:
            df = pd.DataFrame(data)
            # 移除重複項
            df = df.drop_duplicates(subset=['日期', '首長類別', '行程內容'])
            
            st.session_state.schedule_df = df
            st.success(f"🎉 究極清洗同步成功！共取得 {len(df)} 筆完美行程紀錄。")
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
                st.info(f"💡 該日期無公開行程。")
        else:
            st.warning("⚠️ 目前無任何公告日期。")
                
    with tab2:
        st.subheader("📋 官網目前公告之所有行程（含無行程日）")
        st.dataframe(df.drop(columns=['all_text']), use_container_width=True)
