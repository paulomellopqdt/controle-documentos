from __future__ import annotations

from datetime import date, datetime
import pandas as pd
import streamlit as st
from supabase import create_client, Client

RETORNO_STATUS = ["Pendente", "Respondido"]


# =========================================================
# CONFIG / THEME
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

/* ---------- Data editors ---------- */
div[data-testid="stDataEditor"]{
  border: 1px solid rgba(49,51,63,0.10);
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 6px 22px rgba(15, 23, 42, 0.04);
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
                get_supabase().auth.sign_up({"email": email, "password": password})
                st.success("Conta criada. Agora faça login na aba 'Entrar'.")
            except Exception:
                st.error("Não foi possível criar a conta. Tente outro email ou uma senha mais forte.")

    st.stop()


def sidebar_layout() -> tuple[str, str]:
    st.session_state.setdefault("dash_name", "Dashboard")

    with st.sidebar:
        st.markdown("## 📊 Controle de Documentos")
        st.markdown('<div class="small-muted">Dashboard operacional</div>', unsafe_allow_html=True)

        user = st.session_state.get("sb_user")
        if user:
            st.markdown(f"**👤 {user.email}**")

        st.markdown("---")
        st.text_input("Nome", key="dash_name", help="Este nome aparecerá no menu e no título principal.")
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
# Helpers
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


def indicador_status(status: str | None) -> str:
    s = (status or "").strip().lower()
    if s == "respondido":
        return "🟢 Respondido"
    return "🔴 Pendente"


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
# CRUD (Supabase)
# =========================================================
def fetch_casos() -> pd.DataFrame:
    res = _sb_table("casos").select("*").order("id", desc=True).execute()
    return pd.DataFrame(res.data or [])


def fetch_caso(caso_id: int) -> dict | None:
    res = _sb_table("casos").select("*").eq("id", caso_id).limit(1).execute()
    data = res.data or []
    return data[0] if data else None


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


def update_caso_fields(caso_id: int, payload: dict):
    _sb_table("casos").update(payload).eq("id", caso_id).execute()


def update_retorno_fields(retorno_id: int, payload: dict):
    _sb_table("retornos_om").update(payload).eq("id", retorno_id).execute()


def archive_caso(caso_id: int):
    user = st.session_state["sb_user"]
    payload = {"owner_id": user.id, "caso_id": caso_id, "archived_at": datetime.now().isoformat()}
    _sb_table("arquivados").upsert(payload, on_conflict="caso_id").execute()


def unarchive_caso(caso_id: int):
    _sb_table("arquivados").delete().eq("caso_id", caso_id).execute()


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


# =========================================================
# APP START
# =========================================================
require_auth()
page, dash_title = sidebar_layout()


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
                "ID": df_acomp["id"].astype(int),
                "Nr Doc (Recebido)": df_acomp["nr_doc_recebido"].fillna("-"),
                "Assunto (Documento)": df_acomp["assunto_doc"].fillna("-"),
                "Assunto (Solicitação)": df_acomp.get("assunto_solic").fillna("-"),
                "Origem": df_acomp.get("origem").fillna("-"),
                "Prazo Final": pd.to_datetime(df_acomp.get("prazo_final"), errors="coerce").dt.strftime("%d/%m/%Y").fillna("-"),
                "Prazo OM": pd.to_datetime(df_acomp.get("prazo_om"), errors="coerce").dt.strftime("%d/%m/%Y").fillna("-"),
                "Nr Doc (Solicitado)": df_acomp.get("nr_doc_solicitado").fillna("-"),
                "Nr Doc (Resposta)": df_acomp.get("nr_doc_resposta").fillna(""),
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
            st.subheader("Acompanhamento (editável)")
        with topR:
            st.markdown("<div style='padding-top:6px'></div>", unsafe_allow_html=True)
            btn_arquivar = st.button("🗄️ Arquivar selecionado", type="primary", key="dash_btn_arquivar")

        # ---------------------------
        # EDITOR: Acompanhamento
        # ---------------------------
        st.session_state.setdefault("acomp_editor_df", df_show.copy())

        # sempre sincroniza com o que está vindo do banco (evita “editor travado”)
        st.session_state["acomp_editor_df"] = df_show.copy()

        edited_acomp = st.data_editor(
            st.session_state["acomp_editor_df"],
            use_container_width=True,
            hide_index=True,
            column_config={
                "ID": st.column_config.NumberColumn("ID", disabled=True),
                "Nr Doc (Resposta)": st.column_config.TextColumn("Nr Doc (Resposta)", help="Edite e salve para atualizar no banco."),
                "Status": st.column_config.SelectboxColumn("Status", options=["Pendente", "Distribuído", "Recebido", "Resolvido"]),
            },
            disabled=[
                "Nr Doc (Recebido)",
                "Assunto (Documento)",
                "Assunto (Solicitação)",
                "Origem",
                "Prazo Final",
                "Prazo OM",
                "Nr Doc (Solicitado)",
                "Pendências (Qtd)",
            ],
            key="acomp_data_editor",
        )

        # seleção do editor (Streamlit ainda não expõe seleção do data_editor)
        # então: arquivar via campo de ID.
        arch_col1, arch_col2 = st.columns([0.35, 0.65])
        with arch_col1:
            id_para_arquivar = st.number_input("ID para arquivar", min_value=0, value=0, step=1)
        with arch_col2:
            st.markdown("<div class='small-muted'>Dica: o ID está na primeira coluna da tabela.</div>", unsafe_allow_html=True)

        if btn_arquivar:
            if not id_para_arquivar:
                st.warning("Informe um ID válido para arquivar.")
            else:
                archive_caso(int(id_para_arquivar))
                st.toast("Arquivado ✅")
                st.rerun()

        # salvar alterações (com confirmação)
        btn_save_acomp = st.button("Salvar alterações do Acompanhamento", type="primary", key="btn_save_acomp")
        if btn_save_acomp:
            st.session_state["confirm_save_acomp"] = True
            st.session_state["acomp_pending_df"] = edited_acomp.copy()

        if st.session_state.get("confirm_save_acomp"):
            st.warning("Confirma salvar as alterações do Acompanhamento?")
            c1, c2 = st.columns([0.2, 0.2])
            with c1:
                if st.button("Confirmar", type="primary", key="confirm_save_acomp_yes"):
                    pending = st.session_state.get("acomp_pending_df")
                    if pending is not None and not pending.empty:
                        # compara com df_show original (antes de editar)
                        base = df_show.set_index("ID")
                        pend = pending.set_index("ID")
                        changed_ids = sorted(list(set(pend.index) & set(base.index)))

                        for cid in changed_ids:
                            row_new = pend.loc[cid]
                            row_old = base.loc[cid]

                            payload = {}
                            if str(row_new.get("Status", "")).strip() != str(row_old.get("Status", "")).strip():
                                payload["status"] = str(row_new.get("Status", "")).strip() or None

                            # nr_doc_resposta
                            new_nr = str(row_new.get("Nr Doc (Resposta)", "")).strip()
                            old_nr = str(row_old.get("Nr Doc (Resposta)", "")).strip()
                            if new_nr != old_nr:
                                payload["nr_doc_resposta"] = new_nr if new_nr else None
                                # regra simples: se preencher nr resposta, marca como Resolvido
                                if new_nr:
                                    payload["status"] = "Resolvido"
                                    payload["resolved_at"] = date.today().isoformat()
                                else:
                                    payload["resolved_at"] = None

                            if payload:
                                update_caso_fields(int(cid), payload)

                    st.session_state.pop("confirm_save_acomp", None)
                    st.session_state.pop("acomp_pending_df", None)
                    st.toast("Alterações salvas ✅")
                    st.rerun()
            with c2:
                if st.button("Cancelar", key="confirm_save_acomp_no"):
                    st.session_state.pop("confirm_save_acomp", None)
                    st.session_state.pop("acomp_pending_df", None)
                    st.info("Ação cancelada.")

        st.divider()

        # ---------------------------
        # Detalhes + Mensagem + Retornos
        # (pega um ID manual para detalhar)
        # ---------------------------
        detail_id = st.number_input("ID para ver Detalhes/Mensagem/Retornos", min_value=0, value=0, step=1, key="detail_id")
        if detail_id:
            caso = fetch_caso(int(detail_id)) or {}
            ret = fetch_retornos(int(detail_id))

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

            with st.expander("Mensagem", expanded=False):
                msg_key = f"msg_edit_{detail_id}"
                st.session_state.setdefault(msg_key, build_msg_cobranca(caso, ret))
                st.text_area("Mensagem", key=msg_key, height=220, label_visibility="collapsed")

            st.markdown("##### Retorno / Pendências (editável)")
            if ret.empty:
                st.info("Sem responsáveis cadastrados.")
            else:
                # editor único: ID oculto (coluna existe, mas escondemos no UI com disabled e label curto)
                ret_editor = pd.DataFrame(
                    {
                        "retorno_id": ret["id"].astype(int),
                        "Indicador": [indicador_status(x) for x in ret["status"].fillna("Pendente").tolist()],
                        "Responsável": ret["om"].fillna("").astype(str),
                        "Status": ret["status"].fillna("Pendente").astype(str).str.title(),
                        "Obs": ret["observacoes"].fillna("").astype(str),
                    }
                )

                edited_ret = st.data_editor(
                    ret_editor,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "retorno_id": st.column_config.NumberColumn("ID", disabled=True, width="small"),
                        "Indicador": st.column_config.TextColumn(" ", disabled=True, width="small"),
                        "Responsável": st.column_config.TextColumn("Responsável", disabled=True),
                        "Status": st.column_config.SelectboxColumn("Status", options=RETORNO_STATUS),
                        "Obs": st.column_config.TextColumn("Obs"),
                    },
                    disabled=["retorno_id", "Indicador", "Responsável"],
                    key=f"ret_editor_{detail_id}",
                )

                btn_save_ret = st.button("Salvar alterações de Retornos", type="primary", key=f"btn_save_ret_{detail_id}")
                if btn_save_ret:
                    st.session_state[f"confirm_save_ret_{detail_id}"] = True
                    st.session_state[f"ret_pending_{detail_id}"] = edited_ret.copy()

                if st.session_state.get(f"confirm_save_ret_{detail_id}"):
                    st.warning("Confirma salvar as alterações de Retornos/Pendências?")
                    c1, c2 = st.columns([0.2, 0.2])
                    with c1:
                        if st.button("Confirmar", type="primary", key=f"confirm_save_ret_yes_{detail_id}"):
                            pending = st.session_state.get(f"ret_pending_{detail_id}")
                            if pending is not None and not pending.empty:
                                base = ret_editor.set_index("retorno_id")
                                pendx = pending.set_index("retorno_id")

                                ids = sorted(list(set(pendx.index) & set(base.index)))
                                for rid in ids:
                                    new = pendx.loc[rid]
                                    old = base.loc[rid]

                                    payload = {}
                                    if str(new.get("Status", "")).strip().lower() != str(old.get("Status", "")).strip().lower():
                                        payload["status"] = str(new.get("Status", "")).strip().title()

                                    new_obs = str(new.get("Obs", "")).strip()
                                    old_obs = str(old.get("Obs", "")).strip()
                                    if new_obs != old_obs:
                                        payload["observacoes"] = new_obs if new_obs else None

                                    if payload:
                                        update_retorno_fields(int(rid), payload)

                            st.session_state.pop(f"confirm_save_ret_{detail_id}", None)
                            st.session_state.pop(f"ret_pending_{detail_id}", None)
                            st.toast("Retornos atualizados ✅")
                            st.rerun()
                    with c2:
                        if st.button("Cancelar", key=f"confirm_save_ret_no_{detail_id}"):
                            st.session_state.pop(f"confirm_save_ret_{detail_id}", None)
                            st.session_state.pop(f"ret_pending_{detail_id}", None)
                            st.info("Ação cancelada.")


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

    with col_doc:
        st.subheader("Cadastrar Documento")
        r1c1, r1c2 = st.columns(2, gap="small")
        with r1c1:
            doc_nr = st.text_input("Nº do Documento (Recebido)", key="doc_nr")
        with r1c2:
            doc_assunto = st.text_input("Assunto do Documento", key="doc_assunto_doc")

        r2c1, r2c2 = st.columns(2, gap="small")
        with r2c1:
            doc_origem = st.text_input("Origem (opcional)", key="doc_origem")
        with r2c2:
            doc_prazo = st.date_input("Prazo Final", key="doc_prazo_final", value=None, format="DD/MM/YYYY")

        doc_obs = st.text_area("Observações", key="doc_obs", height=220)

        if st.button("Salvar Documento", type="primary", key="btn_save_doc"):
            if not doc_nr.strip() or not doc_assunto.strip():
                st.error("Informe o Nº do Documento (Recebido) e o Assunto do Documento.")
            else:
                insert_documento(doc_nr, doc_assunto, doc_origem, doc_prazo, doc_obs)
                st.toast("Documento salvo ✅")
                st.rerun()

    with col_sol:
        st.subheader("Cadastrar / Atualizar Solicitação")

        df_all = fetch_casos()
        arq_ids = fetch_arquivados_ids()
        if not df_all.empty:
            df_all = df_all[~df_all["id"].astype(int).isin(arq_ids)]

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

        st.session_state.setdefault("sol_doc_select", options[0])
        st.selectbox("Documento", options, key="sol_doc_select")

        assunto_solic = st.text_input("Assunto da Solicitação", key="sol_assunto_solic")
        cS1, cS2 = st.columns([1, 1], gap="small")
        with cS1:
            prazo_om = st.date_input("Prazo das OM", key="sol_prazo_om", value=None, format="DD/MM/YYYY")
        with cS2:
            nr_doc_solicitado = st.text_input("Nr do documento (Solicitado)", key="sol_doc_solicitado")

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
        st.session_state.setdefault("sol_responsaveis", [])

        bar1, bar2, bar3 = st.columns([0.20, 1, 0.30], gap="small")
        with bar1:
            st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
            if st.button("Circular", disabled=(not oms), use_container_width=True):
                st.session_state["sol_responsaveis"] = oms[:]
                st.rerun()
        with bar2:
            st.multiselect("Responsáveis", options=oms, key="sol_responsaveis", label_visibility="collapsed")
        with bar3:
            st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
            salvar = st.button("Salvar Solicitação", type="primary", use_container_width=True)

        if salvar:
            selecionadas = st.session_state.get("sol_responsaveis", []) or []
            if not assunto_solic.strip():
                st.error("Informe o Assunto da Solicitação.")
            elif not selecionadas:
                st.error("Selecione ao menos 1 Responsável.")
            else:
                # nova sem documento sempre (simplificado)
                caso_id = insert_solicitacao_sem_documento(assunto_solic, prazo_om, nr_doc_solicitado or "00")
                salvar_ou_atualizar_solicitacao(caso_id, assunto_solic, prazo_om, selecionadas, nr_doc_solicitado or "00")
                st.toast("Solicitação salva ✅")
                st.rerun()


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
                "ID": df_a["id"].astype(int),
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

        c1, c2 = st.columns([0.3, 0.3])
        with c1:
            rid = st.number_input("ID para restaurar", min_value=0, value=0, step=1)
        with c2:
            if st.button("Restaurar", type="primary"):
                if rid:
                    unarchive_caso(int(rid))
                    st.toast("Restaurado ✅")
                    st.rerun()
