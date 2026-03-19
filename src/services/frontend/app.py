import streamlit as st

st.set_page_config(page_title="Agentic RAG Frontend", layout="wide")

st.title("🤖 Agentic RAG Dashboard")
st.write("Streamlit arayüzü başarıyla yapılandırıldı!")

st.sidebar.info("Buraya API bağlantı ayarlarını ekleyebilirsin.")

if st.button("API Health Check"):
    st.write("API kontrol ediliyor...")
    # Burada backend API'ye istek atılabilir
