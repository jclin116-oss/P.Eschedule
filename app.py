import urllib.request
import ssl
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st

st.set_page_config(page_title="雙首長行程一體化觀測站", layout="wide")
st.title("🏛️ 經濟部 ✖️ 總統府 行程同步觀測站")
st.caption("聯合作戰版：選擇單一日期，同時對照兩大核心單位的公開行程")

# 一鍵同步按鈕（全域同步）
if st.button("🔄 一鍵同步最新行程資料（經濟部 ＋ 總統府）") or 'combined_data_ready' not in st.session_state:
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    context = ssl._create_unverified_context()
    
    # ------------------ 1. 抓取與解析經濟部 ------------------
    moea_list = []
    try:
        url_moea = "https://www.moea.gov.tw/Mns/populace/news/MinisterSchedule.aspx?menu_id=42225"
        req_moea = urllib.request.Request(url_moea, headers=headers)
        with urllib.request.urlopen(req_moea, context=context) as res:
            soup_moea = BeautifulSoup(res.read(), 'html.parser')
        lines_moea = [l.strip() for l in soup_moea.text.split('\n') if l.strip()]
        
        current_date, current_leader, current_buffer = "未定日期", None, []
        def save_moea():
            if current_buffer and current_leader:
                clean = [l for l in current_buffer if not any(n in l for n in ["目前總共有", "筆資料", "上一頁", "下一頁", "網站安全政策", "隱私權保護宣告", "如欲查詢歷史資訊", "首長行程(歷史資料)"])]
                if clean:
                    content = "\n".join(clean)
                    if not any(noise in content for noise in ["首長類別", "關鍵字", "主視覺", "RSS"]) and content.strip():
                        moea_list.append({"日期": current_date, "單位": "經濟部", "首長類別": current_leader, "行程內容": content})
                        
        LEADER_MOEA = ["部長", "次長", "所屬單位記者會"]
        for line in lines_moea:
            if any(stop in line for stop in ["如欲查詢歷史資訊", "首長行程(歷史資料)", "目前總共有", "網站安全政策"]):
                save_moea(); break
            if '月' in line and '日' in line and len(line) < 15:
                if not any(tag in line for tag in LEADER_MOEA):
                    save_moea()
                    current_date = line.replace("2026", "").strip() # 洗成 6月23日
                    current_leader, current_buffer = None, []
                    continue
            if line in LEADER_MOEA:
                save_moea(); current_leader = line; current_buffer = []; continue
            if current_leader:
                if line not in current_buffer: current_buffer.append(line)
                if "本日無公開行程" in line:
                    save_moea(); current_leader, current_buffer = None, []
        save_moea()
    except Exception as e:
        st.error(f"經濟部連線或解析失敗: {e}")

    # ------------------ 2. 抓取與解析總統府 ------------------
    pres_list = []
    try:
        url_pres = "https://www.president.gov.tw/Page/37"
        req_pres = urllib.request.Request(url_pres, headers=headers)
        with urllib.request.urlopen(req_pres, context=context) as res:
            soup_pres = BeautifulSoup(res.read(), 'html.parser')
        lines_pres = [l.strip() for l in soup_pres.text.split('\n') if l.strip()]
        
        current_date, current_leader, current_buffer = "未定日期", None, []
        def save_pres():
            if current_buffer and current_leader:
                clean = [l for l in current_buffer if not any(n in l for n in ["版權所有", "中華民國總統府", "聯絡我們", "隱私權", "政府網站資料開放宣告"])]
                if clean:
                    content = "\n".join(clean)
                    if not any(noise in content for noise in ["影音", "新聞稿", "致詞", "寫信給總統"]) and content.strip():
                        pres_list.append({"日期": current_date, "單位": "總統府", "首長類別": current_leader, "行程內容": content})

        LEADER_PRES = ["總統", "副總統", "總統府"]
        for line in lines_pres:
            if '年' in line and '月' in line and '日' in line and len(line) < 25:
                if not any(tag in line for tag in LEADER_PRES) and "版權所有" not in line:
                    save_pres()
                    # 精準切除：民國年 與 星期幾，只留下「X月X日」以便與經濟部對齊
                    clean_date = line.split("年")[-1].strip() if "年" in line else line
                    if " " in clean_date: 
                        clean_date = clean_date.split(" ")[0].strip() # 拿掉「星期二」
                    current_date = clean_date
                    current_leader, current_buffer = None, []
                    continue
            if line in LEADER_PRES:
                save_pres(); current_leader = line; current_buffer = []; continue
            if current_leader:
                if line not in current_buffer: current_buffer.append(line)
                if "無公開行程" in line:
                    save_pres(); current_leader, current_buffer = None, []
        save_pres()
    except Exception as e:
        st.error(f"總統府連線或解析失敗: {e}")

    # ------------------ 3. 資料整併與清洗 ------------------
    df_moea = pd.DataFrame(moea_list)
    df_pres = pd.DataFrame(pres_list)
    
    st.session_state.moea_df = df_moea
    st.session_state.pres_df = df_pres
    st.session_state.combined_data_ready = True
    st.success("🎉 雙方戰略情資已全數同步完成！")

# ==================== 4. 聯合作戰大面板 ====================
if 'combined_data_ready' in st.session_state:
    df_m = st.session_state.moea_df
    df_p = st.session_state.pres_df
    
    # 撈出兩邊所有的不重複日期，合併做成大下拉選單
    all_dates = set()
    if not df_m.empty: all_dates.update(df_m['日期'].unique())
    if not df_p.empty: all_dates.update(df_p['日期'].unique())
    
    sorted_dates = sorted(list(all_dates), reverse=True)
    
    if sorted_dates:
        st.markdown("---")
        # 👑 唯一的中央控制大選單
        chosen_date = st.selectbox(
            "📅 **請選擇欲觀測的統一日期**（系統會自動對齊並撈出雙方當天行程）：", 
            options=sorted_dates, 
            index=0
        )
        st.markdown(f"### 🔍 觀測焦點：{chosen_date}")
        
        # 左右分欄排列（1比1等寬）
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🏭 經濟部首長行程")
            if not df_m.empty:
                f_m = df_m[df_m['日期'] == chosen_date]
                if not f_m.empty:
                    st.dataframe(f_m[['首長類別', '行程內容']], use_container_width=True)
                else:
                    st.info(f"💡 經濟部在 {chosen_date} 無任何公告行程資料。")
            else:
                st.warning("經濟部無初始資料。")
                
        with col2:
            st.subheader("🏛️ 總統府首長行程")
            if not df_p.empty:
                f_p = df_p[df_p['日期'] == chosen_date]
                if not f_p.empty:
                    st.dataframe(f_p[['首長類別', '行程內容']], use_container_width=True)
                else:
                    st.info(f"💡 總統府在 {chosen_date} 無任何公告行程資料。")
            else:
                st.warning("總統府無初始資料。")
                
        # 底部附上全景對照大表
        st.markdown("---")
        with st.expander("📊 查看當週總表（經濟部 ＋ 總統府全量數據）"):
            st.write("🔧 經濟部全量累積數據：")
            st.dataframe(df_m, use_container_width=True)
            st.write("🔧 總統府全量累積數據：")
            st.dataframe(df_p, use_container_width=True)
    else:
        st.warning("⚠️ 目前資料庫內無任何可供比對的日期。")
