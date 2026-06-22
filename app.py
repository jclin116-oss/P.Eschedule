import urllib.request
import ssl
import feedparser

def read_moea_rss():
    url = "https://www.moea.gov.tw/Mns/populace/news/NewsRSSdetail.aspx?Kind=10"
    
    # 坑 1 解決：偽裝成一般 Chrome 瀏覽器，避免被政府網站防火牆阻擋
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        # 坑 2 解決：創建一個忽略 SSL 憑證驗證的 context，避免安全憑證錯誤
        context = ssl._create_unverified_context()
        
        # 建立請求並獲取網頁文字內容
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=context) as response:
            xml_data = response.read()
        
        # 將下載好的 XML 文字丟給 feedparser 解析
        feed = feedparser.parse(xml_data)
        
        if feed.bozo:
            print("RSS 解析失敗，格式可能有誤。")
            return
            
        print(f"【訂閱來源】: {feed.channel.title}\n" + "="*50)
        
        # 依序印出最新消息
        for entry in feed.entries:
            print(f"發布日期: {entry.get('published', '無日期')}")
            print(f"新聞標題: {entry.title}")
            print(f"詳細連結: {entry.link}")
            print("-" * 50)
            
    except Exception as e:
        print(f"讀取失敗，錯誤原因: {e}")

if __name__ == "__main__":
    read_moea_rss()
