import streamlit as st
import pandas as pd

# ==========================================
# 頁面基本設定
# ==========================================
st.set_page_config(layout="wide", page_title="跨機關行程觀測系統")
st.title("🏛️ 跨機關行程觀測與全量文字協作監測")

target_date = "6月23日"
st.subheader(f"🔍 觀測焦點：{target_date}")

# ==========================================
# 1. 經濟部首長行程 (維持原本做法)
# ==========================================
st.markdown("### 🏭 經濟部首長行程")
mock_moea_data = [
    {"首長類別": "次長", "行程內容": "2:00 PM 何晉滄次長陪同行政院長..."},
    {"首長類別": "所屬單位記者會", "行程內容": "4:00 PM 統計處黃偉傑處長主持..."}
]
st.table(mock_moea_data)

# ==========================================
# 2. 全量文字協作區塊 (替代當週總表)
# ==========================================
st.markdown("---")
st.markdown("### 📝 各機關全量文字擷取 (協作與切分前置)")
st.caption("以下區塊依序呈現各機關直接抓取的 Raw Text，確認文字完整後將進行下一步切分。")

# 建立機關分頁標籤，方便後續擴充
tab_president, tab_agency2, tab_agency3 = st.tabs(["🏛️ 總統府", "🏢 機關 B (待加入)", "🏢 機關 C (待加入)"])

# ------------------------------------------
# 【總統府頁籤邏輯】
# ------------------------------------------
with tab_president:
    st.markdown(f"**【總統府 - {target_date} 撈取文本】**")
    
    # 爬蟲抓取到的原始工整文字
    president_raw_text = """
    中華民國總統府
    115年6月23日 星期二

    總統
    無公開行程

    副總統
    09:30 出席AFACT第44屆期中理事會議暨數位經濟「雙軸轉型」與「新國際合作」亞太區域國際論壇開幕

    總統府
    09:00~11:30 總統府開放參觀(入口報到處:博愛路、寶慶路口)
    """
    
    # 呈現原始文字供檢視
    st.code(president_raw_text.strip(), language="text")
    
    # 總統府專屬切分功能
    def parse_president_and_vice_schedule(text):
        lines = [line.strip() for line in text.strip().split("\n") if line.strip()]
        
        # 僅將「總統」與「副總統」納入目標角色，直接排除「總統府」
        target_roles = {"總統", "副總統"}
        parsed_data = []
        current_role = None
        
        for line in lines:
            if line in target_roles:
                current_role = line
                continue
            elif line == "總統府":
                current_role = None
                continue
                
            if current_role:
                # 排除無公開行程的文字，僅記錄實質行程
                if "無公開行程" not in line:
                    parsed_data.append({
                        "首長類別": current_role,
                        "行程內容": line
                    })
                    
        return pd.DataFrame(parsed_data)

    # 執行切分與呈現
    if st.button("測試總統府文字切分", key="btn_test_pres"):
        df_result = parse_president_and_vice_schedule(president_raw_text)
        
        if not df_result.empty:
            st.success("切分成功！已過濾無行程與總統府項目：")
            st.table(df_result)
        else:
            st.warning("當天首長皆無公開行程。")

# ------------------------------------------
# 【機關 B 頁籤】(留空準備協作)
# ------------------------------------------
with tab_agency2:
    st.markdown("**【機關 B 撈取文本】**")
    agency2_raw_text = "等待爬蟲餵入 Raw Text..."
    st.code(agency2_raw_text, language="text")

# ------------------------------------------
# 【機關 C 頁籤】(留空準備協作)
# ------------------------------------------
with tab_agency3:
    st.markdown("**【機關 C 撈取文本】**")
    agency3_raw_text = "等待爬蟲餵入 Raw Text..."
    st.code(agency3_raw_text, language="text")
