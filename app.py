import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# 1. Conexão Segura
@st.cache_resource
def get_engine():
    # A URL está no secrets do Streamlit Cloud
    return create_engine(st.secrets["DATABASE_URL"])

engine = get_engine()

# 2. Autenticação (Acesso Privado)
user = st.user
if "email" not in user:
    st.error("Acesso não autorizado.")
    st.stop()

user_email = user["email"]

# 3. Query Segura (Sem concatenação de string)
def carregar_dados():
    query = text("SELECT * FROM transacoes WHERE user_email = :email")
    with engine.connect() as conn:
        # Passar o e-mail como parâmetro protege contra SQL Injection
        return pd.read_sql(query, conn, params={"email": user_email})

# 4. Inserção Segura
def salvar_transacao(data, valor, descricao, categoria):
    query = text("""
        INSERT INTO transacoes (data, valor, descricao, categoria, user_email) 
        VALUES (:data, :valor, :desc, :cat, :email)
    """)
    with engine.connect() as conn:
        conn.execute(query, {
            "data": data, "valor": valor, "desc": descricao, 
            "cat": categoria, "email": user_email
        })
        conn.commit()