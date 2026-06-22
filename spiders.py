def get_ey_schedule(self, date_variants):
        """抓取行政院行程：雙層解析版（先抓 RSS，再深入詳細頁抓具體行程）"""
        rss_url = "https://www.ey.gov.tw/RSS/Program/ECE410333003326E"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        
        try:
            # 第一層：讀取 RSS 清單
            res = requests.get(rss_url, headers=headers, timeout=12, verify=False)
            if res.status_code != 200:
                return [{"官職": "行政院", "行程內容": f"RSS 清單回應異常 (HTTP {res.status_code})", "時間/地點": "-"}]
            
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'xml')
            items = soup.find_all('item')
            
            schedules = []
            
            for item in items:
                title = item.find('title').get_text().strip() if item.find('title') else ""
                link = item.find('link').get_text().strip() if item.find('link') else ""
                
                # 檢查 RSS 標題或內容是否符合使用者選定的日期
                if self._match_date(title, date_variants) and link:
                    target = "行政院長" if "院長" in title and "副院長" not in title else ("行政副院長" if "副院長" in title else "行政院綜合")
                    
                    # 第二層：點進去詳細內容頁 (例如 RSS_Content2.aspx?PID=...)
                    try:
                        detail_res = requests.get(link, headers=headers, timeout=10, verify=False)
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
                                    # 組合有意義的行程文字
                                    clean_text = " | ".join(text_lines)
                                    if len(clean_text) > 10:
                                        schedules.append({
                                            "官職": target,
                                            "行程內容": clean_text,
                                            "時間/地點": "見內文說明"
                                        })
                                        detail_found = True
                                        
                    except Exception as detail_err:
                        # 詳細頁解析失敗時，退回保留原本 RSS 的基本標題
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
