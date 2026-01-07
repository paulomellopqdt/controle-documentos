from __future__ import annotations

from datetime import date, datetime
import re
import urllib.parse

import pandas as pd
import streamlit as st
from supabase import Client, create_client


# =========================================================
# CONSTANTS
# =========================================================
RETORNO_STATUS = ["Pendente", "Respondido"]
STATUS_DISPLAY = {"Pendente": "🔴 Pendente", "Respondido": "🟢 Respondido"}
DISPLAY_TO_STATUS = {v: k for k, v in STATUS_DISPLAY.items()}


# =========================================================
# CONFIG
# =========================================================
st.set_page_config(layout="wide")

st.markdown(
    """
<style>
/* ---------- Base ---------- */
.block-container { padding-top: 1.9rem; padding-bottom: 2rem; max-width: 1400px; }
h1, h2, h3 { letter-spacing: -0.4px; line-height: 1.15; padding-top: 0.25rem; }
.small-muted { color: rgba(49, 51, 63, 0.65); font-size: 0.9rem; }

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] { border-right: 1px solid rgba(49,51,63,0.10); }
section[data-testid="stSidebar"] .block-container { padding-top: 1.2rem; }

/* ---------- Metrics ---------- */
div[data-testid="stMetric"]{
  background: rgba(255,255,255,0.85);
  border: 1px solid rgba(49,51,63,0.10);
  border-radius: 16px;
  padding: 14px 14px;
  box-shadow: 0 6px 22px rgba(15, 23, 42, 0.05);
}
div[data-testid="stMetric"] label { opacity: 0.75; }
div[data-testid="stMetric"] [data-testid="stMetricValue"] { font-size: 1.65rem; }

/* ---------- Inputs / Buttons ---------- */
.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
  border-radius: 14px !important;
}
.stButton>button{
  border-radius: 14px;
  padding: 0.55rem 0.95rem;
  border: 1px solid rgba(49,51,63,0.12);
}
.stButton>button:hover{
  border: 1px solid rgba(49,51,63,0.22);
}

/* ---------- Dataframes / Editors ---------- */
div[data-testid="stDataFrame"], div[data-testid="stDataEditor"]{
  border: 1px solid rgba(49,51,63,0.10);
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 6px 22px rgba(15, 23, 42, 0.04);
}

/* Centralizar cabeçalho e células */
div[data-testid="stDataFrame"] table th,
div[data-testid="stDataFrame"] table td,
div[data-testid="stDataEditor"] table th,
div[data-testid="stDataEditor"] table td {
  text-align: center !important;
  vertical-align: middle !important;
}

hr { border-color: rgba(49,51,63,0.10); }

/* Badge (pendente/salvo) */
.badge{
  display:inline-flex; align-items:center; gap:8px;
  padding: 6px 10px; border-radius: 999px;
  font-size: 0.85rem; border:1px solid rgba(49,51,63,0.12);
}
.badge-warn{ background: rgba(234,179,8,0.14); color: #854d0e; }
.badge-ok{ background: rgba(34,197,94,0.12); color: #166534; }

</style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# SUPABASE CLIENT
# =========================================================
@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_ANON_KEY"]
    return create_client(url, key)


def get_session_access_token() -> str | None:
    sess = st.session_state.get("sb_session")
    if not sess:
        return None
    return getattr(sess, "access_token", None)


def _sb_table(name: str):
    sb = get_supabase()
    token = get_session_access_token()
    if token:
        sb.postgrest.auth(token)
    return sb.table(name)


def _auth_set_session_from_state():
    sb = get_supabase()
    sess = st.session_state.get("sb_session")
    if not sess:
        return
    try:
        access_token = getattr(sess, "access_token", None)
        refresh_token = getattr(sess, "refresh_token", None)
        if access_token and refresh_token:
            sb.auth.set_session(access_token, refresh_token)
    except Exception:
        pass


# =========================================================
# DASH NAME (PERSIST IN USER METADATA)
# =========================================================
def load_dash_name_from_user() -> str:
    user = st.session_state.get("sb_user")
    if not user:
        return "Dashboard"
    meta = getattr(user, "user_metadata", None) or {}
    name = (meta.get("dash_name") or "").strip()
    return name or "Dashboard"


def save_dash_name_to_user(name: str):
    name = (name or "").strip() or "Dashboard"
    sb = get_supabase()
    _auth_set_session_from_state()
    try:
        res = sb.auth.update_user({"data": {"dash_name": name}})
        if getattr(res, "user", None):
            st.session_state["sb_user"] = res.user
    except Exception:
        pass


# =========================================================
# AUTH
# =========================================================
def require_auth():
    st.session_state.setdefault("sb_session", None)
    st.session_state.setdefault("sb_user", None)

    if st.session_state["sb_session"] and st.session_state["sb_user"]:
        return

    st.title("🔐 Controle de Documentos — Login")
    st.markdown(
        '<div class="small-muted">Acesse com sua conta para ver apenas seus dados.</div>',
        unsafe_allow_html=True,
    )

    tabs = st.tabs(["Entrar", "Criar conta"])
    sb = get_supabase()

    with tabs[0]:
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="seuemail@exemplo.com")
            password = st.text_input("Senha", type="password")
            ok = st.form_submit_button("Entrar", type="primary")
        if ok:
            try:
                res = sb.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state["sb_session"] = res.session
                st.session_state["sb_user"] = res.user
                st.session_state["dash_name"] = load_dash_name_from_user()
                st.rerun()
            except Exception:
                st.error("Não foi possível entrar. Verifique email e senha.")

    with tabs[1]:
        with st.form("signup_form"):
            email = st.text_input("Email", key="signup_email", placeholder="seuemail@exemplo.com")
            password = st.text_input("Senha", type="password", key="signup_pw")
            ok = st.form_submit_button("Criar conta", type="primary")
        if ok:
            try:
                sb.auth.sign_up({"email": email, "password": password})
                st.success("Conta criada. Agora faça login na aba 'Entrar'.")
            except Exception:
                st.error("Não foi possível criar a conta. Tente outro email ou uma senha mais forte.")

    st.stop()


def _on_change_dash_name():
    save_dash_name_to_user(st.session_state.get("dash_name", "Dashboard"))


def sidebar_layout() -> tuple[str, str]:
    st.session_state.setdefault("dash_name", load_dash_name_from_user())

    with st.sidebar:
        st.markdown("## 📊 Controle de Documentos")
        st.markdown('<div class="small-muted">Dashboard operacional</div>', unsafe_allow_html=True)

        user = st.session_state.get("sb_user")
        if user:
            st.markdown(f"**👤 {user.email}**")

        st.markdown("---")
        st.text_input(
            "Nome",
            key="dash_name",
            help="Este nome aparecerá no menu e no título principal.",
            on_change=_on_change_dash_name,
        )
        dash_title = (st.session_state.get("dash_name") or "Dashboard").strip() or "Dashboard"

        st.markdown("---")
        menu_options = [f"📋 {dash_title}", "👥 Responsável", "🗄️ Arquivados"]
        page = st.radio("Menu", menu_options, index=0)

        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔄 Atualizar", use_container_width=True):
                st.rerun()
        with c2:
            if st.button("🚪 Sair", use_container_width=True):
                try:
                    get_supabase().auth.sign_out()
                except Exception:
                    pass
                st.session_state["sb_session"] = None
                st.session_state["sb_user"] = None
                st.rerun()

        st.caption("v1.0 • Streamlit + Supabase")

    return page, dash_title


# =========================================================
# CRUD: CASOS / ARQUIVOS / RETORNOS
# =========================================================
def fetch_casos() -> pd.DataFrame:
    res = _sb_table("casos").select("*").order("id", desc=True).execute()
    return pd.DataFrame(res.data or [])


def fetch_caso(caso_id: int) -> dict | None:
    res = _sb_table("casos").select("*").eq("id", int(caso_id)).limit(1).execute()
    data = res.data or []
    return data[0] if data else None


def update_caso_by_id(caso_id: int, payload: dict):
    _sb_table("casos").update(payload).eq("id", int(caso_id)).execute()


def insert_documento(
    nr_doc: str,
    assunto_doc: str,
    origem: str | None,
    prazo_final: date | None,
    obs: str | None,
) -> int:
    user = st.session_state["sb_user"]
    payload = {
        "owner_id": user.id,
        "nr_doc_recebido": (nr_doc or "").strip(),
        "assunto_doc": (assunto_doc or "").strip(),
        "origem": (origem or "").strip() if origem and origem.strip() else None,
        "prazo_final": prazo_final.isoformat() if prazo_final else None,
        "observacoes": (obs or "").strip() if obs and obs.strip() else None,
        "status": "Recebido",
        "created_at": datetime.now().isoformat(),
    }
    res = _sb_table("casos").insert(payload).execute()
    return int(res.data[0]["id"])


def insert_solicitacao_sem_documento(assunto_solic: str, prazo_om: date | None, nr_doc_solicitado: str | None) -> int:
    user = st.session_state["sb_user"]
    payload = {
        "owner_id": user.id,
        "nr_doc_recebido": "-",  # mantém NOT NULL
        "assunto_doc": "-",      # mantém NOT NULL
        "origem": "-",
        "prazo_final": None,
        "observacoes": "-",
        "assunto_solic": (assunto_solic or "").strip() or "(sem solicitação)",
        "prazo_om": prazo_om.isoformat() if prazo_om else None,
        "nr_doc_solicitado": (nr_doc_solicitado or "").strip() or "00",
        "status": "Distribuído",
        "created_at": datetime.now().isoformat(),
    }
    res = _sb_table("casos").insert(payload).execute()
    return int(res.data[0]["id"])


def fetch_retornos(caso_id: int) -> pd.DataFrame:
    res = _sb_table("retornos_om").select("*").eq("caso_id", int(caso_id)).order("om").execute()
    return pd.DataFrame(res.data or [])


def fetch_pendencias() -> pd.DataFrame:
    res = _sb_table("retornos_om").select("caso_id,status").execute()
    data = res.data or []
    if not data:
        return pd.DataFrame(columns=["caso_id", "qtd"])
    dff = pd.DataFrame(data)
    dff = dff[dff["status"] == "Pendente"]
    if dff.empty:
        return pd.DataFrame(columns=["caso_id", "qtd"])
    return dff.groupby("caso_id").size().reset_index(name="qtd")


def set_resposta_e_status(caso_id: int, nr_doc_resposta: str | None):
    nr = (nr_doc_resposta or "").strip()
    if nr:
        payload = {"nr_doc_resposta": nr, "status": "Resolvido", "resolved_at": date.today().isoformat()}
    else:
        payload = {"nr_doc_resposta": None, "status": "Pendente", "resolved_at": None}
    _sb_table("casos").update(payload).eq("id", int(caso_id)).execute()


def archive_caso(caso_id: int):
    user = st.session_state["sb_user"]
    payload = {"owner_id": user.id, "caso_id": int(caso_id), "archived_at": datetime.now().isoformat()}
    _sb_table("arquivados").upsert(payload, on_conflict="caso_id").execute()


def fetch_arquivados_ids() -> set[int]:
    res = _sb_table("arquivados").select("caso_id").execute()
    data = res.data or []
    return set(int(x["caso_id"]) for x in data)


def fetch_arquivados_casos() -> pd.DataFrame:
    ids = fetch_arquivados_ids()
    if not ids:
        return pd.DataFrame()
    res = _sb_table("casos").select("*").in_("id", list(ids)).execute()
    df = pd.DataFrame(res.data or [])
    if df.empty:
        return df
    return df.sort_values("id", ascending=False)


# =========================================================
# CRUD: RESPONSÁVEIS (MASTER) + CONTATOS
# =========================================================
def _normalize_name(s: str) -> str:
    return (s or "").replace("\u00A0", " ").strip()


def get_master_oms() -> list[str]:
    res = _sb_table("master_oms").select("nome").order("nome").execute()
    return [x["nome"] for x in (res.data or [])]


def add_master_om(nome: str):
    nome = _normalize_name(nome)
    if not nome:
        return False, "Informe o nome do Responsável."
    user = st.session_state["sb_user"]

    res = _sb_table("master_oms").select("nome").execute()
    exists = any((x.get("nome") or "").strip().lower() == nome.lower() for x in (res.data or []))
    if exists:
        return False, "Esse Responsável já existe."

    payload = {"owner_id": user.id, "nome": nome, "created_at": datetime.now().isoformat()}
    _sb_table("master_oms").insert(payload).execute()
    return True, f"Responsável adicionado: {nome}"


def delete_master_oms(nomes: list[str]):
    nomes = [_normalize_name(n) for n in (nomes or []) if _normalize_name(n)]
    if not nomes:
        return True, "Nada para remover."
    for n in nomes:
        _sb_table("master_oms").delete().eq("nome", n).execute()
        _sb_table("retornos_om").delete().eq("om", n).execute()
        # contatos (se existir)
        try:
            _sb_table("responsaveis_contatos").delete().eq("responsavel", n).execute()
        except Exception:
            pass
    return True, "Responsáveis removidos ✅"


def fetch_contatos_responsaveis() -> pd.DataFrame:
    """
    Tabela esperada: responsaveis_contatos
    colunas: id, owner_id, responsavel, contato_nome, telefone, created_at
    """
    try:
        q = _sb_table("responsaveis_contatos").select("*")
        # tenta ordenar; se a coluna não existir / RLS bloquear, cai no except abaixo
        try:
            q = q.order("responsavel", desc=False).order("contato_nome", desc=False)
        except Exception:
            pass

        res = q.execute()
        return pd.DataFrame(res.data or [])
    except Exception as e:
        st.error(
            "Não foi possível carregar **responsaveis_contatos**.\n\n"
            "✅ Verifique se:\n"
            "- a tabela existe (schema public)\n"
            "- RLS/policies permitem SELECT\n"
            "- colunas: responsavel, contato_nome, telefone\n\n"
            f"Detalhe: {e}"
        )
        return pd.DataFrame(columns=["id", "responsavel", "contato_nome", "telefone"])


def insert_contato_responsavel(responsavel: str, contato_nome: str, telefone: str):
    user = st.session_state["sb_user"]
    payload = {
        "owner_id": user.id,
        "responsavel": _normalize_name(responsavel),
        "contato_nome": _normalize_name(contato_nome),
        "telefone": _normalize_name(telefone),
        "created_at": datetime.now().isoformat(),
    }
    _sb_table("responsaveis_contatos").insert(payload).execute()


def delete_contato_responsavel(contato_id: int):
    _sb_table("responsaveis_contatos").delete().eq("id", int(contato_id)).execute()


# =========================================================
# SOLICITAÇÃO (RETORNOS_OM)
# =========================================================
def salvar_ou_atualizar_solicitacao(
    caso_id: int,
    assunto_solic: str | None,
    prazo_om: date | None,
    selecionadas: list[str],
    nr_doc_solicitado: str | None,
):
    payload = {
        "assunto_solic": (assunto_solic or "").strip() or None,
        "prazo_om": prazo_om.isoformat() if prazo_om else None,
        "status": "Distribuído",
        "nr_doc_solicitado": (nr_doc_solicitado or "").strip() or None,
    }
    _sb_table("casos").update(payload).eq("id", int(caso_id)).execute()

    ret = fetch_retornos(int(caso_id))
    existentes = set(ret["om"].tolist()) if not ret.empty else set()
    selecionadas_set = set([_normalize_name(x) for x in selecionadas if _normalize_name(x)])

    for om in list(existentes - selecionadas_set):
        _sb_table("retornos_om").delete().eq("caso_id", int(caso_id)).eq("om", om).execute()

    user = st.session_state["sb_user"]

    for om in list(existentes & selecionadas_set):
        _sb_table("retornos_om").update({"prazo_om": prazo_om.isoformat() if prazo_om else None}).eq("caso_id", int(caso_id)).eq("om", om).execute()

    for om in list(selecionadas_set - existentes):
        _sb_table("retornos_om").insert(
            {
                "owner_id": user.id,
                "caso_id": int(caso_id),
                "om": om,
                "status": "Pendente",
                "prazo_om": prazo_om.isoformat() if prazo_om else None,
                "dt_resposta": None,
                "observacoes": None,
            }
        ).execute()


# =========================================================
# HELPERS
# =========================================================
def _fmt_date_iso_to_ddmmyyyy(v):
    if not v:
        return "-"
    try:
        return pd.to_datetime(v).strftime("%d/%m/%Y")
    except Exception:
        return "-"


def _parse_ddmmyyyy_to_date(s: str):
    if not s or str(s).strip() in ["-", "NaT", "None"]:
        return None
    try:
        return datetime.strptime(str(s).strip(), "%d/%m/%Y").date()
    except Exception:
        return None


def _row_style_acompanhamento(row):
    status = str(row.get("Status", "")).strip().lower()
    if status == "resolvido":
        return ["background-color: #dcfce7; color: #14532d;"] * len(row)

    prazo = _parse_ddmmyyyy_to_date(row.get("Prazo Final", ""))
    if prazo is None:
        return [""] * len(row)

    today = date.today()
    diff = (prazo - today).days
    if diff <= 0:
        return ["background-color: #fee2e2; color: #7f1d1d;"] * len(row)
    if 1 <= diff <= 5:
        return ["background-color: #fef9c3; color: #713f12;"] * len(row)
    return [""] * len(row)


DOC_KEYS = [
    "doc_nr",
    "doc_assunto_doc",
    "doc_origem",
    "doc_prazo_final",
    "doc_obs",
    "sol_assunto_solic",
    "sol_prazo_om",
    "sol_doc_solicitado",
    "sol_responsaveis",
    "resp_nr_doc_resposta",
]


def _request_clear_doc_box():
    st.session_state["__clear_doc_box__"] = True


def _apply_clear_doc_box():
    # roda ANTES dos widgets existirem
    for k in DOC_KEYS:
        st.session_state.pop(k, None)

    st.session_state.setdefault("doc_nr", "")
    st.session_state.setdefault("doc_assunto_doc", "")
    st.session_state.setdefault("doc_origem", "")
    st.session_state.setdefault("doc_prazo_final", None)
    st.session_state.setdefault("doc_obs", "")

    st.session_state.setdefault("sol_assunto_solic", "")
    st.session_state.setdefault("sol_prazo_om", None)
    st.session_state.setdefault("sol_doc_solicitado", "")
    st.session_state.setdefault("sol_responsaveis", [])
    st.session_state.setdefault("resp_nr_doc_resposta", "")


def _apply_load_selected_into_doc_box(caso_id: int):
    # roda ANTES dos widgets existirem
    caso = fetch_caso(int(caso_id)) or {}

    st.session_state["doc_nr"] = caso.get("nr_doc_recebido") or ""
    st.session_state["doc_assunto_doc"] = caso.get("assunto_doc") or ""
    st.session_state["doc_origem"] = caso.get("origem") or ""
    st.session_state["doc_prazo_final"] = pd.to_datetime(caso["prazo_final"]).date() if caso.get("prazo_final") else None
    st.session_state["doc_obs"] = caso.get("observacoes") or ""

    st.session_state["sol_assunto_solic"] = caso.get("assunto_solic") or ""
    st.session_state["sol_prazo_om"] = pd.to_datetime(caso["prazo_om"]).date() if caso.get("prazo_om") else None
    st.session_state["sol_doc_solicitado"] = caso.get("nr_doc_solicitado") or ""

    st.session_state["resp_nr_doc_resposta"] = caso.get("nr_doc_resposta") or ""

    ret = fetch_retornos(int(caso_id))
    st.session_state["sol_responsaveis"] = ret["om"].fillna("").astype(str).tolist() if not ret.empty else []


def build_msg_cobranca(caso: dict, ret: pd.DataFrame) -> str:
    assunto = caso.get("assunto_solic") or "-"
    nr = caso.get("nr_doc_solicitado") or "-"
    prazo = _fmt_date_iso_to_ddmmyyyy(caso.get("prazo_om"))

    pendentes = []
    if ret is not None and not ret.empty:
        pendentes = ret[ret["status"].fillna("").str.lower() != "respondido"]["om"].fillna("").tolist()

    pend_txt = "\n".join([f"- {p}" for p in pendentes]) if pendentes else "- (nenhum)"
    return (
        "🚨 Atenção!\n\n"
        "Solicito verificar a situação do retorno referente a seguinte solicitação:\n\n"
        f"📌 Assunto: {assunto}\n"
        f"📄 Nr Doc: {nr}\n"
        f"⏳ Prazo: {prazo}\n\n"
        "👥 Pendentes:\n"
        f"{pend_txt}\n"
    )


def _snapshot_from_editor(edited_df: pd.DataFrame) -> list[tuple[str, str]]:
    snap: list[tuple[str, str]] = []
    for _, r in edited_df.iterrows():
        disp = (r.get("Status", "") or STATUS_DISPLAY["Pendente"]).strip()
        status = DISPLAY_TO_STATUS.get(disp, "Pendente")
        obs = (r.get("Obs", "") or "").strip()
        snap.append((status, obs))
    return snap


def _digits_only_phone(s: str) -> str:
    return re.sub(r"\D+", "", s or "")


def whatsapp_web_url(phone: str, text: str | None = None) -> str:
    """
    Use https://wa.me/55DDDNUM?text=...
    """
    p = _digits_only_phone(phone)
    if not p:
        return "https://web.whatsapp.com/"
    # se o usuário não colocar país, assume BR (55)
    if not p.startswith("55"):
        p = "55" + p
    base = f"https://wa.me/{p}"
    if text:
        return base + "?text=" + urllib.parse.quote(text)
    return base


# =========================================================
# APP START
# =========================================================
require_auth()
page, dash_title = sidebar_layout()

# estados principais
st.session_state.setdefault("current_selected_id", None)
st.session_state.setdefault("pending_select_id", None)
st.session_state.setdefault("__clear_doc_box__", False)

# defaults (se ainda não existem)
_apply_clear_doc_box()

# ✅ aplica CLEAR antes dos widgets
if st.session_state.pop("__clear_doc_box__", False):
    _apply_clear_doc_box()
    st.session_state["current_selected_id"] = None
    st.session_state["pending_select_id"] = None

# ✅ aplica LOAD antes dos widgets
pending = st.session_state.get("pending_select_id")
if pending is not None:
    st.session_state["current_selected_id"] = int(pending)
    _apply_load_selected_into_doc_box(int(pending))
    st.session_state["pending_select_id"] = None


# =========================================================
# PAGE: DASHBOARD
# =========================================================
if page == f"📋 {dash_title}":
    hoje = date.today()

    df = fetch_casos()
    arq_ids = fetch_arquivados_ids()
    df_acomp = df[~df["id"].astype(int).isin(arq_ids)].copy() if not df.empty else pd.DataFrame()

    pend = fetch_pendencias()
    pend_total = int(pend["qtd"].sum()) if not pend.empty else 0

    atrasados = 0
    if not df_acomp.empty and "prazo_final" in df_acomp.columns:
        prazos = pd.to_datetime(df_acomp["prazo_final"], errors="coerce").dt.date
        status = df_acomp.get("status", pd.Series([""] * len(df_acomp))).astype(str).str.lower()
        mask = prazos.notna() & (prazos <= hoje) & (status != "resolvido")
        atrasados = int(mask.sum())

    st.title(f"📋 {dash_title}")
    st.markdown('<div class="small-muted">Visão geral, pendências e acompanhamento</div>', unsafe_allow_html=True)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Em acompanhamento", 0 if df_acomp.empty else len(df_acomp))
    k2.metric("Atrasados", atrasados)
    k3.metric("Pendências", pend_total)
    k4.metric("Hoje", hoje.strftime("%d/%m/%Y"))
    st.divider()

    # =========================================================
    # Documento (sempre FECHADA)
    #  - Ao selecionar linha, preenche as caixas
    #  - Salvar com linha selecionada: atualiza
    #  - Salvar sem seleção: cria novo
    # =========================================================
    with st.expander("Documento", expanded=False):
        colA, colB, colC = st.columns([1.15, 1.0, 0.85], gap="large")

        with colA:
            st.markdown("##### Documento")
            a1, a2 = st.columns([1, 1], gap="small")
            with a1:
                st.text_input("Nr (Recebido)", key="doc_nr")
            with a2:
                st.text_input("Origem", key="doc_origem")

            st.text_input("Assunto (Documento)", key="doc_assunto_doc")
            st.date_input("Prazo Final", key="doc_prazo_final", value=None, format="DD/MM/YYYY")
            st.text_area("Obs (Documento)", key="doc_obs", height=110)

        with colB:
            st.markdown("##### Solicitação")
            st.text_input("Assunto (Solicitação)", key="sol_assunto_solic")
            b1, b2 = st.columns(2, gap="small")
            with b1:
                st.text_input("Nr (Solicitado)", key="sol_doc_solicitado")
            with b2:
                st.date_input("Prazo OM", key="sol_prazo_om", value=None, format="DD/MM/YYYY")

            st.markdown("##### Responsáveis")
            oms = get_master_oms()
            st.multiselect(
                "Responsáveis",
                options=oms,
                key="sol_responsaveis",
                label_visibility="collapsed",
                help="Selecione os responsáveis desta solicitação.",
            )

        with colC:
            st.markdown("##### Resposta")
            st.text_input("Nr (Resposta)", key="resp_nr_doc_resposta")
            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

            if st.button("Salvar", type="primary", key="btn_save_all", use_container_width=True):
                sel_id = st.session_state.get("current_selected_id")

                nr_doc = (st.session_state.get("doc_nr") or "").strip()
                assunto_doc = (st.session_state.get("doc_assunto_doc") or "").strip()
                origem = (st.session_state.get("doc_origem") or "").strip() or None
                prazo_final = st.session_state.get("doc_prazo_final")
                obs_doc = (st.session_state.get("doc_obs") or "").strip() or None

                assunto_solic = (st.session_state.get("sol_assunto_solic") or "").strip() or None
                prazo_om = st.session_state.get("sol_prazo_om")
                nr_solic = (st.session_state.get("sol_doc_solicitado") or "").strip() or None
                responsaveis = st.session_state.get("sol_responsaveis") or []

                nr_resp = (st.session_state.get("resp_nr_doc_resposta") or "").strip()

                try:
                    if sel_id:
                        # ✅ mantém NOT NULL com "-"
                        update_payload = {
                            "nr_doc_recebido": nr_doc if nr_doc else "-",
                            "assunto_doc": assunto_doc if assunto_doc else "-",
                            "origem": origem if origem else "-",
                            "prazo_final": prazo_final.isoformat() if prazo_final else None,
                            "observacoes": obs_doc if obs_doc else None,
                        }
                        update_caso_by_id(int(sel_id), update_payload)

                        if assunto_solic or nr_solic or prazo_om or responsaveis:
                            salvar_ou_atualizar_solicitacao(
                                caso_id=int(sel_id),
                                assunto_solic=assunto_solic,
                                prazo_om=prazo_om,
                                selecionadas=responsaveis,
                                nr_doc_solicitado=nr_solic or "00",
                            )

                        set_resposta_e_status(int(sel_id), nr_resp)

                        st.toast("Atualizado ✅")
                        st.rerun()

                    else:
                        # novo registro
                        if nr_doc and assunto_doc:
                            new_id = insert_documento(
                                nr_doc=nr_doc,
                                assunto_doc=assunto_doc,
                                origem=origem,
                                prazo_final=prazo_final,
                                obs=obs_doc,
                            )
                            if assunto_solic or nr_solic or prazo_om or responsaveis:
                                salvar_ou_atualizar_solicitacao(
                                    caso_id=int(new_id),
                                    assunto_solic=assunto_solic,
                                    prazo_om=prazo_om,
                                    selecionadas=responsaveis,
                                    nr_doc_solicitado=nr_solic or "00",
                                )
                            set_resposta_e_status(int(new_id), nr_resp)

                            st.session_state["pending_select_id"] = int(new_id)
                            st.toast("Salvo ✅")
                            st.rerun()

                        elif assunto_solic:
                            new_id = insert_solicitacao_sem_documento(
                                assunto_solic=assunto_solic,
                                prazo_om=prazo_om,
                                nr_doc_solicitado=nr_solic or "00",
                            )
                            if responsaveis:
                                salvar_ou_atualizar_solicitacao(
                                    caso_id=int(new_id),
                                    assunto_solic=assunto_solic,
                                    prazo_om=prazo_om,
                                    selecionadas=responsaveis,
                                    nr_doc_solicitado=nr_solic or "00",
                                )
                            set_resposta_e_status(int(new_id), nr_resp)

                            st.session_state["pending_select_id"] = int(new_id)
                            st.toast("Salvo ✅")
                            st.rerun()
                        else:
                            st.error("Preencha pelo menos **Documento (Nr + Assunto)** ou **Assunto da Solicitação**.")

                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

    # =========================================================
    # Acompanhamento
    # =========================================================
    if df_acomp.empty:
        st.info("Nenhum item em acompanhamento.")
    else:
        pend_map = {int(r["caso_id"]): int(r["qtd"]) for _, r in pend.iterrows()} if not pend.empty else {}
        df_acomp["Pendências (Qtd)"] = df_acomp["id"].astype(int).map(lambda x: pend_map.get(int(x), 0))

        df_show = pd.DataFrame(
            {
                "Id": df_acomp["id"].astype(int),
                "Origem": df_acomp.get("origem").fillna("-"),
                "Nr Doc (Recebido)": df_acomp["nr_doc_recebido"].fillna("-"),
                "Assunto (Documento)": df_acomp["assunto_doc"].fillna("-"),
                "Prazo Final": pd.to_datetime(df_acomp.get("prazo_final"), errors="coerce").dt.strftime("%d/%m/%Y").fillna("-"),
                "Nr Doc (Solicitado)": df_acomp.get("nr_doc_solicitado").fillna("-"),
                "Assunto (Solicitação)": df_acomp.get("assunto_solic").fillna("-"),
                "Prazo OM": pd.to_datetime(df_acomp.get("prazo_om"), errors="coerce").dt.strftime("%d/%m/%Y").fillna("-"),
                "Pendências (Qtd)": df_acomp["Pendências (Qtd)"],
                "Status": df_acomp.get("status").fillna("-"),
                "Nr Doc (Resposta)": df_acomp.get("nr_doc_resposta").fillna("-"),
            }
        )

        topL, topR, topX = st.columns([1, 0.16, 0.22])
        with topL:
            st.subheader("Acompanhamento")
        with topR:
            # ➕ Novo (limpa seleção e caixas) — fora da caixa Documento
            if st.button("➕", key="btn_new_row", help="Novo (limpar seleção)"):
                _request_clear_doc_box()
                st.rerun()
        with topX:
            btn_arquivar = st.button("🗄️ Arquivar", type="primary", key="dash_btn_arquivar", use_container_width=True)

        df_styled = df_show.style.apply(_row_style_acompanhamento, axis=1)

        sel = st.dataframe(
            df_styled,
            use_container_width=True,
            hide_index=True,
            selection_mode="single-row",
            on_select="rerun",
            key="tbl_dash",
        )

        clicked_id = None
        if sel and sel.get("selection", {}).get("rows"):
            idx = sel["selection"]["rows"][0]
            clicked_id = int(df_show.iloc[idx]["Id"])

        current_id = st.session_state.get("current_selected_id")
        if clicked_id is not None and clicked_id != current_id:
            # ✅ carrega na próxima execução (antes dos widgets)
            st.session_state["pending_select_id"] = int(clicked_id)
            st.rerun()

        selected_id = st.session_state.get("current_selected_id")

        if btn_arquivar and selected_id:
            archive_caso(int(selected_id))
            st.toast("Arquivado ✅")
            _request_clear_doc_box()
            st.rerun()
        elif btn_arquivar and not selected_id:
            st.warning("Selecione uma linha na tabela.")

        # ✅ Se NÃO tiver linha selecionada, NÃO mostra Mensagem e Responsável
        if selected_id:
            caso = fetch_caso(int(selected_id)) or {}
            ret = fetch_retornos(int(selected_id))

            with st.expander("Mensagem", expanded=False):
                msg_key = f"msg_edit_{selected_id}"
                st.session_state.setdefault(msg_key, build_msg_cobranca(caso, ret))
                st.text_area("Mensagem", key=msg_key, height=200, label_visibility="collapsed")

            with st.expander("Responsável", expanded=True):
                if ret.empty:
                    st.info("Sem responsáveis cadastrados.")
                else:
                    ret = ret.sort_values("om").reset_index(drop=True)
                    retorno_ids = ret["id"].astype(int).tolist()

                    def to_display_status(s: str) -> str:
                        s0 = (s or "Pendente").strip().title()
                        if s0 not in STATUS_DISPLAY:
                            s0 = "Pendente"
                        return STATUS_DISPLAY[s0]

                    base_df = pd.DataFrame(
                        {
                            "Responsável": ret["om"].fillna("").astype(str),
                            "Status": ret["status"].fillna("Pendente").astype(str).apply(to_display_status),
                            "Obs": ret["observacoes"].fillna("").astype(str),
                        }
                    )

                    orig_key = f"ret_original_snapshot_{selected_id}"
                    if orig_key not in st.session_state:
                        st.session_state[orig_key] = _snapshot_from_editor(base_df)

                    edited = st.data_editor(
                        base_df,
                        use_container_width=True,
                        hide_index=True,
                        key=f"ret_editor_{selected_id}",
                        column_config={
                            "Responsável": st.column_config.TextColumn("Responsável", disabled=True),
                            "Status": st.column_config.SelectboxColumn(
                                "Status",
                                options=[STATUS_DISPLAY["Pendente"], STATUS_DISPLAY["Respondido"]],
                                required=True,
                                width="medium",
                            ),
                            "Obs": st.column_config.TextColumn("Obs", width="large"),
                        },
                        disabled=["Responsável"],
                    )

                    dirty = _snapshot_from_editor(edited) != st.session_state.get(orig_key, [])
                    a1, a2 = st.columns([0.6, 0.4], gap="small")
                    with a1:
                        if dirty:
                            st.markdown('<span class="badge badge-warn">⚠️ Alterações pendentes</span>', unsafe_allow_html=True)
                        else:
                            st.markdown('<span class="badge badge-ok">✅ Tudo salvo</span>', unsafe_allow_html=True)
                    with a2:
                        if dirty and st.button("Salvar alterações", type="primary", key=f"btn_save_ret_{selected_id}", use_container_width=True):
                            st.session_state[f"confirm_save_ret_{selected_id}"] = True

                    if st.session_state.get(f"confirm_save_ret_{selected_id}"):
                        st.warning("Confirma salvar as alterações em Responsável?")
                        cc1, cc2 = st.columns([0.22, 0.78], gap="small")
                        with cc1:
                            if st.button("Confirmar", key=f"btn_confirm_save_ret_{selected_id}"):
                                for i, row in edited.reset_index(drop=True).iterrows():
                                    rid = retorno_ids[i]
                                    disp = (row.get("Status") or STATUS_DISPLAY["Pendente"]).strip()
                                    new_status = DISPLAY_TO_STATUS.get(disp, "Pendente")
                                    new_obs = (row.get("Obs") or "").strip() or None
                                    _sb_table("retornos_om").update({"status": new_status, "observacoes": new_obs}).eq("id", int(rid)).execute()

                                st.session_state[orig_key] = _snapshot_from_editor(edited)
                                st.session_state.pop(f"confirm_save_ret_{selected_id}", None)
                                st.toast("Alterações salvas ✅")
                                st.rerun()
                        with cc2:
                            if st.button("Cancelar", key=f"btn_cancel_save_ret_{selected_id}"):
                                st.session_state.pop(f"confirm_save_ret_{selected_id}", None)
                                st.info("Salvamento cancelado.")


# =========================================================
# PAGE: RESPONSÁVEL
#   - cadastrar responsável (master_oms)
#   - cadastrar múltiplos contatos (nome + telefone) por responsável
#   - botão que abre WhatsApp Web
#   - dashboard: pendências por responsável
# =========================================================
elif page == "👥 Responsável":
    st.title("👥 Responsável")
    st.markdown('<div class="small-muted">Cadastro de responsáveis, contatos e visão de pendências</div>', unsafe_allow_html=True)
    st.divider()

    # -------- Dashboard: pendências por responsável --------
    st.subheader("Pendências por responsável")
    try:
        res = _sb_table("retornos_om").select("om,status").execute()
        d = pd.DataFrame(res.data or [])
    except Exception as e:
        st.error(f"Erro ao carregar pendências: {e}")
        d = pd.DataFrame(columns=["om", "status"])

    if d.empty:
        st.info("Sem dados de pendências.")
    else:
        d["status"] = d["status"].fillna("Pendente").astype(str)
        d["om"] = d["om"].fillna("").astype(str)
        d = d[d["om"].str.strip() != ""]
        pend = d[d["status"].str.lower() == "pendente"]
        agg = pend.groupby("om").size().reset_index(name="Pendentes").sort_values("Pendentes", ascending=False)

        c1, c2 = st.columns([1.2, 1.0], gap="large")
        with c1:
            st.dataframe(agg, use_container_width=True, hide_index=True)
        with c2:
            # gráfico simples
            if not agg.empty:
                chart_df = agg.set_index("om")["Pendentes"]
                st.bar_chart(chart_df)

    st.divider()

    # -------- Gerenciar responsáveis (master_oms) --------
    st.subheader("Gerenciar responsáveis")
    with st.expander("Adicionar / Remover", expanded=False):
        add_c1, add_c2 = st.columns([1, 0.28], gap="small")
        with add_c1:
            novo = st.text_input("Nome do responsável", key="resp_new_name", placeholder="Ex.: 25 BI Pqdt")
        with add_c2:
            if st.button("Adicionar", type="primary", key="btn_add_resp", use_container_width=True):
                ok, msg = add_master_om(novo)
                if ok:
                    st.toast("Adicionado ✅")
                    st.success(msg)
                    st.session_state["resp_new_name"] = ""
                    st.rerun()
                else:
                    st.error(msg)

        st.markdown("---")
        lista = get_master_oms()
        rm = st.multiselect("Remover responsáveis", options=lista, key="resp_rm_list")
        if st.button("Remover selecionados", key="btn_rm_resp", use_container_width=True):
            ok, msg = delete_master_oms(rm)
            if ok:
                st.toast("Removido ✅")
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

    st.divider()

    # -------- Contatos por responsável --------
    st.subheader("Contatos (nome + telefone) por responsável")

    oms = get_master_oms()
    cA, cB = st.columns([0.9, 1.1], gap="large")

    with cA:
        st.markdown("##### Cadastrar contato")
        resp_sel = st.selectbox("Responsável", options=["(selecione)"] + oms, index=0, key="cont_resp_sel")
        nome_cont = st.text_input("Nome do contato", key="cont_nome", placeholder="Ex.: Sgt Paulo")
        tel_cont = st.text_input("Telefone", key="cont_tel", placeholder="Ex.: 21999998888")

        if st.button("Salvar contato", type="primary", key="btn_save_contact", use_container_width=True):
            if resp_sel == "(selecione)":
                st.error("Selecione um responsável.")
            elif not _normalize_name(nome_cont):
                st.error("Informe o nome do contato.")
            elif not _digits_only_phone(tel_cont):
                st.error("Informe um telefone válido.")
            else:
                try:
                    insert_contato_responsavel(resp_sel, nome_cont, tel_cont)
                    st.toast("Contato salvo ✅")
                    st.session_state["cont_nome"] = ""
                    st.session_state["cont_tel"] = ""
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar contato: {e}")

    with cB:
        st.markdown("##### Lista de contatos")
        dfc = fetch_contatos_responsaveis()
        if dfc.empty:
            st.info("Sem contatos cadastrados.")
        else:
            # filtro opcional por responsável
            f = st.selectbox("Filtrar", options=["Todos"] + sorted(dfc["responsavel"].dropna().astype(str).unique().tolist()), key="cont_filter")
            dfv = dfc.copy()
            if f != "Todos":
                dfv = dfv[dfv["responsavel"].astype(str) == f]

            # tabela visual
            show = pd.DataFrame(
                {
                    "ID": dfv.get("id", "").astype(str),
                    "Responsável": dfv.get("responsavel", "").astype(str),
                    "Contato": dfv.get("contato_nome", "").astype(str),
                    "Telefone": dfv.get("telefone", "").astype(str),
                }
            )
            st.dataframe(show, use_container_width=True, hide_index=True)

            # ações: abrir whatsapp + excluir (linha por linha)
            st.markdown("##### Ações")
            for _, r in dfv.iterrows():
                rid = int(r.get("id"))
                resp = str(r.get("responsavel") or "")
                nome = str(r.get("contato_nome") or "")
                tel = str(r.get("telefone") or "")
                msg_padrao = f"Olá, {nome}! Tudo bem? Poderia me atualizar sobre as pendências do {resp}, por gentileza?"
                url = whatsapp_web_url(tel, msg_padrao)

                row1, row2, row3 = st.columns([1.2, 0.55, 0.25], gap="small")
                with row1:
                    st.write(f"**{resp}** — {nome} ({tel})")
                with row2:
                    st.link_button("Abrir WhatsApp", url, use_container_width=True)
                with row3:
                    if st.button("🗑️", key=f"del_contact_{rid}", help="Excluir contato"):
                        try:
                            delete_contato_responsavel(rid)
                            st.toast("Excluído ✅")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao excluir: {e}")


# =========================================================
# PAGE: ARQUIVADOS
# =========================================================
else:
    st.title("🗄️ Arquivados")
    st.divider()

    df_a = fetch_arquivados_casos()
    if df_a.empty:
        st.info("Nenhum documento arquivado.")
    else:
        df_a_show = pd.DataFrame(
            {
                "Nr Doc (Recebido)": df_a["nr_doc_recebido"].fillna("-"),
                "Assunto (Documento)": df_a["assunto_doc"].fillna("-"),
                "Assunto (Solicitação)": df_a.get("assunto_solic").fillna("-"),
                "Origem": df_a.get("origem").fillna("-"),
                "Prazo Final": pd.to_datetime(df_a.get("prazo_final"), errors="coerce").dt.strftime("%d/%m/%Y").fillna("-"),
                "Prazo OM": pd.to_datetime(df_a.get("prazo_om"), errors="coerce").dt.strftime("%d/%m/%Y").fillna("-"),
                "Nr Doc (Solicitado)": df_a.get("nr_doc_solicitado").fillna("-"),
                "Nr Doc (Resposta)": df_a.get("nr_doc_resposta").fillna("-"),
                "Status": df_a.get("status").fillna("-"),
            }
        )
        st.dataframe(df_a_show, use_container_width=True, hide_index=True)
