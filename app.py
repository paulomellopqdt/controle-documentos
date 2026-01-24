from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="Controle de Docs",
    page_icon="icon.png",
    layout="wide",
)

st.markdown("""
<style>
/* ===============================
   Controle de Docs - UI (Lovable-like)
   Mantém 100% da lógica intacta
   =============================== */

:root{
  --bg: #F6F8FC;
  --card: #FFFFFF;
  --text: #0F172A;
  --muted: rgba(15, 23, 42, 0.62);
  --border: rgba(15, 23, 42, 0.10);
  --shadow: 0 10px 30px rgba(15, 23, 42, 0.06);

  --primary: #2563EB;
  --danger: #EF4444;
  --warn: #F59E0B;
  --success: #22C55E;
}

/* Fundo do app */
.stApp{
  background: var(--bg);
}

/* Container principal */
.block-container{
  padding-top: 1.6rem;
  padding-bottom: 2rem;
  max-width: 1400px;
}

/* Tipografia */
h1,h2,h3{
  letter-spacing: -0.35px;
  line-height: 1.1;
  color: var(--text);
  padding-top: 0.25rem;
}
.small-muted{
  color: var(--muted);
  font-size: 0.92rem;
}

/* ===============================
   Sidebar (escura)
   =============================== */
section[data-testid="stSidebar"]{
  background: linear-gradient(180deg, #0b1220 0%, #0a1020 100%);
  border-right: 1px solid rgba(255,255,255,0.08);
}
section[data-testid="stSidebar"] .block-container{
  padding-top: 1.2rem;
}
section[data-testid="stSidebar"] *{
  color: rgba(255,255,255,0.92) !important;
}
section[data-testid="stSidebar"] hr{
  border: none;
  height: 1px;
  background: rgba(255,255,255,0.10);
}

/* Radios (Menu) na sidebar: deixa mais “botão” */
section[data-testid="stSidebar"] div[role="radiogroup"] label{
  border-radius: 12px;
  padding: 8px 10px;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover{
  background: rgba(255,255,255,0.06);
}

/* Botões na sidebar */
section[data-testid="stSidebar"] .stButton>button{
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 14px;
  padding: .60rem .95rem;
  font-weight: 800;
  transition: all 120ms ease;
}
section[data-testid="stSidebar"] .stButton>button:hover{
  transform: translateY(-1px);
  background: rgba(255,255,255,0.10);
  border-color: rgba(255,255,255,0.18);
}

/* ===============================
   Cards / Expander / Containers
   =============================== */
div[data-testid="stVerticalBlockBorderWrapper"]{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 16px;
  box-shadow: var(--shadow);
}

/* Expander mais “card” */
details[data-testid="stExpander"]{
  border: 1px solid var(--border);
  border-radius: 16px;
  background: var(--card);
  box-shadow: var(--shadow);
  overflow: hidden;
}
details[data-testid="stExpander"] > summary{
  padding: 10px 14px;
}

/* ===============================
   Métricas (st.metric)
   =============================== */
div[data-testid="stMetric"]{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 14px 14px;
  box-shadow: var(--shadow);
}
div[data-testid="stMetric"] label{
  opacity: 0.75;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"]{
  font-size: 1.75rem;
  font-weight: 800;
}

/* ===============================
   Inputs
   =============================== */
div[data-baseweb="input"] > div,
div[data-baseweb="select"] > div,
div[data-baseweb="textarea"] > div{
  border-radius: 14px !important;
  border: 1px solid rgba(15,23,42,0.14) !important;
  background: #FFFFFF !important;
}

/* ===============================
   Botões (geral)
   =============================== */
.stButton>button{
  border-radius: 14px;
  padding: .60rem 1rem;
  font-weight: 800;
  border: 1px solid rgba(15,23,42,0.14);
  background: rgba(37,99,235,0.10);
  color: var(--primary);
  transition: all 120ms ease;
}
.stButton>button:hover{
  transform: translateY(-1px);
  border-color: rgba(37,99,235,0.26);
  background: rgba(37,99,235,0.16);
}

/* Botões primary do Streamlit */
button[kind="primary"]{
  background: var(--primary) !important;
  color: #FFFFFF !important;
  border: 1px solid rgba(37,99,235,0.35) !important;
}
button[kind="primary"]:hover{
  filter: brightness(0.97);
}

/* ===============================
   DataFrames / DataEditor
   =============================== */
div[data-testid="stDataFrame"], div[data-testid="stDataEditor"]{
  border: 1px solid var(--border);
  border-radius: 16px;
  overflow: hidden;
  background: var(--card);
  box-shadow: var(--shadow);
}

/* Centralizar cabeçalho e células (você já faz isso) */
div[data-testid="stDataFrame"] table th,
div[data-testid="stDataFrame"] table td,
div[data-testid="stDataEditor"] table th,
div[data-testid="stDataEditor"] table td{
  text-align: center !important;
  vertical-align: middle !important;
}

/* Separadores */
hr{
  border-color: rgba(15,23,42,0.10);
}

/* Badges (você já usa .badge) */
.badge{
  display:inline-flex;
  align-items:center;
  gap:8px;
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 0.85rem;
  border:1px solid rgba(15,23,42,0.12);
}
.badge-warn{ background: rgba(245,158,11,0.14); color: #854d0e; }
.badge-ok{ background: rgba(34,197,94,0.12); color: #166534; }
</style>
""", unsafe_allow_html=True)



