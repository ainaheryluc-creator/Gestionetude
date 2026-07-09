import streamlit as st
from bson.objectid import ObjectId
from bson.errors import InvalidId
from werkzeug.security import generate_password_hash
from db import get_collection
from datetime import date, datetime

DEPARTEMENTS = ["Informatique", "Gestion", "Genie Civil", "Communication"]
SEMESTRES = ["S1", "S2", "S3", "S4"]
UES = ["U001", "U002", "U003", "U004", "U005"]

def render(page):
    if not st.session_state.authenticated or st.session_state.user.get_role() != "head":
        st.session_state.page = "login"
        st.rerun()
        return
    if page == "head_dashboard":
        render_dashboard()
    elif page == "head_etudiants":
        render_etudiants()
    elif page == "head_annonces":
        render_annonces()
    elif page == "head_cours":
        render_cours()
    elif page == "head_inscriptions":
        render_inscriptions()
    elif page == "head_notes":
        render_notes()
    elif page == "head_chefs":
        render_chefs()
    elif page == "head_messages":
        render_messages()
    elif page == "head_moyennes":
        render_moyennes()
    elif page == "head_profile":
        render_profile()

def get_dept():
    return st.session_state.user.get_departement()

# ─── DASHBOARD ───

def render_dashboard():
    st.markdown("<h2 style='color: #e2e8f0;'>📊 Tableau de bord</h2>", unsafe_allow_html=True)
    dept = get_dept()
    stats = {
        "etudiants": get_collection("users").count_documents({"role": "student", "departement": dept}),
        "annonces": get_collection("annonces").count_documents({"departement": dept}),
        "cours": get_collection("cours").count_documents({}),
    }
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"<div style='background: linear-gradient(135deg, #1e3a8a, #1e40af); border-radius: 12px; padding: 1.25rem;'><p style='color: rgba(255,255,255,0.6); font-size: 0.75rem; text-transform: uppercase;'>Étudiants</p><h2 style='color: #fff; font-weight: 800;'>{stats['etudiants']}</h2></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div style='background: linear-gradient(135deg, #92400e, #b45309); border-radius: 12px; padding: 1.25rem;'><p style='color: rgba(255,255,255,0.6); font-size: 0.75rem; text-transform: uppercase;'>Annonces</p><h2 style='color: #fff; font-weight: 800;'>{stats['annonces']}</h2></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div style='background: linear-gradient(135deg, #065f46, #047857); border-radius: 12px; padding: 1.25rem;'><p style='color: rgba(255,255,255,0.6); font-size: 0.75rem; text-transform: uppercase;'>Cours</p><h2 style='color: #fff; font-weight: 800;'>{stats['cours']}</h2></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns([3, 2])

    with c1:
        st.markdown("<h5 style='color: #e2e8f0;'>👥 Derniers étudiants</h5>", unsafe_allow_html=True)
        etudiants = list(get_collection("users").find({"role": "student", "departement": dept}).sort("_id", -1).limit(5))
        if etudiants:
            for e in etudiants:
                st.markdown(f"<div style='background: #1e293b; border-radius: 8px; padding: 0.5rem 1rem; margin-bottom: 0.25rem; display: flex; justify-content: space-between;'><span><span style='background: rgba(100,116,139,0.2); color: #94a3b8; padding: 1px 6px; border-radius: 4px; font-size: 0.75rem;'>{e.get('matricule','')}</span> <strong style='color: #e2e8f0;'>{e.get('prenom','')} {e.get('nom','')}</strong></span><span style='color: #64748b; font-size: 0.85rem;'>{e.get('email','')}</span></div>", unsafe_allow_html=True)
        else:
            st.info("Aucun étudiant.")

    with c2:
        st.markdown("<h5 style='color: #e2e8f0;'>⚡ Actions rapides</h5>", unsafe_allow_html=True)
        actions = [
            ("👤 Créer un étudiant", "head_etudiants", "Ajouter un étudiant au département"),
            ("📢 Publier une annonce", "head_annonces", "Choisir la visibilité"),
            ("📝 Ajouter une note", "head_notes", "Saisir une note pour un étudiant"),
            ("📚 Inscrire un étudiant", "head_inscriptions", "Inscrire à un cours"),
        ]
        for label, page, desc in actions:
            if st.button(f"{label}  →", use_container_width=True):
                st.session_state.page = page
                st.rerun()

# ─── ÉTUDIANTS ───

