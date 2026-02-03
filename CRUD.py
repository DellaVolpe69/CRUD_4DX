import sys
import subprocess
import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from pathlib import Path, PureWindowsPath
import time
import requests

modulos_dir = Path(__file__).parent / "Modulos"
if not modulos_dir.exists():
    subprocess.run([
        "git", "clone",
        "https://github.com/DellaVolpe69/Modulos.git",
        str(modulos_dir)
    ], check=True)
if str(modulos_dir) not in sys.path:
    sys.path.insert(0, str(modulos_dir))
from Modulos import ConectionSupaBase
from Modulos.Minio.examples.MinIO import read_file






# --- LINK DIRETO DA IMAGEM NO GITHUB ---
url_imagem = (
    "https://raw.githubusercontent.com/DellaVolpe69/Images/main/AppBackground02.png"
)
url_logo = "https://raw.githubusercontent.com/DellaVolpe69/Images/main/DellaVolpeLogoBranco.png"
fox_image = "https://raw.githubusercontent.com/DellaVolpe69/Images/main/Foxy4.png"

st.markdown(
    f"""
    <style>
    /* Remove fundo padrão dos elementos de cabeçalho que às vezes ‘brigam’ com o BG */
    header, [data-testid="stHeader"] {{
        background: transparent;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------
# IMPORTA CONEXÃO SUPABASE
# ---------------------------------------------------



# ===============================
# Configuração da página
# ===============================
st.set_page_config(page_title="4DX - Gestão de Metas", layout="wide")

# ===============================
# Constantes de Tabelas
# ===============================
TABELA_EQUIPES = "EQUIPES_4DX"
TABELA_USUARIOS = "USUARIOS_4DX"
TABELA_METAS = "METAS_CRUCIAIS_4DX"
TABELA_MEDIDAS = "MEDIDAS_DIRECAO_4DX"
TABELA_SEMANAS = "SEMANAS_4DX"

# ===============================
# Funções utilitárias Supabase
# ===============================
def run_query(table_name):
    """Retorna um DataFrame com os dados da tabela."""
    try:
        response = supabase.table(table_name).select("*").execute()
        data = response.data
        return pd.DataFrame(data) if data else pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao carregar dados de {table_name}: {e}")
        return pd.DataFrame()

def insert_data(table_name, data):
    """Insere dados na tabela."""
    try:
        response = supabase.table(table_name).insert(data).execute()
        return response.data
    except Exception as e:
        st.error(f"Erro ao inserir em {table_name}: {e}")
        return None

def update_data(table_name, data, match_col, match_val):
    """Atualiza dados na tabela."""
    try:
        response = supabase.table(table_name).update(data).eq(match_col, match_val).execute()
        return response.data
    except Exception as e:
        st.error(f"Erro ao atualizar em {table_name}: {e}")
        return None

def delete_data(table_name, match_col, match_val):
    """Deleta dados da tabela."""
    try:
        response = supabase.table(table_name).delete().eq(match_col, match_val).execute()
        return response.data
    except Exception as e:
        st.error(f"Erro ao deletar de {table_name}: {e}")
        return None

# ===============================
# Funções de tempo
# ===============================
def inicio_semana(d=None):
    d = d or datetime.today()
    return (d - timedelta(days=d.weekday())).date()

def semana_anterior():
    return inicio_semana() - timedelta(days=7)

# ===============================
# Session State
# ===============================
for k in [
    "usuario_ok",
    "meta_ok",
    "meta_edit_visao",
    "medida_edit"
]:
    if k not in st.session_state:
        st.session_state[k] = None

# ===============================
# UI
# ===============================
st.title("🎯 4DX – Gestão de Metas")

tabs = st.tabs([
    "👥 Equipes & Usuários",
    "➕ Meta Crucial",
    "➕ Medida de Direção",
    "📊 Visão Geral"
])

# ======================================================
# TAB 0 – EQUIPES & USUÁRIOS
# ======================================================
with tabs[0]:
    st.subheader("Cadastro de Equipes")

    with st.form("form_equipe"):
        equipe = st.text_input("Equipe", key="nova_equipe")
        if st.form_submit_button("Salvar") and equipe:
            df = run_query(TABELA_EQUIPES)
            exists = False
            if not df.empty and "equipe" in df.columns:
                 if equipe in df["equipe"].values:
                     exists = True
            
            if not exists:
                insert_data(TABELA_EQUIPES, {"equipe": equipe})
                st.success("Equipe cadastrada com sucesso")
                st.rerun()
            else:
                st.warning("Equipe já existe.")

    st.divider()
    st.subheader("Cadastro de Usuários")

    if st.session_state.usuario_ok:
        st.success("Usuário cadastrado com sucesso")
        st.session_state.usuario_ok = False

    df_eq = run_query(TABELA_EQUIPES)

    if df_eq.empty:
        st.info("Cadastre uma equipe primeiro.")
    else:
        with st.form("form_user"):
            nome = st.text_input("Nome", key="user_nome")
            email = st.text_input("Email", key="user_email")
            equipe = st.selectbox("Equipe", df_eq["equipe"], key="user_equipe")
            if st.form_submit_button("Salvar") and nome and email:
                df = run_query(TABELA_USUARIOS)
                exists = False
                if not df.empty and "email" in df.columns:
                    if email in df["email"].values:
                        exists = True
                
                if not exists:
                    insert_data(TABELA_USUARIOS, {
                        "nome": nome,
                        "email": email,
                        "equipe": equipe
                    })
                    st.session_state.usuario_ok = True
                    st.rerun()
                else:
                    st.warning("Email já cadastrado.")

# ======================================================
# TAB 1 – META CRUCIAL
# ======================================================
with tabs[1]:
    st.subheader("Cadastrar Meta Crucial")

    if st.session_state.meta_ok:
        st.success("Meta salva com sucesso")
        st.session_state.meta_ok = False

    df_eq = run_query(TABELA_EQUIPES)
    df_u = run_query(TABELA_USUARIOS)
    df_m = run_query(TABELA_METAS)

    if df_eq.empty or df_u.empty:
        st.warning("Cadastre equipes e usuários antes de definir metas.")
    else:
        equipe = st.selectbox("Equipe", df_eq["equipe"], key="meta_equipe")
        # Filtrar usuarios da equipe
        users_da_equipe = df_u[df_u["equipe"] == equipe] if "equipe" in df_u.columns else pd.DataFrame()
        
        if users_da_equipe.empty:
            st.info("Sem usuários neta equipe.")
        else:
            responsavel = st.selectbox(
                "Responsável",
                users_da_equipe["nome"],
                key="resp_meta"
            )

            existente = pd.DataFrame()
            if not df_m.empty and "responsavel" in df_m.columns:
                existente = df_m[df_m["responsavel"] == responsavel]

            with st.form("form_meta"):
                # Se ja existir, preenche.
                default_meta = existente.iloc[0]["meta_crucial"] if not existente.empty else ""
                default_ind = existente.iloc[0]["indicador"] if not existente.empty else ""
                default_final = existente.iloc[0]["meta_final"] if not existente.empty else ""
                default_prazo = existente.iloc[0]["prazo"] if not existente.empty else ""

                meta = st.text_area("Meta Crucial", default_meta, key="meta_txt")
                indicador = st.text_input("Indicador", default_ind, key="meta_ind")
                meta_final = st.text_input("Meta Final", default_final, key="meta_final")
                prazo = st.text_input("Prazo", default_prazo, key="meta_prazo")

                if st.form_submit_button("Salvar"):
                    # Logica: deletar anterior do responsável e criar nova (garante 1 por resp)
                    delete_data(TABELA_METAS, "responsavel", responsavel)
                    
                    insert_data(TABELA_METAS, {
                        "equipe": equipe,
                        "responsavel": responsavel,
                        "meta_crucial": meta,
                        "indicador": indicador,
                        "meta_final": meta_final,
                        "prazo": prazo
                    })
                    st.session_state.meta_ok = True
                    st.rerun()

# ======================================================
# TAB 2 – MEDIDA DE DIREÇÃO
# ======================================================
with tabs[2]:
    st.subheader("🧭 Medidas de Direção")

    df_m = run_query(TABELA_METAS)
    df_med = run_query(TABELA_MEDIDAS)

    if df_m.empty:
        st.info("Nenhuma meta cadastrada.")
    else:
        resp_options = df_m["responsavel"].unique() if "responsavel" in df_m.columns else []
        resp = st.selectbox("Responsável", resp_options, key="resp_med")
        
        meta_options = df_m[df_m["responsavel"] == resp]["meta_crucial"] if "responsavel" in df_m.columns else []
        meta = st.selectbox(
            "Meta",
            meta_options,
            key="meta_med"
        )

        # Listar Medidas
        filtered_med = pd.DataFrame()
        if not df_med.empty and "responsavel" in df_med.columns and "meta_crucial" in df_med.columns:
           filtered_med = df_med[(df_med["responsavel"] == resp) & (df_med["meta_crucial"] == meta)]

        for idx, m in filtered_med.iterrows():
            c1, c2, c3 = st.columns([6, 1, 1])
            c1.write(f"{m['medida_direcao']} ({m['frequencia']})")

            # ID Único para edição pode vir do Supabase se existir coluna 'id', caso contrário usamos identificadores
            # Assumindo que o Supabase retorna 'id' (int8) por padrão.
            row_id = m.get('id')

            if c2.button("✏️", key=f"edit_med_{idx}"):
                st.session_state.medida_edit = idx # Usando idx do pandas para controle de UI, mas update via ID se possivel

            if c3.button("🗑️", key=f"del_med_{idx}"):
                if row_id:
                     delete_data(TABELA_MEDIDAS, "id", row_id)
                else:
                     # Fallback se não tiver ID: tenta deletar por todos os campos (arriscado se duplicado)
                     # Mas vamos tentar deletar pelo conteudo
                     (supabase.table(TABELA_MEDIDAS)
                         .delete()
                         .eq("responsavel", resp)
                         .eq("meta_crucial", meta)
                         .eq("medida_direcao", m["medida_direcao"])
                         .execute())
                st.rerun()

            if st.session_state.medida_edit == idx:
                with st.form(f"form_edit_med_{idx}"):
                    txt = st.text_input("Medida", m["medida_direcao"], key=f"txt_med_{idx}")
                    freq = st.selectbox(
                        "Frequência",
                        ["Diária", "Semanal", "Mensal", "Projeto"],
                        index=["Diária", "Semanal", "Mensal", "Projeto"].index(m["frequencia"]) if m["frequencia"] in ["Diária", "Semanal", "Mensal", "Projeto"] else 0,
                        key=f"freq_med_{idx}"
                    )
                    if st.form_submit_button("Salvar"):
                        if row_id:
                            update_data(TABELA_MEDIDAS, {"medida_direcao": txt, "frequencia": freq}, "id", row_id)
                        else:
                            # Fallback update
                            (supabase.table(TABELA_MEDIDAS)
                                .update({"medida_direcao": txt, "frequencia": freq})
                                .eq("responsavel", resp)
                                .eq("meta_crucial", meta)
                                .eq("medida_direcao", m["medida_direcao"]) # filtro pelo antigo
                                .execute())
                        
                        st.session_state.medida_edit = None
                        st.rerun()

        st.divider()
        with st.form("form_nova_med"):
            novas = st.text_area("Nova(s) medida(s) – uma por linha", key="nova_med_txt")
            freq = st.selectbox("Frequência", ["Diária", "Semanal", "Mensal", "Projeto"], key="nova_med_freq")
            if st.form_submit_button("Adicionar"):
                for t in novas.split("\n"):
                    if t.strip():
                        insert_data(TABELA_MEDIDAS, {
                            "responsavel": resp,
                            "meta_crucial": meta,
                            "medida_direcao": t.strip(),
                            "frequencia": freq
                        })
                st.rerun()

# ======================================================
# TAB 3 – VISÃO GERAL + SEMANAS
# ======================================================
with tabs[3]:
    st.subheader("📊 Visão Geral")

    df_m = run_query(TABELA_METAS)
    df_med = run_query(TABELA_MEDIDAS)
    df_sem = run_query(TABELA_SEMANAS)

    if df_m.empty:
        st.info("Sem metas cadastradas.")
    else:
        for equipe, grupo in df_m.groupby("equipe"):
            st.markdown(f"## 🏷️ {equipe}")

            for idx, m in grupo.iterrows():
                with st.expander(f"🎯 {m['meta_crucial']} — {m['responsavel']}"):
                    st.markdown("### 🧭 Medidas")
                    if not df_med.empty:
                        medidas_meta = df_med[df_med["meta_crucial"] == m["meta_crucial"]]
                        for _, md in medidas_meta.iterrows():
                            st.write(f"- {md['medida_direcao']} ({md['frequencia']})")
                    
                    st.markdown("### 📅 Semana")

                    sem_pass = semana_anterior()
                    sem_atual = inicio_semana()

                    # Filtrar semana
                    reg = pd.DataFrame()
                    if not df_sem.empty:
                        reg = df_sem[
                            (df_sem["responsavel"] == m["responsavel"]) &
                            (df_sem["meta_crucial"] == m["meta_crucial"]) &
                            (df_sem["semana_ref"] == str(sem_pass))
                        ]

                    if reg.empty:
                        status = st.radio(
                            "Semana passada concluída?",
                            ["SIM", "NAO"],
                            horizontal=True,
                            key=f"concl_{idx}"
                        )
                        if st.button("Confirmar semana passada", key=f"conf_{idx}"):
                            insert_data(TABELA_SEMANAS, {
                                "responsavel": m["responsavel"],
                                "meta_crucial": m["meta_crucial"],
                                "semana_ref": str(sem_pass),
                                "concluido": status,
                                "planejado": ""
                            })
                            st.rerun()
                    else:
                        st.success(f"Semana passada: {reg.iloc[0]['concluido']}")

                    planejamento = st.text_area(
                        "Próxima semana – compromisso",
                        key=f"plan_{idx}"
                    )
                    if st.button("Salvar compromisso", key=f"save_{idx}"):
                        insert_data(TABELA_SEMANAS, {
                             "responsavel": m["responsavel"],
                             "meta_crucial": m["meta_crucial"],
                             "semana_ref": str(sem_atual),
                             "concluido": "",
                             "planejado": planejamento
                        })
                        st.rerun()