from datetime import date, datetime
import re
import pandas as pd
from supabase import create_client, Client


RETORNO_STATUS = ["Pendente", "Respondido"]
STATUS_DISPLAY = {"Pendente": "🔴 Pendente", "Respondido": "🟢 Respondido"}
DISPLAY_TO_STATUS = {v: k for k, v in STATUS_DISPLAY.items()}


# =========================================================
# Supabase client
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
# Auth
# =========================================================
def require_auth():
    st.session_state.setdefault("sb_session", None)
    st.session_state.setdefault("sb_user", None)

    if st.session_state["sb_session"] and st.session_state["sb_user"]:
        return

    st.title("🔐 Controle de Documentos — Login")
    st.markdown('<div class="small-muted">Acesse com sua conta para ver apenas seus dados.</div>', unsafe_allow_html=True)

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
# CRUD
# =========================================================
def fetch_casos() -> pd.DataFrame:
    res = _sb_table("casos").select("*").order("id", desc=True).execute()
    return pd.DataFrame(res.data or [])


def fetch_caso(caso_id: int) -> dict | None:
    res = _sb_table("casos").select("*").eq("id", int(caso_id)).limit(1).execute()
    data = res.data or []
    return data[0] if data else None


def update_caso_by_id_safe(caso_id: int, payload: dict):
    if "nr_doc_recebido" in payload and (payload["nr_doc_recebido"] is None or str(payload["nr_doc_recebido"]).strip() == ""):
        payload["nr_doc_recebido"] = "-"
    if "assunto_doc" in payload and (payload["assunto_doc"] is None or str(payload["assunto_doc"]).strip() == ""):
        payload["assunto_doc"] = "-"
    if "origem" in payload and (payload["origem"] is None or str(payload["origem"]).strip() == ""):
        payload["origem"] = "-"
    if "observacoes" in payload and (payload["observacoes"] is None or str(payload["observacoes"]).strip() == ""):
        payload["observacoes"] = "-"
    _sb_table("casos").update(payload).eq("id", int(caso_id)).execute()


def insert_documento_safe(nr_doc: str, assunto_doc: str, origem: str | None, prazo_final: date | None, obs: str | None) -> int:
    user = st.session_state["sb_user"]
    nr_doc = (nr_doc or "").strip() or "-"
    assunto_doc = (assunto_doc or "").strip() or "-"
    origem = (origem or "").strip() if origem and origem.strip() else "-"
    obs = (obs or "").strip() if obs and obs.strip() else "-"
    payload = {
        "owner_id": user.id,
        "nr_doc_recebido": nr_doc,
        "assunto_doc": assunto_doc,
        "origem": origem,
        "prazo_final": prazo_final.isoformat() if prazo_final else None,
        "observacoes": obs,
        "status": "Recebido",
        "created_at": datetime.now().isoformat(),
    }
    res = _sb_table("casos").insert(payload).execute()
    return int(res.data[0]["id"])


