import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# Configuração da página para melhor visualização
st.set_page_config(page_title="Finanças Pro", layout="wide")

# 1. Conexão Segura com o Supabase
# Certifique-se de que a chave DATABASE_URL está no 'Secrets' do Streamlit Cloud
@st.cache_resource
def get_engine():
    return create_engine(st.secrets["DATABASE_URL"])

engine = get_engine()

# 2. Autenticação Nativa do Streamlit Cloud
# O Streamlit Cloud já injeta o e-mail do usuário logado no objeto st.user
user = st.user

if not user or not user.get("email"):
    st.error("Acesso negado: Você precisa estar logado na plataforma para acessar este dashboard.")
    st.stop()

user_email = user["email"]
st.title(f"💰 Gestão Financeira: {user_email}")

# 3. Funções de Banco de Dados (Seguras contra SQL Injection)
def carregar_dados():
    # A consulta filtra estritamente pelo e-mail do usuário autenticado
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
    st.subheader("Suas Transações")
    st.dataframe(df, use_container_width=True)
    
    # Exemplo de lógica (60/30/10)
    total_renda = df[df['valor'] > 0]['valor'].sum()
    st.metric("Renda Total", f"R$ {total_renda:,.2f}")
else:
    st.info("Nenhuma transação encontrada. Adicione a primeira!")

# Sidebar para inserção de dados
st.sidebar.subheader("Nova Transação")
with st.sidebar.form("nova_transacao", clear_on_submit=True):
    data = st.date_input("Data")
    valor = st.number_input("Valor", step=0.01)
    desc = st.text_input("Descrição")
    cat = st.selectbox("Categoria", ["Essenciais", "Estilo de Vida", "Investimentos"])
    
    if st.form_submit_button("Salvar"):
        salvar_transacao(data, valor, desc, cat)
        st.success("Salvo com sucesso!")
        st.rerun()