import streamlit as st
import pandas as pd
from spiders import ScheduleSpider
from datetime import datetime

st.set_page_config(page_title="政府公開行程", layout="wide")

st.title("🏛️ 政府首長公開行程即時看板")

# --- 日期選擇器 ---
today = datetime.now().date()
selected_date = st.date_input("請選擇欲查詢的行程日期：", today)
date_str = selected_date.strftime("%Y-%m-%d")

# 建立多元日期字串格式，供總統府與經濟部 RSS 進行過濾
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

st.caption(f"目前檢索日期：【{date_str}】。資料將依據中華民國政府官階職位進行排序。")

spider = ScheduleSpider()

if st.button("🔄 立即更新並篩選行程資料", type="primary"):
    with st.spinner(f"正在連線各部會數據源並篩選 {date_str} 資料..."):
        
        # 抓取各數據源
        ey_data = spider.get_ey_schedule(date_str)
        president_data = spider.get_president_schedule(date_variants)
        moea_data = spider.get_moea_schedule(date_variants)
        
        # 合併所有行程資料列表
        all_data = president_data + ey_data + moea_data
        
        if all_data:
            df = pd.DataFrame(all_data)
            
            # --- 核心：定義官階排序邏輯 ---
            # 定義官職的嚴格層級順序
            job_order = ["總統", "副總統", "行政院長", "行政副院長", "經濟部長"]
            
            # 將無公開行程的提示進行基本清理（避免污染正常的欄位過濾邏輯）
            # 若某些官職顯示無行程，仍會參與排序
            df['官職'] = pd.Categorical(df['官職'], categories=job_order, ordered=True)
            
            # 依據官職層級進行排序 (由高至低)
            df = df.sort_values(by='官職').dropna(subset=['官職'])
            
            # 補上資料檢查時間戳記
            df['檢查時間'] = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            # 依要求重新編排欄位順序：官職 -> 行程內容 -> 時間/地點 -> 檢查時間
            df = df[['官職', '行程內容', '時間/地點', '檢查時間']]
            
            st.success(f"{date_str} 資料篩選與官階排序完成！")
            st.subheader(f"📅 {date_str} 行程列表")
            
            # 渲染數據表格
            st.dataframe(df, use_container_width=True, hide_index=True)
            
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