def render_etudiants():
    st.markdown("<h2 style='color: #e2e8f0;'>👥 Gestion des étudiants</h2>", unsafe_allow_html=True)
    dept = get_dept()
    tab1, tab2 = st.tabs(["📋 Liste", "➕ Ajouter"])

    with tab1:
        etudiants = list(get_collection("users").find({"role": "student", "departement": dept}).sort("nom", 1))
        if etudiants:
            for e in etudiants:
                eid = str(e["_id"])
                c1, c2, c3, c4, c5 = st.columns([1, 2, 2, 1, 1])
                with c1:
                    st.markdown(f"<span style='background: rgba(100,116,139,0.2); color: #94a3b8; padding: 1px 6px; border-radius: 4px; font-size: 0.75rem;'>{e.get('matricule','')}</span>", unsafe_allow_html=True)
                with c2:
                    st.write(f"{e.get('prenom','')} {e.get('nom','')}")
                with c3:
                    st.write(e.get("email", ""))
                with c4:
                    if st.button("✏️", key=f"edit_stu_{eid}"):
                        edit_etudiant_modal(eid)
                with c5:
                    if st.button("🗑️", key=f"del_stu_{eid}"):
                        get_collection("users").delete_one({"_id": ObjectId(eid)})
                        etu = get_collection("etudiants").find_one({"matricule": e.get("matricule", "")})
                        if etu:
                            get_collection("inscriptions").delete_many({"id_etudiant": etu["_id"]})
                            get_collection("notes").delete_many({"id_etudiant": etu["_id"]})
                            get_collection("etudiants").delete_one({"_id": etu["_id"]})
                        st.success("Étudiant supprimé.")
                        st.rerun()
                st.markdown("<hr style='margin: 0; border-color: rgba(255,255,255,0.04);'>", unsafe_allow_html=True)
        else:
            st.info("Aucun étudiant.")

    with tab2:
        create_etudiant()

def edit_etudiant_modal(eid):
    with st.form(f"edit_form_{eid}"):
        user = get_collection("users").find_one({"_id": ObjectId(eid)})
        if not user:
            st.error("Étudiant introuvable.")
            return
        nom = st.text_input("Nom", value=user.get("nom", ""))
        prenom = st.text_input("Prénom", value=user.get("prenom", ""))
        tel = st.text_input("Téléphone", value=user.get("telephone", ""))
        pw = st.text_input("Nouveau mot de passe (laisser vide pour ne pas changer)", type="password")
        if st.form_submit_button("💾 Enregistrer"):
            update = {"nom": nom.strip().upper(), "prenom": prenom.strip().capitalize(), "telephone": tel.strip()}
            if pw.strip():
                if len(pw.strip()) < 4:
                    st.error("Mot de passe trop court (min 4 caractères).")
                    return
                update["password"] = generate_password_hash(pw.strip())
            get_collection("users").update_one({"_id": ObjectId(eid)}, {"$set": update})
            etu = get_collection("etudiants").find_one({"matricule": user.get("matricule", "")})
            if etu:
                get_collection("etudiants").update_one({"_id": etu["_id"]}, {"$set": {"nom": update["nom"], "prenom": update["prenom"], "telephone": update["telephone"]}})
            st.success("Étudiant modifié.")
            st.rerun()

def create_etudiant():
    dept = get_dept()
    prefix_map = {"Informatique": "INF", "Gestion": "GES", "Genie Civil": "GC", "Communication": "COM"}
    prefix = prefix_map.get(dept, "ETU")
    count = get_collection("etudiants").count_documents({"departement": dept}) + 1
    auto_mat = f"{prefix}{count:04d}"

    with st.form("create_student"):
        email = st.text_input("📧 Email")
        pw = st.text_input("🔒 Mot de passe (min 4 car.)", type="password")
        nom = st.text_input("👤 Nom")
        prenom = st.text_input("👤 Prénom")
        matricule = st.text_input("📋 Matricule (laisser vide pour auto)", value=auto_mat)
        tel = st.text_input("📞 Téléphone")
        date_naiss = st.date_input("🎂 Date de naissance", value=date(2000, 1, 1))
        adresse = st.text_input("📍 Adresse", value=f"Adresse de {prenom} {nom}" if prenom and nom else "")

        if st.form_submit_button("✅ Créer l'étudiant", use_container_width=True, type="primary"):
            if not email or not pw or not nom or not prenom:
                st.error("Veuillez remplir les champs obligatoires.")
                return
            if len(pw) < 4:
                st.error("Mot de passe trop court.")
                return
            if get_collection("users").find_one({"email": email}):
                st.error("Cet email est déjà utilisé.")
                return
            mat = matricule.strip() or auto_mat
            user_doc = {
                "email": email.strip(),
                "password": generate_password_hash(pw.strip()),
                "role": "student", "nom": nom.strip().upper(),
                "prenom": prenom.strip().capitalize(),
                "departement": dept, "matricule": mat, "telephone": tel.strip(),
            }
            user_result = get_collection("users").insert_one(user_doc)
            get_collection("etudiants").insert_one({
                "matricule": mat, "nom": nom.strip().upper(),
                "prenom": prenom.strip().capitalize(), "email": email.strip(),
                "telephone": tel.strip(), "date_naissance": str(date_naiss),
                "adresse": adresse.strip(), "departement": dept,
            })
            st.success(f"Étudiant créé (matricule: {mat}).")
            st.rerun()

