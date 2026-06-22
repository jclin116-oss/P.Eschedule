import urllib.request
import ssl
from bs4 import BeautifulSoup
import streamlit as st

st.set_page_config(page_title="官網原始文字流檢測器", layout="wide")
st.title("🔍 經濟部官網原始文字流（未切分）")
st.caption("這個版本不做任何表格轉換與篩選，直接顯示 BeautifulSoup 抓到的最原始文字排序列")

if st.button("🔄 重新抓取並傾倒原始文字"):
    st.cache_data.clear()

url = "https://www.moea.gov.tw/Mns/populace/news/MinisterSchedule.aspx?menu_id=42225"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

try:
    context = ssl._create_unverified_context()
    req = urllib.request.Request(url, headers=headers)
    
    with urllib.request.urlopen(req, context=context) as response:
        html = response.read()
        
    soup = BeautifulSoup(html, 'html.parser')
    
    # 這是最純粹的切分：只要有換行，就切成一列，並且移除兩端空白
    raw_lines = [line.strip() for line in soup.text.split('\n') if line.strip()]
    
    st.info(f"💡 成功抓取！整個網頁目前的純文字流總共有 {len(raw_lines)} 行。")
    
    # 用 Streamlit 的 Code 區塊或 Text 顯示，方便複製與觀察
    st.subheader("📋 網頁純文字行（由上往下排列）")
    
    # 為了方便你找到 6月23日，我們加上行號
    display_text = ""
    for idx, line in enumerate(raw_lines):
        display_text += f"[{idx}] {line}\n"
        
    st.text_area("請往下捲動尋找「6月23日」附近的行號與文字排列：", value=display_text, height=600)

except Exception as e:
    st.error(f"抓取失敗: {e}")
