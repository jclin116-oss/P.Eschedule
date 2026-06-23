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
    針對特定政要的獨立網頁進行行程撈取
    """
    # 組合該政要的日期查詢網址
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
            
            # 撈取個別行程區塊
            timeline_blocks = soup.find_all(class_="timeline-content")
            
            if not timeline_blocks:
                return []
                
            blocks_text = []
            for block in timeline_blocks:
                content = block.get_text(separator="\n", strip=True)
                if content:
                    # 直接人工強制加上該網址對應的政要職稱
                    blocks_text.append(f"【{title}】\n{content}")
            return blocks_text
        else:
            return [f"【{title}】連線失敗，狀態碼: {res.status_code}"]
    except Exception as e:
        return [f"【{title}】連線發生錯誤: {str(e)}"]

# 點擊執行按鈕
if st.sidebar.button("擷取原始文本"):
    date_str = target_date.strftime("%Y-%m-%d")
    
    # 定義三位政要的獨立網址來源
    urls = {
        "院長": "https://www.ey.gov.tw/Page/278197D37F0FCDA",
        "副院長": "https://www.ey.gov.tw/Page/EE0A18CCA0C9BC4",
        "秘書長": "https://www.ey.gov.tw/Page/98C9B1D4B4F70B85"
    }
    
    all_outputs = []
    
    with st.spinner(f"正在平行下載 {date_str} 各政要行程資料..."):
        # 依序撈取並組合
        for title, base_url in urls.items():
            result_list = get_politician_text(base_url, title, date_str)
            if result_list:
                all_outputs.extend(result_list)
        
        st.subheader(f"📅 {date_str} 行政院政要官網原始文字內容：")
        
        # 組合最終文本
        if all_outputs:
            final_raw_text = "\n\n==============================\n\n".join(all_outputs)
        else:
            final_raw_text = f"📅 {date_str} 當天此三位政要似乎皆沒有安排公開行程。"
            
        st.text_area(
            label="以下為爬蟲抓到的 Raw Text", 
            value=final_raw_text, 
            height=600
        )
else:
    st.info("請於左側選擇日期後，點擊「擷取原始文本」按鈕。")