# ─── ANNONCES ───

def render_annonces():
    st.markdown("<h2 style='color: #e2e8f0;'>📢 Gestion des annonces</h2>", unsafe_allow_html=True)
    dept = get_dept()
    tab1, tab2 = st.tabs(["📋 Liste", "➕ Créer"])

    with tab1:
        annonces = list(get_collection("annonces").find({"departement": dept}).sort("date_creation", -1))
        if annonces:
            for a in annonces:
                aid = str(a["_id"])
                vis = "🌍 Public" if a.get("visibilite") == "public" else "🏫 Département"
                with st.container():
                    c1, c2 = st.columns([5, 1])
                    with c1:
                        st.markdown(f"<strong style='color: #e2e8f0;'>{a['titre']}</strong> <span style='background: rgba(37,99,235,0.15); color: #60a5fa; padding: 1px 8px; border-radius: 4px; font-size: 0.75rem;'>{vis}</span><br><span style='color: #94a3b8; font-size: 0.85rem;'>{a['contenu'][:200]}</span>", unsafe_allow_html=True)
                    with c2:
                        if st.button("🗑️", key=f"del_ann_{aid}"):
                            get_collection("annonces").delete_one({"_id": ObjectId(aid)})
                            st.success("Annonce supprimée.")
                            st.rerun()
                st.markdown("<hr style='margin: 0; border-color: rgba(255,255,255,0.04);'>", unsafe_allow_html=True)
        else:
            st.info("Aucune annonce.")

    with tab2:
        with st.form("create_annonce"):
            titre = st.text_input("📌 Titre")
            contenu = st.text_area("📝 Contenu", height=150)
            visibilite = st.selectbox("👁️ Visibilité", ["departement", "public"], format_func=lambda x: "🏫 Département" if x == "departement" else "🌍 Public")
            if st.form_submit_button("✅ Publier", use_container_width=True, type="primary"):
                if titre and contenu:
                    get_collection("annonces").insert_one({
                        "titre": titre.strip(), "contenu": contenu.strip(),
                        "departement": dept, "auteur": ObjectId(st.session_state.user.id),
                        "date_creation": str(date.today()), "publie": True, "visibilite": visibilite,
                    })
                    st.success("Annonce publiée.")
                    st.rerun()
                else:
                    st.error("Titre et contenu requis.")

# ─── COURS ───

