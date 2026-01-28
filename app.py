from __future__ import annotations

import re
from contextlib import contextmanager
from datetime import date, datetime

import pandas as pd
import streamlit as st
from supabase import Client, create_client

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Controle de Docs",
    page_icon="icon.png",
    layout="wide",
)

# =========================================================
# UI / CSS  (SEM MEXER EM INPUTS)
# =========================================================
st.markdown("""
<style>
:root{
  --bg:#F6F8FC;
  --card:#FFFFFF;
  --text:#0F172A;
  --muted:rgba(15,23,42,.62);
  --border:rgba(15,23,42,.10);
  --shadow:0 10px 30px rgba(15,23,42,.06);
  --primary:#2563EB;
}

.stApp{ background:var(--bg); }

.block-container{
  padding-top:1.6rem;
  padding-bottom:2rem;
  max-width:1400px;
}

h1,h2,h3{
  letter-spacing:-0.35px;
  color:var(--text);
}
.small-muted{ color:var(--muted); }

/* Sidebar */
section[data-testid="stSidebar"]{
  background:#0B1220;
  border-right:1px solid rgba(255,255,255,.08);
}
section[data-testid="stSidebar"] *{
  color:rgba(255,255,255,.92)!important;
}
section[data-testid="stSidebar"] hr{
  background:rgba(255,255,255,.10);
  border:none;
  height:1px;
}

/* Cards e Expanders */
div[data-testid="stVerticalBlockBorderWrapper"],
details[data-testid="stExpander"]{
  background:var(--card);
  border:1px solid var(--border);
  border-radius:16px;
  box-shadow:var(--shadow);
}

/* Métricas */
div[data-testid="stMetric"]{
  background:var(--card);
  border:1px solid var(--border);
  border-radius:16px;
  padding:14px;
  box-shadow:var(--shadow);
}

/* Botões */
.stButton>button{
  border-radius:14px;
  padding:.6rem 1rem;
  font-weight:800;
}
button[kind="primary"]{
  background:var(--primary)!important;
  color:#FFF!important;
  border:1px solid rgba(37,99,235,.35)!important;
}

/* Tabelas */
div[data-testid="stDataFrame"],
div[data-testid="stDataEditor"]{
  background:var(--card);
  border:1px solid var(--border);
  border-radius:16px;
  overflow:hidden;
  box-shadow:var(--shadow);
}

hr{ border-color:var(--border); }
</style>
""", unsafe_allow_html=True)

# =========================================================
# CONSTANTES
# =========================================================
RETORNO_STATUS = ["Pendente", "Respondido"]
STATUS_DISPLAY = {"Pendente": "🔴 Pendente", "Respondido": "🟢 Respondido"}
DISPLAY_TO_STATUS = {v: k for k, v in STATUS_DISPLAY.items()}

# =========================================================
# SUPABASE
# =========================================================
@st.cache_resource
def get_supabase() -> Client:
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_ANON_KEY"],
    )

def _sb_table(name: str):
    return get_supabase().table(name)

# =========================================================
# AUTH
# =========================================================
def require_auth():
    st.session_state.setdefault("sb_session", None)
    st.session_state.setdefault("sb_user", None)

    if st.session_state["sb_session"] and st.session_state["sb_user"]:
        return

    st.title("🔐 Controle de Documentos")

    with st.form("login"):
        email = st.text_input("Email")
        senha = st.text_input("Senha", type="password")
        ok = st.form_submit_button("Entrar", type="primary")

    if ok:
        try:
            sb = get_supabase()
            res = sb.auth.sign_in_with_password({"email": email, "password": senha})
            st.session_state["sb_session"] = res.session
            st.session_state["sb_user"] = res.user
            st.rerun()
        except Exception:
            st.error("Erro ao autenticar")

    st.stop()

# =========================================================
# SIDEBAR
# =========================================================
def sidebar_layout():
    with st.sidebar:
        st.markdown("## 📊 Controle de Docs")
        st.markdown('<div class="small-muted">Dashboard operacional</div>', unsafe_allow_html=True)
        st.markdown("---")
        page = st.radio("Menu", ["📋 Dashboard", "👥 Responsável", "🗄️ Arquivados"])
        st.markdown("---")
        if st.button("🚪 Sair", use_container_width=True):
            st.session_state.clear()
            st.rerun()
    return page

# =========================================================
# APP START
# =========================================================
require_auth()
page = sidebar_layout()

# =========================================================
# DASHBOARD
# =========================================================
if page == "📋 Dashboard":
    st.title("📋 Dashboard")
    st.markdown('<div class="small-muted">Cadastro e acompanhamento</div>', unsafe_allow_html=True)

    with st.expander("Documento", expanded=True):
        c1, c2, c3 = st.columns([1.2, 1, 0.8])

        with c1:
            st.text_input("Nr (Recebido)")
            st.text_input("Origem")
            st.text_input("Assunto (Documento)")
            st.date_input("Prazo Final")
            st.text_area("Obs (Documento)", height=110)

        with c2:
            st.text_input("Assunto (Solicitação)")
            st.text_input("Nr (Solicitado)")
            st.date_input("Prazo OM")
            st.multiselect("Responsáveis", [])

        with c3:
            st.text_input("Nr (Resposta)")
            st.button("Salvar", type="primary", use_container_width=True)
            st.button("Limpar", use_container_width=True)

# =========================================================
# RESPONSÁVEL
# =========================================================
elif page == "👥 Responsável":
    st.title("👥 Responsável")
    st.text_input("Novo Responsável")
    st.button("Adicionar", type="primary")

# =========================================================
# ARQUIVADOS
# =========================================================
else:
    st.title("🗄️ Arquivados")
    st.info("Tabela de arquivados")
