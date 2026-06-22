import urllib.request
import ssl
import feedparser
import streamlit as st

# 設定網頁標題
st.set_page_config(page_title="經濟部經貿新聞即時看板", page_icon="📰")
st.title("📰 經濟部經貿新聞即時看板")
st.caption("資料來源：經濟部官網 RSS（即時更新，不透過第三方轉換）")

# 建立一個重新整理按鈕
if st.button("🔄 手動重新整理"):
    st.rerun()

url = "https://www.moea.gov.tw/Mns/populace/news/NewsRSSdetail.aspx?Kind=10"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

try:
    # 解決 SSL 憑證與阻擋問題
    context = ssl._create_unverified_context()
    req = urllib.request.Request(url, headers=headers)
    
    with urllib.request.urlopen(req, context=context) as response:
        feed = feedparser.parse(response.read())
    
    # 畫一條分隔線
    st.divider()
    
    # 依序渲染新聞到 Streamlit 網頁上
    if feed.entries:
        for entry in feed.entries:
            title = entry.title
            link = entry.link
            pub_date = entry.get('published', '未知時間')
            
            # 使用 Streamlit 的擴充元件漂亮呈現
            with st.container():
                st.markdown(f"#### [{title}]({link})")
                st.caption(f"📅 發布日期: {pub_date}")
                st.write(f"[點此閱讀官網原文]({link})")
                st.divider()
    else:
        st.info("目前沒有更新的新聞。")

except Exception as e:
    st.error(f"連線或解析失敗，錯誤原因: {e}")
