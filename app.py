import streamlit as st
from datetime import datetime, timedelta

st.set_page_config(page_title="經濟部首長行程自動觀測站", layout="wide", initial_sidebar_state="collapsed")

st.title("💼 經濟部首長行程自動觀測站")
st.caption("由於官方網站採用動態時間軸（Timeline）前端框架，為確保首長行程與日期對應 100% 精準、不漏看資訊，本站直接即時串接官網核心區塊。")

# 1. 頂部明日日期提示區
st.divider()
now = datetime.now() + timedelta(days=1)
tomorrow_chinese = f"{now.month}月{now.day}日"

st.markdown(f"### 🎯 觀測重點提示")
st.info(f"💡 請在下方官方看板中，直接尋找 **【 {tomorrow_chinese} 】** 區塊，即可掌握明日部長、次長的最新公開行程！")

# 2. 嵌入官方原汁原味的時間軸看板
st.markdown("### 📊 經濟部官網即時行程看板")

# 嵌入經濟部官方行程網頁，高度調大方便手機與電腦滑動
st.components.v1.iframe(
    "https://www.moea.gov.tw/Mns/populace/news/MinisterSchedule.aspx?menu_id=42225", 
    height=750, 
    scrolling=True
)

st.divider()
st.caption("⚙️ 本觀測站已自動為您跳過過期或斷更的舊版 RSS 系統。")