def insert_solicitacao_sem_documento(assunto_solic: str, prazo_om: date | None, nr_doc_solicitado: str | None) -> int:
    user = st.session_state["sb_user"]
    payload = {
        "owner_id": user.id,
        "nr_doc_recebido": "-",
        "assunto_doc": "-",
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


def unarchive_caso(caso_id: int):
    _sb_table("arquivados").delete().eq("caso_id", int(caso_id)).execute()


def delete_caso(caso_id: int):
    _sb_table("retornos_om").delete().eq("caso_id", int(caso_id)).execute()
    _sb_table("arquivados").delete().eq("caso_id", int(caso_id)).execute()
    _sb_table("casos").delete().eq("id", int(caso_id)).execute()


def get_master_oms() -> list[str]:
    res = _sb_table("master_oms").select("nome").order("nome").execute()
    return [x["nome"] for x in (res.data or [])]


def add_master_om(nome: str):
    nome = (nome or "").strip()
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
    nomes = [(n or "").strip() for n in (nomes or []) if (n or "").strip()]
    if not nomes:
        return True, "Nada para remover."
    for n in nomes:
        _sb_table("master_oms").delete().eq("nome", n).execute()
        _sb_table("retornos_om").delete().eq("om", n).execute()
    return True, "Responsáveis removidos ✅"


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
    selecionadas_set = set(selecionadas)

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
# Contatos por responsável (tabela: responsaveis_contatos)
# =========================================================
def _only_digits_phone(s: str) -> str:
    return re.sub(r"[^0-9]", "", s or "")


def _wa_web_link(phone_digits: str, text: str = "") -> str:
    phone_digits = _only_digits_phone(phone_digits)
    if not phone_digits:
        return "https://web.whatsapp.com/"
    phone = phone_digits if phone_digits.startswith("55") else "55" + phone_digits
    text_q = (text or "").replace(" ", "%20").replace("\n", "%0A")
    return f"https://web.whatsapp.com/send?phone={phone}&text={text_q}"


def fetch_contatos_responsaveis() -> pd.DataFrame:
    res = _sb_table("responsaveis_contatos").select("*").order("responsavel").order("contato_nome").execute()
    return pd.DataFrame(res.data or [])


def insert_contato_responsavel(responsavel: str, contato_nome: str, telefone: str):
    user = st.session_state["sb_user"]
    payload = {
        "owner_id": user.id,
        "responsavel": (responsavel or "").strip(),
        "contato_nome": (contato_nome or "").strip(),
        "telefone": (telefone or "").strip(),
        "created_at": datetime.now().isoformat(),
    }
    _sb_table("responsaveis_contatos").insert(payload).execute()


def delete_contato_responsavel(contato_id: int):
    _sb_table("responsaveis_contatos").delete().eq("id", int(contato_id)).execute()


# =========================================================
# Helpers UI
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
    "doc_nr", "doc_assunto_doc", "doc_origem", "doc_prazo_final", "doc_obs",
    "sol_assunto_solic", "sol_prazo_om", "sol_doc_solicitado", "sol_responsaveis",
    "resp_nr_doc_resposta",
]


def _apply_defaults_if_missing():
    st.session_state.setdefault("current_selected_id", None)
    st.session_state.setdefault("pending_select_id", None)
    st.session_state.setdefault("__clear_doc_box__", False)

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


def _request_clear_doc_box():
    st.session_state["__clear_doc_box__"] = True


def _apply_clear_doc_box():
    for k in DOC_KEYS:
        if k in st.session_state:
            st.session_state.pop(k, None)
    _apply_defaults_if_missing()


def _apply_load_selected_into_doc_box(caso_id: int):
    caso = fetch_caso(int(caso_id)) or {}

    def _un_dash(x):
        return "" if x in [None, "-"] else x

    st.session_state["doc_nr"] = _un_dash(caso.get("nr_doc_recebido"))
    st.session_state["doc_assunto_doc"] = _un_dash(caso.get("assunto_doc"))
    st.session_state["doc_origem"] = _un_dash(caso.get("origem"))
    st.session_state["doc_prazo_final"] = pd.to_datetime(caso["prazo_final"]).date() if caso.get("prazo_final") else None
    st.session_state["doc_obs"] = _un_dash(caso.get("observacoes"))

    st.session_state["sol_assunto_solic"] = _un_dash(caso.get("assunto_solic"))
    st.session_state["sol_prazo_om"] = pd.to_datetime(caso["prazo_om"]).date() if caso.get("prazo_om") else None
    st.session_state["sol_doc_solicitado"] = _un_dash(caso.get("nr_doc_solicitado"))
    st.session_state["resp_nr_doc_resposta"] = _un_dash(caso.get("nr_doc_resposta"))

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


