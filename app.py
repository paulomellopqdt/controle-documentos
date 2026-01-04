from __future__ import annotations

from datetime import date, datetime
import pandas as pd
import streamlit as st
from supabase import create_client, Client


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
h1 span, h2 span, h3 span { display: inline-block; padding-top: 2px; }

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

/* Separador vertical no Documento */
.vline { height: 100%; border-left: 2px solid rgba(49,51,63,0.10); margin: 0 auto; }
</style>
""",
    unsafe_allow_html=True,
)


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
    """Garante que o client auth está com a sessão atual (pra update_user persistir)."""
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

                # carrega nome salvo do usuário
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
    # salva no Supabase Auth (persistente por usuário)
    save_dash_name_to_user(st.session_state.get("dash_name", "Dashboard"))


def sidebar_layout() -> tuple[str, str]:
    # garante que existe e vem do perfil
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
            if st.button("🔄 Atualizar"):
                st.rerun()
        with c2:
            if st.button("🚪 Sair"):
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
# CRUD (Supabase)
# =========================================================
def fetch_casos() -> pd.DataFrame:
    res = _sb_table("casos").select("*").order("id", desc=True).execute()
    return pd.DataFrame(res.data or [])


def fetch_caso(caso_id: int) -> dict | None:
    res = _sb_table("casos").select("*").eq("id", caso_id).limit(1).execute()
    data = res.data or []
    return data[0] if data else None


def fetch_caso_by_nr_recebido(nr_doc_recebido: str) -> dict | None:
    nr = (nr_doc_recebido or "").strip()
    if not nr:
        return None
    res = _sb_table("casos").select("*").eq("nr_doc_recebido", nr).order("id", desc=True).limit(1).execute()
    data = res.data or []
    return data[0] if data else None


def update_documento_by_nr_recebido(
    nr_doc_recebido: str,
    assunto_doc: str,
    origem: str | None,
    prazo_final: date | None,
    obs: str | None,
):
    payload = {
        "assunto_doc": (assunto_doc or "").strip(),
        "origem": (origem or "").strip() if origem and origem.strip() else None,
        "prazo_final": prazo_final.isoformat() if prazo_final else None,
        "observacoes": (obs or "").strip() if obs and obs.strip() else None,
    }
    _sb_table("casos").update(payload).eq("nr_doc_recebido", (nr_doc_recebido or "").strip()).execute()


def insert_documento(nr_doc: str, assunto_doc: str, origem: str | None, prazo_final: date | None, obs: str | None):
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
    _sb_table("casos").insert(payload).execute()


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
    res = _sb_table("retornos_om").select("*").eq("caso_id", caso_id).order("om").execute()
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
    _sb_table("casos").update(payload).eq("id", caso_id).execute()


def archive_caso(caso_id: int):
    user = st.session_state["sb_user"]
    payload = {"owner_id": user.id, "caso_id": caso_id, "archived_at": datetime.now().isoformat()}
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
    _sb_table("casos").update(payload).eq("id", caso_id).execute()

    ret = fetch_retornos(caso_id)
    existentes = set(ret["om"].tolist()) if not ret.empty else set()
    selecionadas_set = set(selecionadas)

    for om in list(existentes - selecionadas_set):
        _sb_table("retornos_om").delete().eq("caso_id", caso_id).eq("om", om).execute()

    user = st.session_state["sb_user"]

    for om in list(existentes & selecionadas_set):
        _sb_table("retornos_om").update({"prazo_om": prazo_om.isoformat() if prazo_om else None}).eq("caso_id", caso_id).eq("om", om).execute()

    for om in list(selecionadas_set - existentes):
        _sb_table("retornos_om").insert(
            {
                "owner_id": user.id,
                "caso_id": caso_id,
                "om": om,
                "status": "Pendente",
                "prazo_om": prazo_om.isoformat() if prazo_om else None,
                "dt_resposta": None,
                "observacoes": None,
            }
        ).execute()


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


def _parse_caso_id_from_label(label: str) -> int | None:
    if "(ID " not in label:
        return None
    try:
        return int(label.split("(ID ")[1].split(")")[0])
    except Exception:
        return None


def _clear_forms(keep_doc_select: bool = False):
    st.session_state["selected_doc_id"] = None
    st.session_state["doc_disabled"] = False

    st.session_state["doc_nr"] = ""
    st.session_state["doc_assunto_doc"] = ""
    st.session_state["doc_origem"] = ""
    st.session_state["doc_prazo_final"] = None
    st.session_state["doc_obs"] = ""

    st.session_state["sol_assunto_solic"] = ""
    st.session_state["sol_prazo_om"] = None
    st.session_state["sol_doc_solicitado"] = ""
    st.session_state["sol_responsaveis"] = []
    st.session_state["nr_doc_resposta_input"] = ""

    if not keep_doc_select:
        st.session_state["sol_doc_select"] = "00 | Nova Solicitação sem Documento"


def _load_selected_document_into_forms():
    label = st.session_state.get("sol_doc_select", "00 | Nova Solicitação sem Documento")
    if label.startswith("00 | Nova"):
        _clear_forms(keep_doc_select=True)
        return

    caso_id = _parse_caso_id_from_label(label)
    if not caso_id:
        _clear_forms(keep_doc_select=True)
        return

    caso = fetch_caso(caso_id)
    if not caso:
        _clear_forms(keep_doc_select=True)
        return

    st.session_state["selected_doc_id"] = caso_id

    is_sem_doc = (caso.get("nr_doc_recebido") == "-" or caso.get("assunto_doc") == "-")
    st.session_state["doc_disabled"] = bool(is_sem_doc)

    st.session_state["doc_nr"] = caso.get("nr_doc_recebido") or ""
    st.session_state["doc_assunto_doc"] = caso.get("assunto_doc") or ""
    st.session_state["doc_origem"] = caso.get("origem") or ""
    st.session_state["doc_prazo_final"] = pd.to_datetime(caso["prazo_final"]).date() if caso.get("prazo_final") else None
    st.session_state["doc_obs"] = caso.get("observacoes") or ""

    st.session_state["sol_assunto_solic"] = caso.get("assunto_solic") or ""
    st.session_state["sol_prazo_om"] = pd.to_datetime(caso["prazo_om"]).date() if caso.get("prazo_om") else None
    st.session_state["sol_doc_solicitado"] = caso.get("nr_doc_solicitado") or ""


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


# =========================================================
# APP START
# =========================================================
require_auth()
page, dash_title = sidebar_layout()

st.session_state.setdefault("sol_responsaveis", [])
st.session_state.setdefault("doc_disabled", False)
st.session_state.setdefault("sol_doc_select", "00 | Nova Solicitação sem Documento")


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

    f1, f2, f3 = st.columns([1.2, 0.9, 0.9])
    with f1:
        q = st.text_input("🔎 Buscar", placeholder="Nr / assunto / origem / solicitação...")
    with f2:
        status_filter = st.selectbox("Status", ["Todos", "Pendente", "Distribuído", "Recebido", "Resolvido"])
    with f3:
        only_pend = st.toggle("Somente com pendências", value=False)

    if df_acomp.empty:
        st.info("Nenhum item em acompanhamento.")
    else:
        pend_map = {int(r["caso_id"]): int(r["qtd"]) for _, r in pend.iterrows()} if not pend.empty else {}
        df_acomp["Pendências (Qtd)"] = df_acomp["id"].astype(int).map(lambda x: pend_map.get(int(x), 0))

        df_show = pd.DataFrame(
            {
                "id": df_acomp["id"],
                "Nr Doc (Recebido)": df_acomp["nr_doc_recebido"].fillna("-"),
                "Assunto (Documento)": df_acomp["assunto_doc"].fillna("-"),
                "Assunto (Solicitação)": df_acomp.get("assunto_solic").fillna("-"),
                "Origem": df_acomp.get("origem").fillna("-"),
                "Prazo Final": pd.to_datetime(df_acomp.get("prazo_final"), errors="coerce").dt.strftime("%d/%m/%Y").fillna("-"),
                "Prazo OM": pd.to_datetime(df_acomp.get("prazo_om"), errors="coerce").dt.strftime("%d/%m/%Y").fillna("-"),
                "Nr Doc (Solicitado)": df_acomp.get("nr_doc_solicitado").fillna("-"),
                "Nr Doc (Resposta)": df_acomp.get("nr_doc_resposta").fillna("-"),
                "Status": df_acomp.get("status").fillna("-"),
                "Pendências (Qtd)": df_acomp["Pendências (Qtd)"],
            }
        )

        if status_filter != "Todos":
            df_show = df_show[df_show["Status"].astype(str).str.lower() == status_filter.lower()]
        if only_pend:
            df_show = df_show[df_show["Pendências (Qtd)"] > 0]
        if q and not df_show.empty:
            ql = q.lower().strip()
            df_show = df_show[df_show.apply(lambda r: ql in " ".join(map(str, r.values)).lower(), axis=1)]

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

        selected_id = None
        if sel and sel.get("selection", {}).get("rows"):
            idx = sel["selection"]["rows"][0]
            selected_id = int(df_show.iloc[idx]["id"])

        if btn_arquivar and selected_id:
            archive_caso(selected_id)
            st.toast("Arquivado ✅")
            st.rerun()
        elif btn_arquivar and not selected_id:
            st.warning("Selecione uma linha na tabela.")

        if selected_id:
            caso = fetch_caso(selected_id) or {}
            ret = fetch_retornos(selected_id)

            with st.expander("Detalhes", expanded=True):
                cA, cB, cC = st.columns([1, 1, 1], gap="large")
                with cA:
                    st.markdown("##### Documento")
                    st.write("**Nr:**", caso.get("nr_doc_recebido") or "-")
                    st.write("**Assunto:**", caso.get("assunto_doc") or "-")
                    st.write("**Origem:**", caso.get("origem") or "-")
                    st.write("**Prazo final:**", _fmt_date_iso_to_ddmmyyyy(caso.get("prazo_final")))
                with cB:
                    st.markdown("##### Solicitação")
                    st.write("**Assunto:**", caso.get("assunto_solic") or "-")
                    st.write("**Nr solicitado:**", caso.get("nr_doc_solicitado") or "-")
                    st.write("**Prazo OM:**", _fmt_date_iso_to_ddmmyyyy(caso.get("prazo_om")))
                with cC:
                    st.markdown("##### Resposta")
                    st.write("**Nr resposta:**", caso.get("nr_doc_resposta") or "-")
                    st.write("**Resolvido em:**", _fmt_date_iso_to_ddmmyyyy(caso.get("resolved_at")))
                    nr_input = st.text_input("Atualizar Nr Resposta", value="", key="dash_nr_resp")
                    if st.button("Salvar resposta", key="dash_salvar_resp", type="primary"):
                        set_resposta_e_status(selected_id, nr_input.strip())
                        st.toast("Atualizado ✅")
                        st.rerun()

            with st.expander("Mensagem", expanded=False):
                msg_key = f"msg_edit_{selected_id}"
                st.session_state.setdefault(msg_key, build_msg_cobranca(caso, ret))
                st.text_area("Mensagem", key=msg_key, height=200, label_visibility="collapsed")

            # =========================================================
            # ✅ Retorno / Pendências (EDITÁVEL na própria tabela)
            # - SEM coluna separada
            # - Status com bolinha no próprio campo
            # - Status e Obs editáveis
            # - tudo centralizado (CSS global acima)
            # =========================================================
            st.markdown("##### Retorno / Pendências")

            if ret.empty:
                st.info("Sem responsáveis cadastrados.")
            else:
                ret = ret.sort_values("om").reset_index(drop=True)
                retorno_ids = ret["id"].astype(int).tolist()

                # Status exibido com emoji no próprio texto
                def to_display_status(s: str) -> str:
                    s0 = (s or "Pendente").strip().title()
                    if s0 not in STATUS_DISPLAY:
                        s0 = "Pendente"
                    return STATUS_DISPLAY[s0]

                edit_df = pd.DataFrame(
                    {
                        "Responsável": ret["om"].fillna("").astype(str),
                        "Status": ret["status"].fillna("Pendente").astype(str).apply(to_display_status),
                        "Obs": ret["observacoes"].fillna("").astype(str),
                    }
                )

                editor_key = f"ret_editor_{selected_id}"
                edited = st.data_editor(
                    edit_df,
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

                c1, c2 = st.columns([0.22, 0.78])
                with c1:
                    if st.button("Salvar alterações", type="primary", key=f"btn_save_ret_{selected_id}"):
                        st.session_state[f"confirm_save_ret_{selected_id}"] = True

                if st.session_state.get(f"confirm_save_ret_{selected_id}"):
                    st.warning("Confirma salvar as alterações em Retorno / Pendências?")
                    cc1, cc2 = st.columns([0.22, 0.78])
                    with cc1:
                        if st.button("Confirmar", key=f"btn_confirm_save_ret_{selected_id}"):
                            for i, row in edited.reset_index(drop=True).iterrows():
                                rid = retorno_ids[i]
                                disp = (row.get("Status") or STATUS_DISPLAY["Pendente"]).strip()
                                new_status = DISPLAY_TO_STATUS.get(disp, "Pendente")
                                new_obs = (row.get("Obs") or "").strip() or None

                                _sb_table("retornos_om").update(
                                    {"status": new_status, "observacoes": new_obs}
                                ).eq("id", int(rid)).execute()

                            st.session_state.pop(f"confirm_save_ret_{selected_id}", None)
                            st.toast("Alterações salvas ✅")
                            st.rerun()
                    with cc2:
                        if st.button("Cancelar", key=f"btn_cancel_save_ret_{selected_id}"):
                            st.session_state.pop(f"confirm_save_ret_{selected_id}", None)
                            st.info("Salvamento cancelado.")


# =========================================================
# PAGE: DOCUMENTO
# =========================================================
elif page == "📄 Documento":
    dias = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
    hoje = date.today()

    headerL, headerR = st.columns([4, 1])
    with headerL:
        st.title("📄 Documento & Solicitação")
        st.markdown('<div class="small-muted">Cadastro e distribuição para responsáveis</div>', unsafe_allow_html=True)
    with headerR:
        st.markdown(
            f"<div style='text-align:right'><b>{dias[hoje.weekday()]}</b><br>{hoje.strftime('%d/%m/%Y')}</div>",
            unsafe_allow_html=True,
        )

    st.divider()
    col_doc, col_sep, col_sol = st.columns([1, 0.06, 1], gap="large")

    with col_sep:
        st.markdown('<div class="vline"></div>', unsafe_allow_html=True)

    # ---- Cadastrar Documento ----
    with col_doc:
        st.subheader("Cadastrar Documento")
        doc_disabled = bool(st.session_state.get("doc_disabled", False))

        r1c1, r1c2 = st.columns(2, gap="small")
        with r1c1:
            st.text_input("Nº do Documento (Recebido)", key="doc_nr", disabled=doc_disabled)
        with r1c2:
            st.text_input("Assunto do Documento", key="doc_assunto_doc", disabled=doc_disabled)

        r2c1, r2c2 = st.columns(2, gap="small")
        with r2c1:
            st.text_input("Origem (opcional)", key="doc_origem", disabled=doc_disabled)
        with r2c2:
            st.date_input("Prazo Final", key="doc_prazo_final", value=None, disabled=doc_disabled, format="DD/MM/YYYY")

        st.text_area("Observações", key="doc_obs", height=220, disabled=doc_disabled)

        if st.button("Salvar Documento", type="primary", key="btn_salvar_doc_novo", disabled=doc_disabled):
            nr_doc_in = (st.session_state.get("doc_nr") or "").strip()
            assunto_doc = (st.session_state.get("doc_assunto_doc") or "").strip()

            if not nr_doc_in or not assunto_doc:
                st.error("Informe o Nº do Documento (Recebido) e o Assunto do Documento.")
            else:
                existente = fetch_caso_by_nr_recebido(nr_doc_in)
                st.session_state["confirm_doc_action"] = {
                    "mode": "update" if existente else "insert",
                    "nr": nr_doc_in,
                    "assunto_doc": assunto_doc,
                    "origem": st.session_state.get("doc_origem") or "",
                    "prazo_final": st.session_state.get("doc_prazo_final"),
                    "obs": st.session_state.get("doc_obs") or "",
                }

        if st.session_state.get("confirm_doc_action"):
            payload = st.session_state["confirm_doc_action"]
            st.warning("Confirma **SALVAR**? (Atualiza se já existir.)")
            cx1, cx2 = st.columns([0.3, 0.3], gap="small")
            with cx1:
                if st.button("Confirmar", type="primary", key="btn_confirm_doc"):
                    try:
                        if payload.get("mode") == "update":
                            update_documento_by_nr_recebido(
                                nr_doc_recebido=payload["nr"],
                                assunto_doc=payload["assunto_doc"],
                                origem=payload["origem"],
                                prazo_final=payload["prazo_final"],
                                obs=payload["obs"],
                            )
                            st.toast("Documento atualizado ✅")
                        else:
                            insert_documento(
                                nr_doc=payload["nr"],
                                assunto_doc=payload["assunto_doc"],
                                origem=payload["origem"],
                                prazo_final=payload["prazo_final"],
                                obs=payload["obs"],
                            )
                            st.toast("Documento salvo ✅")

                        st.session_state.pop("confirm_doc_action", None)
                        _clear_forms()
                        st.success("Operação concluída ✅")
                        st.rerun()
                    except Exception as e:
                        st.session_state.pop("confirm_doc_action", None)
                        st.error(f"Erro ao salvar documento: {e}")
            with cx2:
                if st.button("Cancelar", key="btn_cancel_doc"):
                    st.session_state.pop("confirm_doc_action", None)
                    st.info("Ação cancelada. (Campos mantidos)")

    # ---- Solicitação ----
    with col_sol:
        st.subheader("Cadastrar / Atualizar Solicitação")

        df_all = fetch_casos()
        arquivados_ids = fetch_arquivados_ids()
        if not df_all.empty:
            df_all = df_all[~df_all["id"].astype(int).isin(arquivados_ids)]

        options = ["00 | Nova Solicitação sem Documento"]
        if not df_all.empty:
            for _, r in df_all.iterrows():
                nr_rec = (r.get("nr_doc_recebido") or "").strip()
                assunto_doc = (r.get("assunto_doc") or "").strip()
                assunto_solic = (r.get("assunto_solic") or "").strip()
                nr_solic = (r.get("nr_doc_solicitado") or "").strip()

                if nr_rec == "-" or assunto_doc == "-":
                    label = f"{assunto_solic} | {nr_solic or '00'} (ID {r['id']})"
                else:
                    label = f"{nr_rec} | {assunto_doc} (ID {r['id']})"
                options.append(label)

        if st.session_state.get("sol_doc_select") not in options:
            st.session_state["sol_doc_select"] = options[0]

        st.selectbox("Documento", options, key="sol_doc_select", on_change=_load_selected_document_into_forms)

        st.text_input("Assunto da Solicitação", key="sol_assunto_solic")

        cS1, cS2 = st.columns([1, 1], gap="small")
        with cS1:
            st.date_input("Prazo das OM", key="sol_prazo_om", value=None, format="DD/MM/YYYY")
        with cS2:
            st.text_input("Nr do documento (Solicitado)", key="sol_doc_solicitado")

        st.markdown("### Responsáveis")
        with st.expander("Gerenciar responsáveis", expanded=False):
            c_add1, c_add2 = st.columns([1, 0.25], gap="small")
            with c_add1:
                novo_nome = st.text_input("Adicionar novo responsável", key="resp_add_text")
            with c_add2:
                if st.button("Adicionar", key="resp_add_btn", type="primary", use_container_width=True):
                    ok, msg = add_master_om(novo_nome)
                    if ok:
                        st.toast("Responsável adicionado ✅")
                        st.session_state["resp_add_text"] = ""
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

            st.markdown("---")
            lista_atual = get_master_oms()
            remover = st.multiselect("Remover responsáveis do sistema", options=lista_atual, key="resp_del_ms")
            if st.button("Remover selecionados", key="resp_del_btn", use_container_width=True):
                ok, msg = delete_master_oms(remover)
                if ok:
                    st.toast("Responsáveis removidos ✅")
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

        oms = get_master_oms()
        bar1, bar2, bar3 = st.columns([0.20, 1, 0.30], gap="small")

        with bar1:
            st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
            if st.button("Circular", key="resp_circular", disabled=(not oms), use_container_width=True):
                st.session_state["sol_responsaveis"] = oms[:]
                st.rerun()

        with bar2:
            st.multiselect(
                "Responsáveis",
                options=oms,
                key="sol_responsaveis",
                help="Digite para buscar. Você pode selecionar vários.",
                label_visibility="collapsed",
            )

        with bar3:
            st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
            btn_salvar_solic = st.button("Salvar Solicitação", type="primary", key="btn_salvar_solic", use_container_width=True)

        if btn_salvar_solic:
            assunto_solic = (st.session_state.get("sol_assunto_solic") or "").strip()
            selecionadas = st.session_state.get("sol_responsaveis", []) or []
            nr_doc_solicitado = (st.session_state.get("sol_doc_solicitado") or "").strip() or "00"

            if not assunto_solic:
                st.error("Informe o Assunto da Solicitação.")
            elif not selecionadas:
                st.error("Selecione ao menos 1 Responsável.")
            else:
                st.session_state["confirm_solic_action"] = {
                    "assunto_solic": assunto_solic,
                    "prazo_om": st.session_state.get("sol_prazo_om"),
                    "selecionadas": selecionadas,
                    "nr_doc_solicitado": nr_doc_solicitado,
                    "selected_label": st.session_state.get("sol_doc_select"),
                    "selected_doc_id": st.session_state.get("selected_doc_id"),
                }

        if st.session_state.get("confirm_solic_action"):
            st.warning("Confirma **SALVAR** esta Solicitação?")
            cx1, cx2 = st.columns([0.3, 0.3], gap="small")
            with cx1:
                if st.button("Confirmar", type="primary", key="btn_confirm_solic"):
                    payload = st.session_state["confirm_solic_action"]
                    selected_label = payload["selected_label"] or "00 | Nova Solicitação sem Documento"
                    sel_id = payload["selected_doc_id"]

                    if selected_label.startswith("00 | Nova") or sel_id is None:
                        sel_id = insert_solicitacao_sem_documento(
                            assunto_solic=payload["assunto_solic"],
                            prazo_om=payload["prazo_om"],
                            nr_doc_solicitado=payload["nr_doc_solicitado"],
                        )
                        st.session_state["selected_doc_id"] = sel_id
                        st.session_state["sol_doc_select"] = f"{payload['assunto_solic']} | {payload['nr_doc_solicitado']} (ID {sel_id})"

                    salvar_ou_atualizar_solicitacao(
                        caso_id=sel_id,
                        assunto_solic=payload["assunto_solic"],
                        prazo_om=payload["prazo_om"],
                        selecionadas=payload["selecionadas"],
                        nr_doc_solicitado=payload["nr_doc_solicitado"],
                    )

                    st.session_state.pop("confirm_solic_action", None)
                    st.toast("Solicitação salva ✅")
                    _clear_forms()
                    st.rerun()

            with cx2:
                if st.button("Cancelar", key="btn_cancel_solic"):
                    st.session_state.pop("confirm_solic_action", None)
                    st.info("Ação cancelada.")


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
