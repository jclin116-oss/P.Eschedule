import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import urllib3

# 關閉 SSL 憑證警告資訊
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 設定網頁標題與佈局
st.set_page_config(page_title="行政院政要行程撈取工具", layout="wide")
st.title("🏛️ 行政院 - 院長/副院長/秘書長當日行程看板")

# 側邊欄配置：日期篩選器
st.sidebar.header("📅 日期篩選")
target_date = st.sidebar.date_input("選擇抓取日期", datetime.today())

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
            
            # 抓取包含日期與內容的完整外殼區塊
            outer_blocks = soup.find_all(class_="timeline_block")
            
            if not outer_blocks:
                return []
                
            blocks_text = []
            for block in outer_blocks:
                # 提取日期文字
                date_tag = block.find(class_=["timeline-date", "newsDate"])
                date_prefix = ""
                if date_tag:
                    date_prefix = f"【{date_tag.get_text(separator=' ', strip=True)}】\n"
                
                # 提取行程內容文字
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
if st.sidebar.button("擷取當日行程"):
    date_str = target_date.strftime("%Y-%m-%d")
    
    # 三位政要的獨立網址來源
    urls = {
        "院長": "https://www.ey.gov.tw/Page/278197D37F0FCDA",
        "副院長": "https://www.ey.gov.tw/Page/EE0A18CCA0C9BC4",
        "秘書長": "https://www.ey.gov.tw/Page/98C9B1D4B4F70B85"
    }
    
    final_output_sections = []
    
    with st.spinner(f"正在查詢 {date_str} 各政要行程..."):
        # 逐一檢查各政要行程
        for title, base_url in urls.items():
            result_list = get_politician_text(base_url, title, date_str)
            
            # 如果該政要當天有行程，就把行程串接起來
            if result_list:
                section_text = "\n\n------------------------------\n\n".join(result_list)
            # 如果該政要當天無行程，則強制輸出「今日無行程」
            else:
                section_text = f"【{title}】\n📅 {date_str}\n❌ 今日無公開行程。"
                
            final_output_sections.append(section_text)
        
        # 呈現結果
        st.subheader(f"📋 篩選日期：{date_str} 行程結果")
        
        # 將三位政要的區塊用明顯的大分隔線連起來
        final_raw_text = "\n\n============================================================\n\n".join(final_output_sections)
            
        st.text_area(
            label="Raw Text 輸出結果", 
            value=final_raw_text, 
            height=650
        )
else:
    st.info("請於左側月曆選擇日期後，點擊「擷取當日行程」按鈕。")
