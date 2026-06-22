import streamlit as tf
import pandas as pd
from spiders import ScheduleSpider

# 網頁基本設定
st.set_page_config(page_title="政府首長公開行程監測", layout="wide")

st.title("🏛️ 政府首長公開行程即時看板")
st.caption("本系統自動爬取總統府、行政院、經濟部之公開行程資訊。")

# 初始化爬蟲
spider = ScheduleSpider()

# 介面按鈕：觸發即時爬取
if st.button("🔄 立即更新行程資料", type="primary"):
    with st.spinner("正在爬取最新行程，請稍候..."):
        
        # 執行爬蟲
        premier_data = spider.get_ey_schedule("premier")
        vice_data = spider.get_ey_schedule("vice")
        
        # 合併資料
        all_data = premier_data + vice_data
        
        # 轉換為 DataFrame 呈現
        if all_data:
            df = pd.DataFrame(all_data)
            st.success("資料更新成功！")
            
            # 顯示表格
            st.subheader("今日行程列表")
            st.dataframe(df, use_container_width=True)
            
            # 提供下載 CSV 功能
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 下載行程報表 (CSV)",
                data=csv,
                file_name="government_schedule.csv",
                mime="text/csv",
            )
        else:
            st.warning("未抓取到任何行程資料。")
else:
    st.info("請點擊上方按鈕開始抓取今日行程。")