import streamlit as st
import pandas as pd
from spiders import ScheduleSpider
from datetime import datetime

# 網頁基本設定
st.set_page_config(page_title="政府首長公開行程監測", layout="wide")

st.title("🏛️ 政府首長公開行程即時看板")
st.caption(f"本系統自動爬取總統府、行政院、經濟部之公開行程資訊。目前查詢時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 初始化爬蟲模組
spider = ScheduleSpider()

# 介面按鈕：觸發即時爬取
if st.button("🔄 立即更新所有行程資料", type="primary"):
    with st.spinner("正在安全連線並爬取各部會最新行程，請稍候..."):
        
        # 執行各部會爬蟲
        premier_data = spider.get_ey_schedule("premier")
        vice_data = spider.get_ey_schedule("vice")
        president_data = spider.get_president_schedule()
        moea_data = spider.get_moea_schedule()
        
        # 合併所有蒐集到的資料
        all_data = president_data + premier_data + vice_data + moea_data
        
        if all_data:
            df = pd.DataFrame(all_data)
            
            # 清理 DataFrame 欄位順序與呈現
            df['檢查時間'] = datetime.now().strftime("%Y-%m-%d %H:%M")
            df = df[['官職', '時間/地點', '行程內容', '檢查時間']]
            
            st.success("所有資料更新成功！")
            
            # 顯示資料表格
            st.subheader("今日行程列表")
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # 提供下載 CSV 功能
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 下載行程報表 (CSV)",
                data=csv,
                file_name=f"gov_schedule_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
            )
        else:
            st.warning("未能成功獲取任何首長資料。")
else:
    st.info("請點擊上方按鈕開始抓取今日行程。")
