import streamlit as st

st.set_page_config(layout="wide")
st.title(" 跨機關行程觀測與全量文字協作監測")

# 模擬目前選擇的日期（與你的系統連動）
target_date = "6月23日"
st.subheader(f"🔍 觀測焦點：{target_date}")

# ==========================================
# 1. 經濟部首長行程 (原本已完成的表格)
# ==========================================
st.markdown("### 🏭 經濟部首長行程")
# 這裡維持你原本的 DataFrame 顯示邏輯
mock_moea_data = [
    {"首長類別": "次長", "行程內容": "2:00 PM 何晉滄次長陪同行政院長..."},
    {"首長類別": "所屬單位記者會", "行程內容": "4:00 PM 統計處黃偉傑處長主持..."}
]
st.table(mock_moea_data)


# ==========================================
# 2. 全量文字協作區塊 (替代原本的當週總表)
# ==========================================
st.markdown("---")
st.markdown("### 📝 各機關全量文字擷取 (協作與切分前置)")
st.caption("以下區塊依序呈現各機關直接抓取的 Raw Text，確認文字完整後將進行下一步切分。")

# 建立頁籤（Tabs），方便管理多個機關，畫面會非常乾淨
tab_president, tab_agency2, tab_agency3 = st.tabs(["🏛️ 總統府", "🏢 機關 B (待加入)", "🏢 機關 C (待加入)"])

# --- 總統府頁籤 ---
with tab_president:
    st.markdown(f"**【總統府 - {target_date} 撈取文本】**")
    
    # 📌 這裡放你剛剛利用 `.get_text()` 或 `.text` 抓下來的原始文字
    # 這裡我先用 image_2 的內容做為示意
    president_raw_text = """
    中華民國總統府
    115年6月23日 星期二
    
    總統
    無公開行程
    
    副總統
    09:30 出席AFACT第44屆期中理事會議暨數位經濟「雙軸轉型」與「新國際合作」亞太區域國際論壇開幕式
    
    總統府
    09:00~11:30 總統府開放參觀(入口報到處:博愛路、寶慶路口)
    """
    
    # 使用 code 區塊或是 text_area 呈現，方便複製、查看換行符號，且文字不會亂掉
    st.code(president_raw_text.strip(), language="text")
    
    # 預留未來的切分測試按鈕（等一下可以用）
    if st.button("測試總統府文字切分", key="btn_test_pres"):
        st.info("等待切分邏輯寫入...")

# --- 機關 B 頁籤 (留空準備協作) ---
with tab_agency2:
    st.markdown("**【機關 B 撈取文本】**")
    agency2_raw_text = "等待爬蟲餵入 Raw Text..."
    st.code(agency2_raw_text, language="text")

# --- 機關 C 頁籤 (留空準備協作) ---
with tab_agency3:
    st.markdown("**【機關 C 撈取文本】**")
    agency3_raw_text = "等待爬蟲餵入 Raw Text..."
    st.code(agency3_raw_text, language="text")
