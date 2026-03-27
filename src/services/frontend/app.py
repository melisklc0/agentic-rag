import logging

import streamlit as st

from src.core.logger import setup_logging


if "_logging_configured" not in st.session_state:
    setup_logging()
    st.session_state["_logging_configured"] = True
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Agentic RAG Frontend", layout="wide")

st.title("🤖 Agentic RAG Dashboard")
st.write("Streamlit arayüzü başarıyla yapılandırıldı!")

st.sidebar.info("Buraya API bağlantı ayarlarını ekleyebilirsin.")

if st.button("API Health Check"):
    logger.info("API Health Check button clicked")
    st.write("API kontrol ediliyor...")
    # Burada backend API'ye istek atılabilir
