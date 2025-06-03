import streamlit as st
import json

st.title("Verificando credenciais...")

try:
    creds = json.loads(st.secrets["gcp_service_account"])
    st.success("✅ Credenciais carregadas com sucesso!")
    st.json(creds)
except Exception as e:
    st.error(f"❌ Erro ao carregar credenciais: {e}")
