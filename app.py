import streamlit as st
import pandas as pd
import requests
from io import StringIO

st.set_page_config(page_title="📈 Ações Mensais - Fundamentus", layout="wide")
st.title("📈 Ações Mensais - Fundamentus")

url = "https://www.fundamentus.com.br/resultado.php"
headers = {"User-Agent": "Mozilla/5.0"}

# Buscar dados do Fundamentus
try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    df = pd.read_html(StringIO(response.text), decimal=",", thousands=".")[0]
except Exception as e:
    st.error(f"Erro ao buscar dados do Fundamentus: {e}")
    st.stop()

# Padroniza os nomes de colunas conforme Fundamentus
df.columns = [
    'Papel', 'Cotação', 'P/L', 'P/VP', 'PSR', 'Div.Yield', 'P/Ativo', 'P/Cap.Giro',
    'P/EBIT', 'P/Ativ Circ.Liq', 'EV/EBIT', 'EV/EBITDA', 'Mrg Ebit', 'Mrg. Líq.',
    'Liq. Corr.', 'ROIC', 'ROE', 'Liq.2meses', 'Patrim. Líq', 'Div.Brut/ Patrim.',
    'Cresc. Rec.5a'
]

# Converter colunas numéricas
cols_numericas = ['P/L', 'P/VP', 'Div.Yield', 'ROE', 'ROIC', 'Liq.2meses', 'Cresc. Rec.5a']
for col in cols_numericas:
    df[col] = (
        df[col]
        .astype(str)
        .str.replace("%", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.replace("-", "0", regex=False)
    )
    df[col] = pd.to_numeric(df[col], errors="coerce")

# --- Filtros fixos (ajuste à vontade) ---
pl_min = 3.0
pl_max = 12.0
roe_min = 15.0
roe_max = 50.0
dy_min = 5.0
dy_max = 20.0
roic_min = 8.0
liq_2m = 60000000.0
cresc_5a = 5

filtros = (
    (df['P/L'] >= pl_min) &
    (df['P/L'] <= pl_max) &
    (df['ROE'] >= roe_min) &
    (df['ROE'] <= roe_max) &
    (df['Div.Yield'] >= dy_min) &
    (df['Div.Yield'] <= dy_max) &
    (df['Liq.2meses'] >= liq_2m) &
    (df['Cresc. Rec.5a'] >= cresc_5a)
)
df_filtrado = df.loc[filtros].copy()

st.subheader("📊 Ações filtradas")
st.dataframe(df_filtrado, use_container_width=True)

# Função genérica para pegar Top 5 por critério
def top5(df_, coluna, ascending):
    base = df_[['Papel', coluna]].dropna().copy()
    if base.empty:
        return pd.DataFrame(columns=['Papel', coluna])
    return base.sort_values(by=coluna, ascending=ascending).head(5)

# Gera Top 5s
rank_pl    = top5(df_filtrado, 'P/L',          ascending=True)
rank_pvp   = top5(df_filtrado, 'P/VP',         ascending=True)
rank_dy    = top5(df_filtrado, 'Div.Yield',    ascending=False)
rank_roe   = top5(df_filtrado, 'ROE',          ascending=False)
rank_liq   = top5(df_filtrado, 'Liq.2meses',   ascending=False)
rank_cresc = top5(df_filtrado, 'Cresc. Rec.5a',ascending=False)

# Combina todos os Top 5s
all_tops = pd.concat([
    rank_pl.assign(Critério='P/L'),
    rank_pvp.assign(Critério='P/VP'),
    rank_dy.assign(Critério='Div.Yield'),
    rank_roe.assign(Critério='ROE'),
    rank_liq.assign(Critério='Liq.2meses'),
    rank_cresc.assign(Critério='Cresc. Rec.5a')
], ignore_index=True)

# Conta quantas vezes cada Papel aparece no Top 5
ranking_final = (
    all_tops.groupby('Papel', as_index=False)
    .agg(Ranking=('Critério', 'count'))
    .sort_values('Ranking', ascending=False)
)

# Junta alguns indicadores de referência
ranking_final = ranking_final.merge(
    df_filtrado[['Papel', 'P/L', 'P/VP', 'Div.Yield', 'ROE', 'Liq.2meses', 'Cresc. Rec.5a']],
    on='Papel',
    how='left'
)

# Exibe resultado final
st.subheader("🏆 Ações que mais apareceram nos Top 5")
st.dataframe(ranking_final, use_container_width=True)

# Download CSV
st.download_button(
    "📥 Baixar Ranking (CSV)",
    ranking_final.to_csv(index=False).encode('utf-8'),
    "ranking_top5_frequencia.csv",
    "text/csv"
)
