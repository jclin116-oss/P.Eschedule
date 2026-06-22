import streamlit as st
import pandas as pd
from spiders import ScheduleSpider
from datetime import datetime

st.set_page_config(layout="wide")
st.title("🏛️ 政府首長行程看板")

selected_date = st.date_input("選擇查詢日期：", datetime.now())
date_str = selected_date.strftime("%Y-%m-%d")

if st.button("🔄 獲取行程"):
    spider = ScheduleSpider()
    
    # 【關鍵修正】：請使用 get_all_schedules，不要再呼叫舊的 get_ey_schedule
    all_data = spider.get_all_schedules(date_str)
    
    df = pd.DataFrame(all_data) if all_data else pd.DataFrame(columns=['官職', '行程內容', '時間/地點', '網址'])
    
    # 補齊表格
    jobs = ["總統/副總統", "行政院長", "行政副院長", "經濟部長"]
    for job in jobs:
        if job not in df['官職'].values:
            df = pd.concat([df, pd.DataFrame([{"官職": job, "行程內容": "無公開行程", "時間/地點": "-", "網址": "#"}])], ignore_index=True)

    st.dataframe(df, use_container_width=True, hide_index=True, column_config={
        "網址": st.column_config.LinkColumn("連結", display_text="前往查閱")
    })
