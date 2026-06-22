import streamlit as st
import pandas as pd
from spiders import ScheduleSpider
from datetime import datetime

st.set_page_config(page_title="政府首長公開行程監測", layout="wide")

st.title("🏛️ 政府首長公開行程即時看板")import requests
from bs4 import BeautifulSoup
from datetime import datetime
import urllib3
from urllib3.exceptions import InsecureRequestWarning

urllib3.disable_warnings(InsecureRequestWarning)

class ScheduleSpider:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7"
        }

    def _match_date(self, text, *date_variants):
        """內部工具：檢查文本是否包含指定的任一日期格式"""
        return any(v in text for v in date_variants)

    def get_ey_schedule(self, *date_variants):
        """抓取行政院行程並過濾日期"""
        url = "https://www.ey.gov.tw/Page/ECE410333003326E"
        try:
            res = requests.get(url, headers=self.headers, timeout=12, verify=False)
            if res.status_code != 200:
                return [{"官職": "行政院", "行程內容": f"站點回應錯誤 (HTTP {res.status_code})", "時間/地點": "-"}]

            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            schedules = []
            
            items = soup.select('tr') or soup.select('.schedule-item') or soup.select('li')
            
            for item in items:
                text = " ".join(item.get_text(separator=" ").split())
                if not text or "暫無行程" in text or "目前無相關資料" in text or len(text) < 10:
                    continue
                
                # 行項必須符合所選日期才納入
                if self._match_date(text, *date_variants):
                    target = "行政院長" if "院長" in text and "副院長" not in text else ("行政副院長" if "副院長" in text else "行政院綜合")
                    schedules.append({
                        "官職": target,
                        "行程內容": text,
                        "時間/地點": "見內文"
                    })
            
            if not schedules:
                return [{"官職": "行政院", "行程內容": "該日期於官網首頁無公開行程顯示", "時間/地點": "-"}]
            return schedules
        except Exception as e:
            return [{"官職": "行政院", "行程內容": f"連線異常: {str(e)}", "時間/地點": "-"}]

    def get_president_schedule(self, *date_variants):
        """抓取總統府行程並過濾日期"""
        url = "https://www.president.gov.tw/Page/37"
        target_name = "總統"
        try:
            res = requests.get(url, headers=self.headers, timeout=12, verify=False)
            if res.status_code != 200:
                return [{"官職": target_name, "行程內容": f"站點回應錯誤 (HTTP {res.status_code})", "時間/地點": "-"}]
                
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            schedules = []
            
            items = soup.select('tr') or soup.select('li') or soup.select('.p-list-item')
            for item in items:
                text = " ".join(item.get_text(separator=" ").split())
                if text and len(text) > 10 and "頁面" not in text and "版權所有" not in text:
                    # 篩選特定日期
                    if self._match_date(text, *date_variants):
                        schedules.append({
                            "官職": target_name,
                            "行程內容": text,
                            "時間/地點": "詳見官網行程頁"
                        })
            
            if not schedules:
                return [{"官職": target_name, "行程內容": "該日期於官網首頁無公開行程顯示", "時間/地點": "-"}]
            return schedules
        except Exception as e:
            return [{"官職": target_name, "行程內容": f"連線異常: {str(e)}", "時間/地點": "-"}]

    def get_moea_schedule(self, *date_variants):
        """抓取經濟部長行程並過濾日期"""
        url = "https://www.moea.gov.tw/Mns/populace/news/MinisterSchedule.aspx?menu_id=42225"
        target_name = "經濟部長"
        try:
            res = requests.get(url, headers=self.headers, timeout=12, verify=False)
            if res.status_code != 200:
                return [{"官職": target_name, "行程內容": f"站點回應錯誤 (HTTP {res.status_code})", "時間/地點": "-"}]
                
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            schedules = []
            
            items = soup.select('tr') or soup.select('table tr')
            for item in items:
                tds = item.select('td')
                if len(tds) >= 2:
                    time_info = " ".join(tds[0].get_text(separator=" ").split())
                    content_info = " ".join(tds[1].get_text(separator=" ").split())
                    
                    full_text = f"{time_info} {content_info}"
                    if "暫無行程" in content_info or "無公開行程" in content_info:
                        continue
                        
                    # 檢查時間欄位或內文是否包含所選日期
                    if self._match_date(full_text, *date_variants):
                        schedules.append({
                            "官職": target_name,
                            "行程內容": content_info,
                            "時間/地點": time_info
                        })
            
            if not schedules:
                return [{"官職": target_name, "行程內容": "該日期於官網首頁無公開行程顯示", "時間/地點": "-"}]
            return schedules
        except Exception as e:
            return [{"官職": target_name, "行程內容": f"連線異常: {str(e)}", "時間/地點": "-"}]

# --- 新增功能：日期選擇器 ---
today = datetime.now().date()
selected_date = st.date_input("請選擇欲查詢的行程日期：", today)
date_str = selected_date.strftime("%Y-%m-%d")
# 中文格式用於部分網頁關鍵字比對 (例如 115/06/22 或 115年6月22日)
roc_year = selected_date.year - 1911
date_zh_variant1 = f"{roc_year}年{selected_date.month}月{selected_date.day}日"
date_zh_variant2 = f"{roc_year}/{selected_date.month:02d}/{selected_date.day:02d}"

st.caption(f"本系統將檢索官網近期行程，並自動過濾出符合 【{date_str}】 或 【{date_zh_variant1}】 的資料。")

spider = ScheduleSpider()

if st.button("🔄 立即更新並篩選行程資料", type="primary"):
    with st.spinner(f"正在檢索並篩選 {date_str} 的行程，請稍候..."):
        
        # 執行爬蟲，將日期變體傳入過濾
        ey_data = spider.get_ey_schedule(date_str, date_zh_variant1, date_zh_variant2)
        president_data = spider.get_president_schedule(date_str, date_zh_variant1, date_zh_variant2)
        moea_data = spider.get_moea_schedule(date_str, date_zh_variant1, date_zh_variant2)
        
        all_data = president_data + ey_data + moea_data
        
        if all_data:
            df = pd.DataFrame(all_data)
            df['檢查時間'] = datetime.now().strftime("%Y-%m-%d %H:%M")
            df = df[['官職', '時間/地點', '行程內容', '檢查時間']]
            
            st.success(f"{date_str} 資料篩選完成！")
            st.subheader(f"📅 {date_str} 行程列表")
            st.dataframe(df, use_container_width=True, hide_index=True)
            
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
