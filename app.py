import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# Configuração da página
st.set_page_config(page_title="Finanças Pro", layout="wide")

# 1. Conexão Segura com o Supabase
@st.cache_resource
def get_engine():
    return create_engine(st.secrets["DATABASE_URL"])

engine = get_engine()

# 2. Login e Autenticação (Integrado ao Streamlit Cloud)
user = st.user

# Verifica se o Streamlit já carregou as informações do usuário
# Usamos o acesso por chave ["email"] e verificamos se o dicionário não está vazio
if not user or "email" not in user or not user["email"]:
    st.info("Autenticando... por favor, aguarde.")
    st.rerun() 

user_email = user["email"]
st.title(f"💰 Gestão Financeira: {user_email}")

# 3. Funções de Banco de Dados (Seguras contra SQL Injection)
def carregar_dados():
    query = text("SELECT * FROM transacoes WHERE user_email = :email")
    with engine.connect() as conn:
        return pd.read_sql(query, conn, params={"email": user_email})

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

# 4. Interface do Dashboard
df = carregar_dados()

if not df.empty:
    st.dataframe(df)
    
    # Exemplo de lógica 60/30/10
    total_renda = df[df['valor'] > 0]['valor'].sum()
    st.metric("Renda Total Registrada", f"R$ {total_renda:,.2f}")
else:
    st.write("Nenhuma transação encontrada para este usuário.")

# Upload de novos dados (opcional)
st.sidebar.subheader("Nova Transação")
with st.sidebar.form("nova_transacao"):
    data = st.date_input("Data")
    valor = st.number_input("Valor", step=0.01)
    desc = st.text_input("Descrição")
    cat = st.selectbox("Categoria", ["Essenciais", "Estilo de Vida", "Investimentos"])
    if st.form_submit_button("Salvar"):
        salvar_transacao(data, valor, desc, cat)
        st.success("Salvo!")
        st.rerun()