import requests
from bs4 import BeautifulSoup
from datetime import datetime

class ScheduleSpider:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def get_ey_schedule(self, target_type="premier"):
        """
        抓取行政院行程
        target_type: "premier" (院長) 或 "vice" (副院長)
        """
        # 根據職位切換網址
        if target_type == "premier":
            url = "https://www.ey.gov.tw/Page/278197D37F0FCDA"
            target_name = "行政院長"
        else:
            url = "https://www.ey.gov.tw/Page/D674EEBCEF9D67A4"
            target_name = "行政副院長"

        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            if res.status_code != 200:
                return []

            soup = BeautifulSoup(res.text, 'html.parser')
            schedules = []

            # 抓取行政院行事曆表格或列表區塊 (請依實際網頁 class 調整)
            # 這裡以常見的 tr 或 list-item 結構做防錯處理
            items = soup.select('tr') or soup.select('.list_item') 
            
            for item in items:
                text = item.get_text(separator=" ").strip()
                if not text or "暫無行程" in text:
                    continue
                
                # 簡單清理文字作為示意
                schedules.append({
                    "官職": target_name,
                    "行程內容": text.replace("\n", " ").split()[0:5], # 擷取部分文字
                    "檢查時間": datetime.now().strftime("%Y-%m-%d %H:%M")
                })
            
            # 若無資料，回傳模擬資料供測試
            return schedules if schedules else [{"官職": target_name, "行程內容": "今日無公開行程", "檢查時間": datetime.now().strftime("%Y-%m-%d %H:%M")}]

        except Exception as e:
            return [{"官職": target_name, "行程內容": f"錯誤: {str(e)}", "檢查時間": datetime.now().strftime("%Y-%m-%d %H:%M")}]