# =========================================================
# APP START
# =========================================================
require_auth()
page, dash_title = sidebar_layout()
_apply_defaults_if_missing()

if st.session_state.pop("__clear_doc_box__", False):
    _apply_clear_doc_box()
    st.session_state["current_selected_id"] = None
    st.session_state["pending_select_id"] = None

pending = st.session_state.get("pending_select_id")
if pending is not None:
    st.session_state["current_selected_id"] = int(pending)
    _apply_load_selected_into_doc_box(int(pending))
    st.session_state["pending_select_id"] = None


# =========================================================
# PAGE: DASHBOARD (Acompanhamento sem alteração)
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
            st.multiselect("Responsáveis", options=oms, key="sol_responsaveis", label_visibility="collapsed")

        with colC:
            st.markdown("##### Resposta")
            st.text_input("Nr (Resposta)", key="resp_nr_doc_resposta")

            if st.button("Salvar", type="primary", key="btn_save_all", use_container_width=True):
                sel_id = st.session_state.get("current_selected_id")

                nr_doc = (st.session_state.get("doc_nr") or "").strip()
                assunto_doc = (st.session_state.get("doc_assunto_doc") or "").strip()
                origem = (st.session_state.get("doc_origem") or "").strip()
                prazo_final = st.session_state.get("doc_prazo_final")
                obs_doc = (st.session_state.get("doc_obs") or "").strip()

                assunto_solic = (st.session_state.get("sol_assunto_solic") or "").strip()
                prazo_om = st.session_state.get("sol_prazo_om")
                nr_solic = (st.session_state.get("sol_doc_solicitado") or "").strip()
                responsaveis = st.session_state.get("sol_responsaveis") or []
                nr_resp = (st.session_state.get("resp_nr_doc_resposta") or "").strip()

                try:
                    if sel_id:
                        update_payload = {
                            "nr_doc_recebido": nr_doc,
                            "assunto_doc": assunto_doc,
                            "origem": origem,
                            "prazo_final": prazo_final.isoformat() if prazo_final else None,
                            "observacoes": obs_doc,
                            "assunto_solic": assunto_solic or None,
                            "prazo_om": prazo_om.isoformat() if prazo_om else None,
                            "nr_doc_solicitado": nr_solic or None,
                        }
                        update_caso_by_id_safe(int(sel_id), update_payload)

                        if assunto_solic or nr_solic or prazo_om or responsaveis:
                            salvar_ou_atualizar_solicitacao(
                                caso_id=int(sel_id),
                                assunto_solic=assunto_solic or None,
                                prazo_om=prazo_om,
                                selecionadas=responsaveis,
                                nr_doc_solicitado=nr_solic or "00",
                            )

                        set_resposta_e_status(int(sel_id), nr_resp)
                        st.toast("Atualizado ✅")
                        st.rerun()
                    else:
                        if nr_doc or assunto_doc or origem or prazo_final or obs_doc:
                            new_id = insert_documento_safe(nr_doc, assunto_doc, origem or None, prazo_final, obs_doc or None)
                            if assunto_solic or nr_solic or prazo_om or responsaveis:
                                salvar_ou_atualizar_solicitacao(
                                    caso_id=int(new_id),
                                    assunto_solic=assunto_solic or None,
                                    prazo_om=prazo_om,
                                    selecionadas=responsaveis,
                                    nr_doc_solicitado=nr_solic or "00",
                                )
                            set_resposta_e_status(int(new_id), nr_resp)
                            st.session_state["pending_select_id"] = int(new_id)
                            st.toast("Salvo ✅")
                            st.rerun()
                        elif assunto_solic:
                            new_id = insert_solicitacao_sem_documento(assunto_solic, prazo_om, nr_solic or "00")
                            if responsaveis:
                                salvar_ou_atualizar_solicitacao(int(new_id), assunto_solic, prazo_om, responsaveis, nr_solic or "00")
                            set_resposta_e_status(int(new_id), nr_resp)
                            st.session_state["pending_select_id"] = int(new_id)
                            st.toast("Salvo ✅")
                            st.rerun()
                        else:
                            st.error("Preencha algum campo para salvar.")
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

            if st.button("Limpar", key="btn_clear_doc", use_container_width=True):
                # ✅ também deseleciona a linha no Acompanhamento
                st.session_state.pop("tbl_dash", None)
                st.session_state["current_selected_id"] = None
                st.session_state["pending_select_id"] = None
                _request_clear_doc_box()
                st.rerun()

    # --------- ACOMPANHAMENTO (SEM ALTERAÇÃO) ----------
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

        topL, topR = st.columns([1, 0.22])
        with topL:
            st.subheader("Acompanhamento")
        with topR:
            st.markdown("<div style='padding-top:6px'></div>", unsafe_allow_html=True)
            btn_arquivar = st.button("🗄️ Arquivar", type="primary", key="dash_btn_arquivar")

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

        prev_id = st.session_state.get("current_selected_id")

        # ✅ quando "desmarca" (volta sem seleção), limpa campos
        if clicked_id is None:
            if prev_id is not None:
                st.session_state["current_selected_id"] = None
                _request_clear_doc_box()
                st.rerun()
        else:
            if clicked_id != prev_id:
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
# =========================================================
elif page == "👥 Responsável":
    st.title("👥 Responsável")
    st.markdown('<div class="small-muted">Gestão de responsáveis e contatos</div>', unsafe_allow_html=True)
    st.divider()

    st.markdown("#### Gerenciar Responsável")
    oms = get_master_oms()

    r1, r2, r3 = st.columns([1.2, 1.2, 0.8], gap="small")
    with r1:
        novo = st.text_input("Novo", placeholder="Ex: 25º BI Pqdt", key="resp_add_name")
    with r2:
        remover = st.multiselect("Remover", options=oms, key="resp_rm_ms")
    with r3:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        cbtn1, cbtn2 = st.columns(2, gap="small")
        with cbtn1:
            if st.button("➕", help="Adicionar responsável", use_container_width=True, key="btn_add_resp"):
                ok, msg = add_master_om(novo)
                if ok:
                    st.toast("Responsável adicionado ✅")
                    st.rerun()
                else:
                    st.error(msg)
        with cbtn2:
            if st.button("🗑️", help="Remover responsáveis selecionados", use_container_width=True, key="btn_rm_resp"):
                ok, msg = delete_master_oms(remover)
                if ok:
                    st.toast("Responsável removido ✅")
                    st.rerun()
                else:
                    st.error(msg)

    st.divider()

    st.markdown("#### Contatos")
    with st.expander("➕ Novo contato", expanded=False):
        c1, c2, c3 = st.columns([1.1, 1.1, 1.0], gap="small")
        with c1:
            resp = st.selectbox("Responsável", options=oms, key="ct_resp_sel")
        with c2:
            nome = st.text_input("Nome", key="ct_nome_in")
        with c3:
            tel = st.text_input("Telefone", placeholder="Ex: 21999999999", key="ct_tel_in")

        a1, a2 = st.columns([0.18, 0.82], gap="small")
        with a1:
            if st.button("💾", help="Salvar contato", type="primary", use_container_width=True, key="btn_ct_save"):
                if not resp or not nome.strip() or not tel.strip():
                    st.error("Preencha Responsável, Nome e Telefone.")
                else:
                    insert_contato_responsavel(resp, nome.strip(), tel.strip())
                    st.toast("Contato salvo ✅")
                    st.session_state["ct_nome_in"] = ""
                    st.session_state["ct_tel_in"] = ""
                    st.rerun()
        with a2:
            st.markdown("<div class='small-muted'>Dica: você pode cadastrar mais de um contato para o mesmo responsável.</div>", unsafe_allow_html=True)

    dfc = fetch_contatos_responsaveis()
    if dfc.empty:
        st.info("Nenhum contato cadastrado.")
    else:
        df_view = dfc[["responsavel", "contato_nome", "telefone"]].copy()
        df_view.columns = ["Responsável", "Nome", "Telefone"]
        st.dataframe(df_view, use_container_width=True, hide_index=True)

        st.markdown("#### Ações")
        a1, a2, a3 = st.columns([1.1, 1.2, 0.7], gap="small")
        with a1:
            resp_sel = st.selectbox("Responsável", options=sorted(df_view["Responsável"].unique()), key="act_resp")
        with a2:
            nomes = df_view[df_view["Responsável"] == resp_sel]["Nome"].tolist()
            nome_sel = st.selectbox("Contato", options=nomes, key="act_nome")

        row = df_view[(df_view["Responsável"] == resp_sel) & (df_view["Nome"] == nome_sel)].iloc[0]
        telefone = row["Telefone"]
        link = f"https://web.whatsapp.com/send?phone=55{''.join(filter(str.isdigit, str(telefone)))}"

        # ✅ WhatsApp + Remover lado a lado (padronizado)
        with a3:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            bwh, brm = st.columns(2, gap="small")
            with bwh:
                st.link_button("🟢", link, use_container_width=True)
            with brm:
                if st.button("🗑️", help="Remover contato selecionado", use_container_width=True, key="btn_ct_rm"):
                    st.session_state["confirm_rm_contact"] = True

        if st.session_state.get("confirm_rm_contact"):
            st.warning("Confirmar remoção do contato?")
            cc1, cc2 = st.columns([0.2, 0.2], gap="small")
            with cc1:
                if st.button("✅", help="Confirmar", use_container_width=True, key="btn_ct_rm_yes"):
                    cid = dfc[(dfc["responsavel"] == resp_sel) & (dfc["contato_nome"] == nome_sel)]["id"].iloc[0]
                    delete_contato_responsavel(int(cid))
                    st.session_state.pop("confirm_rm_contact", None)
                    st.toast("Contato removido ✅")
                    st.rerun()
            with cc2:
                if st.button("❌", help="Cancelar", use_container_width=True, key="btn_ct_rm_no"):
                    st.session_state.pop("confirm_rm_contact", None)


