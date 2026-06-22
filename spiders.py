import requests
from bs4 import BeautifulSoup
from datetime import datetime
import urllib3
# 修正重點：改從 urllib3.exceptions 匯入錯誤類型
from urllib3.exceptions import InsecureRequestWarning

# 關閉 SSL 驗證警告
urllib3.disable_warnings(InsecureRequestWarning)

class ScheduleSpider:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7"
        }

    def get_ey_schedule(self, target_type="premier"):
        """抓取行政院長/副院長行程"""
        if target_type == "premier":
            url = "https://www.ey.gov.tw/Page/278197D37F0FCDA"
            target_name = "行政院長"
        else:
            url = "https://www.ey.gov.tw/Page/D674EEBCEF9D67A4"
            target_name = "行政副院長"

        try:
            res = requests.get(url, headers=self.headers, timeout=12, verify=False)
            if res.status_code != 200:
                return [{"官職": target_name, "行程內容": f"站點回應錯誤 (HTTP {res.status_code})，可能遭 IP 封鎖", "時間/地點": "-"}]

            soup = BeautifulSoup(res.text, 'html.parser')
            schedules = []
            
            items = soup.select('.table tr') or soup.select('tr')
            
            for item in items:
                tds = item.select('td')
                if len(tds) >= 2:
                    time_loc = tds[0].get_text(separator=" ").strip()
                    content = tds[1].get_text(separator=" ").strip()
                    
                    if "暫無行程" in content or "目前無相關資料" in content:
                        continue
                        
                    schedules.append({
                        "官職": target_name,
                        "行程內容": content,
                        "時間/地點": time_loc
                    })
            
            if not schedules:
                return [{"官職": target_name, "行程內容": "今日無公開行程", "時間/地點": "-"}]
            return schedules

        except Exception as e:
            return [{"官職": target_name, "行程內容": f"連線異常: {str(e)}", "時間/地點": "-"}]

    def get_president_schedule(self):
        """抓取總統府行程"""
        url = "https://www.president.gov.tw/Page/94"
        target_name = "總統"
        try:
            res = requests.get(url, headers=self.headers, timeout=12, verify=False)
            if res.status_code != 200:
                return [{"官職": target_name, "行程內容": f"站點回應錯誤 (HTTP {res.status_code})", "時間/地點": "-"}]
                
            soup = BeautifulSoup(res.text, 'html.parser')
            schedules = []
            
            items = soup.select('.news_list li') or soup.select('tr')
            for item in items:
                text = item.get_text(separator=" ").strip()
                if text:
                    schedules.append({
                        "官職": target_name,
                        "行程內容": text.replace("\n", " "),
                        "時間/地點": "詳見官網新聞"
                    })
            
            if not schedules:
                return [{"官職": target_name, "行程內容": "未偵測到今日公開行程新聞", "時間/地點": "-"}]
            return schedules
        except Exception as e:
            return [{"官職": target_name, "行程內容": f"連線異常: {str(e)}", "時間/地點": "-"}]

    def get_moea_schedule(self):
        """抓取經濟部長行程"""
        url = "https://www.moea.gov.tw/Mns/populace/news/News.aspx?kind=4"
        target_name = "經濟部長"
        try:
            res = requests.get(url, headers=self.headers, timeout=12, verify=False)
            if res.status_code != 200:
                return [{"官職": target_name, "行程內容": f"站點回應錯誤 (HTTP {res.status_code})", "時間/地點": "-"}]
                
            soup = BeautifulSoup(res.text, 'html.parser')
            schedules = []
            
            items = soup.select('.news_title') or soup.select('tr')
            for item in items:
                text = item.get_text(separator=" ").strip()
                if "部長" in text or "出席" in text:
                    schedules.append({
                        "官職": target_name,
                        "行程內容": text,
                        "時間/地點": "由採訪通知擷取"
                    })
            
            if not schedules:
                return [{"官職": target_name, "行程內容": "今日無部長公開採訪行程", "時間/地點": "-"}]
            return schedules
        except Exception as e:
            return [{"官職": target_name, "行程內容": f"連線異常: {str(e)}", "時間/地點": "-"}]
