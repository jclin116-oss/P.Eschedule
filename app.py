import streamlit as st
import spiders

st.set_page_config(page_title="政府政要行程儀表板", layout="wide")
st.title("政府政要行程與公告監測")

# 快取設定：避免頻繁存取造成被封鎖
@st.cache_data(ttl=3600)
def load_moea():
    return spiders.fetch_rss_data("https://www.moea.gov.tw/Mns/populace/news/NewsRSSdetail.aspx?Kind=10")

@st.cache_data(ttl=3600)
def load_ey():
    return spiders.fetch_rss_data("https://www.ey.gov.tw/RSS_Content2.aspx?PID=c98e07e2-66b4-4c90-a68d-2ef8ef8cf550")

@st.cache_data(ttl=3600)
def load_president():
    return spiders.get_president_schedule()

# 介面佈局
tab1, tab2, tab3 = st.tabs(["經濟部", "行政院", "總統府"])

with tab1:
    st.subheader("經濟部最新公告")
    st.dataframe(load_moea(), use_container_width=True)

with tab2:
    st.subheader("行政院最新公告")
    st.dataframe(load_ey(), use_container_width=True)

with tab3:
    st.subheader("總統/副總統行程")
    df_po = load_president()
    if not df_po.empty:
        st.table(df_po)
    else:
        st.info("目前無公開行程。")
