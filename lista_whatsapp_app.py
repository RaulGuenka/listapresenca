"""
Lista WhatsApp - Checklist de Kit por Equipe (com Supabase)
=============================================================
Reproduz em Streamlit a tabela de checkboxes das colunas D:I da planilha
"Batedores - Equipes" (aba "Lista WhatsApp"):

    Equipe / Nome | Presença | Apito | Lanterna | Lanterna Sinalizadora | Colete

Os dados agora ficam na tabela `kit_checklist` do Supabase, então os
checkboxes marcados persistem mesmo fechando o app ou reiniciando o servidor.

Setup (uma vez só):
    1. Rode supabase_schema.sql no SQL Editor do seu projeto Supabase.
    2. Rode supabase_seed.sql para popular a tabela com as equipes/nomes.
    3. Crie .streamlit/secrets.toml (veja exemplo no final deste arquivo).
    4. pip install streamlit pandas supabase
    5. streamlit run lista_whatsapp_app.py
"""

import pandas as pd
import streamlit as st
from supabase import create_client, Client

st.set_page_config(page_title="Lista WhatsApp - Checklist de Kit", page_icon="✅", layout="wide")

KIT_COLS = {
    "presenca": "Presença",
    "apito": "Apito",
    "lanterna": "Lanterna",
    "lanterna_sinalizadora": "Lanterna Sinalizadora",
    "colete": "Colete",
}
LABEL_COLS = list(KIT_COLS.values())      # nomes exibidos na tela
TABLE = "kit_checklist"


# ---------------------------------------------------------------------------
# Conexão com o Supabase
# ---------------------------------------------------------------------------
@st.cache_resource
def get_client() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


@st.cache_data(ttl=5)
def fetch_checklist() -> pd.DataFrame:
    supabase = get_client()
    resp = (
        supabase.table(TABLE)
        .select("id, equipe, nome, presenca, apito, lanterna, lanterna_sinalizadora, colete, ordem")
        .order("equipe")
        .order("ordem")
        .execute()
    )
    return pd.DataFrame(resp.data)


def update_row(row_id: int, changes: dict):
    """Grava no Supabase apenas os campos que mudaram para essa linha."""
    supabase = get_client()
    supabase.table(TABLE).update(changes).eq("id", row_id).execute()


# ---------------------------------------------------------------------------
# Carregar dados
# ---------------------------------------------------------------------------
st.title("✅ Lista WhatsApp — Checklist de Kit")
st.caption("Marque a presença e os itens de kit entregues a cada batedor, por equipe. Salva direto no Supabase.")

try:
    df_all = fetch_checklist()
except Exception as e:
    st.error(
        "Não consegui conectar ao Supabase. Confira `SUPABASE_URL` e `SUPABASE_KEY` "
        "em `.streamlit/secrets.toml` e se a tabela `kit_checklist` já existe.\n\n"
        f"Erro: {e}"
    )
    st.stop()

if df_all.empty:
    st.warning(
        "A tabela `kit_checklist` está vazia. Rode o script `supabase_seed.sql` "
        "no SQL Editor do Supabase para popular as equipes e nomes."
    )
    st.stop()

df_all = df_all.rename(columns={"nome": "Nome", **KIT_COLS})

# ---------------------------------------------------------------------------
# Resumo geral (métricas)
# ---------------------------------------------------------------------------
total_pessoas = len(df_all)
total_presentes = int(df_all["Presença"].sum())

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Pessoas", total_pessoas)
col2.metric("Presentes", f"{total_presentes}/{total_pessoas}")
for col, key in zip([col3, col4, col5, col6], ["Apito", "Lanterna", "Lanterna Sinalizadora", "Colete"]):
    entregues = int(df_all[key].sum())
    col.metric(key, f"{entregues}/{total_pessoas}")

st.divider()

# ---------------------------------------------------------------------------
# Filtro rápido
# ---------------------------------------------------------------------------
busca = st.text_input("🔎 Buscar por nome", placeholder="Digite um nome para filtrar...")

if st.button("🔄 Recarregar do banco"):
    fetch_checklist.clear()
    st.rerun()

# ---------------------------------------------------------------------------
# Tabelas por equipe (checkboxes editáveis, gravando no Supabase)
# ---------------------------------------------------------------------------
column_config = {
    "id": None,  # coluna oculta, usada só para saber qual linha atualizar
    "Nome": st.column_config.TextColumn("Nome", disabled=True, width="medium"),
}
for label in LABEL_COLS:
    column_config[label] = st.column_config.CheckboxColumn(label, default=False, width="small")

inverse_kit_cols = {v: k for k, v in KIT_COLS.items()}  # "Presença" -> "presenca", etc.

for equipe, df_equipe in df_all.groupby("equipe", sort=False):
    df_equipe = df_equipe[["id", "Nome", *LABEL_COLS]].reset_index(drop=False)

    view_df = df_equipe
    if busca:
        view_df = df_equipe[df_equipe["Nome"].str.contains(busca, case=False, na=False)]
        if view_df.empty:
            continue

    marcados = int(df_equipe["Presença"].sum())
    total = len(df_equipe)

    with st.expander(f"**{equipe}** — {marcados}/{total} presentes", expanded=bool(busca)):
        edited = st.data_editor(
            view_df,
            column_config=column_config,
            hide_index=True,
            use_container_width=True,
            key=f"editor_{equipe}",
        )

        # Compara o que mudou linha a linha e grava só as diferenças no Supabase
        original_idx = view_df.set_index("id")[LABEL_COLS]
        edited_idx = edited.set_index("id")[LABEL_COLS]
        diffs = original_idx.compare(edited_idx)

        if not diffs.empty:
            for row_id in diffs.index.unique():
                changes_label = edited_idx.loc[row_id].to_dict()
                changes_db = {inverse_kit_cols[k]: bool(v) for k, v in changes_label.items()}
                update_row(int(row_id), changes_db)
            fetch_checklist.clear()
            st.rerun()

st.divider()

# ---------------------------------------------------------------------------
# Exportar
# ---------------------------------------------------------------------------
export_df = df_all[["equipe", "Nome", *LABEL_COLS]].rename(columns={"equipe": "Equipe"})
csv = export_df.to_csv(index=False).encode("utf-8-sig")
st.download_button(
    "⬇️ Baixar checklist (CSV)",
    data=csv,
    file_name="lista_whatsapp_checklist.csv",
    mime="text/csv",
)

# ---------------------------------------------------------------------------
# Exemplo de .streamlit/secrets.toml
# ---------------------------------------------------------------------------
# [Cole isto em .streamlit/secrets.toml, com seus valores reais]
#
# SUPABASE_URL = "https://SEU-PROJETO.supabase.co"
# SUPABASE_KEY = "sua-anon-key-ou-service-role-key"
