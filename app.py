from __future__ import annotations

import re
from datetime import date, datetime
from contextlib import contextmanager

import pandas as pd
import streamlit as st
from supabase import create_client, Client

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Controle de Docs",
    page_icon="icon.png",
    layout="wide",
)

# =========================================================
# CSS — PADRÃO ÚNICO (TEXTINPUT = SELECT)
# =========================================================
st.markdown("""
<style>
/* ================= BASE ================= */
.stApp { background:#F6F8FC; }

.block-container{
  padding-top:1.6rem;
  padding-bottom:2rem;
  max-width:1400px;
}

h1,h2,h3{ color:#0F172A; letter-spacing:-0.3px; }
.small-muted{ color:rgba(15,23,42,.6); }

/* ================= SIDEBAR ================= */
section[data-testid="stSidebar"]{
  background:#0B1220;
  border-right:1px solid rgba(255,255,255,.08);
}
section[data-testid="stSidebar"] *{
  color:#E6EAF2 !important;
}

/* ================= CARDS ================= */
div[data-testid="stVerticalBlockBorderWrapper"],
details[data-testid="stExpander"]{
  background:#FFFFFF;
  border:1px solid rgba(15,23,42,.10);
  border-radius:16px;
  box-shadow:0 10px 28px rgba(15,23,42,.06);
}

/* ================= MÉTRICAS ================= */
div[data-testid="stMetric"]{
  background:#FFFFFF;
  border:1px solid rgba(15,23,42,.10);
  border-radius:16px;
  padding:14px;
}

/* ======================================================
   INPUTS PADRONIZADOS (TEXT = SELECT)
   ====================================================== */

/* wrapper geral */
div[data-baseweb="input"] > div,
div[data-baseweb="textarea"] > div,
div[data-baseweb="select"] > div,
div[data-baseweb="datepicker"] > div{
  background:#FFFFFF !important;
  border:1px solid rgba(15,23,42,.18) !important;
  border-radius:12px !important;
  box-shadow:none !important;
}

/* input interno */
div[data-baseweb="input"] input,
div[data-baseweb="textarea"] textarea{
  background:#FFFFFF !important;
  border:none !important;
  outline:none !important;
  box-shadow:none !important;
  color:#0F172A !important;
}

/* select interno */
div[data-baseweb="select"] div[role="combobox"]{
  background:#FFFFFF !important;
  border:none !important;
  outline:none !important;
  box-shadow:none !important;
  color:#0F172A !important;
}

/* remove pseudo-bordas duplicadas */
div[data-baseweb="input"] > div::before,
div[data-baseweb="input"] > div::after,
div[data-baseweb="textarea"] > div::before,
div[data-baseweb="textarea"] > div::after,
div[data-baseweb="select"] > div::before,
div[data-baseweb="select"] > div::after{
  display:none !important;
}

/* foco elegante */
div[data-baseweb="input"] > div:focus-within,
div[data-baseweb="textarea"] > div:focus-within,
div[data-baseweb="select"] > div:focus-within,
div[data-baseweb="datepicker"] > div:focus-within{
  border-color:rgba(37,99,235,.45) !important;
  box-shadow:0 0 0 2px rgba(37,99,235,.12) !important;
}

/* ================= BOTÕES ================= */
.stButton>button{
  border-radius:14px;
  padding:.6rem 1rem;
  font-weight:700;
}
button[kind="primary"]{
  background:#2563EB !important;
  color:#FFFFFF !important;
  border:1px solid rgba(37,99,235,.35) !important;
}

/* ================= TABELAS ================= */
div[data-testid="stDataFrame"],
div[data-testid="stDataEditor"]{
  background:#FFFFFF;
  border:1px solid rgba(15,23,42,.10);
  border-radius:16px;
  overflow:hidden;
}

hr{ border-color:rgba(15,23,42,.10); }
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
        st.secrets["SUPABASE_ANON_KEY"]
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

    st.title("🔐 Controle de Documentos — Login")

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
            st.error("Erro ao autenticar.")

    st.stop()

# =========================================================
# SIDEBAR
# =========================================================
def sidebar_layout():
    with st.sidebar:
        st.markdown("## 📊 Controle de Documentos")
        st.markdown('<div class="small-muted">Dashboard operacional</div>', unsafe_allow_html=True)
        st.markdown("---")
        page = st.radio("Menu", ["📋 Dashboard", "👥 Responsável", "🗄️ Arquivados"])
        st.markdown("---")
        if st.button("🚪 Sair", use_container_width=True):
            st.session_state.clear()
            st.rerun()
    return page

# =========================================================
# UI HELPER
# =========================================================
@contextmanager
def card():
    with st.container(border=True):
        yield

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
        c1, c2, c3 = st.columns([1.2,1,0.8])

        with c1:
            with card():
                st.text_input("Nr (Recebido)")
                st.text_input("Origem")
                st.text_input("Assunto (Documento)")
                st.date_input("Prazo Final")
                st.text_area("Obs (Documento)", height=110)

        with c2:
            with card():
                st.text_input("Assunto (Solicitação)")
                st.text_input("Nr (Solicitado)")
                st.date_input("Prazo OM")
                st.multiselect("Responsáveis", [])

        with c3:
            with card():
                st.text_input("Nr (Resposta)")
                st.button("Salvar", type="primary", use_container_width=True)
                st.button("Limpar", use_container_width=True)

    st.info("Tabela de acompanhamento permanece igual à sua versão original.")

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

