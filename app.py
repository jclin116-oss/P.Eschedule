import streamlit as st
import pandas as pd

# ==========================================
# 頁面基本設定
# ==========================================
st.set_page_config(layout="wide", page_title="跨機關行程觀測系統")
st.title("🏛️ 跨機關行程觀測系統")

# ==========================================
# 1. 全域日期選擇器 (主控台)
# ==========================================
# 系統會自動對齊並撈出雙方當天行程
target_date = st.selectbox(
    "📅 請選擇欲觀測的統一日期（系統會自動對齊並撈出雙方當天行程）：",
    options=["6月23日", "6月24日"]
)

st.markdown(f"## 🔍 觀測焦點：{target_date}")

# ==========================================
# 2. 資料庫 / 爬蟲 Raw Text 模擬來源
# ==========================================
# 這裡模擬你各機關爬蟲抓到的 Raw Data，實務上可對接你的資料庫或檔案
raw_data_store = {
    "6月23日": {
        "moea": [
            {"首長類別": "次長", "行程內容": "2:00 PM 何晉滄次長陪同行政院長..."},
            {"首長類別": "所屬單位記者會", "行程內容": "4:00 PM 統計處黃偉傑處長主持..."}
        ],
        "president_raw": """
        中華民國總統府
        115年6月23日 星期二

        總統
        無公開行程

        副總統
        09:30 出席AFACT第44屆期中理事會議暨數位經濟「雙軸轉型」與「新國際合作」亞太區域國際論壇開幕

        總統府
        09:00~11:30 總統府開放參觀(入口報到處:博愛路、寶慶路口)
        """
    },
    "6月24日": {
        "moea": [
            {"首長類別": "部長", "行程內容": "10:00 AM 部長出席部務會議"}
        ],
        "president_raw": """
        中華民國總統府
        115年6月24日 星期三

        總統
        10:00 接見外賓特使團

        副總統
        無公開行程
        """
    }
}

# ==========================================
# 3. 總統府核心切分邏輯解析器
# ==========================================
def parse_president_schedule(text):
    if not text:
        return pd.DataFrame()
        
    lines = [line.strip() for line in text.strip().split("\n") if line.strip()]
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
            # 排除無公開行程，僅紀錄實質行程
            if "無公開行程" not in line:
                parsed_data.append({
                    "首長類別": current_role,
                    "行程內容": line
                })
                
    return pd.DataFrame(parsed_data)

# 獲取當前日期的資料
current_data = raw_data_store.get(target_date, {"moea": [], "president_raw": ""})

# ==========================================
# 4. 經濟部首長行程看板
# ==========================================
st.markdown("### 🏭 經濟部首長行程")
if current_data["moea"]:
    df_moea = pd.DataFrame(current_data["moea"])
    st.table(df_moea)
else:
    st.info("經濟部在當天無公告行程資料。")

# ==========================================
# 5. 總統府首長行程看板 (與經濟部完全一致的表格樣式)
# ==========================================
st.markdown("### 🏛️ 總統府首長行程")

# 呼叫解析器處理當天 Raw Text
df_president = parse_president_schedule(current_data["president_raw"])

if not df_president.empty:
    # 樣式與欄位名稱完全對齊經濟部
    st.table(df_president)
else:
    # 預留原本的提示藍框樣式
    st.info(f"總統府在 {target_date} 無任何公告行程資料。")

# ==========================================
# 6. 後台全量文字協作區塊 (置於底部，方便除錯與新機關協作)
# ==========================================
st.markdown("---")
with st.expander("📝 查看各機關原始撈取文本 (後台除錯與協作用)"):
    tab_p, tab_b, tab_c = st.tabs(["🏛️ 總統府", "🏢 機關 B", "🏢 機關 C"])
    
    with tab_p:
        st.code(current_data["president_raw"].strip(), language="text")
    with tab_b:
        st.text("等待爬蟲餵入 Raw Text...")
    with tab_c:
        st.text("等待爬蟲餵入 Raw Text...")
