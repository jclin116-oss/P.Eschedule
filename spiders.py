import requests
from bs4 import BeautifulSoup
from datetime import datetime

class ScheduleSpider:
    def __init__(self):
        self.rss_sources = {
            "行政院長": "https://www.ey.gov.tw/RSS_Content2.aspx?PID=c98e07e2-66b4-4c90-a68d-2ef8ef8cf550",
            "行政副院長": "https://www.ey.gov.tw/RSS_Content2.aspx?PID=018a38fc-8461-4687-9bc1-35606d50db8a",
            "經濟部長": "https://www.moea.gov.tw/Mns/populace/news/RSSDetail.aspx?Kind=10"
        }

    def get_all_schedules(self, target_date_str):
        results = []
        # 將日期轉為字串格式用於比對
        date_query = target_date_str.replace("-", "")

        # 1. RSS 解析 (行政院、經濟部)
        for name, url in self.rss_sources.items():
            try:
                res = requests.get(url, timeout=10)
                soup = BeautifulSoup(res.text, 'xml')
                for item in soup.find_all('item'):
                    title = item.find('title').text
                    link = item.find('link').text
                    desc = item.find('description').text if item.find('description') else "-"
                    pub_date = item.find('pubDate').text if item.find('pubDate') else ""
                    
                    # 只要 pubDate 中包含目標日期 (例如 22 Jun 2026)
                    if date_query in pub_date.replace(" ", ""): 
                        results.append({"官職": name, "行程內容": title, "時間/地點": desc, "網址": link})
            except: continue

        # 2. HTML 解析 (總統府)
        try:
            res = requests.get("https://www.president.gov.tw/Page/37", timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            for item in soup.select('tr'):
                text = item.get_text(separator=" ")
                if target_date_str.replace("-", "/") in text:
                    results.append({"官職": "總統/副總統", "行程內容": text.strip(), "時間/地點": "詳見連結", "網址": "https://www.president.gov.tw/Page/37"})
        except: pass
        return results
