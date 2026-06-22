import requests
from bs4 import BeautifulSoup
import urllib3
from urllib3.exceptions import InsecureRequestWarning

urllib3.disable_warnings(InsecureRequestWarning)

class ScheduleSpider:
    def __init__(self):
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

    def _is_valid_date(self, text, clean_date):
        """檢查文本是否包含目標日期的關鍵字（月/日）"""
        month, day = str(int(clean_date[4:6])), str(int(clean_date[6:8]))
        # 檢查是否含有 "6/22" 或 "6月22日"
        return f"{month}/{day}" in text or f"{month}月{day}日" in text

    def get_ey_schedule(self, clean_date):
        """行政院：精準 RSS 比對"""
        schedules = []
        for pid, name in [("c98e07e2-66b4-4c90-a68d-2ef8ef8cf550", "行政院長"), ("018a38fc-8461-4687-9bc1-35606d50db8a", "行政副院長")]:
            url = f"https://www.ey.gov.tw/RSS_Content2.aspx?PID={pid}&SD={clean_date}&ED={clean_date}"
            try:
                res = requests.get(url, headers=self.headers, timeout=10, verify=False)
                soup = BeautifulSoup(res.text, 'xml')
                for item in soup.find_all('item'):
                    title = item.find('title').get_text().strip()
                    pub_date = item.find('pubDate').get_text() if item.find('pubDate') else ""
                    # 比對發布日期是否包含目標年份與月日
                    if clean_date[:4] in pub_date and f"{int(clean_date[4:6])} " in pub_date:
                        schedules.append({"官職": name, "行程內容": title, "時間/地點": item.find('description').get_text().strip(), "網址": item.find('link').get_text()})
            except: pass
        return schedules

    def get_president_schedule(self, clean_date):
        """總統府：網頁解析並過濾"""
        schedules = []
        url = "https://www.president.gov.tw/Page/37"
        try:
            res = requests.get(url, headers=self.headers, timeout=10, verify=False)
            soup = BeautifulSoup(res.text, 'html.parser')
            for row in soup.select('tr'):
                text = row.get_text(separator=" ")
                if self._is_valid_date(text, clean_date):
                    schedules.append({"官職": "總統/副總統", "行程內容": text.strip(), "時間/地點": "詳見官網", "網址": url})
        except: pass
        return schedules

    def get_moea_schedule(self, clean_date):
        """經濟部：RSS 比對"""
        schedules = []
        url = "https://www.moea.gov.tw/Mns/populace/news/NewsRSSDetail.aspx?Kind=10"
        try:
            res = requests.get(url, headers=self.headers, timeout=10, verify=False)
            soup = BeautifulSoup(res.text, 'xml')
            for item in soup.find_all('item'):
                title = item.find('title').get_text()
                if self._is_valid_date(title, clean_date):
                    schedules.append({"官職": "經濟部長", "行程內容": title, "時間/地點": item.find('description').get_text(), "網址": item.find('link').get_text()})
        except: pass
        return schedules
