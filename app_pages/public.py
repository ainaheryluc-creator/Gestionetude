import streamlit as st
from bson.objectid import ObjectId
from db import get_collection
from utils.auth import login

DEPARTEMENTS = ["Informatique", "Gestion", "Genie Civil", "Communication"]

def render(page):
    if page == "accueil":
        render_accueil()
    elif page == "public_annonces":
        render_annonces()
    elif page == "login":
        render_login()

def render_accueil():
    st.markdown("""
        <style>
        .hero { background: linear-gradient(135deg, #1e3a5f, #0f172a); padding: 3rem 2rem; border-radius: 16px; margin-bottom: 2rem; border: 1px solid rgba(255,255,255,0.06); }
        .hero h1 { color: #fff; font-size: 2.5rem; font-weight: 800; margin-bottom: 0.5rem; }
        .hero p { color: #94a3b8; font-size: 1.1rem; }
        .hero .btn-primary { background: #2563eb; color: #fff; padding: 0.6rem 2rem; border-radius: 50px; text-decoration: none; display: inline-block; margin-top: 1rem; }
        .hero .btn-outline { border: 1px solid rgba(255,255,255,0.2); color: #e2e8f0; padding: 0.6rem 2rem; border-radius: 50px; text-decoration: none; display: inline-block; margin-top: 1rem; margin-left: 0.5rem; }
        .dept-card { background: #1e293b; border-radius: 12px; padding: 1.5rem; text-align: center; border: 1px solid rgba(255,255,255,0.06); }
        .dept-card h3 { font-size: 2rem; font-weight: 800; margin: 0; }
        .dept-card p { color: #64748b; margin: 0; font-size: 0.85rem; }
        .dept-card .icon { font-size: 1.5rem; margin-bottom: 0.5rem; }
        .info-card { background: linear-gradient(135deg, #1e293b, #0f172a); border-radius: 12px; padding: 1.5rem; border: 1px solid rgba(255,255,255,0.06); }
        .annonce-item { padding: 1rem 0; border-bottom: 1px solid rgba(255,255,255,0.06); }
        .annonce-item h6 { color: #e2e8f0; font-weight: 600; }
        .annonce-item p { color: #94a3b8; font-size: 0.9rem; }
        .annonce-item small { color: #64748b; }
        </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("<div class='hero'><h1>🎓 Université Privée Hay (UPH)</h1><p><strong>Qualité — Efficacité — Excellence</strong><br>Système LMD — Immeuble CNAPS 67 Ha, Antananarivo</p>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔑 Accès plateforme", use_container_width=True):
                st.session_state.page = "login"
                st.rerun()
        with c2:
            if st.button("📢 Annonces", use_container_width=True):
                st.session_state.page = "public_annonces"
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    stats = {}
    for d in DEPARTEMENTS:
        stats[d] = get_collection("users").count_documents({"role": "student", "departement": d})

    cols = st.columns(4)
    icons = {"Informatique": "💻", "Gestion": "📊", "Genie Civil": "🏗️", "Communication": "🌐"}
    colors = {"Informatique": "#3b82f6", "Gestion": "#10b981", "Genie Civil": "#f59e0b", "Communication": "#06b6d4"}
    for i, d in enumerate(DEPARTEMENTS):
        with cols[i]:
            st.markdown(f"<div class='dept-card'><div class='icon' style='color: {colors[d]}'>{icons[d]}</div><h3 style='color: {colors[d]}'>{stats[d]}</h3><p>étudiants — {d}</p></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns([3, 2])

    with c1:
        st.markdown("<div class='info-card'><h5 style='color: #e2e8f0;'>📌 À propos</h5>", unsafe_allow_html=True)
        st.markdown("""
        <p style='color: #94a3b8;'>
        📍 <strong style='color: #e2e8f0;'>Adresse :</strong> Immeuble CNAPS, 67 Ha Nord-Est, Antananarivo - Madagascar<br>
        📞 <strong style='color: #e2e8f0;'>Tél :</strong> 032 78 665 91 / 034 66 602 52 / 22 216 95<br>
        🎓 <strong style='color: #e2e8f0;'>Formations :</strong> Informatique de Gestion, Gestion-Économie, Génie Civil, Communication
        </p>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("<div class='info-card'><h5 style='color: #e2e8f0;'>🔒 Accès plateforme</h5>", unsafe_allow_html=True)
        st.markdown("<p style='color: #94a3b8;'>Connectez-vous pour accéder à votre espace personnel</p>", unsafe_allow_html=True)
        if st.button("🔑 Se connecter", use_container_width=True, type="primary"):
            st.session_state.page = "login"
            st.rerun()
        st.markdown("<hr style='border-color: rgba(255,255,255,0.06);'>", unsafe_allow_html=True)
        st.markdown("""
        <p style='color: #94a3b8; font-size: 0.85rem;'>
        👑 <strong style='color: #475569;'>Chefs</strong> : Gèrent les comptes et publient les annonces<br>
        🎓 <strong style='color: #475569;'>Étudiants</strong> : Consultent leurs notes, cours et annonces
        </p>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Dernières annonces publiques
    st.markdown("<br><h4 style='color: #e2e8f0;'>📢 Dernières annonces</h4>", unsafe_allow_html=True)
    annonces = list(get_collection("annonces").find({"publie": True, "visibilite": "public"}).sort("date_creation", -1).limit(5))
    if annonces:
        for a in annonces:
            chef = get_collection("users").find_one({"_id": ObjectId(a["auteur"])})
            auteur_nom = f"{chef['prenom']} {chef['nom']}" if chef else "Inconnu"
            st.markdown(f"<div class='annonce-item'><h6>{a['titre']}</h6><p>{a['contenu'][:200]}{'...' if len(a['contenu']) > 200 else ''}</p><small>👤 {auteur_nom} · 📅 {a['date_creation']} · 🏷️ {a['departement']}</small></div>", unsafe_allow_html=True)
        if st.button("📢 Voir toutes les annonces"):
            st.session_state.page = "public_annonces"
            st.rerun()
    else:
        st.info("Aucune annonce publique pour le moment.")

def render_annonces():
    st.markdown("<h2 style='color: #e2e8f0;'>📢 Annonces</h2>", unsafe_allow_html=True)
    annonces = list(get_collection("annonces").find({"publie": True, "visibilite": "public"}).sort("date_creation", -1))
    if annonces:
        cols = st.columns(3)
        for i, a in enumerate(annonces):
            chef = get_collection("users").find_one({"_id": ObjectId(a["auteur"])})
            auteur_nom = f"{chef['prenom']} {chef['nom']}" if chef else "Inconnu"
            with cols[i % 3]:
                st.markdown(f"""
                <div style='background: #1e293b; border-radius: 12px; padding: 1.25rem; margin-bottom: 1rem; border: 1px solid rgba(255,255,255,0.06);'>
                <h6 style='color: #e2e8f0; font-weight: 600;'>{a['titre']} <span style='background: rgba(37,99,235,0.15); color: #60a5fa; font-size: 0.7rem; padding: 2px 8px; border-radius: 10px;'>{a['departement']}</span></h6>
                <p style='color: #94a3b8; font-size: 0.9rem;'>{a['contenu']}</p>
                <small style='color: #64748b;'>👤 {auteur_nom} · 📅 {a['date_creation']}</small>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Aucune annonce publique pour le moment.")

def render_login():
    st.markdown("<h2 style='color: #e2e8f0; text-align: center;'>🔑 Connexion</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94a3b8;'>Université Privée Hay (UPH) — 67 Ha</p>", unsafe_allow_html=True)
    with st.form("login_form"):
        email = st.text_input("📧 Email", placeholder="votre@email.com")
        password = st.text_input("🔒 Mot de passe", type="password", placeholder="Votre mot de passe")
        if st.form_submit_button("🔑 Se connecter", use_container_width=True, type="primary"):
            if login(email, password):
                role = st.session_state.user.get_role()
                st.session_state.page = "head_dashboard" if role == "head" else "student_dashboard"
                st.rerun()
    st.markdown("<hr style='border-color: rgba(255,255,255,0.06);'>", unsafe_allow_html=True)
    st.markdown("""
    <div style='text-align: center; color: #64748b; font-size: 0.85rem;'>
    <p><strong style='color: #475569;'>👑 Chefs</strong> : Utilisez votre email professionnel</p>
    <p><strong style='color: #475569;'>🎓 Étudiants</strong> : Utilisez l'email fourni par votre département</p>
    </div>
    """, unsafe_allow_html=True)
