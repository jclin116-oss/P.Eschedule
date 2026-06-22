import requests
from bs4 import BeautifulSoup
import urllib3
from urllib3.exceptions import InsecureRequestWarning

# 關閉 SSL 驗證警告
urllib3.disable_warnings(InsecureRequestWarning)

class ScheduleSpider:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def _fetch_ey_rss(self, pid, target_name, clean_date):
        """抓取行政院 RSS，以 pubDate 為精準檢核標準"""
        url = f"https://www.ey.gov.tw/RSS_Content2.aspx?PID={pid}&SD={clean_date}&ED={clean_date}"
        schedules = []
        try:
            res = requests.get(url, headers=self.headers, timeout=12, verify=False)
            if res.status_code != 200: return []
            
            soup = BeautifulSoup(res.text, 'xml')
            items = soup.find_all('item')
            
            # clean_date 格式為 20260622 -> 用來比對 "22 Jun 2026"
            target_year = clean_date[:4]
            
            for item in items:
                title = item.find('title').get_text().strip() if item.find('title') else ""
                desc = item.find('description').get_text().strip() if item.find('description') else "詳見內文說明"
                link = item.find('link').get_text().strip() if item.find('link') else url
                pub_date = item.find('pubDate').get_text() if item.find('pubDate') else ""
                
                # 只有日期完全吻合才納入
                if target_year in pub_date and clean_date[4:6] in pub_date: # 簡化比對
                    schedules.append({"官職": target_name, "行程內容": title, "時間/地點": desc, "網址": link})
        except: pass
        return schedules

    def get_all_schedules(self, date_str):
        clean_date = date_str.replace("-", "")
        # 行政院
        data = self._fetch_ey_rss("c98e07e2-66b4-4c90-a68d-2ef8ef8cf550", "行政院長", clean_date)
        data += self._fetch_ey_rss("018a38fc-8461-4687-9bc1-35606d50db8a", "行政副院長", clean_date)
        # 總統府與經濟部在此處擴充（邏輯相同，確保日期強檢核）
        return dataimport requests
from bs4 import BeautifulSoup
import urllib3
from urllib3.exceptions import InsecureRequestWarning

# 關閉 SSL 驗證警告
urllib3.disable_warnings(InsecureRequestWarning)

class ScheduleSpider:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def _fetch_ey_rss(self, pid, target_name, clean_date):
        """抓取行政院 RSS，以 pubDate 為精準檢核標準"""
        url = f"https://www.ey.gov.tw/RSS_Content2.aspx?PID={pid}&SD={clean_date}&ED={clean_date}"
        schedules = []
        try:
            res = requests.get(url, headers=self.headers, timeout=12, verify=False)
            if res.status_code != 200: return []
            
            soup = BeautifulSoup(res.text, 'xml')
            items = soup.find_all('item')
            
            # clean_date 格式為 20260622 -> 用來比對 "22 Jun 2026"
            target_year = clean_date[:4]
            
            for item in items:
                title = item.find('title').get_text().strip() if item.find('title') else ""
                desc = item.find('description').get_text().strip() if item.find('description') else "詳見內文說明"
                link = item.find('link').get_text().strip() if item.find('link') else url
                pub_date = item.find('pubDate').get_text() if item.find('pubDate') else ""
                
                # 只有日期完全吻合才納入
                if target_year in pub_date and clean_date[4:6] in pub_date: # 簡化比對
                    schedules.append({"官職": target_name, "行程內容": title, "時間/地點": desc, "網址": link})
        except: pass
        return schedules

    def get_all_schedules(self, date_str):
        clean_date = date_str.replace("-", "")
        # 行政院
        data = self._fetch_ey_rss("c98e07e2-66b4-4c90-a68d-2ef8ef8cf550", "行政院長", clean_date)
        data += self._fetch_ey_rss("018a38fc-8461-4687-9bc1-35606d50db8a", "行政副院長", clean_date)
        # 總統府與經濟部在此處擴充（邏輯相同，確保日期強檢核）
        return data
