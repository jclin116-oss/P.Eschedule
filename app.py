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

st.caption(f"目前檢索日期：【{date_str}】。點擊行程內容文字可直接跳轉至原始公告內文頁面。")

spider = ScheduleSpider()

if st.button("🔄 立即更新並篩選行程資料", type="primary"):
    with st.spinner(f"正在連線各部會數據源並篩選 {date_str} 資料..."):
        
        # 抓取數據
        ey_data = spider.get_ey_schedule(date_str)
        president_data = spider.get_president_schedule(date_variants)
        moea_data = spider.get_moea_schedule(date_variants)
        
        all_data = president_data + ey_data + moea_data
        
        if all_data:
            df = pd.DataFrame(all_data)
            
            # 官階排序
            job_order = ["總統", "副總統", "行政院長", "行政副院長", "經濟部長"]
            df['官職'] = pd.Categorical(df['官職'], categories=job_order, ordered=True)
            df = df.sort_values(by='官職').dropna(subset=['官職'])
            
            # 時間戳記
            df['檢查時間'] = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            # 欄位順序 (保留網址欄位供 LinkColumn 讀取)
            df = df[['官職', '行程內容', '時間/地點', '檢查時間', '網址']]
            
            st.success(f"{date_str} 資料篩選完成！")
            st.subheader(f"📅 {date_str} 行程列表")
            
            # --- 關鍵：配置連結顯示功能 ---
            st.data_editor(
                df,
                use_container_width=True,
                hide_index=True,
                disabled=True, # 設為唯讀表格
                column_config={
                    "行程內容": st.column_config.LinkColumn(
                        "行程內容 (可點擊跳轉)",
                        help="點擊文字可直接開啟對應政府公開頁面",
                        url_column="網址", # 指定超連結指向網址欄位
                        display_text="^.*$" # 顯示原本的完整標題文字
                    ),
                    "網址": None # 隱藏難看的純網址欄位，不直接露出
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
            st.warning(f"未能成功獲取任何首長資料。")
else:
    st.info("請選擇日期並點擊上方按鈕開始查詢。")
