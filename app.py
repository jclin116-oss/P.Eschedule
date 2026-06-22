import streamlit as st
import pandas as pd
from spiders import ScheduleSpider
from datetime import datetime

st.set_page_config(page_title="政府首長公開行程監測", layout="wide")

st.title("🏛️ 政府首長公開行程即時看板")

# --- 日期選擇器 ---
today = datetime.now().date()
selected_date = st.date_input("請選擇欲查詢的行程日期：", today)
date_str = selected_date.strftime("%Y-%m-%d")

# 建立多元日期字串格式
roc_year = selected_date.year - 1911
date_variants = [
    date_str,                                      # 2026-06-22
    selected_date.strftime("%Y/%m/%d"),           # 2026/06/22
    f"{roc_year}年{selected_date.month}月{selected_date.day}日", # 115年6月22日
    f"{roc_year}年度{selected_date.month}月{selected_date.day}日", # 115年度6月22日
    f"{roc_year}/{selected_date.month:02d}/{selected_date.day:02d}", # 115/06/22
    f"{roc_year}/{selected_date.month}/{selected_date.day}", # 115/6/22
    f"{selected_date.month}/{selected_date.day}", # 6/22
    f"{selected_date.month}月{selected_date.day}日" # 6月22日
]

st.caption(f"目前檢索日期：【{date_str}】。可透過詳細內文欄位直接點擊跳轉至原始網頁。")

spider = ScheduleSpider()

if st.button("🔄 立即更新並篩選行程資料", type="primary"):
    with st.spinner(f"正在連線各部會數據源並篩選 {date_str} 資料..."):
        
        # 修正：將 date_variants 傳入 get_ey_schedule 進行二次日期核對
        ey_data = spider.get_ey_schedule(date_str, date_variants)
        president_data = spider.get_president_schedule(date_variants)
        moea_data = spider.get_moea_schedule(date_variants)
        
        all_data = president_data + ey_data + moea_data
        
        # 轉換為初始 DataFrame
        if all_data:
            df = pd.DataFrame(all_data)
        else:
            df = pd.DataFrame(columns=['官職', '行程內容', '時間/地點', '網址'])
            
        # --- 全局補齊機制：確保 5 個官職必定出現在表格中 ---
        job_order = ["總統", "副總統", "行政院長", "行政副院長", "經濟部長"]
        default_urls = {
            "總統": "https://www.president.gov.tw/Page/37",
            "副總統": "https://www.president.gov.tw/Page/37",
            "行政院長": "https://www.ey.gov.tw",
            "行政副院長": "https://www.ey.gov.tw",
            "經濟部長": "https://www.moea.gov.tw/Mns/populace/news/NewsRSSDetail.aspx?Kind=10"
        }
        
        existing_jobs = df['官職'].unique() if not df.empty else []
        missing_rows = []
        for job in job_order:
            if job not in existing_jobs:
                missing_rows.append({
                    "官職": job,
                    "行程內容": "該日期無公開行程",
                    "時間/地點": "-",
                    "網址": default_urls[job]
                })
        
        if missing_rows:
            df = pd.concat([df, pd.DataFrame(missing_rows)], ignore_index=True)
        
        # 官階排序
        df['官職'] = pd.Categorical(df['官職'], categories=job_order, ordered=True)
        df = df.sort_values(by='官職').dropna(subset=['官職'])
        
        # 檢查時間戳記
        df['檢查時間'] = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # 調整欄位排序
        df = df[['官職', '行程內容', '時間/地點', '網址', '檢查時間']]
        
        st.success(f"{date_str} 資料篩選與官階排序完成！")
        st.subheader(f"📅 {date_str} 行程列表")
        
        # 表格渲染
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "官職": st.column_config.TextColumn("官職"),
                "行程內容": st.column_config.TextColumn("行程內容"),
                "時間/地點": st.column_config.TextColumn("時間/地點"),
                "網址": st.column_config.LinkColumn(
                    "詳細內文",
                    help="點擊即可開啟原始公告網頁查看詳細說明",
                    display_text="🔗 前往內文"
                ),
                "檢查時間": st.column_config.TextColumn("檢查時間")
            }
        )
        
        # 下載 CSV 功能
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 下載此日期行程報表 (CSV)",
            data=csv,
            file_name=f"gov_schedule_{date_str}.csv",
            mime="text/csv",
        )
else:
    st.info("請選擇日期並點擊上方按鈕開始查詢。")
