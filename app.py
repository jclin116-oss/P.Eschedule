import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import urllib3
import re

# 關閉 SSL 憑證警告資訊
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 設定網頁標題與佈局
st.set_page_config(page_title="行政院政要行程撈取工具", layout="wide")
st.title("🏛️ 行政院 - 院長/副院長/秘書長當日行程看板")

# 側邊欄配置：日期篩選器
st.sidebar.header("📅 日期篩選")
target_date = st.sidebar.date_input("選擇抓取日期", datetime.today())

def parse_taiwan_date(date_text):
    """
    將網頁上的民國日期字串（例如: "6月 23日 115年 週二" 或 "06月 23日 115年"）
    轉換為標準的西元日期字串 "YYYY-MM-DD"。若格式不符則回傳 None。
    """
    if not date_text:
        return None
    try:
        # 使用正則表達式提取數字
        month_match = re.search(r'(\d+)\s*月', date_text)
        day_match = re.search(r'(\d+)\s*日', date_text)
        year_match = re.search(r'(\d+)\s*年', date_text)
        
        if month_match and day_match and year_match:
            month = int(month_match.group(1))
            day = int(day_match.group(1))
            tw_year = int(year_match.group(1))
            
            # 民國年轉西元年
            ad_year = tw_year + 1911
            
            return f"{ad_year}-{month:02d}-{day:02d}"
    except Exception:
        pass
    return None

def get_politician_text(url, title, target_date_str):
    """
    針對特定政要的獨立網頁進行行程撈取，並在程式端嚴格篩選目標日期
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7"
    }

    try:
        # 直接請求主網址，由後端程式接手篩選
        res = requests.get(url, headers=headers, timeout=15, verify=False)
        if res.status_code == 200:
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, "html.parser")
            
            outer_blocks = soup.find_all(class_="timeline_block")
            
            if not outer_blocks:
                return []
                
            blocks_text = []
            for block in outer_blocks:
                # 1. 提取並解析網頁日期
                date_tag = block.find(class_=["timeline-date", "newsDate"])
                if not date_tag:
                    continue
                    
                raw_date_text = date_tag.get_text(separator=' ', strip=True)
                parsed_date_str = parse_taiwan_date(raw_date_text)
                
                # 2. 精準比對：如果網頁日期與使用者選的日期（YYYY-MM-DD）不符，直接跳過不抓
                if parsed_date_str != target_date_str:
                    continue
                
                # 3. 提取行程內容文字
                content_tag = block.find(class_="timeline-content")
                if content_tag:
                    content_text = content_tag.get_text(separator="\n", strip=True)
                    if content_text:
                        date_prefix = f"【{raw_date_text}】\n"
                        blocks_text.append(f"【{title}】{date_prefix}{content_text}")
            return blocks_text
        else:
            return [f"【{title}】連線失敗，狀態碼: {res.status_code}"]
    except Exception as e:
        return [f"【{title}】連線發生錯誤: {str(e)}"]

# 點擊執行按鈕
if st.sidebar.button("擷取當日行程"):
    # 將使用者在介面選的日期轉為 "YYYY-MM-DD" 格式
    date_str = target_date.strftime("%Y-%m-%d")
    
    urls = {
        "院長": "https://www.ey.gov.tw/Page/278197D37F0FCDA",
        "副院長": "https://www.ey.gov.tw/Page/EE0A18CCA0C9BC4",
        "秘書長": "https://www.ey.gov.tw/Page/98C9B1D4B4F70B85"
    }
    
    final_output_sections = []
    
    with st.spinner(f"正在擷取並精準篩選 {date_str} 的行程資料..."):
        for title, base_url in urls.items():
            # 傳入 date_str 讓邏輯進行比對過濾
            result_list = get_politician_text(base_url, title, date_str)
            
            if result_list:
                section_text = "\n\n------------------------------\n\n".join(result_list)
            else:
                # 如果過濾後沒有當天行程，就顯示無行程
                section_text = f"【{title}】\n📅 {date_str}\n❌ 今日無公開行程。"
                
            final_output_sections.append(section_text)
        
        st.subheader(f"📋 篩選日期：{date_str} 行程結果")
        
        final_raw_text = "\n\n============================================================\n\n".join(final_output_sections)
            
        st.text_area(
            label="Raw Text 輸出結果", 
            value=final_raw_text, 
            height=650
        )
else:
    st.info("請於左側月曆選擇日期後，點擊「擷取當日行程」按鈕。")