# =========================================================
# PAGE: ARQUIVADOS (tabela igual ao Acompanhamento + botões em cima)
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
                "Id": df_a["id"].astype(int),
                "Origem": df_a.get("origem").fillna("-"),
                "Nr Doc (Recebido)": df_a["nr_doc_recebido"].fillna("-"),
                "Assunto (Documento)": df_a["assunto_doc"].fillna("-"),
                "Prazo Final": pd.to_datetime(df_a.get("prazo_final"), errors="coerce").dt.strftime("%d/%m/%Y").fillna("-"),
                "Nr Doc (Solicitado)": df_a.get("nr_doc_solicitado").fillna("-"),
                "Assunto (Solicitação)": df_a.get("assunto_solic").fillna("-"),
                "Prazo OM": pd.to_datetime(df_a.get("prazo_om"), errors="coerce").dt.strftime("%d/%m/%Y").fillna("-"),
                "Nr Doc (Resposta)": df_a.get("nr_doc_resposta").fillna("-"),
                "Status": df_a.get("status").fillna("-"),
            }
        )

        # botões em cima (como no Acompanhamento)
        tL, tR1, tR2 = st.columns([1, 0.12, 0.12], gap="small")
        with tL:
            st.subheader("Arquivados")
        with tR1:
            btn_restaurar = st.button("↩️", help="Restaurar selecionado", type="primary", use_container_width=True, key="btn_arq_restore")
        with tR2:
            btn_excluir = st.button("🗑️", help="Excluir selecionado", use_container_width=True, key="btn_arq_del")

        df_styled = df_a_show.style.apply(_row_style_acompanhamento, axis=1)

        sel_arq = st.dataframe(
            df_styled,
            use_container_width=True,
            hide_index=True,
            selection_mode="single-row",
            on_select="rerun",
            key="tbl_arq",
        )

        selected_arch_id = None
        if sel_arq and sel_arq.get("selection", {}).get("rows"):
            idx = sel_arq["selection"]["rows"][0]
            selected_arch_id = int(df_a_show.iloc[idx]["Id"])

        if btn_restaurar:
            if not selected_arch_id:
                st.warning("Selecione uma linha na tabela.")
            else:
                unarchive_caso(int(selected_arch_id))
                st.toast("Restaurado ✅")
                st.rerun()

        if btn_excluir:
            if not selected_arch_id:
                st.warning("Selecione uma linha na tabela.")
            else:
                st.session_state["confirm_del_arch_one"] = int(selected_arch_id)

        if st.session_state.get("confirm_del_arch_one"):
            st.warning("Confirmar EXCLUIR? (não pode desfazer)")
            c1, c2 = st.columns([0.18, 0.18], gap="small")
            with c1:
                if st.button("✅", use_container_width=True, key="btn_del_arch_yes"):
                    delete_caso(int(st.session_state["confirm_del_arch_one"]))
                    st.session_state.pop("confirm_del_arch_one", None)
                    st.toast("Excluído ✅")
                    st.rerun()
            with c2:
                if st.button("❌", use_container_width=True, key="btn_del_arch_no"):
                    st.session_state.pop("confirm_del_arch_one", None)