def render_cours():
    st.markdown("<h2 style='color: #e2e8f0;'>📚 Gestion des cours</h2>", unsafe_allow_html=True)
    dept = get_dept()
    tab1, tab2 = st.tabs(["📋 Liste", "➕ Ajouter"])

    with tab1:
        cours = list(get_collection("cours").find({"departement": dept}).sort("semestre", 1).sort("code_ue", 1))
        if cours:
            for c in cours:
                cid = str(c["_id"])
                with st.container():
                    cols = st.columns([1, 2, 2, 1, 1, 1])
                    with cols[0]:
                        st.markdown(f"<span style='background: rgba(6,182,212,0.15); color: #67e8f9; padding: 1px 6px; border-radius: 4px; font-size: 0.75rem;'>{c['code']}</span>", unsafe_allow_html=True)
                    with cols[1]:
                        st.write(c["intitule"])
                    with cols[2]:
                        st.write(c.get("enseignant", ""))
                    with cols[3]:
                        st.write(f"S{c.get('semestre','S1')} · {c.get('code_ue','U000')}")
                    with cols[4]:
                        st.write(f"Crédit: {c.get('credit',3)}")
                    with cols[5]:
                        if st.button("🗑️", key=f"del_cours_{cid}"):
                            get_collection("cours").delete_one({"_id": ObjectId(cid)})
                            get_collection("inscriptions").delete_many({"id_cours": ObjectId(cid)})
                            get_collection("notes").delete_many({"id_cours": ObjectId(cid)})
                            st.success("Cours supprimé.")
                            st.rerun()
                st.markdown("<hr style='margin: 0; border-color: rgba(255,255,255,0.04);'>", unsafe_allow_html=True)
        else:
            st.info("Aucun cours.")

    with tab2:
        with st.form("create_cours"):
            code = st.text_input("📌 Code du cours (ex: INF101)")
            intitule = st.text_input("📝 Intitulé")
            credit = st.number_input("🎯 Crédit", min_value=1, max_value=10, value=3)
            enseignant = st.text_input("👨‍🏫 Enseignant")
            semestre = st.selectbox("📅 Semestre", SEMESTRES)
            code_ue = st.selectbox("🏷️ UE", UES)
            if st.form_submit_button("✅ Ajouter", use_container_width=True, type="primary"):
                if code and intitule:
                    if get_collection("cours").find_one({"code": code}):
                        st.error("Ce code existe déjà.")
                    else:
                        get_collection("cours").insert_one({
                            "code": code.strip(), "intitule": intitule.strip(),
                            "credit": int(credit), "enseignant": enseignant.strip().title(),
                            "semestre": semestre, "code_ue": code_ue, "departement": dept,
                        })
                        st.success("Cours ajouté.")
                        st.rerun()
                else:
                    st.error("Code et intitulé requis.")

# ─── INSCRIPTIONS ───

def render_inscriptions():
    st.markdown("<h2 style='color: #e2e8f0;'>📝 Gestion des inscriptions</h2>", unsafe_allow_html=True)
    dept = get_dept()
    tab1, tab2 = st.tabs(["📋 Liste", "➕ Ajouter"])

    with tab1:
        etu_ids = [e["_id"] for e in get_collection("etudiants").find({"departement": dept}, {"_id": 1})]
        inscriptions = list(get_collection("inscriptions").find({"id_etudiant": {"$in": etu_ids}}).sort("date_inscription", -1))
        if inscriptions:
            for ins in inscriptions:
                iid = str(ins["_id"])
                etu = get_collection("etudiants").find_one({"_id": ins["id_etudiant"]})
                c = get_collection("cours").find_one({"_id": ins["id_cours"]})
                nom_e = f"{etu['prenom']} {etu['nom']}" if etu else "Inconnu"
                nom_c = c["intitule"] if c else "Inconnu"
                cols = st.columns([3, 3, 2, 1])
                with cols[0]:
                    st.write(nom_e)
                with cols[1]:
                    st.write(nom_c)
                with cols[2]:
                    st.write(ins.get("annee_academique", ""))
                with cols[3]:
                    if st.button("🗑️", key=f"del_ins_{iid}"):
                        get_collection("inscriptions").delete_one({"_id": ObjectId(iid)})
                        st.success("Inscription supprimée.")
                        st.rerun()
                st.markdown("<hr style='margin: 0; border-color: rgba(255,255,255,0.04);'>", unsafe_allow_html=True)
        else:
            st.info("Aucune inscription.")

    with tab2:
        etudiants = list(get_collection("etudiants").find({"departement": dept}).sort("nom", 1))
        cours = list(get_collection("cours").find({"departement": dept}).sort("intitule", 1))
        if not etudiants or not cours:
            st.warning("Vous devez d'abord créer des étudiants et des cours.")
            return
        with st.form("create_inscription"):
            id_etudiant = st.selectbox("🎓 Étudiant", etudiants, format_func=lambda e: f"{e['prenom']} {e['nom']} ({e['matricule']})")
            id_cours = st.selectbox("📚 Cours", cours, format_func=lambda c: f"{c['code']} - {c['intitule']}")
            annee = st.text_input("📅 Année académique", value="2025-2026")
            if st.form_submit_button("✅ Inscrire", use_container_width=True, type="primary"):
                get_collection("inscriptions").insert_one({
                    "id_etudiant": id_etudiant["_id"],
                    "id_cours": id_cours["_id"],
                    "annee_academique": annee.strip(),
                    "date_inscription": str(date.today()),
                })
                st.success("Inscription ajoutée.")
                st.rerun()

# ─── NOTES ───

