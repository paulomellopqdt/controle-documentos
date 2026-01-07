from __future__ import annotations

from datetime import date, datetime
import pandas as pd
import streamlit as st
from supabase import create_client, Client


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

/* Badge */
.badge{
  display:inline-flex; align-items:center; gap:8px;
  padding: 6px 10px; border-radius: 999px;
  font-size: 0.85rem; border:1px solid rgba(49,51,63,0.12);
}
.badge-warn{ background: rgba(234,179,8,0.14); color: #854d0e; }
.badge-ok{ background: rgba(34,197,94,0.12); color: #166534; }

/* Compact buttons row */
.btnrow button { width: 100%; }

/* subtle box spacing inside expanders */
.exp-inner { padding-top: 4px; }
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
        menu_options = [f"📋 {dash_title}", "📄 Documento", "🗄️ Arquivados"]
        page = st.radio("Menu", menu_options, index=0)

        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="btnrow">', unsafe_allow_html=True)
            if st.button("🔄 Atualizar", use_container_width=True):
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="btnrow">', unsafe_allow_html=True)
            if st.button("🚪 Sair", use_container_width=True):
                try:
                    get_supabase().auth.sign_out()
                except Exception:
                    pass
                st.session_state["sb_session"] = None
                st.session_state["sb_user"] = None
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        st.caption("v1.0 • Streamlit + Supabase")

    return page, dash_title


# =========================================================
# CRUD (SUPABASE)
# =========================================================
def fetch_casos() -> pd.DataFrame:
    res = _sb_table("casos").select("*").order("id", desc=True).execute()
    return pd.DataFrame(res.data or [])


def fetch_caso(caso_id: int) -> dict | None:
    res = _sb_table("casos").select("*").eq("id", int(caso_id)).limit(1).execute()
    data = res.data or []
    return data[0] if data else None


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


def fetch_retornos(caso_id: int) -> pd.DataFrame:
    res = _sb_table("retornos_om").select("*").eq("caso_id", int(caso_id)).order("om").execute()
    return pd.DataFrame(res.data or [])


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


def archive_caso(caso_id: int):
    user = st.session_state["sb_user"]
    payload = {"owner_id": user.id, "caso_id": int(caso_id), "archived_at": datetime.now().isoformat()}
    _sb_table("arquivados").upsert(payload, on_conflict="caso_id").execute()


def insert_documento_minimo(
    nr_doc_recebido: str,
    assunto_doc: str,
    origem: str | None,
    prazo_final: date | None,
    observacoes: str | None,
    assunto_solic: str | None,
    prazo_om: date | None,
    nr_doc_solicitado: str | None,
    nr_doc_resposta: str | None,
):
    """Insere um 'caso' completo (documento + opcional solicitação/resposta)."""
    user = st.session_state["sb_user"]

    # blindagem NOT NULL
    nr_doc_recebido = (nr_doc_recebido or "").strip() or "-"
    assunto_doc = (assunto_doc or "").strip() or "-"
    origem = (origem or "").strip() if origem and origem.strip() else "-"
    observacoes = (observacoes or "").strip() if observacoes and observacoes.strip() else "-"

    payload = {
        "owner_id": user.id,
        "nr_doc_recebido": nr_doc_recebido,
        "assunto_doc": assunto_doc,
        "origem": origem,
        "prazo_final": prazo_final.isoformat() if prazo_final else None,
        "observacoes": observacoes,
        "assunto_solic": (assunto_solic or "").strip() or None,
        "prazo_om": prazo_om.isoformat() if prazo_om else None,
        "nr_doc_solicitado": (nr_doc_solicitado or "").strip() or None,
        "nr_doc_resposta": (nr_doc_resposta or "").strip() or None,
        "status": "Recebido",
        "created_at": datetime.now().isoformat(),
        "resolved_at": date.today().isoformat() if (nr_doc_resposta or "").strip() else None,
    }
    if payload["nr_doc_resposta"]:
        payload["status"] = "Resolvido"

    res = _sb_table("casos").insert(payload).execute()
    return int(res.data[0]["id"]) if (res.data or []) else None


def update_caso_by_id(caso_id: int, payload: dict):
    """Update com blindagem NOT NULL (evita erro 23502)."""
    if "nr_doc_recebido" in payload and (payload["nr_doc_recebido"] is None or str(payload["nr_doc_recebido"]).strip() == ""):
        payload["nr_doc_recebido"] = "-"
    if "assunto_doc" in payload and (payload["assunto_doc"] is None or str(payload["assunto_doc"]).strip() == ""):
        payload["assunto_doc"] = "-"
    if "origem" in payload and (payload["origem"] is None or str(payload["origem"]).strip() == ""):
        payload["origem"] = "-"
    if "observacoes" in payload and (payload["observacoes"] is None or str(payload["observacoes"]).strip() == ""):
        payload["observacoes"] = "-"

    _sb_table("casos").update(payload).eq("id", int(caso_id)).execute()


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
    return True, "Responsáveis removidos ✅"


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


def _docbox_defaults():
    """Seta defaults ANTES dos widgets serem criados (evita StreamlitAPIException)."""
    st.session_state.setdefault("doc_sel_id", None)

    st.session_state.setdefault("doc_origem", "")
    st.session_state.setdefault("doc_nr_recebido", "")
    st.session_state.setdefault("doc_assunto_doc", "")
    st.session_state.setdefault("doc_prazo_final", None)
    st.session_state.setdefault("doc_observacoes", "")

    st.session_state.setdefault("doc_nr_solicitado", "")
    st.session_state.setdefault("doc_assunto_solic", "")
    st.session_state.setdefault("doc_prazo_om", None)

    st.session_state.setdefault("doc_nr_resposta", "")


def _docbox_apply_from_caso(caso: dict):
    """Atualiza valores da caixa Documento e dá rerun (atualização segura)."""
    if not caso:
        return

    st.session_state["doc_origem"] = (caso.get("origem") or "") if caso.get("origem") != "-" else ""
    st.session_state["doc_nr_recebido"] = (caso.get("nr_doc_recebido") or "") if caso.get("nr_doc_recebido") != "-" else ""
    st.session_state["doc_assunto_doc"] = (caso.get("assunto_doc") or "") if caso.get("assunto_doc") != "-" else ""

    st.session_state["doc_prazo_final"] = pd.to_datetime(caso["prazo_final"]).date() if caso.get("prazo_final") else None
    st.session_state["doc_observacoes"] = (caso.get("observacoes") or "") if caso.get("observacoes") != "-" else ""

    st.session_state["doc_nr_solicitado"] = (caso.get("nr_doc_solicitado") or "")
    st.session_state["doc_assunto_solic"] = (caso.get("assunto_solic") or "")
    st.session_state["doc_prazo_om"] = pd.to_datetime(caso["prazo_om"]).date() if caso.get("prazo_om") else None

    st.session_state["doc_nr_resposta"] = (caso.get("nr_doc_resposta") or "")


def _docbox_reset_values():
    """Pede reset via flag (não mexe em chave de widget no mesmo ciclo)."""
    st.session_state["docbox_reset_flag"] = True
    st.rerun()


def _apply_docbox_reset_if_needed():
    if st.session_state.get("docbox_reset_flag"):
        st.session_state.pop("docbox_reset_flag", None)
        # pode setar aqui com segurança, antes dos widgets
        st.session_state["doc_sel_id"] = None
        st.session_state["doc_origem"] = ""
        st.session_state["doc_nr_recebido"] = ""
        st.session_state["doc_assunto_doc"] = ""
        st.session_state["doc_prazo_final"] = None
        st.session_state["doc_observacoes"] = ""
        st.session_state["doc_nr_solicitado"] = ""
        st.session_state["doc_assunto_solic"] = ""
        st.session_state["doc_prazo_om"] = None
        st.session_state["doc_nr_resposta"] = ""


# =========================================================
# APP START
# =========================================================
require_auth()
page, dash_title = sidebar_layout()

_docbox_defaults()


# =========================================================
# PAGE: DASHBOARD
# =========================================================
if page == f"📋 {dash_title}":
    hoje = date.today()
    _apply_docbox_reset_if_needed()

    # data
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
    # DOCUMENTO BOX (compacto) - acima de Acompanhamento
    # =========================================================
    with st.expander("Documento", expanded=True):
        st.markdown('<div class="exp-inner"></div>', unsafe_allow_html=True)

        sel_id = st.session_state.get("doc_sel_id")

        top1, top2 = st.columns([1, 0.20], gap="small")
        with top1:
            if sel_id:
                st.markdown(f'<span class="badge badge-ok">🧾 Selecionado: ID {sel_id}</span>', unsafe_allow_html=True)
            else:
                st.markdown(f'<span class="badge badge-warn">🆕 Novo registro</span>', unsafe_allow_html=True)
        with top2:
            if st.button("🧹 Limpar", use_container_width=True, key="btn_docbox_clear"):
                _docbox_reset_values()

        r1, r2, r3, r4 = st.columns([0.8, 0.8, 1.2, 0.8], gap="small")
        with r1:
            st.text_input("Origem", key="doc_origem")
        with r2:
            st.text_input("Nr Doc (Recebido)", key="doc_nr_recebido")
        with r3:
            st.text_input("Assunto (Documento)", key="doc_assunto_doc")
        with r4:
            st.date_input("Prazo Final", key="doc_prazo_final", value=st.session_state.get("doc_prazo_final"), format="DD/MM/YYYY")

        r5, r6, r7, r8 = st.columns([0.9, 1.5, 0.9, 0.7], gap="small")
        with r5:
            st.text_input("Nr Doc (Solicitado)", key="doc_nr_solicitado")
        with r6:
            st.text_input("Assunto (Solicitação)", key="doc_assunto_solic")
        with r7:
            st.date_input("Prazo OM", key="doc_prazo_om", value=st.session_state.get("doc_prazo_om"), format="DD/MM/YYYY")
        with r8:
            st.text_input("Nr Doc (Resposta)", key="doc_nr_resposta")

        st.text_area("Observações", key="doc_observacoes", height=110)

        # botão único salvar
        b1, b2 = st.columns([0.75, 0.25], gap="small")
        with b2:
            if st.button("💾 Salvar", type="primary", use_container_width=True, key="btn_docbox_save"):
                st.session_state["confirm_save_docbox"] = True

        if st.session_state.get("confirm_save_docbox"):
            st.warning("Confirma salvar os dados do Documento?")
            c1, c2 = st.columns([0.25, 0.75], gap="small")
            with c1:
                if st.button("Confirmar", key="btn_confirm_save_docbox"):
                    try:
                        nr_rec = (st.session_state.get("doc_nr_recebido") or "").strip()
                        assunto_doc = (st.session_state.get("doc_assunto_doc") or "").strip()
                        origem = (st.session_state.get("doc_origem") or "").strip()
                        prazo_final = st.session_state.get("doc_prazo_final")
                        obs = (st.session_state.get("doc_observacoes") or "").strip()

                        nr_solic = (st.session_state.get("doc_nr_solicitado") or "").strip()
                        assunto_solic = (st.session_state.get("doc_assunto_solic") or "").strip()
                        prazo_om = st.session_state.get("doc_prazo_om")

                        nr_resp = (st.session_state.get("doc_nr_resposta") or "").strip()

                        # regra: se tudo vazio, não salva
                        if not any([nr_rec, assunto_doc, origem, obs, nr_solic, assunto_solic, nr_resp, prazo_final, prazo_om]):
                            st.error("Preencha pelo menos um campo para salvar.")
                            st.session_state.pop("confirm_save_docbox", None)
                            st.stop()

                        if sel_id:
                            payload = {
                                "origem": origem or "-",
                                "nr_doc_recebido": nr_rec or "-",
                                "assunto_doc": assunto_doc or "-",
                                "prazo_final": prazo_final.isoformat() if prazo_final else None,
                                "observacoes": obs or "-",
                                "nr_doc_solicitado": nr_solic or None,
                                "assunto_solic": assunto_solic or None,
                                "prazo_om": prazo_om.isoformat() if prazo_om else None,
                                "nr_doc_resposta": nr_resp or None,
                                "resolved_at": date.today().isoformat() if nr_resp else None,
                                "status": "Resolvido" if nr_resp else (None),
                            }
                            # se não tiver resposta, não força status (mantém o atual se já existir)
                            if payload["status"] is None:
                                payload.pop("status", None)

                            update_caso_by_id(sel_id, payload)
                            st.toast("Salvo ✅")
                        else:
                            # novo
                            new_id = insert_documento_minimo(
                                nr_doc_recebido=nr_rec,
                                assunto_doc=assunto_doc,
                                origem=origem or None,
                                prazo_final=prazo_final,
                                observacoes=obs or None,
                                assunto_solic=assunto_solic or None,
                                prazo_om=prazo_om,
                                nr_doc_solicitado=nr_solic or None,
                                nr_doc_resposta=nr_resp or None,
                            )
                            if new_id:
                                st.session_state["doc_sel_id"] = int(new_id)
                                st.toast(f"Criado ✅ (ID {new_id})")

                        st.session_state.pop("confirm_save_docbox", None)
                        st.rerun()

                    except Exception as e:
                        st.session_state.pop("confirm_save_docbox", None)
                        st.error(f"Erro ao salvar: {e}")

            with c2:
                if st.button("Cancelar", key="btn_cancel_save_docbox"):
                    st.session_state.pop("confirm_save_docbox", None)
                    st.info("Salvamento cancelado.")

    # =========================================================
    # ACOMPANHAMENTO (dentro de uma “caixa”)
    # =========================================================
    with st.expander("Acompanhamento", expanded=True):
        if df_acomp.empty:
            st.info("Nenhum item em acompanhamento.")
        else:
            pend_map = {int(r["caso_id"]): int(r["qtd"]) for _, r in pend.iterrows()} if not pend.empty else {}
            df_acomp["Pendências (Qtd)"] = df_acomp["id"].astype(int).map(lambda x: pend_map.get(int(x), 0))

            # ORDEM DAS COLUNAS (como você pediu)
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

            # botões compactos em cima
            a1, a2, a3 = st.columns([0.16, 0.16, 0.68], gap="small")
            with a1:
                if st.button("🗄️", help="Arquivar selecionado", use_container_width=True, key="btn_dash_archive_emoji"):
                    st.session_state["confirm_archive_dash"] = True
            with a2:
                if st.button("🔁", help="Recarregar", use_container_width=True, key="btn_dash_reload_emoji"):
                    st.rerun()
            with a3:
                st.markdown('<div class="small-muted">Selecione uma linha para carregar no Documento (acima).</div>', unsafe_allow_html=True)

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

            # ao selecionar: carregar no Documento
            if clicked_id is not None and clicked_id != st.session_state.get("doc_sel_id"):
                st.session_state["doc_sel_id"] = int(clicked_id)
                caso = fetch_caso(clicked_id) or {}
                _docbox_apply_from_caso(caso)
                st.rerun()

            # arquivar
            if st.session_state.get("confirm_archive_dash"):
                if not st.session_state.get("doc_sel_id"):
                    st.warning("Selecione uma linha para arquivar.")
                    st.session_state.pop("confirm_archive_dash", None)
                else:
                    st.warning(f"Confirma arquivar o ID {st.session_state['doc_sel_id']}?")
                    c1, c2 = st.columns([0.25, 0.75], gap="small")
                    with c1:
                        if st.button("Confirmar", key="btn_confirm_archive_dash"):
                            archive_caso(int(st.session_state["doc_sel_id"]))
                            st.session_state.pop("confirm_archive_dash", None)
                            _docbox_reset_values()
                    with c2:
                        if st.button("Cancelar", key="btn_cancel_archive_dash"):
                            st.session_state.pop("confirm_archive_dash", None)
                            st.info("Arquivamento cancelado.")

    # =========================================================
    # DETALHES + MENSAGEM + RESPONSÁVEL (para item selecionado)
    # =========================================================
    sel_id = st.session_state.get("doc_sel_id")
    if sel_id:
        caso = fetch_caso(sel_id) or {}
        ret = fetch_retornos(sel_id)

        with st.expander("Detalhes", expanded=False):
            cA, cB, cC = st.columns([1, 1, 1], gap="large")
            with cA:
                st.markdown("##### Documento")
                st.write("**Origem:**", (caso.get("origem") or "-"))
                st.write("**Nr:**", (caso.get("nr_doc_recebido") or "-"))
                st.write("**Assunto:**", (caso.get("assunto_doc") or "-"))
                st.write("**Prazo final:**", _fmt_date_iso_to_ddmmyyyy(caso.get("prazo_final")))
            with cB:
                st.markdown("##### Solicitação")
                st.write("**Nr solicitado:**", (caso.get("nr_doc_solicitado") or "-"))
                st.write("**Assunto:**", (caso.get("assunto_solic") or "-"))
                st.write("**Prazo OM:**", _fmt_date_iso_to_ddmmyyyy(caso.get("prazo_om")))
            with cC:
                st.markdown("##### Resposta")
                st.write("**Nr resposta:**", (caso.get("nr_doc_resposta") or "-"))
                st.write("**Status:**", (caso.get("status") or "-"))
                st.write("**Resolvido em:**", _fmt_date_iso_to_ddmmyyyy(caso.get("resolved_at")))

        with st.expander("Mensagem", expanded=False):
            msg_key = f"msg_edit_{sel_id}"
            st.session_state.setdefault(msg_key, build_msg_cobranca(caso, ret))
            st.text_area("Mensagem", key=msg_key, height=200, label_visibility="collapsed")

        # Responsável (retornos / pendências) editável na tabela
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

                orig_key = f"ret_original_snapshot_{sel_id}"
                if orig_key not in st.session_state:
                    st.session_state[orig_key] = _snapshot_from_editor(base_df)

                editor_key = f"ret_editor_{sel_id}"
                edited = st.data_editor(
                    base_df,
                    use_container_width=True,
                    hide_index=True,
                    key=editor_key,
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

                current_snap = _snapshot_from_editor(edited)
                dirty = current_snap != st.session_state.get(orig_key, [])

                # topo com badge + salvar
                a1, a2 = st.columns([0.7, 0.3], gap="small")
                with a1:
                    if dirty:
                        st.markdown('<span class="badge badge-warn">⚠️ Alterações pendentes</span>', unsafe_allow_html=True)
                    else:
                        st.markdown('<span class="badge badge-ok">✅ Tudo salvo</span>', unsafe_allow_html=True)
                with a2:
                    if dirty:
                        if st.button("Salvar", type="primary", key=f"btn_save_ret_{sel_id}", use_container_width=True):
                            st.session_state[f"confirm_save_ret_{sel_id}"] = True

                if st.session_state.get(f"confirm_save_ret_{sel_id}"):
                    st.warning("Confirma salvar as alterações em Responsável?")
                    cc1, cc2 = st.columns([0.25, 0.75], gap="small")
                    with cc1:
                        if st.button("Confirmar", key=f"btn_confirm_save_ret_{sel_id}"):
                            try:
                                for i, row in edited.reset_index(drop=True).iterrows():
                                    rid = retorno_ids[i]
                                    disp = (row.get("Status") or STATUS_DISPLAY["Pendente"]).strip()
                                    new_status = DISPLAY_TO_STATUS.get(disp, "Pendente")
                                    new_obs = (row.get("Obs") or "").strip() or None

                                    _sb_table("retornos_om").update(
                                        {"status": new_status, "observacoes": new_obs}
                                    ).eq("id", int(rid)).execute()

                                st.session_state[orig_key] = _snapshot_from_editor(edited)
                                st.session_state.pop(f"confirm_save_ret_{sel_id}", None)
                                st.toast("Alterações salvas ✅")
                                st.rerun()
                            except Exception as e:
                                st.session_state.pop(f"confirm_save_ret_{sel_id}", None)
                                st.error(f"Erro ao salvar responsáveis: {e}")
                    with cc2:
                        if st.button("Cancelar", key=f"btn_cancel_save_ret_{sel_id}"):
                            st.session_state.pop(f"confirm_save_ret_{sel_id}", None)
                            st.info("Salvamento cancelado.")


# =========================================================
# PAGE: DOCUMENTO (mantida como estava, opcional)
# =========================================================
elif page == "📄 Documento":
    st.title("📄 Documento")
    st.markdown('<div class="small-muted">Use o Dashboard para o fluxo principal. Esta aba pode ser usada como apoio.</div>', unsafe_allow_html=True)
    st.info("Se quiser, eu removo esta aba e deixo o app só com Dashboard + Arquivados.")


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
