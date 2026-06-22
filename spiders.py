import requests
from bs4 import BeautifulSoup
import urllib3
from urllib3.exceptions import InsecureRequestWarning

# 關閉 SSL 驗證警告
urllib3.disable_warnings(InsecureRequestWarning)

class ScheduleSpider:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7"
        }

    def _match_date(self, text, date_variants):
        """檢查文本內是否包含任何一種日期變體"""
        return any(v in text for v in date_variants)

    def _fetch_ey_rss(self, pid, target_name, clean_date):
        """內部工具：抓取行政院特定首長 RSS"""
        url = f"https://www.ey.gov.tw/RSS_Content2.aspx?PID={pid}&SD={clean_date}&ED={clean_date}"
        schedules = []
        try:
            res = requests.get(url, headers=self.headers, timeout=12, verify=False)
            if res.status_code != 200:
                return []
            
            res.encoding = 'utf-8'
            try:
                soup = BeautifulSoup(res.text, 'xml')
                items = soup.find_all('item')
            except Exception:
                soup = BeautifulSoup(res.text, 'html.parser')
                items = soup.find_all('item')
                
            for item in items:
                title_node = item.find('title')
                desc_node = item.find('description')
                link_node = item.find('link')
                
                title = title_node.get_text().strip() if title_node else ""
                description = desc_node.get_text().strip() if desc_node else ""
                link = link_node.get_text().strip() if link_node else ""
                
                if title:
                    schedules.append({
                        "官職": target_name,
                        "行程內容": title,
                        "時間/地點": description if description else "詳見內文說明",
                        "網址": link if link else url
                    })
        except Exception:
            pass
        return schedules

    def get_ey_schedule(self, date_str):
        """抓取行政院行程（院長與副院長 RSS 頻道）"""
        clean_date = date_str.replace("-", "")
        premier_schedules = self._fetch_ey_rss("c98e07e2-66b4-4c90-a68d-2ef8ef8cf550", "行政院長", clean_date)
        vice_premier_schedules = self._fetch_ey_rss("018a38fc-8461-4687-9bc1-35606d50db8a", "行政副院長", clean_date)
        
        schedules = premier_schedules + vice_premier_schedules
        if not schedules:
            return [
                {"官職": "行政院長", "行程內容": "該日期無公開行程", "時間/地點": "-", "網址": "https://www.ey.gov.tw"},
                {"官職": "行政副院長", "行程內容": "該日期無公開行程", "時間/地點": "-", "網址": "https://www.ey.gov.tw"}
            ]
        return schedules

    def get_president_schedule(self, date_variants):
        """抓取總統府行程（網頁 HTML 解析）"""
        url = "https://www.president.gov.tw/Page/37"
        target_name = "總統"
        try:
            res = requests.get(url, headers=self.headers, timeout=12, verify=False)
            if res.status_code != 200:
                return [{"官職": target_name, "行程內容": f"站點回應錯誤 (HTTP {res.status_code})", "時間/地點": "-", "網址": url}]
                
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            schedules = []
            
            items = soup.select('tr') or soup.select('li') or soup.select('.p-list-item')
            for item in items:
                text = " ".join(item.get_text(separator=" ").split())
                if text and len(text) > 10 and "頁面" not in text and "版權所有" not in text:
                    if self._match_date(text, date_variants):
                        display_name = "副總統" if "副總統" in text else "總統"
                        
                        item_link = item.find('a')
                        href = item_link.get('href') if item_link else ""
                        if href and not href.startswith('http'):
                            href = "https://www.president.gov.tw" + href
                            
                        schedules.append({
                            "官職": display_name,
                            "行程內容": text,
                            "時間/地點": "詳見官網行程頁",
                            "網址": href if href else url
                        })
            
            if not schedules:
                return [{"官職": target_name, "行程內容": "該日期於官網頁面無公開行程顯示", "時間/地點": "-", "網址": url}]
            return schedules
        except Exception as e:
            return [{"官職": target_name, "行程內容": f"連線異常: {str(e)}", "時間/地點": "-", "網址": url}]

    def get_moea_schedule(self, date_variants):
        """使用 RSS 抓取經濟部長行程"""
        url = "https://www.moea.gov.tw/Mns/populace/news/NewsRSSDetail.aspx?Kind=10"
        target_name = "經濟部長"
        try:
            res = requests.get(url, headers=self.headers, timeout=12, verify=False)
            if res.status_code != 200:
                return [{"官職": target_name, "行程內容": f"RSS站點回應錯誤 (HTTP {res.status_code})", "時間/地點": "-", "網址": url}]
                
            res.encoding = 'utf-8'
            try:
                soup = BeautifulSoup(res.text, 'xml')
                items = soup.find_all('item')
            except Exception:
                soup = BeautifulSoup(res.text, 'html.parser')
                items = soup.find_all('item')
                
            schedules = []
            for item in items:
                title_node = item.find('title')
                desc_node = item.find('description')
                link_node = item.find('link')
                
                title = title_node.get_text().strip() if title_node else ""
                description = desc_node.get_text().strip() if desc_node else ""
                link = link_node.get_text().strip() if link_node else ""
                
                full_text = f"{title} {description}"
                
                if self._match_date(full_text, date_variants):
                    if "暫無行程" in description or "無公開行程" in description:
                        continue
                    schedules.append({
                        "官職": target_name,
                        "行程內容": description if description else title,
                        "時間/地點": title,
                        "網址": link if link else url
                    })
            
            if not schedules:
                return [{"官職": target_name, "行程內容": "該日期於經濟部 RSS 中無公開行程", "時間/地點": "-", "網址": url}]
            return schedules
        except Exception as e:
            return [{"官職": target_name, "行程內容": f"RSS連線異常: {str(e)}", "時間/地點": "-", "網址": url}]
