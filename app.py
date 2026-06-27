import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

# --- Configuração ---
st.set_page_config(page_title="Finanças Pro 60/30/10", layout="wide")

# Conexão com o Supabase via Secrets
@st.cache_resource
def get_engine():
    return create_engine(st.secrets["DATABASE_URL"])

engine = get_engine()

# --- Autenticação (Acesso Privado no Streamlit Cloud) ---
if "email" not in st.experimental_user:
    st.warning("Acesso restrito. Faça login.")
    st.stop()

st.title("💰 Gestão Financeira Pessoal")

# --- Funções de Banco de Dados ---
def carregar_dados():
    return pd.read_sql("SELECT * FROM transacoes", engine)

def salvar_mapping(mapping_dict):
    # Salva o dicionário de mapeamento no banco ou em uma tabela de configurações
    # Por simplicidade, aqui usamos o estado da sessão e você pode expandir para salvar no SQL
    st.session_state.mapping = mapping_dict

# --- Lógica de Negócio ---
if 'mapping' not in st.session_state:
    st.session_state.mapping = {}

# Upload de novos CSVs
uploaded_file = st.sidebar.file_uploader("Importar novos lançamentos (CSV)", type="csv")
if uploaded_file:
    df_novo = pd.read_csv(uploaded_file)
    df_novo.to_sql('transacoes', engine, if_exists='append', index=False)
    st.success("Dados importados!")

# Carregar dados atuais
df = carregar_dados()
df['Data'] = pd.to_datetime(df['Data'])

# Regras de Categorização
def classificar(desc):
    if desc in st.session_state.mapping: return st.session_state.mapping[desc]
    d = desc.upper()
    if any(x in d for x in ["UBER", "99", "ABASTEC"]): return "Transporte"
    if "RDB" in d or "INVESTIMENTO" in d: return "Investimentos"
    return "Outros"

df['Categoria'] = df['Descrição'].apply(classificar)

# Definição 60/30/10
mapa_fatias = {"Essenciais": ["Transporte", "Educação"], "Estilo de Vida": ["Outros"], "Investimentos": ["Investimentos"]}
df['Fatia'] = df['Categoria'].apply(lambda x: next((k for k, v in mapa_fatias.items() if x in v), "Estilo de Vida"))

# --- Dashboard ---
mes = st.selectbox("Selecione o Mês", sorted(df['Data'].dt.month.unique()))
df_mes = df[df['Data'].dt.month == mes]

# Exibição
total_renda = df_mes[df_mes['Valor'] > 0]['Valor'].sum()
st.metric("Renda Mensal", f"R$ {total_renda:,.2f}")

st.subheader("🎯 Metodologia 60/30/10")
cols = st.columns(3)
metas = {"Essenciais": 0.6, "Estilo de Vida": 0.3, "Investimentos": 0.1}

for i, (fatia, meta) in enumerate(metas.items()):
    gastos = df_mes[(df_mes['Valor'] < 0) & (df_mes['Fatia'] == fatia)]['Valor'].sum()
    pct = abs(gastos) / total_renda if total_renda > 0 else 0
    cols[i].write(f"**{fatia}**")
    cols[i].progress(min(pct / meta, 1.0))
    cols[i].caption(f"Atual: {pct:.1%} | Meta: {meta:.0%}")