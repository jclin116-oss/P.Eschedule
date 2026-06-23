import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import urllib3
import re
import pandas as pd

# 關閉 SSL 憑證警告資訊
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 設定網頁標題與佈局
st.set_page_config(page_title="行政院行程解析工具", layout="wide")

# --- 側邊欄配置：日期篩選器 ---
st.sidebar.header("設定抓取日期")
target_date = st.sidebar.date_input("選擇日期", datetime.today())
start_search = st.sidebar.button("開始同步並篩選資料")


def parse_taiwan_date(date_text):
    """
    將網頁上的民國日期字串轉換為標準的西元日期字串 "YYYY-MM-DD"
    """
    if not date_text:
        return None
    try:
        month_match = re.search(r'(\d+)\s*月', date_text)
        day_match = re.search(r'(\d+)\s*日', date_text)
        year_match = re.search(r'(\d+)\s*年', date_text)
        
        if month_match and day_match and year_match:
            month = int(month_match.group(1))
            day = int(day_match.group(1))
            tw_year = int(year_match.group(1))
            ad_year = tw_year + 1911
            return f"{ad_year}-{month:02d}-{day:02d}"
    except Exception:
        pass
    return None


def get_politician_data(url, title, target_date_str):
    """
    撈取特定政要行程，並解析出時間、官階、行程內容三個欄位
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7"
    }

    scraped_data = []

    try:
        res = requests.get(url, headers=headers, timeout=15, verify=False)
        if res.status_code == 200:
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, "html.parser")
            outer_blocks = soup.find_all(class_="timeline_block")
            
            for block in outer_blocks:
                # 1. 日期比對
                date_tag = block.find(class_=["timeline-date", "newsDate"])
                if not date_tag:
                    continue
                    
                raw_date_text = date_tag.get_text(separator=' ', strip=True)
                parsed_date_str = parse_taiwan_date(raw_date_text)
                
                if parsed_date_str != target_date_str:
                    continue
                
                # 2. 解析行程內容與時間
                content_tag = block.find(class_="timeline-content")
                if content_tag:
                    # 抓取區塊內所有文字
                    lines = [line.strip() for line in content_tag.get_text(separator="\n", strip=True).split("\n") if line.strip()]
                    
                    if lines:
                        # 通常第一行是時間（例如：下午02:00 出席... 或 上午09:30）
                        first_line = lines[0]
                        time_match = re.match(r'^([上下]午\d+:\d+(?:~\d+:\d+)?|上午|下午)', first_line)
                        
                        if time_match:
                            time_str = time_match.group(1)
                            # 行程內容移除開頭的時間文字
                            content_str = " ".join(lines).replace(time_str, "", 1).strip()
                        else:
                            time_str = "-"
                            content_str = " ".join(lines)
                            
                        scraped_data.append({
                            "時間": time_str,
                            "官階": title,
                            "行程內容": content_str
                        })
    except Exception:
        pass
        
    # 如果該政要當天完全沒有行程，塞入一筆「無公開行程」
    if not scraped_data:
        scraped_data.append({
            "時間": "-",
            "官階": title,
            "行程內容": "無公開行程"
        })
        
    return scraped_data


# --- 主畫面排版 ---
st.title("🏛️ 行政院 - 行程解析工具")

if start_search:
    date_str = target_date.strftime("%Y-%m-%d")
    
    urls = {
        "院長": "https://www.ey.gov.tw/Page/278197D37F0FCDA",
        "副院長": "https://www.ey.gov.tw/Page/EE0A18CCA0C9BC4",
        "秘書長": "https://www.ey.gov.tw/Page/98C9B1D4B4F70B85"
    }
    
    all_rows = []
    
    with st.spinner(f"正在同步並解析 {date_str} 的行程資料..."):
        # 依序抓取三位政要的資料
        for title, base_url in urls.items():
            politician_rows = get_politician_data(base_url, title, date_str)
            all_rows.extend(politician_rows)
            
        # 轉換為 DataFrame 格式
        df = pd.DataFrame(all_rows)
        
        # 顯示綠色成功提示
        st.success(f"查詢成功！已完成 {date_str} 的行程解析。")
        
        # 以表格形式呈現在畫面上
        st.dataframe(df, use_container_width=True, hide_index=False)
        
        # 產生 CSV 檔案以下載
        csv_data = df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            label="匯出此表格為 CSV",
            data=csv_data,
            file_name=f"行政院政要行程_{date_str}.csv",
            mime="text/csv"
        )
else:
    st.info("請於左側設定抓取日期後，點擊「開始同步並篩選資料」按鈕。")