def render_notes():
    st.markdown("<h2 style='color: #e2e8f0;'>📋 Gestion des notes</h2>", unsafe_allow_html=True)
    dept = get_dept()
    tabs = st.tabs(["📋 Toutes les notes", "➕ Ajouter", "📅 Par semestre"])

    with tabs[0]:
        etu_ids = [e["_id"] for e in get_collection("etudiants").find({"departement": dept}, {"_id": 1})]
        notes = list(get_collection("notes").find({"id_etudiant": {"$in": etu_ids}}).sort("date_evaluation", -1))
        if notes:
            for n in notes:
                nid = str(n["_id"])
                etu = get_collection("etudiants").find_one({"_id": n["id_etudiant"]})
                c = get_collection("cours").find_one({"_id": n["id_cours"]})
                nom_e = f"{etu['prenom']} {etu['nom']}" if etu else "Inconnu"
                nom_c = c["intitule"] if c else "Inconnu"
                cols = st.columns([2, 2, 1, 1, 1])
                with cols[0]:
                    st.write(nom_e)
                with cols[1]:
                    st.write(nom_c)
                with cols[2]:
                    st.markdown(f"<span style='color: {'#22c55e' if n['valeur'] >= 16 else '#3b82f6' if n['valeur'] >= 12 else '#f59e0b' if n['valeur'] >= 10 else '#ef4444'}; font-weight: 600;'>{n['valeur']}/20</span>", unsafe_allow_html=True)
                with cols[3]:
                    st.write(n.get("type_note", ""))
                with cols[4]:
                    if st.button("🗑️", key=f"del_note_{nid}"):
                        get_collection("notes").delete_one({"_id": ObjectId(nid)})
                        st.success("Note supprimée.")
                        st.rerun()
                st.markdown("<hr style='margin: 0; border-color: rgba(255,255,255,0.04);'>", unsafe_allow_html=True)
        else:
            st.info("Aucune note.")

    with tabs[1]:
        etudiants = list(get_collection("etudiants").find({"departement": dept}).sort("nom", 1))
        cours = list(get_collection("cours").find({"departement": dept}).sort("intitule", 1))
        if not etudiants or not cours:
            st.warning("Créez d'abord des étudiants et des cours.")
            return
        with st.form("add_note"):
            id_etudiant = st.selectbox("🎓 Étudiant", etudiants, format_func=lambda e: f"{e['prenom']} {e['nom']} ({e['matricule']})")
            id_cours = st.selectbox("📚 Cours", cours, format_func=lambda c: f"{c['code']} - {c['intitule']}")
            valeur = st.number_input("🎯 Note (0-20)", min_value=0.0, max_value=20.0, value=10.0, step=0.25)
            type_note = st.selectbox("📋 Type", ["cc", "examen", "devoir", "tp"])
            date_eval = st.date_input("📅 Date", value=date.today())
            if st.form_submit_button("✅ Ajouter", use_container_width=True, type="primary"):
                get_collection("notes").insert_one({
                    "id_etudiant": id_etudiant["_id"],
                    "id_cours": id_cours["_id"],
                    "valeur": valeur,
                    "type_note": type_note,
                    "date_evaluation": str(date_eval),
                })
                st.success("Note ajoutée.")
                st.rerun()

    with tabs[2]:
        semestre = st.selectbox("📅 Choisir un semestre", SEMESTRES)
        etudiants = list(get_collection("etudiants").find({"departement": dept}).sort("nom", 1))
        cours_sem = list(get_collection("cours").find({"departement": dept, "semestre": semestre}).sort("code_ue", 1))
        if not etudiants or not cours_sem:
            st.info(f"Aucun étudiant ou cours pour le {semestre}.")
            return
        st.markdown(f"<h5 style='color: #e2e8f0;'>Saisie des notes — Semestre {semestre}</h5>", unsafe_allow_html=True)

        for etu in etudiants:
            st.markdown(f"<div style='background: #1e293b; border-radius: 8px; padding: 0.75rem 1rem; margin: 0.5rem 0;'><strong style='color: #e2e8f0;'>{etu['prenom']} {etu['nom']}</strong> <span style='color: #64748b; font-size: 0.85rem;'>({etu['matricule']})</span></div>", unsafe_allow_html=True)
            cols = st.columns(len(cours_sem) * 2)
            for i, c in enumerate(cours_sem):
                idx = i * 2
                with cols[idx]:
                    cc = get_collection("notes").find_one({"id_etudiant": etu["_id"], "id_cours": c["_id"], "type_note": "cc"})
                    cc_val = cc["valeur"] if cc else None
                    new_cc = st.number_input(f"CC {c['code']}", min_value=0.0, max_value=20.0, value=cc_val or 0.0, step=0.25, key=f"cc_{etu['_id']}_{c['_id']}")
                with cols[idx + 1]:
                    ex = get_collection("notes").find_one({"id_etudiant": etu["_id"], "id_cours": c["_id"], "type_note": "examen"})
                    ex_val = ex["valeur"] if ex else None
                    new_ex = st.number_input(f"Exam {c['code']}", min_value=0.0, max_value=20.0, value=ex_val or 0.0, step=0.25, key=f"ex_{etu['_id']}_{c['_id']}")

            if st.button(f"💾 Enregistrer {etu['prenom']} {etu['nom']}", key=f"save_{etu['_id']}"):
                for c in cours_sem:
                    cc_key = f"cc_{etu['_id']}_{c['_id']}"
                    ex_key = f"ex_{etu['_id']}_{c['_id']}"
                    if cc_key in st.session_state and st.session_state[cc_key] > 0:
                        val = st.session_state[cc_key]
                        existing = get_collection("notes").find_one({"id_etudiant": etu["_id"], "id_cours": c["_id"], "type_note": "cc"})
                        if existing:
                            get_collection("notes").update_one({"_id": existing["_id"]}, {"$set": {"valeur": val}})
                        else:
                            get_collection("notes").insert_one({"id_etudiant": etu["_id"], "id_cours": c["_id"], "valeur": val, "type_note": "cc", "date_evaluation": str(date.today())})
                    if ex_key in st.session_state and st.session_state[ex_key] > 0:
                        val = st.session_state[ex_key]
                        existing = get_collection("notes").find_one({"id_etudiant": etu["_id"], "id_cours": c["_id"], "type_note": "examen"})
                        if existing:
                            get_collection("notes").update_one({"_id": existing["_id"]}, {"$set": {"valeur": val}})
                        else:
                            get_collection("notes").insert_one({"id_etudiant": etu["_id"], "id_cours": c["_id"], "valeur": val, "type_note": "examen", "date_evaluation": str(date.today())})
                st.success(f"Notes enregistrées pour {etu['prenom']} {etu['nom']}.")
                st.rerun()

