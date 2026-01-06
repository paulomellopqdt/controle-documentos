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
  padding: 0.55rem 0.80rem;
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

/* Badge */
.badge{
  display:inline-flex; align-items:center; gap:8px;
  padding: 6px 10px; border-radius: 999px;
  font-size: 0.85rem; border:1px solid rgba(49,51,63,0.12);
}
.badge-warn{ background: rgba(234,179,8,0.14); color: #854d0e; }
.badge-ok{ background: rgba(34,197,94,0.12); color: #166534; }

/* Caixa principal */
.main-box{
  border: 1px solid rgba(49,51,63,0.10);
  border-radius: 16px;
  padding: 14px 14px;
  background: rgba(255,255,255,0.65);
  box-shadow: 0 6px 22px rgba(15, 23, 42, 0.04);
}
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
        menu_options = [f"📋 {dash_title}", "📄 Documento", "🗄️ Arquivados"]
        page = st.radio("Menu", menu_options, index=0)

        st.markdown("---")
        c1, c2 = st.columns(2, gap="small")
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


def archive_caso(caso_id: int):
    user = st.session_state["sb_user"]
    payload = {"owner_id": user.id, "caso_id": caso_id, "archived_at": datetime.now().isoformat()}
    _sb_table("arquivados").upsert(payload, on_conflict="caso_id").execute()


def unarchive_caso(caso_id: int):
    _sb_table("arquivados").delete().eq("caso_id", caso_id).execute()


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
# Helpers
# =========================================================
def _fmt_date_iso_to_date(v):
    if not v:
        return None
    try:
        return pd.to_datetime(v).date()
    except Exception:
        return None


def _fmt_date_to_iso(v):
    if v is None or str(v).strip() in ["", "NaT", "None"]:
        return None
    if isinstance(v, (datetime, pd.Timestamp)):
        return v.date().isoformat()
    if isinstance(v, date):
        return v.isoformat()
    try:
        return pd.to_datetime(v).date().isoformat()
    except Exception:
        return None


def build_msg_cobranca(caso: dict, ret: pd.DataFrame) -> str:
    assunto = caso.get("assunto_solic") or "-"
    nr = caso.get("nr_doc_solicitado") or "-"
    prazo = "-"
    try:
        prazo = pd.to_datetime(caso.get("prazo_om")).strftime("%d/%m/%Y") if caso.get("prazo_om") else "-"
    except Exception:
        prazo = "-"

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


def _make_acomp_df(df_acomp: pd.DataFrame, pend: pd.DataFrame) -> pd.DataFrame:
    pend_map = {int(r["caso_id"]): int(r["qtd"]) for _, r in pend.iterrows()} if not pend.empty else {}
    if df_acomp.empty:
        return pd.DataFrame(
            columns=[
                "Sel",
                "Id",
                "Origem",
                "Nr Doc (Recebido)",
                "Assunto (Documento)",
                "Prazo Final",
                "Nr Doc (Solicitado)",
                "Assunto (Solicitação)",
                "Prazo OM",
                "Pendências (Qtd)",
                "Status",
                "Nr Doc (Resposta)",
            ]
        )

    df_acomp = df_acomp.copy()
    df_acomp["Pendências (Qtd)"] = df_acomp["id"].astype(int).map(lambda x: pend_map.get(int(x), 0))

    # ✅ ORDEM DAS COLUNAS (como você pediu)
    out = pd.DataFrame(
        {
            "Sel": [False] * len(df_acomp),
            "Id": df_acomp["id"].astype(int),
            "Origem": df_acomp.get("origem").fillna("-"),
            "Nr Doc (Recebido)": df_acomp.get("nr_doc_recebido").fillna("-"),
            "Assunto (Documento)": df_acomp.get("assunto_doc").fillna("-"),
            "Prazo Final": df_acomp.get("prazo_final").apply(_fmt_date_iso_to_date),
            "Nr Doc (Solicitado)": df_acomp.get("nr_doc_solicitado").fillna("-"),
            "Assunto (Solicitação)": df_acomp.get("assunto_solic").fillna("-"),
            "Prazo OM": df_acomp.get("prazo_om").apply(_fmt_date_iso_to_date),
            "Pendências (Qtd)": df_acomp["Pendências (Qtd)"].fillna(0).astype(int),
            "Status": df_acomp.get("status").fillna("Recebido"),
            "Nr Doc (Resposta)": df_acomp.get("nr_doc_resposta").fillna("-"),
        }
    )
    return out


def _upsert_casos_from_editor(df_editor: pd.DataFrame):
    """
    Salva/atualiza 'casos' baseado no que o usuário editou na tabela.
    - Se Id existir => UPDATE
    - Se Id vazio => INSERT
    """
    user = st.session_state["sb_user"]
    now_iso = datetime.now().isoformat()

    for _, r in df_editor.iterrows():
        rid = r.get("Id", None)
        origem = (str(r.get("Origem", "")).strip() or None)
        nr_rec = (str(r.get("Nr Doc (Recebido)", "")).strip() or None)
        assunto_doc = (str(r.get("Assunto (Documento)", "")).strip() or None)
        prazo_final_iso = _fmt_date_to_iso(r.get("Prazo Final"))
        nr_solic = (str(r.get("Nr Doc (Solicitado)", "")).strip() or None)
        assunto_solic = (str(r.get("Assunto (Solicitação)", "")).strip() or None)
        prazo_om_iso = _fmt_date_to_iso(r.get("Prazo OM"))
        status = (str(r.get("Status", "")).strip() or "Recebido")
        nr_resp = (str(r.get("Nr Doc (Resposta)", "")).strip() or None)

        # Normalizações visuais
        def dash_to_none(x):
            if x is None:
                return None
            if str(x).strip() in ["-", "None", "nan", "NaN"]:
                return None
            return x

        origem = dash_to_none(origem)
        nr_rec = dash_to_none(nr_rec)
        assunto_doc = dash_to_none(assunto_doc)
        nr_solic = dash_to_none(nr_solic)
        assunto_solic = dash_to_none(assunto_solic)
        nr_resp = dash_to_none(nr_resp)

        if rid and str(rid).strip().isdigit():
            # UPDATE
            payload = {
                "origem": origem,
                "nr_doc_recebido": nr_rec or "-",
                "assunto_doc": assunto_doc or "-",
                "prazo_final": prazo_final_iso,
                "nr_doc_solicitado": nr_solic,
                "assunto_solic": assunto_solic,
                "prazo_om": prazo_om_iso,
                "status": status,
                "nr_doc_resposta": nr_resp,
            }
            _sb_table("casos").update(payload).eq("id", int(rid)).execute()
        else:
            # INSERT (linha nova)
            # Regras simples: se não tiver doc recebido, vira "sem documento"
            is_sem_doc = (not nr_rec and not assunto_doc) and bool(assunto_solic or nr_solic)

            payload = {
                "owner_id": user.id,
                "created_at": now_iso,
                "origem": origem if origem is not None else ("-" if is_sem_doc else None),
                "nr_doc_recebido": (nr_rec or ("-" if is_sem_doc else "")) or "-",
                "assunto_doc": (assunto_doc or ("-" if is_sem_doc else "")) or "-",
                "prazo_final": prazo_final_iso,
                "nr_doc_solicitado": nr_solic,
                "assunto_solic": assunto_solic,
                "prazo_om": prazo_om_iso,
                "status": "Distribuído" if is_sem_doc else status,
                "nr_doc_resposta": nr_resp,
            }

            # Evita inserir linha totalmente vazia
            meaningful = any(
                [
                    (payload.get("nr_doc_recebido") not in [None, "", "-"]),
                    (payload.get("assunto_doc") not in [None, "", "-"]),
                    bool(payload.get("assunto_solic")),
                    bool(payload.get("nr_doc_solicitado")),
                ]
            )
            if meaningful:
                _sb_table("casos").insert(payload).execute()


# =========================================================
# APP START
# =========================================================
require_auth()
page, dash_title = sidebar_layout()

st.session_state.setdefault("current_selected_id", None)
st.session_state.setdefault("ret_dirty_for_selected", False)

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

    # ========= Caixa principal (destaque) =========
    st.markdown('<div class="main-box">', unsafe_allow_html=True)
    st.subheader("Acompanhamento")

    # Carrega tabela para editor (com ordem de colunas)
    editor_state_key = "acomp_editor_df"
    if editor_state_key not in st.session_state:
        st.session_state[editor_state_key] = _make_acomp_df(df_acomp, pend)

    # Barra de ações (compacta, só emoji)
    b1, b2, b3, b4 = st.columns([0.10, 0.10, 0.10, 0.70], gap="small")
    with b1:
        if st.button("➕", key="btn_add_row", help="Adicionar nova linha", use_container_width=True):
            d = st.session_state[editor_state_key].copy()
            new_row = {
                "Sel": False,
                "Id": None,
                "Origem": "",
                "Nr Doc (Recebido)": "",
                "Assunto (Documento)": "",
                "Prazo Final": None,
                "Nr Doc (Solicitado)": "",
                "Assunto (Solicitação)": "",
                "Prazo OM": None,
                "Pendências (Qtd)": 0,
                "Status": "Recebido",
                "Nr Doc (Resposta)": "",
            }
            d = pd.concat([pd.DataFrame([new_row]), d], ignore_index=True)
            st.session_state[editor_state_key] = d
            st.rerun()

    with b2:
        if st.button("💾", key="btn_save_acomp", help="Salvar alterações", use_container_width=True):
            st.session_state["confirm_save_acomp"] = True

    with b3:
        if st.button("🗄️", key="btn_archive_acomp", help="Arquivar selecionado", use_container_width=True):
            st.session_state["confirm_archive_acomp"] = True

    # Editor
    df_editor_in = st.session_state[editor_state_key].copy()

    edited_df = st.data_editor(
        df_editor_in,
        use_container_width=True,
        hide_index=True,
        key="acomp_editor_widget",
        column_config={
            "Sel": st.column_config.CheckboxColumn("Sel", help="Marque 1 linha para arquivar", width="small"),
            "Id": st.column_config.NumberColumn("Id", disabled=True, width="small"),
            "Origem": st.column_config.TextColumn("Origem", width="medium"),
            "Nr Doc (Recebido)": st.column_config.TextColumn("Nr Doc (Recebido)", width="medium"),
            "Assunto (Documento)": st.column_config.TextColumn("Assunto (Documento)", width="large"),
            "Prazo Final": st.column_config.DateColumn("Prazo Final", format="DD/MM/YYYY", width="medium"),
            "Nr Doc (Solicitado)": st.column_config.TextColumn("Nr Doc (Solicitado)", width="medium"),
            "Assunto (Solicitação)": st.column_config.TextColumn("Assunto (Solicitação)", width="large"),
            "Prazo OM": st.column_config.DateColumn("Prazo OM", format="DD/MM/YYYY", width="medium"),
            "Pendências (Qtd)": st.column_config.NumberColumn("Pendências (Qtd)", disabled=True, width="small"),
            "Status": st.column_config.SelectboxColumn("Status", options=["Pendente", "Distribuído", "Recebido", "Resolvido"], width="medium"),
            "Nr Doc (Resposta)": st.column_config.TextColumn("Nr Doc (Resposta)", width="medium"),
        },
        disabled=["Id", "Pendências (Qtd)"],
    )

    # Mantém no estado (para não perder edição)
    st.session_state[editor_state_key] = edited_df.copy()

    # Confirmações
    if st.session_state.get("confirm_save_acomp"):
        st.warning("Confirma salvar as alterações do Acompanhamento?")
        c1, c2 = st.columns([0.18, 0.82], gap="small")
        with c1:
            if st.button("Confirmar", type="primary", key="confirm_save_acomp_btn"):
                _upsert_casos_from_editor(edited_df)
                # recarrega do banco (para atualizar Ids novos)
                df_new = fetch_casos()
                arq_ids_new = fetch_arquivados_ids()
                df_acomp_new = df_new[~df_new["id"].astype(int).isin(arq_ids_new)].copy() if not df_new.empty else pd.DataFrame()
                pend_new = fetch_pendencias()
                st.session_state[editor_state_key] = _make_acomp_df(df_acomp_new, pend_new)
                st.session_state.pop("confirm_save_acomp", None)
                st.toast("Salvo ✅")
                st.rerun()
        with c2:
            if st.button("Cancelar", key="cancel_save_acomp_btn"):
                st.session_state.pop("confirm_save_acomp", None)
                st.info("Salvamento cancelado.")

    if st.session_state.get("confirm_archive_acomp"):
        # pega 1 selecionado
        sel_rows = edited_df[edited_df["Sel"] == True]  # noqa: E712
        if sel_rows.empty:
            st.warning("Marque 1 linha em **Sel** para arquivar.")
            st.session_state.pop("confirm_archive_acomp", None)
        elif len(sel_rows) > 1:
            st.warning("Marque somente **1** linha para arquivar.")
            st.session_state.pop("confirm_archive_acomp", None)
        else:
            rid = sel_rows.iloc[0].get("Id", None)
            if not rid or not str(rid).strip().isdigit():
                st.warning("A linha selecionada ainda não foi salva (sem Id). Salve antes de arquivar.")
                st.session_state.pop("confirm_archive_acomp", None)
            else:
                st.warning("Confirma arquivar o item selecionado?")
                cc1, cc2 = st.columns([0.18, 0.82], gap="small")
                with cc1:
                    if st.button("Confirmar", type="primary", key="confirm_archive_btn"):
                        archive_caso(int(rid))
                        # recarrega
                        df_new = fetch_casos()
                        arq_ids_new = fetch_arquivados_ids()
                        df_acomp_new = df_new[~df_new["id"].astype(int).isin(arq_ids_new)].copy() if not df_new.empty else pd.DataFrame()
                        pend_new = fetch_pendencias()
                        st.session_state[editor_state_key] = _make_acomp_df(df_acomp_new, pend_new)
                        st.session_state.pop("confirm_archive_acomp", None)
                        st.toast("Arquivado ✅")
                        st.rerun()
                with cc2:
                    if st.button("Cancelar", key="cancel_archive_btn"):
                        st.session_state.pop("confirm_archive_acomp", None)
                        st.info("Arquivamento cancelado.")

    st.markdown("</div>", unsafe_allow_html=True)  # fecha main-box

    # Mensagem/Responsável continuam abaixo quando selecionar um item salvo
    # (seleção pelo Sel + Id)
    sel_rows = st.session_state[editor_state_key]
    sel_one = sel_rows[sel_rows["Sel"] == True]  # noqa: E712
    if len(sel_one) == 1:
        rid = sel_one.iloc[0].get("Id", None)
        if rid and str(rid).strip().isdigit():
            selected_id = int(rid)
            caso = fetch_caso(selected_id) or {}
            ret = fetch_retornos(selected_id)

            with st.expander("Mensagem", expanded=False):
                msg_key = f"msg_edit_{selected_id}"
                st.session_state.setdefault(msg_key, build_msg_cobranca(caso, ret))
                st.text_area("Mensagem", key=msg_key, height=200, label_visibility="collapsed")

            with st.expander("Responsável", expanded=False):
                if ret.empty:
                    st.info("Sem responsáveis cadastrados.")
                else:
                    # visual simples (edição de retornos fica na aba Documento, se você quiser eu trago p/ cá também)
                    view_df = pd.DataFrame(
                        {
                            "Responsável": ret["om"].fillna("").astype(str),
                            "Status": ret["status"].fillna("Pendente").astype(str),
                            "Obs": ret["observacoes"].fillna("").astype(str),
                        }
                    )
                    st.dataframe(view_df, use_container_width=True, hide_index=True)


# =========================================================
# PAGE: DOCUMENTO (mantida)
# =========================================================
elif page == "📄 Documento":
    st.title("📄 Documento & Solicitação")
    st.info("Esta aba continua disponível, mas o Acompanhamento agora permite editar tudo direto na tabela.")


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
                "Id": df_a["id"].astype(int),
                "Origem": df_a.get("origem").fillna("-"),
                "Nr Doc (Recebido)": df_a["nr_doc_recebido"].fillna("-"),
                "Assunto (Documento)": df_a["assunto_doc"].fillna("-"),
                "Prazo Final": pd.to_datetime(df_a.get("prazo_final"), errors="coerce").dt.strftime("%d/%m/%Y").fillna("-"),
                "Nr Doc (Solicitado)": df_a.get("nr_doc_solicitado").fillna("-"),
                "Assunto (Solicitação)": df_a.get("assunto_solic").fillna("-"),
                "Prazo OM": pd.to_datetime(df_a.get("prazo_om"), errors="coerce").dt.strftime("%d/%m/%Y").fillna("-"),
                "Status": df_a.get("status").fillna("-"),
                "Nr Doc (Resposta)": df_a.get("nr_doc_resposta").fillna("-"),
            }
        )
        st.dataframe(df_a_show, use_container_width=True, hide_index=True)
