import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime

class ScheduleSpider:
    def __init__(self):
        self.rss_sources = {
            "行政院長": "https://www.ey.gov.tw/RSS_Content2.aspx?PID=c98e07e2-66b4-4c90-a68d-2ef8ef8cf550",
            "行政副院長": "https://www.ey.gov.tw/RSS_Content2.aspx?PID=018a38fc-8461-4687-9bc1-35606d50db8a",
            "經濟部長": "https://www.moea.gov.tw/Mns/populace/news/NewsRSSDetail.aspx?Kind=10"
        }

    def get_all_schedules(self, target_date_str):
        results = []
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()

        # 1. RSS 解析 (行政院、經濟部)
        for name, url in self.rss_sources.items():
            feed = feedparser.parse(url)
            for entry in feed.entries:
                if hasattr(entry, 'published_parsed'):
                    pub_date = datetime.fromtimestamp(datetime.mktime(entry.published_parsed)).date()
                    if pub_date == target_date:
                        results.append({
                            "官職": name,
                            "行程內容": entry.title,
                            "時間/地點": entry.description if 'description' in entry else "-",
                            "網址": entry.link
                        })

        # 2. HTML 解析 (總統府)
        try:
            res = requests.get("https://www.president.gov.tw/Page/37", timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            # 總統府網頁結構通常在 table 或 list 中
            for item in soup.select('tr'): # 視實際網頁結構調整
                text = item.get_text(separator=" ")
                # 簡單日期比對：檢查字串中是否有當天日期
                if target_date_str.replace("-", "/") in text or str(target_date.day) in text:
                    results.append({
                        "官職": "總統/副總統",
                        "行程內容": text.strip(),
                        "時間/地點": "詳見連結",
                        "網址": "https://www.president.gov.tw/Page/37"
                    })
        except:
            pass

        return results
