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

    def get_ey_schedule(self, date_str):
        """
        抓取行政院行程：直接帶入參數型 RSS 網址
        date_str 格式固定為 'YYYY-MM-DD' (來自 app.py)
        """
        # 將 '2026-06-22' 轉換為行政院需要的 '20260622' 格式
        clean_date = date_str.replace("-", "")
        
        # 動態拼接網址，讓行政院直接吐回該日期的精準 RSS
        url = f"https://www.ey.gov.tw/RSS_Content2.aspx?PID=c98e07e2-66b4-4c90-a68d-2ef8ef8cf550&SD={clean_date}&ED={clean_date}"
        
        try:
            res = requests.get(url, headers=self.headers, timeout=12, verify=False)
            if res.status_code != 200:
                return [{"官職": "行政院", "行程內容": f"RSS 回應異常 (HTTP {res.status_code})", "時間/地點": "-"}]
            
            res.encoding = 'utf-8'
            
            # 容錯解析 XML
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
                
                title = title_node.get_text().strip() if title_node else ""
                description = desc_node.get_text().strip() if desc_node else ""
                
                if title:
                    # 判斷院長或副院長
                    target = "行政院長" if "院長" in title and "副院長" not in title else ("行政副院長" if "副院長" in title else "行政院行程")
                    
                    schedules.append({
                        "官職": target,
                        "行程內容": title,
                        "時間/地點": description if description else "詳見內文"
                    })
            
            if not schedules:
                return [{"官職": "行政院行程", "行程內容": "該日期於行政院 RSS 中無公開行程", "時間/地點": "-"}]
            return schedules
            
        except Exception as e:
            return [{"官職": "行政院", "行程內容": f"RSS 連線異常: {str(e)}", "時間/地點": "-"}]

    def get_president_schedule(self, date_variants):
        """抓取總統府行程並過濾日期"""
        url = "https://www.president.gov.tw/Page/37"
        target_name = "總統"
        try:
            res = requests.get(url, headers=self.headers, timeout=12, verify=False)
            if res.status_code != 200:
                return [{"官職": target_name, "行程內容": f"站點回應錯誤 (HTTP {res.status_code})", "時間/地點": "-"}]
                
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            schedules = []
            
            items = soup.select('tr') or soup.select('li') or soup.select('.p-list-item')
            for item in items:
                text = " ".join(item.get_text(separator=" ").split())
                if text and len(text) > 10 and "頁面" not in text and "版權所有" not in text:
                    if self._match_date(text, date_variants):
                        schedules.append({
                            "官職": target_name,
                            "行程內容": text,
                            "時間/地點": "詳見官網行程頁"
                        })
            
            if not schedules:
                return [{"官職": target_name, "行程內容": "該日期於官網頁面無公開行程顯示", "時間/地點": "-"}]
            return schedules
        except Exception as e:
            return [{"官職": target_name, "行程內容": f"連線異常: {str(e)}", "時間/地點": "-"}]

    def get_moea_schedule(self, date_variants):
        """抓取經濟部長行程並過濾日期"""
        url = "https://www.moea.gov.tw/Mns/populace/news/MinisterSchedule.aspx?menu_id=42225"
        target_name = "經濟部長"
        try:
            res = requests.get(url, headers=self.headers, timeout=12, verify=False)
            if res.status_code != 200:
                return [{"官職": target_name, "行程內容": f"站點回應錯誤 (HTTP {res.status_code})", "時間/地點": "-"}]
                
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            schedules = []
            
            items = soup.select('tr') or soup.select('table tr')
            for item in items:
                tds = item.select('td')
                if len(tds) >= 2:
                    time_info = " ".join(tds[0].get_text(separator=" ").split())
                    content_info = " ".join(tds[1].get_text(separator=" ").split())
                    
                    full_text = f"{time_info} {content_info}"
                    if "暫無行程" in content_info or "無公開行程" in content_info:
                        continue
                        
                    if self._match_date(full_text, date_variants):
                        schedules.append({
                            "官職": target_name,
                            "行程內容": content_info,
                            "時間/地點": time_info
                        })
                else:
                    text = " ".join(item.get_text(separator=" ").split())
                    if text and len(text) > 15 and self._match_date(text, date_variants):
                        schedules.append({
                            "官職": target_name,
                            "行程內容": text,
                            "時間/地點": "見內文"
                        })
            
            if not schedules:
                return [{"官職": target_name, "行程內容": "該日期於官網頁面無公開行程顯示", "時間/地點": "-"}]
            return schedules
        except Exception as e:
            return [{"官職": target_name, "行程內容": f"連線異常: {str(e)}", "時間/地點": "-"}]
