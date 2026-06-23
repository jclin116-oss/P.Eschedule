import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import urllib3

# 關閉 SSL 憑證警告資訊
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 設定網頁標題與佈局
st.set_page_config(page_title="行政院政要行程撈取工具", layout="wide")
st.title("🏛️ 行政院 - 院長/副院長/秘書長行程原始純文字撈取")

# 側邊欄配置
st.sidebar.header("設定抓取日期")
target_date = st.sidebar.date_input("選擇日期", datetime.today())

def get_politician_text(url, title, date_str):
    """
    針對特定政要的獨立網頁進行行程與日期撈取
    """
    full_url = f"{url}?SDate={date_str}&EDate={date_str}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7"
    }

    try:
        res = requests.get(full_url, headers=headers, timeout=15, verify=False)
        if res.status_code == 200:
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, "html.parser")
            
            # 1. 改為抓取同時包含日期與內容的完整外殼區塊
            outer_blocks = soup.find_all(class_="timeline_block")
            
            if not outer_blocks:
                return []
                
            blocks_text = []
            for block in outer_blocks:
                # 2. 提取日期文字 (從 class="timeline-date" 或 "newsDate" 內提取)
                date_tag = block.find(class_=["timeline-date", "newsDate"])
                date_prefix = ""
                if date_tag:
                    # 將 u 和 i 標籤內的文字（例如：6月、23日、115年、週二）串接起來，並用空格隔開
                    date_prefix = f"【{date_tag.get_text(separator=' ', strip=True)}】\n"
                
                # 3. 提取行程內容文字
                content_tag = block.find(class_="timeline-content")
                if content_tag:
                    content_text = content_tag.get_text(separator="\n", strip=True)
                    if content_text:
                        # 組合 職稱 + 日期 + 行程內文
                        blocks_text.append(f"【{title}】{date_prefix}{content_text}")
            return blocks_text
        else:
            return [f"【{title}】連線失敗，狀態碼: {res.status_code}"]
    except Exception as e:
        return [f"【{title}】連線發生錯誤: {str(e)}"]

# 點擊執行按鈕
if st.sidebar.button("擷取原始文本"):
    date_str = target_date.strftime("%Y-%m-%d")
    
    # 三位政要的獨立網址來源
    urls = {
        "院長": "https://www.ey.gov.tw/Page/278197D37F0FCDA",
        "副院長": "https://www.ey.gov.tw/Page/EE0A18CCA0C9BC4",
        "秘書長": "https://www.ey.gov.tw/Page/98C9B1D4B4F70B85"
    }
    
    all_outputs = []
    
    with st.spinner(f"正在平行下載 {date_str} 各政要行程資料..."):
        for title, base_url in urls.items():
            result_list = get_politician_text(base_url, title, date_str)
            if result_list:
                all_outputs.extend(result_list)
        
        st.subheader(f"📅 {date_str} 行政院政要官網原始文字內容：")
        
        if all_outputs:
            final_raw_text = "\n\n==============================\n\n".join(all_outputs)
        else:
            final_raw_text = f"📅 {date_str} 當天此三位政要公佈的行程似乎皆無資料。"
            
        st.text_area(
            label="以下為爬蟲抓到的 Raw Text", 
            value=final_raw_text, 
            height=600
        )
else:
    st.info("請於左側選擇日期後，點擊「擷取原始文本」按鈕。")
