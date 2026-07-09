import streamlit as st
from db import connect
from utils.auth import init_session, login, logout, show_flash, User
from app_pages import public, etudiant, chef

st.set_page_config(
    page_title="Université Privée Hay (UPH) — Plateforme Académique",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="auto",
)

connect()
init_session()

# --- Sidebar navigation ---
with st.sidebar:
    st.markdown(
        """
        <style>
        .sidebar-header { padding: 1rem 0.5rem; text-align: center; }
        .sidebar-header h3 { color: #e2e8f0; margin-bottom: 0.25rem; }
        .sidebar-header p { color: #64748b; font-size: 0.85rem; }
        .nav-btn { width: 100%; text-align: left; padding: 0.6rem 1rem !important; margin-bottom: 0.25rem; border-radius: 8px; background: transparent; border: none; color: #94a3b8; cursor: pointer; font-size: 0.9rem; }
        .nav-btn:hover { background: rgba(37,99,235,0.1); color: #e2e8f0; }
        .nav-btn.active { background: rgba(37,99,235,0.2); color: #60a5fa; border-left: 3px solid #3b82f6; }
        .nav-btn .icon { margin-right: 10px; }
        .user-badge { display: flex; align-items: center; gap: 10px; padding: 0.75rem; background: rgba(255,255,255,0.05); border-radius: 10px; margin-bottom: 1rem; }
        .user-badge .avatar { width: 36px; height: 36px; border-radius: 50%; background: linear-gradient(135deg, #3b82f6, #1d4ed8); display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.9rem; color: #fff; flex-shrink: 0; }
        .user-badge .info { font-size: 0.85rem; }
        .user-badge .info .name { color: #e2e8f0; font-weight: 600; }
        .user-badge .info .detail { color: #64748b; font-size: 0.75rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div class='sidebar-header'><h3>🏛️ UPH</h3><p>Plateforme Académique</p></div>", unsafe_allow_html=True)

    if st.session_state.authenticated:
        user = st.session_state.user
        initials = (user.user_data.get("prenom", "?")[0] + user.user_data.get("nom", "?")[0]).upper()
        role_label = "👑 Chef" if user.get_role() == "head" else "🎓 Étudiant"
        st.markdown(
            f"<div class='user-badge'>"
            f"<div class='avatar'>{initials}</div>"
            f"<div class='info'><div class='name'>{user.get_nom_complet()}</div>"
            f"<div class='detail'>{role_label} · {user.get_departement()}</div></div></div>",
            unsafe_allow_html=True,
        )

    # Define navigation
    if not st.session_state.authenticated:
        pages = [
            ("accueil", "🏠", "Accueil"),
            ("public_annonces", "📢", "Annonces"),
            ("login", "🔑", "Connexion"),
        ]
    elif st.session_state.user.get_role() == "student":
        pages = [
            ("student_dashboard", "📊", "Tableau de bord"),
            ("student_notes", "📝", "Mes notes"),
            ("student_cours", "📚", "Mes cours"),
            ("student_annonces", "📢", "Annonces"),
            ("student_messages", "💬", "Messagerie"),
        ]
    else:
        pages = [
            ("head_dashboard", "📊", "Tableau de bord"),
            ("head_etudiants", "👥", "Étudiants"),
            ("head_annonces", "📢", "Annonces"),
            ("head_cours", "📚", "Cours"),
            ("head_inscriptions", "📝", "Inscriptions"),
            ("head_notes", "📋", "Notes"),
            ("head_chefs", "👑", "Chefs"),
            ("head_messages", "💬", "Messagerie"),
            ("head_moyennes", "📈", "Moyennes"),
        ]

    for key, icon, label in pages:
        if st.button(f"{icon} {label}", key=f"nav_{key}", use_container_width=True):
            st.session_state.page = key
            st.rerun()

    if st.session_state.authenticated:
        st.markdown("<hr style='border-color: rgba(255,255,255,0.06);'>", unsafe_allow_html=True)
        if st.button("⚙️ Mon profil", key="nav_profile", use_container_width=True):
            target = "head_profile" if st.session_state.user.get_role() == "head" else "student_dashboard"
            st.session_state.page = target
            st.rerun()
        if st.button("🚪 Déconnexion", key="nav_logout", use_container_width=True):
            logout()

# --- Main content area ---
show_flash()

page = st.session_state.get("page", "accueil")
if not st.session_state.authenticated:
    public.render(page)
elif st.session_state.user.get_role() == "student":
    etudiant.render(page)
elif st.session_state.user.get_role() == "head":
    chef.render(page)
else:
    public.render("accueil")
