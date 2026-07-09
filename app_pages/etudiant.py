import streamlit as st
from bson.objectid import ObjectId
from db import get_collection
from datetime import datetime

SEMESTRES = ["S1", "S2", "S3", "S4"]
UES = ["U001", "U002", "U003", "U004", "U005"]

def render(page):
    if not st.session_state.authenticated or st.session_state.user.get_role() != "student":
        st.session_state.page = "login"
        st.rerun()
        return
    if page == "student_dashboard":
        render_dashboard()
    elif page == "student_notes":
        render_notes()
    elif page == "student_cours":
        render_cours()
    elif page == "student_annonces":
        render_annonces()
    elif page == "student_messages":
        render_messages()

def get_etudiant():
    matricule = st.session_state.user.get_matricule()
    return get_collection("etudiants").find_one({"matricule": matricule})

def render_dashboard():
    st.markdown("<h2 style='color: #e2e8f0;'>📊 Tableau de bord</h2>", unsafe_allow_html=True)
    user = st.session_state.user
    etu = get_etudiant()

    stats = {
        "cours": get_collection("inscriptions").count_documents({"id_etudiant": etu["_id"]}) if etu else 0,
        "notes": get_collection("notes").count_documents({"id_etudiant": etu["_id"]}) if etu else 0,
    }
    if etu:
        pipeline = [{"$match": {"id_etudiant": etu["_id"]}}, {"$group": {"_id": None, "moyenne": {"$avg": "$valeur"}}}]
        result = list(get_collection("notes").aggregate(pipeline))
        stats["moyenne"] = round(result[0]["moyenne"], 2) if result else None
    else:
        stats["moyenne"] = None

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"<div style='background: linear-gradient(135deg, #1e3a8a, #1e40af); border-radius: 12px; padding: 1.25rem;'><p style='color: rgba(255,255,255,0.6); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em;'>Matricule</p><h3 style='color: #fff; font-weight: 800;'>{user.get_matricule()}</h3></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div style='background: linear-gradient(135deg, #065f46, #047857); border-radius: 12px; padding: 1.25rem;'><p style='color: rgba(255,255,255,0.6); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em;'>Cours inscrits</p><h3 style='color: #fff; font-weight: 800;'>{stats['cours']}</h3></div>", unsafe_allow_html=True)
    with c3:
        avg = stats["moyenne"]
        avg_color = "#22c55e" if avg and avg >= 16 else "#3b82f6" if avg and avg >= 12 else "#f59e0b" if avg and avg >= 10 else "#ef4444"
        st.markdown(f"<div style='background: linear-gradient(135deg, #581c87, #6d28d9); border-radius: 12px; padding: 1.25rem;'><p style='color: rgba(255,255,255,0.6); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em;'>Moyenne générale</p><h3 style='color: {avg_color}; font-weight: 800;'>{avg}/20</h3></div>" if avg else "<div style='background: linear-gradient(135deg, #581c87, #6d28d9); border-radius: 12px; padding: 1.25rem;'><p style='color: rgba(255,255,255,0.6); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em;'>Moyenne générale</p><p style='color: rgba(255,255,255,0.4);'>Aucune note</p></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns([3, 2])

    with c1:
        st.markdown("<h5 style='color: #e2e8f0;'>📢 Annonces récentes</h5>", unsafe_allow_html=True)
        dept = user.get_departement()
        annonces = list(get_collection("annonces").find({"departement": dept, "publie": True}).sort("date_creation", -1).limit(5))
        if annonces:
            for a in annonces:
                chef = get_collection("users").find_one({"_id": ObjectId(a["auteur"])})
                auteur = f"{chef['prenom']} {chef['nom']}" if chef else "Inconnu"
                st.markdown(f"<div style='background: #1e293b; border-radius: 8px; padding: 0.75rem 1rem; margin-bottom: 0.5rem; border-left: 3px solid #f59e0b;'><strong style='color: #e2e8f0;'>{a['titre']}</strong><p style='color: #94a3b8; font-size: 0.85rem; margin: 0;'>{a['contenu'][:150]}{'...' if len(a['contenu']) > 150 else ''}</p><small style='color: #64748b;'>👤 {auteur} · 📅 {a['date_creation']}</small></div>", unsafe_allow_html=True)
        else:
            st.info("Aucune annonce récente.")

    with c2:
        st.markdown(f"<h5 style='color: #e2e8f0;'>👤 Mon profil</h5>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style='background: #1e293b; border-radius: 12px; padding: 1.25rem; border: 1px solid rgba(255,255,255,0.06);'>
        <p><strong style='color: #e2e8f0;'>Nom :</strong> <span style='color: #94a3b8;'>{user.user_data.get('prenom', '')} {user.user_data.get('nom', '')}</span></p>
        <p><strong style='color: #e2e8f0;'>Email :</strong> <span style='color: #94a3b8;'>{user.user_data.get('email', '')}</span></p>
        <p><strong style='color: #e2e8f0;'>Matricule :</strong> <span style='color: #94a3b8;'>{user.get_matricule()}</span></p>
        <p><strong style='color: #e2e8f0;'>Département :</strong> <span style='color: #94a3b8;'>{user.get_departement()}</span></p>
        </div>
        """, unsafe_allow_html=True)

def render_notes():
    st.markdown("<h2 style='color: #e2e8f0;'>📝 Mes notes par semestre</h2>", unsafe_allow_html=True)
    etu = get_etudiant()
    if not etu:
        st.error("Profil étudiant introuvable.")
        return

    notes = list(get_collection("notes").find({"id_etudiant": etu["_id"]}))
    cours_map = {}
    for n in notes:
        c = get_collection("cours").find_one({"_id": n["id_cours"]})
        if c:
            sem = c.get("semestre", "S1")
            ue = c.get("code_ue", "U000")
            ntype = n.get("type_note", "examen")
            if sem not in cours_map:
                cours_map[sem] = {}
            if ue not in cours_map[sem]:
                cours_map[sem][ue] = {
                    "intitule": c["intitule"], "code": c["code"],
                    "enseignant": c.get("enseignant", ""), "coeff": c.get("credit", 3),
                    "cc": None, "examen": None,
                }
            cours_map[sem][ue][ntype] = n["valeur"]

    for sem in SEMESTRES:
        if sem not in cours_map:
            continue
        ues_list = []
        total_coeff = 0
        somme_ponderee = 0
        for ue in UES:
            if ue not in cours_map[sem]:
                continue
            d = cours_map[sem][ue]
            cc, examen = d["cc"], d["examen"]
            vals = [v for v in (cc, examen) if v is not None]
            moy = round(sum(vals) / len(vals), 2) if vals else None
            ues_list.append({**d, "cc": cc, "examen": examen, "moyenne": moy})
            if moy is not None:
                total_coeff += d["coeff"]
                somme_ponderee += moy * d["coeff"]
        moy_sem = round(somme_ponderee / total_coeff, 2) if total_coeff > 0 else None

        moy_color = "#22c55e" if moy_sem and moy_sem >= 16 else "#3b82f6" if moy_sem and moy_sem >= 12 else "#f59e0b" if moy_sem and moy_sem >= 10 else "#ef4444"
        st.markdown(f"""
        <div style='background: #1e293b; border-radius: 12px; margin-bottom: 1rem; border: 1px solid rgba(255,255,255,0.06);'>
        <div style='padding: 0.75rem 1.25rem; border-bottom: 2px solid rgba(37,99,235,0.15); display: flex; justify-content: space-between; align-items: center;'>
        <span style='background: linear-gradient(135deg, #3b82f6, #1d4ed8); color: #fff; padding: 0.25rem 0.75rem; border-radius: 8px; font-weight: 600; font-size: 0.9rem;'>Semestre {sem}</span>
        <span style='color: #64748b; font-size: 0.85rem;'>Moyenne : <strong style='color: {moy_color};'>{moy_sem}/20</strong></span>
        </div>
        <div style='padding: 0;'>
        """, unsafe_allow_html=True)

        data = []
        for ue_data in ues_list:
            def badge(v, label):
                if v is not None:
                    c = "#22c55e" if v >= 16 else "#3b82f6" if v >= 12 else "#f59e0b" if v >= 10 else "#ef4444"
                    return f"<span style='background: {c}20; color: {c}; padding: 2px 10px; border-radius: 6px; font-weight: 600;'>{v}</span>"
                return "<span style='color: #475569;'>—</span>"
            data.append({
                "UE": ue_data["code_ue"],
                "Code": ue_data["code"],
                "Intitulé": ue_data["intitule"],
                "Enseignant": ue_data["enseignant"],
                "CC": badge(ue_data["cc"], "CC"),
                "Examen": badge(ue_data["examen"], "Ex"),
                "Moy.": badge(ue_data["moyenne"], "Moy"),
                "Coeff.": ue_data["coeff"],
            })
        for d in data:
            st.markdown(f"<div style='display: grid; grid-template-columns: 50px 70px 1fr 120px 60px 60px 60px 40px; gap: 8px; padding: 0.5rem 1.25rem; align-items: center; color: #94a3b8; font-size: 0.85rem; border-bottom: 1px solid rgba(255,255,255,0.04);'><span style='background: rgba(100,116,139,0.2); color: #94a3b8; padding: 1px 6px; border-radius: 4px; font-size: 0.75rem;'>{d['UE']}</span><span style='color: #67e8f9; font-size: 0.8rem;'>{d['Code']}</span><span style='color: #e2e8f0; font-weight: 500;'>{d['Intitulé']}</span><span style='color: #64748b;'>{d['Enseignant']}</span><span style='text-align: center;'>{d['CC']}</span><span style='text-align: center;'>{d['Examen']}</span><span style='text-align: center;'>{d['Moy.']}</span><span style='text-align: center; color: #94a3b8;'>{d['Coeff.']}</span></div>", unsafe_allow_html=True)

        st.markdown("</div></div>", unsafe_allow_html=True)

    if not cours_map:
        st.info("Aucune note pour le moment.")

def render_cours():
    st.markdown("<h2 style='color: #e2e8f0;'>📚 Mes cours</h2>", unsafe_allow_html=True)
    etu = get_etudiant()
    if not etu:
        st.error("Profil étudiant introuvable.")
        return
    inscriptions = list(get_collection("inscriptions").find({"id_etudiant": etu["_id"]}))
    if not inscriptions:
        st.info("Aucun cours trouvé.")
        return
    cours_list = []
    for ins in inscriptions:
        c = get_collection("cours").find_one({"_id": ins["id_cours"]})
        if c:
            cours_list.append({**c, "annee": ins.get("annee_academique", ""), "date_ins": ins.get("date_inscription", "")})
    for c in cours_list:
        st.markdown(f"""
        <div style='background: #1e293b; border-radius: 10px; padding: 1rem 1.25rem; margin-bottom: 0.75rem; border: 1px solid rgba(255,255,255,0.06);'>
        <div style='display: flex; justify-content: space-between; align-items: start;'>
        <div><span style='background: rgba(6,182,212,0.15); color: #67e8f9; padding: 1px 8px; border-radius: 4px; font-size: 0.75rem;'>{c['code']}</span>
        <strong style='color: #e2e8f0; margin-left: 8px;'>{c['intitule']}</strong></div>
        <span style='background: rgba(251,191,36,0.15); color: #fcd34d; padding: 2px 10px; border-radius: 6px; font-size: 0.8rem;'>Crédit: {c.get('credit', 3)}</span>
        </div>
        <p style='color: #64748b; font-size: 0.85rem; margin: 0.5rem 0 0;'>👨‍🏫 {c.get('enseignant', '')} · 📅 {c.get('annee', '')} · Semestre {c.get('semestre', 'S1')} · UE {c.get('code_ue', 'U000')}</p>
        </div>
        """, unsafe_allow_html=True)

def render_annonces():
    st.markdown("<h2 style='color: #e2e8f0;'>📢 Annonces</h2>", unsafe_allow_html=True)
    dept = st.session_state.user.get_departement()
    annonces = list(get_collection("annonces").find({"departement": dept, "publie": True}).sort("date_creation", -1))
    if annonces:
        cols = st.columns(2)
        for i, a in enumerate(annonces):
            chef = get_collection("users").find_one({"_id": ObjectId(a["auteur"])})
            auteur = f"{chef['prenom']} {chef['nom']}" if chef else "Inconnu"
            with cols[i % 2]:
                st.markdown(f"""
                <div style='background: #1e293b; border-radius: 12px; padding: 1.25rem; margin-bottom: 1rem; border: 1px solid rgba(255,255,255,0.06);'>
                <h6 style='color: #e2e8f0; font-weight: 600;'>{a['titre']}</h6>
                <p style='color: #94a3b8; font-size: 0.9rem;'>{a['contenu']}</p>
                <small style='color: #64748b;'>👤 {auteur} · 📅 {a['date_creation']}</small>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Aucune annonce pour votre département.")

def render_messages():
    st.markdown("<h2 style='color: #e2e8f0;'>💬 Messagerie</h2>", unsafe_allow_html=True)
    etu = get_etudiant()
    if not etu:
        st.error("Profil étudiant introuvable.")
        return
    id_etu = etu["_id"]
    dept = st.session_state.user.get_departement()
    chef = get_collection("users").find_one({"role": "head", "departement": dept})
    chef_id = chef["_id"] if chef else None
    chef_nom = f"{chef['prenom']} {chef['nom']}" if chef else "Chef de département"

    messages = list(get_collection("messages").find({
        "$or": [{"id_etudiant": id_etu, "id_chef": chef_id}]
    }).sort("date_envoi", 1))

    st.markdown(f"<p style='color: #94a3b8;'>Discussion avec <strong style='color: #e2e8f0;'>{chef_nom}</strong></p>", unsafe_allow_html=True)

    for m in messages:
        is_etu = m.get("expediteur") == "etudiant"
        align = "right" if is_etu else "left"
        bg = "rgba(37,99,235,0.2)" if is_etu else "rgba(255,255,255,0.06)"
        color = "#e2e8f0" if is_etu else "#94a3b8"
        st.markdown(f"<div style='text-align: {align}; margin-bottom: 0.5rem;'><div style='display: inline-block; background: {bg}; color: {color}; padding: 0.5rem 1rem; border-radius: 12px; max-width: 70%; font-size: 0.9rem;'>{m['contenu']}</div></div>", unsafe_allow_html=True)

    with st.form("message_form"):
        contenu = st.text_area("Votre message", placeholder="Écrivez votre message ici...", height=100)
        if st.form_submit_button("📤 Envoyer", use_container_width=True, type="primary"):
            if contenu.strip():
                get_collection("messages").insert_one({
                    "id_etudiant": id_etu,
                    "id_chef": chef_id,
                    "expediteur": "etudiant",
                    "contenu": contenu.strip(),
                    "date_envoi": datetime.now(),
                    "lu": False,
                })
                st.success("Message envoyé au chef de département.")
                st.rerun()
            else:
                st.error("Le message ne peut pas être vide.")
