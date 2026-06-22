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

    def get_ey_schedule(self, date_variants):
        """抓取行政院行程：雙層解析版（先抓 RSS 列表，再深入內頁抓具體行程時間與地點）"""
        rss_url = "https://www.ey.gov.tw/RSS/Program/ECE410333003326E"
        
        try:
            # 第一層：讀取 RSS 清單
            res = requests.get(rss_url, headers=self.headers, timeout=12, verify=False)
            if res.status_code != 200:
                return [{"官職": "行政院", "行程內容": f"RSS 清單回應異常 (HTTP {res.status_code})", "時間/地點": "-"}]
            
            # 強制指定編碼，防範亂碼
            res.encoding = 'utf-8'
            
            # 容錯處理：優先使用 xml 解析器，若環境缺少 lxml 則自動降級使用 html.parser
            try:
                soup = BeautifulSoup(res.text, 'xml')
                items = soup.find_all('item')
            except Exception:
                soup = BeautifulSoup(res.text, 'html.parser')
                items = soup.find_all('item')
            
            schedules = []
            
            for item in items:
                title_node = item.find('title')
                link_node = item.find('link')
                
                title = title_node.get_text().strip() if title_node else ""
                link = link_node.get_text().strip() if link_node else ""
                
                # 檢查 RSS 標題是否符合使用者選定的日期
                if self._match_date(title, date_variants) and link:
                    target = "行政院長" if "院長" in title and "副院長" not in title else ("行政副院長" if "副院長" in title else "行政院綜合")
                    
                    # 第二層：點進去詳細內容頁 (例如 RSS_Content2.aspx?PID=...)
                    try:
                        detail_res = requests.get(link, headers=self.headers, timeout=10, verify=False)
                        if detail_res.status_code == 200:
                            detail_res.encoding = 'utf-8'
                            detail_soup = BeautifulSoup(detail_res.text, 'html.parser')
                            
                            # 優先抓取詳細頁內部的表格結構 (通常行程都在表格內)
                            rows = detail_soup.select('tr')
                            detail_found = False
                            
                            for row in rows:
                                tds = row.select('td')
                                if len(tds) >= 2:
                                    time_loc = " ".join(tds[0].get_text(separator=" ").split())
                                    content = " ".join(tds[1].get_text(separator=" ").split())
                                    
                                    if content and "暫無行程" not in content and "無公開行程" not in content and len(content) > 3:
                                        schedules.append({
                                            "官職": target,
                                            "行程內容": content,
                                            "時間/地點": time_loc
                                        })
                                        detail_found = True
                            
                            # 備用方案：如果表格沒抓到，抓取特定文章主體區塊的文字
                            if not detail_found:
                                main_content = detail_soup.select_one('.p-content') or detail_soup.select_one('article') or detail_soup.select_one('#Content')
                                if main_content:
                                    text_lines = [line.strip() for line in main_content.get_text(separator="\n").split("\n") if line.strip()]
                                    clean_text = " | ".join(text_lines)
                                    if len(clean_text) > 10:
                                        schedules.append({
                                            "官職": target,
                                            "行程內容": clean_text,
                                            "時間/地點": "見內文說明"
                                        })
                                        detail_found = True
                                        
                    except Exception as detail_err:
                        # 詳細頁連線失敗時，降級保留原本 RSS 的基本標題
                        schedules.append({
                            "官職": target,
                            "行程內容": f"{title} (詳細頁連線失敗: {str(detail_err)})",
                            "時間/地點": link
                        })
            
            if not schedules:
                return [{"官職": "行政院行程", "行程內容": "該日期於 RSS 詳細頁面內無公開行程內容", "時間/地點": "-"}]
            return schedules
            
        except Exception as e:
            return [{"官職": "行政院", "行程內容": f"RSS 雙層解析異常: {str(e)}", "時間/地點": "-"}]

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