# ─── CHEFS ───

def render_chefs():
    st.markdown("<h2 style='color: #e2e8f0;'>👑 Gestion des chefs</h2>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["📋 Liste", "➕ Ajouter"])

    with tab1:
        chefs = list(get_collection("users").find({"role": "head"}).sort("departement", 1))
        if chefs:
            for c in chefs:
                cid = str(c["_id"])
                cols = st.columns([2, 2, 2, 1, 1])
                with cols[0]:
                    st.write(f"{c.get('prenom','')} {c.get('nom','')}")
                with cols[1]:
                    st.write(c.get("email", ""))
                with cols[2]:
                    st.write(c.get("departement", ""))
                with cols[3]:
                    if st.button("✏️", key=f"edit_chef_{cid}"):
                        edit_chef_modal(cid)
                with cols[4]:
                    if str(c["_id"]) != st.session_state.user.id:
                        if st.button("🗑️", key=f"del_chef_{cid}"):
                            get_collection("users").delete_one({"_id": ObjectId(cid)})
                            st.success("Chef supprimé.")
                            st.rerun()
                st.markdown("<hr style='margin: 0; border-color: rgba(255,255,255,0.04);'>", unsafe_allow_html=True)
        else:
            st.info("Aucun chef.")

    with tab2:
        with st.form("create_chef"):
            email = st.text_input("📧 Email")
            pw = st.text_input("🔒 Mot de passe (min 4 car.)", type="password")
            nom = st.text_input("👤 Nom")
            prenom = st.text_input("👤 Prénom")
            departement = st.selectbox("🏫 Département", DEPARTEMENTS)
            tel = st.text_input("📞 Téléphone")
            if st.form_submit_button("✅ Ajouter", use_container_width=True, type="primary"):
                if not email or not pw or not nom or not prenom:
                    st.error("Champs obligatoires.")
                    return
                if len(pw) < 4:
                    st.error("Mot de passe trop court.")
                    return
                if get_collection("users").find_one({"email": email}):
                    st.error("Email déjà utilisé.")
                    return
                if get_collection("users").find_one({"role": "head", "departement": departement}):
                    st.error(f"Un chef existe déjà pour {departement}.")
                    return
                prefix_map = {"Informatique": "CHEF-INF", "Gestion": "CHEF-GES", "Genie Civil": "CHEF-GC", "Communication": "CHEF-COM"}
                get_collection("users").insert_one({
                    "email": email.strip(), "password": generate_password_hash(pw.strip()),
                    "role": "head", "nom": nom.strip().upper(),
                    "prenom": prenom.strip().capitalize(),
                    "departement": departement, "matricule": prefix_map.get(departement, "CHEF"),
                    "telephone": tel.strip(),
                })
                st.success("Chef ajouté.")
                st.rerun()

def edit_chef_modal(cid):
    with st.form(f"edit_chef_{cid}"):
        chef = get_collection("users").find_one({"_id": ObjectId(cid)})
        if not chef:
            st.error("Chef introuvable.")
            return
        nom = st.text_input("Nom", value=chef.get("nom", ""))
        prenom = st.text_input("Prénom", value=chef.get("prenom", ""))
        departement = st.selectbox("Département", DEPARTEMENTS, index=DEPARTEMENTS.index(chef.get("departement", "Informatique")))
        tel = st.text_input("Téléphone", value=chef.get("telephone", ""))
        pw = st.text_input("Nouveau mot de passe (laisser vide)", type="password")
        if st.form_submit_button("💾 Enregistrer"):
            if get_collection("users").find_one({"role": "head", "departement": departement, "_id": {"$ne": ObjectId(cid)}}):
                st.error(f"Le département {departement} a déjà un chef.")
                return
            update = {
                "nom": nom.strip().upper(), "prenom": prenom.strip().capitalize(),
                "departement": departement, "telephone": tel.strip(),
            }
            if pw.strip():
                if len(pw.strip()) < 4:
                    st.error("Mot de passe trop court.")
                    return
                update["password"] = generate_password_hash(pw.strip())
            prefix_map = {"Informatique": "CHEF-INF", "Gestion": "CHEF-GES", "Genie Civil": "CHEF-GC", "Communication": "CHEF-COM"}
            update["matricule"] = prefix_map.get(departement, "CHEF")
            get_collection("users").update_one({"_id": ObjectId(cid)}, {"$set": update})
            st.success("Chef modifié.")
            st.rerun()

# ─── MESSAGES ───

def render_messages():
    st.markdown("<h2 style='color: #e2e8f0;'>💬 Messagerie</h2>", unsafe_allow_html=True)
    chef_id = ObjectId(st.session_state.user.id)
    pipeline = [
        {"$match": {"id_chef": chef_id}},
        {"$sort": {"date_envoi": -1}},
        {"$group": {
            "_id": "$id_etudiant",
            "dernier_message": {"$first": "$contenu"},
            "dernier_date": {"$first": "$date_envoi"},
            "non_lus": {"$sum": {"$cond": [{"$and": [{"$eq": ["$lu", False]}, {"$eq": ["$expediteur", "etudiant"]}]}, 1, 0]}},
        }},
        {"$sort": {"dernier_date": -1}},
    ]
    conversations = list(get_collection("messages").aggregate(pipeline))

    if conversations:
        for conv in conversations:
            etu = get_collection("etudiants").find_one({"_id": conv["_id"]})
            nom = f"{etu['prenom']} {etu['nom']}" if etu else "Inconnu"
            mat = etu["matricule"] if etu else ""
            non_lus = conv.get("non_lus", 0)
            badge = f" <span style='background: #ef4444; color: #fff; padding: 1px 6px; border-radius: 10px; font-size: 0.7rem;'>{non_lus} nouveau(x)</span>" if non_lus else ""
            cols = st.columns([3, 1])
            with cols[0]:
                st.markdown(f"<div style='background: #1e293b; border-radius: 8px; padding: 0.75rem 1rem; margin-bottom: 0.5rem; cursor: pointer;'><strong style='color: #e2e8f0;'>{nom}</strong>{badge}<br><span style='color: #64748b; font-size: 0.85rem;'>{mat} · {conv.get('dernier_message', '')[:80]}</span></div>", unsafe_allow_html=True)
            with cols[1]:
                if st.button(f"💬 Ouvrir {nom}", key=f"conv_{conv['_id']}"):
                    show_conversation(conv["_id"])
    else:
        st.info("Aucune conversation.")

def show_conversation(id_etu):
    chef_id = ObjectId(st.session_state.user.id)
    messages = list(get_collection("messages").find({
        "id_etudiant": id_etu, "id_chef": chef_id
    }).sort("date_envoi", 1))

    get_collection("messages").update_many(
        {"id_etudiant": id_etu, "id_chef": chef_id, "expediteur": "etudiant", "lu": False},
        {"$set": {"lu": True}},
    )

    etu = get_collection("etudiants").find_one({"_id": id_etu})
    nom = f"{etu['prenom']} {etu['nom']}" if etu else "Étudiant"

    st.markdown(f"<h5 style='color: #e2e8f0;'>💬 {nom}</h5>", unsafe_allow_html=True)

    for m in messages:
        is_chef = m.get("expediteur") == "chef"
        align = "right" if is_chef else "left"
        bg = "rgba(245,158,11,0.2)" if is_chef else "rgba(255,255,255,0.06)"
        color = "#e2e8f0" if is_chef else "#94a3b8"
        st.markdown(f"<div style='text-align: {align}; margin-bottom: 0.5rem;'><div style='display: inline-block; background: {bg}; color: {color}; padding: 0.5rem 1rem; border-radius: 12px; max-width: 70%; font-size: 0.9rem;'>{m['contenu']}</div></div>", unsafe_allow_html=True)

    with st.form("reply_form"):
        contenu = st.text_area("Votre réponse", placeholder="Écrivez votre réponse...", height=100)
        if st.form_submit_button("📤 Envoyer", use_container_width=True, type="primary"):
            if contenu.strip():
                get_collection("messages").insert_one({
                    "id_etudiant": id_etu,
                    "id_chef": chef_id,
                    "expediteur": "chef",
                    "contenu": contenu.strip(),
                    "date_envoi": datetime.now(),
                    "lu": True,
                })
                st.success("Réponse envoyée.")
                st.rerun()
            else:
                st.error("Message vide.")

# ─── MOYENNES ───

def render_moyennes():
    st.markdown("<h2 style='color: #e2e8f0;'>📈 Moyennes des étudiants</h2>", unsafe_allow_html=True)
    dept = get_dept()
    etu_ids = [e["_id"] for e in get_collection("etudiants").find({"departement": dept}, {"_id": 1})]
    pipeline = [
        {"$match": {"id_etudiant": {"$in": etu_ids}}},
        {"$group": {"_id": "$id_etudiant", "moyenne": {"$avg": "$valeur"}, "nb_notes": {"$sum": 1}}},
        {"$sort": {"moyenne": -1}},
    ]
    resultats = list(get_collection("notes").aggregate(pipeline))
    if resultats:
        for r in resultats:
            etu = get_collection("etudiants").find_one({"_id": r["_id"]})
            nom = f"{etu['prenom']} {etu['nom']}" if etu else "Inconnu"
            moy = round(r["moyenne"], 2)
            color = "#22c55e" if moy >= 16 else "#3b82f6" if moy >= 12 else "#f59e0b" if moy >= 10 else "#ef4444"
            st.markdown(f"<div style='display: flex; justify-content: space-between; background: #1e293b; border-radius: 8px; padding: 0.75rem 1rem; margin-bottom: 0.5rem;'><span><strong style='color: #e2e8f0;'>{nom}</strong> <span style='color: #64748b; font-size: 0.85rem;'>({r['nb_notes']} notes)</span></span><span style='color: {color}; font-weight: 700; font-size: 1.1rem;'>{moy}/20</span></div>", unsafe_allow_html=True)
    else:
        st.info("Aucune donnée.")

# ─── PROFIL ───

def render_profile():
    st.markdown("<h2 style='color: #e2e8f0;'>⚙️ Mon profil</h2>", unsafe_allow_html=True)
    user = st.session_state.user
    with st.form("profile_form"):
        nom = st.text_input("Nom", value=user.user_data.get("nom", ""))
        prenom = st.text_input("Prénom", value=user.user_data.get("prenom", ""))
        new_pw = st.text_input("Nouveau mot de passe", type="password", placeholder="Laisser vide pour ne pas changer")
        confirm_pw = st.text_input("Confirmer le mot de passe", type="password", placeholder="Confirmer")
        if st.form_submit_button("💾 Mettre à jour", use_container_width=True, type="primary"):
            if nom.strip() and prenom.strip():
                get_collection("users").update_one(
                    {"_id": ObjectId(user.id)},
                    {"$set": {"nom": nom.strip().upper(), "prenom": prenom.strip().capitalize()}},
                )
            if new_pw:
                if new_pw == confirm_pw:
                    get_collection("users").update_one(
                        {"_id": ObjectId(user.id)},
                        {"$set": {"password": generate_password_hash(new_pw)}},
                    )
                    st.success("Mot de passe modifié.")
                else:
                    st.error("Les mots de passe ne correspondent pas.")
                    return
            st.success("Profil mis à jour.")
            st.rerun()
