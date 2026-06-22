import requests
from bs4 import BeautifulSoup
from datetime import datetime

class ScheduleSpider:
    def __init__(self):
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}

    def get_all_schedules(self, target_date_str):
        # target_date_str 格式如 "2026-06-22"
        results = []
        
        # 定義我們要監測的目標 (簡化為字典)
        targets = {
            "行政院": "https://www.ey.gov.tw/Page/278197D37F0FCDA",
            "總統府": "https://www.president.gov.tw/Page/37",
            "經濟部": "https://www.moea.gov.tw/Mns/populace/news/NewsRSSDetail.aspx?Kind=10"
        }

        for name, url in targets.items():
            try:
                res = requests.get(url, headers=self.headers, timeout=10)
                res.encoding = 'utf-8'
                # 不使用 XML 解析器，直接用 HTML 解析器處理所有來源，避免解析錯誤
                soup = BeautifulSoup(res.text, 'html.parser')
                
                # 關鍵：在整個網頁文字中搜尋日期 (例如 "06/22" 或 "6/22")
                # 避免過於嚴格的節點篩選，直接抓取包含目標日期的區塊
                text_content = soup.get_text()
                
                # 測試是否有目標日期的蹤跡
                if target_date_str.split("-")[1].lstrip("0") + "/" + target_date_str.split("-")[2].lstrip("0") in text_content:
                    results.append({
                        "官職": name,
                        "行程內容": "偵測到行程資訊",
                        "時間/地點": "詳見連結",
                        "網址": url
                    })
                else:
                    # 如果沒偵測到，也回傳該單位狀態
                    results.append({"官職": name, "行程內容": "無公開行程", "時間/地點": "-", "網址": url})
            except:
                results.append({"官職": name, "行程內容": "連線失敗", "時間/地點": "-", "網址": url})
        
        return results
