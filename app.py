def get_raw_text(scraped_date):
    """
    行政院行程專用精準版：
    同時抓取 data-name 屬性（如：院長、副院長）與行程內文
    """
    date_str = scraped_date.strftime("%Y-%m-%d")
    base_url = f"https://www.ey.gov.tw/Page/ECE410333003326E?SDate={date_str}&EDate={date_str}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7"
    }

    try:
        res = requests.get(base_url, headers=headers, timeout=15, verify=False)
        if res.status_code == 200:
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, "html.parser")
            
            # 1. 尋找網頁中所有的行程區塊 (如您圖中所示的 class="timeline-content")
            timeline_blocks = soup.find_all(class_="timeline-content")
            
            if not timeline_blocks:
                return f"📅 {date_str} 當天似乎沒有安排公開行程，或格式已變更。"
                
            formatted_outputs = []
            
            for block in timeline_blocks:
                # 2. 找出該區塊內藏有職稱的 li 標籤 (帶有 data-name 屬性)
                title_tag = block.find(attrs={"data-name": True})
                job_title = ""
                if title_tag:
                    # 成功抓到 data-name="院長" 裡面的值！
                    job_title = f"【{title_tag['data-name']}】\n"
                
                # 3. 取得該區塊的其他行程純文字內容
                content_text = block.get_text(separator="\n", strip=True)
                
                # 4. 組合職稱與內文
                full_item_text = f"{job_title}{content_text}"
                formatted_outputs.append(full_item_text)
                
            # 將所有行程用分隔線連起來輸出
            return "\n\n==============================\n\n".join(formatted_outputs)
            
        else:
            return f"連線失敗，伺服器回應狀態碼: {res.status_code}"
    except Exception as e:
        return f"執行過程中發生連線錯誤: {str(e)}"
