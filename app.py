import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from bson.objectid import ObjectId
from bson.errors import InvalidId
from werkzeug.security import generate_password_hash, check_password_hash
from config import SECRET_KEY
from db import connect, disconnect, get_collection

app = Flask(__name__)
app.secret_key = SECRET_KEY

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "public_login"

DEPARTEMENTS = ["Informatique", "Gestion", "Genie Civil", "Communication"]
SEMESTRES = ["S1", "S2", "S3", "S4"]
UES = ["U001", "U002", "U003", "U004", "U005"]

class User(UserMixin):
    def __init__(self, user_data):
        self.user_data = user_data
        self.id = str(user_data["_id"])

    def get_role(self):
        return self.user_data.get("role")

    def get_departement(self):
        return self.user_data.get("departement")

    def get_nom_complet(self):
        return f"{self.user_data.get('prenom', '')} {self.user_data.get('nom', '')}"

    def get_matricule(self):
        return self.user_data.get("matricule", "")

@login_manager.user_loader
def load_user(user_id):
    user_data = get_collection("users").find_one({"_id": ObjectId(user_id)})
    return User(user_data) if user_data else None

@app.before_request
def before_request():
    connect()

@app.teardown_request
def teardown_request(exception=None):
    disconnect()

# --- Helpers ---
def get_head_departement():
    if current_user.is_authenticated and current_user.get_role() == "head":
        return current_user.get_departement()
    return None

# ====================== INTERFACE PUBLIQUE ======================

@app.route("/")
def public_index():
    annonces = list(get_collection("annonces").find({"publie": True, "visibilite": "public"}).sort("date_creation", -1).limit(5))
    for a in annonces:
        a["_id"] = str(a["_id"])
        chef = get_collection("users").find_one({"_id": ObjectId(a["auteur"])})
        a["auteur_nom"] = f"{chef['prenom']} {chef['nom']}" if chef else "Inconnu"
    dept_stats = {}
    for d in DEPARTEMENTS:
        dept_stats[d] = get_collection("users").count_documents({"role": "student", "departement": d})
    return render_template("public/index.html", annonces=annonces, dept_stats=dept_stats, departements=DEPARTEMENTS)

@app.route("/public/annonces")
def public_annonces():
    annonces = list(get_collection("annonces").find({"publie": True, "visibilite": "public"}).sort("date_creation", -1))
    for a in annonces:
        a["_id"] = str(a["_id"])
        chef = get_collection("users").find_one({"_id": ObjectId(a["auteur"])})
        a["auteur_nom"] = f"{chef['prenom']} {chef['nom']}" if chef else "Inconnu"
    return render_template("public/annonces.html", annonces=annonces)

@app.route("/login", methods=["GET", "POST"])
def public_login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard_redirect"))
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        user_data = get_collection("users").find_one({"email": email})
        if user_data and check_password_hash(user_data["password"], password):
            user = User(user_data)
            login_user(user)
            flash(f"Bienvenue, {user.get_nom_complet()} !", "success")
            return redirect(url_for("dashboard_redirect"))
        flash("Email ou mot de passe incorrect.", "danger")
    return render_template("public/login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Vous êtes déconnecté.", "info")
    return redirect(url_for("public_index"))

@app.route("/dashboard")
@login_required
def dashboard_redirect():
    if current_user.get_role() == "head":
        return redirect(url_for("head_dashboard"))
    elif current_user.get_role() == "student":
        return redirect(url_for("student_dashboard"))
    return redirect(url_for("public_index"))

# ====================== INTERFACE ÉTUDIANT ======================

@app.route("/etudiant/dashboard")
@login_required
def student_dashboard():
    if current_user.get_role() != "student":
        flash("Accès réservé aux étudiants.", "danger")
        return redirect(url_for("public_index"))
    matricule = current_user.get_matricule()
    etu = get_collection("etudiants").find_one({"matricule": matricule})
    stats_etudiant = {
        "cours": get_collection("inscriptions").count_documents({"id_etudiant": etu["_id"]}) if etu else 0,
        "notes": get_collection("notes").count_documents({"id_etudiant": etu["_id"]}) if etu else 0,
    }
    if etu:
        pipeline = [{"$match": {"id_etudiant": etu["_id"]}}, {"$group": {"_id": None, "moyenne": {"$avg": "$valeur"}}}]
        result = list(get_collection("notes").aggregate(pipeline))
        stats_etudiant["moyenne"] = round(result[0]["moyenne"], 2) if result else None
    else:
        stats_etudiant["moyenne"] = None
    dept = current_user.get_departement()
    annonces = list(get_collection("annonces").find({"departement": dept, "publie": True}).sort("date_creation", -1).limit(5))
    for a in annonces:
        a["_id"] = str(a["_id"])
        chef = get_collection("users").find_one({"_id": ObjectId(a["auteur"])})
        a["auteur_nom"] = f"{chef['prenom']} {chef['nom']}" if chef else "Inconnu"
    return render_template("student/dashboard.html", user=current_user.user_data, stats=stats_etudiant, annonces=annonces)

@app.route("/etudiant/notes")
@login_required
def student_notes():
    if current_user.get_role() != "student":
        flash("Accès réservé aux étudiants.", "danger")
        return redirect(url_for("public_index"))
    matricule = current_user.get_matricule()
    etu = get_collection("etudiants").find_one({"matricule": matricule})
    if not etu:
        flash("Profil étudiant introuvable.", "danger")
        return redirect(url_for("student_dashboard"))
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
                    "intitule": c["intitule"],
                    "code": c["code"],
                    "enseignant": c.get("enseignant", ""),
                    "coeff": c.get("credit", 3),
                    "cc": None,
                    "examen": None,
                }
            cours_map[sem][ue][ntype] = n["valeur"]
    semestres = []
    for sem in SEMESTRES:
        if sem in cours_map:
            ues_list = []
            total_coeff = 0
            somme_ponderee = 0
            for ue in UES:
                if ue in cours_map[sem]:
                    d = cours_map[sem][ue]
                    cc = d["cc"]
                    examen = d["examen"]
                    vals = [v for v in (cc, examen) if v is not None]
                    moy = round(sum(vals) / len(vals), 2) if vals else None
                    coeff = d["coeff"]
                    ues_list.append({
                        "code_ue": ue,
                        "code": d["code"],
                        "intitule": d["intitule"],
                        "enseignant": d["enseignant"],
                        "cc": cc,
                        "examen": examen,
                        "moyenne": moy,
                        "coeff": coeff,
                    })
                    if moy is not None:
                        total_coeff += coeff
                        somme_ponderee += moy * coeff
            moyenne_semestre = round(somme_ponderee / total_coeff, 2) if total_coeff > 0 else None
            semestres.append({
                "semestre": sem,
                "ues": ues_list,
                "moyenne": moyenne_semestre,
            })
    return render_template("student/notes.html", semestres=semestres)

@app.route("/etudiant/cours")
@login_required
def student_cours():
    if current_user.get_role() != "student":
        flash("Accès réservé aux étudiants.", "danger")
        return redirect(url_for("public_index"))
    matricule = current_user.get_matricule()
    etu = get_collection("etudiants").find_one({"matricule": matricule})
    if not etu:
        flash("Profil étudiant introuvable.", "danger")
        return redirect(url_for("student_dashboard"))
    inscriptions = list(get_collection("inscriptions").find({"id_etudiant": etu["_id"]}))
    cours_list = []
    for ins in inscriptions:
        c = get_collection("cours").find_one({"_id": ins["id_cours"]})
        if c:
            c["_id"] = str(c["_id"])
            c["annee_academique"] = ins["annee_academique"]
            c["date_inscription"] = ins["date_inscription"]
            cours_list.append(c)
    return render_template("student/cours.html", cours=cours_list)

@app.route("/etudiant/annonces")
@login_required
def student_annonces():
    if current_user.get_role() != "student":
        flash("Accès réservé aux étudiants.", "danger")
        return redirect(url_for("public_index"))
    dept = current_user.get_departement()
    annonces = list(get_collection("annonces").find({"departement": dept, "publie": True}).sort("date_creation", -1))
    for a in annonces:
        a["_id"] = str(a["_id"])
        chef = get_collection("users").find_one({"_id": ObjectId(a["auteur"])})
        a["auteur_nom"] = f"{chef['prenom']} {chef['nom']}" if chef else "Inconnu"
    return render_template("student/annonces.html", annonces=annonces, departement=dept)

# --- Messagerie Étudiant (↔ Chef) ---
@app.route("/etudiant/messages")
@login_required
def student_messages():
    if current_user.get_role() != "student":
        flash("Accès réservé aux étudiants.", "danger")
        return redirect(url_for("public_index"))
    matricule = current_user.get_matricule()
    etu = get_collection("etudiants").find_one({"matricule": matricule})
    if not etu:
        flash("Profil étudiant introuvable.", "danger")
        return redirect(url_for("student_dashboard"))
    id_etu = etu["_id"]
    dept = current_user.get_departement()
    chef = get_collection("users").find_one({"role": "head", "departement": dept})
    chef_id = chef["_id"] if chef else None
    messages = list(get_collection("messages").find({
        "$or": [
            {"id_etudiant": id_etu, "id_chef": chef_id},
        ]
    }).sort("date_envoi", 1))
    for m in messages:
        m["_id"] = str(m["_id"])
    chef_nom = f"{chef['prenom']} {chef['nom']}" if chef else "Chef de département"
    return render_template("student/messages.html", messages=messages, chef_nom=chef_nom)

@app.route("/etudiant/messages/envoyer", methods=["POST"])
@login_required
def student_message_send():
    if current_user.get_role() != "student":
        flash("Accès refusé.", "danger")
        return redirect(url_for("public_index"))
    from datetime import datetime
    matricule = current_user.get_matricule()
    etu = get_collection("etudiants").find_one({"matricule": matricule})
    if not etu:
        flash("Profil étudiant introuvable.", "danger")
        return redirect(url_for("student_dashboard"))
    dept = current_user.get_departement()
    chef = get_collection("users").find_one({"role": "head", "departement": dept})
    if not chef:
        flash("Aucun chef de département trouvé.", "danger")
        return redirect(url_for("student_messages"))
    contenu = request.form.get("contenu", "").strip()
    if not contenu:
        flash("Le message ne peut pas être vide.", "danger")
        return redirect(url_for("student_messages"))
    get_collection("messages").insert_one({
        "id_etudiant": etu["_id"],
        "id_chef": chef["_id"],
        "expediteur": "etudiant",
        "contenu": contenu,
        "date_envoi": datetime.now(),
        "lu": False,
    })
    flash("Message envoyé au chef de département.", "success")
    return redirect(url_for("student_messages"))

# ====================== INTERFACE CHEF DÉPARTEMENT ======================

@app.route("/chef/dashboard")
@login_required
def head_dashboard():
    if current_user.get_role() != "head":
        flash("Accès réservé aux chefs de département.", "danger")
        return redirect(url_for("public_index"))
    dept = current_user.get_departement()
    stats = {
        "etudiants": get_collection("users").count_documents({"role": "student", "departement": dept}),
        "annonces": get_collection("annonces").count_documents({"departement": dept}),
        "cours": get_collection("cours").count_documents({}),
    }
    etudiants_recents = list(get_collection("users").find({"role": "student", "departement": dept}).sort("_id", -1).limit(5))
    return render_template("head/dashboard.html", stats=stats, etudiants=etudiants_recents, departement=dept)

# --- CRUD Chefs de département ---
@app.route("/chef/chefs")
@login_required
def head_chefs_liste():
    if current_user.get_role() != "head":
        flash("Accès refusé.", "danger")
        return redirect(url_for("public_index"))
    chefs = list(get_collection("users").find({"role": "head"}).sort("departement", 1))
    for c in chefs:
        c["_id"] = str(c["_id"])
    return render_template("head/chefs/liste.html", chefs=chefs)

@app.route("/chef/chefs/ajouter", methods=["GET", "POST"])
@login_required
def head_chefs_ajouter():
    if current_user.get_role() != "head":
        flash("Accès refusé.", "danger")
        return redirect(url_for("public_index"))
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        if get_collection("users").find_one({"email": email}):
            flash("Cet email est déjà utilisé.", "danger")
            return render_template("head/chefs/form.html", data=request.form, departements=DEPARTEMENTS)
        password = request.form.get("password", "").strip()
        if len(password) < 4:
            flash("Le mot de passe doit contenir au moins 4 caractères.", "danger")
            return render_template("head/chefs/form.html", data=request.form, departements=DEPARTEMENTS)
        departement = request.form.get("departement", "").strip()
        if departement not in DEPARTEMENTS:
            flash("Département invalide.", "danger")
            return render_template("head/chefs/form.html", data=request.form, departements=DEPARTEMENTS)
        existing = get_collection("users").find_one({"role": "head", "departement": departement})
        if existing:
            flash(f"Un chef est déjà assigné au département {departement}.", "danger")
            return render_template("head/chefs/form.html", data=request.form, departements=DEPARTEMENTS)
        prefix_map = {"Informatique": "CHEF-INF", "Gestion": "CHEF-GES", "Genie Civil": "CHEF-GC", "Communication": "CHEF-COM"}
        get_collection("users").insert_one({
            "email": email,
            "password": generate_password_hash(password),
            "role": "head",
            "nom": request.form.get("nom", "").strip().upper(),
            "prenom": request.form.get("prenom", "").strip().capitalize(),
            "departement": departement,
            "matricule": prefix_map.get(departement, "CHEF"),
            "telephone": request.form.get("telephone", "").strip(),
        })
        flash("Chef de département ajouté avec succès.", "success")
        return redirect(url_for("head_chefs_liste"))
    return render_template("head/chefs/form.html", data=None, departements=DEPARTEMENTS)

@app.route("/chef/chefs/<id>/modifier", methods=["GET", "POST"])
@login_required
def head_chefs_modifier(id):
    if current_user.get_role() != "head":
        flash("Accès refusé.", "danger")
        return redirect(url_for("public_index"))
    try:
        chef = get_collection("users").find_one({"_id": ObjectId(id)})
    except InvalidId:
        flash("ID invalide.", "danger")
        return redirect(url_for("head_chefs_liste"))
    if not chef or chef.get("role") != "head":
        flash("Chef introuvable.", "danger")
        return redirect(url_for("head_chefs_liste"))
    if request.method == "POST":
        departement = request.form.get("departement", "").strip()
        if departement not in DEPARTEMENTS:
            flash("Département invalide.", "danger")
            return render_template("head/chefs/form.html", data=request.form, departements=DEPARTEMENTS, chef=chef)
        existing = get_collection("users").find_one({"role": "head", "departement": departement, "_id": {"$ne": ObjectId(id)}})
        if existing:
            flash(f"Le département {departement} a déjà un chef.", "danger")
            return render_template("head/chefs/form.html", data=request.form, departements=DEPARTEMENTS, chef=chef)
        update = {
            "nom": request.form.get("nom", "").strip().upper(),
            "prenom": request.form.get("prenom", "").strip().capitalize(),
            "departement": departement,
            "telephone": request.form.get("telephone", "").strip(),
        }
        new_pw = request.form.get("password", "").strip()
        if new_pw:
            if len(new_pw) < 4:
                flash("Le mot de passe doit contenir au moins 4 caractères.", "danger")
                return render_template("head/chefs/form.html", data=request.form, departements=DEPARTEMENTS, chef=chef)
            update["password"] = generate_password_hash(new_pw)
        prefix_map = {"Informatique": "CHEF-INF", "Gestion": "CHEF-GES", "Genie Civil": "CHEF-GC", "Communication": "CHEF-COM"}
        update["matricule"] = prefix_map.get(departement, "CHEF")
        get_collection("users").update_one({"_id": ObjectId(id)}, {"$set": update})
        flash("Chef de département modifié.", "success")
        return redirect(url_for("head_chefs_liste"))
    return render_template("head/chefs/form.html", data=chef, departements=DEPARTEMENTS, chef=chef)

@app.route("/chef/chefs/<id>/supprimer", methods=["POST"])
@login_required
def head_chefs_supprimer(id):
    if current_user.get_role() != "head":
        flash("Accès refusé.", "danger")
        return redirect(url_for("public_index"))
    try:
        chef = get_collection("users").find_one({"_id": ObjectId(id)})
        if chef and chef.get("role") == "head":
            if str(chef["_id"]) == current_user.id:
                flash("Vous ne pouvez pas supprimer votre propre compte.", "danger")
                return redirect(url_for("head_chefs_liste"))
            get_collection("users").delete_one({"_id": ObjectId(id)})
            flash("Chef de département supprimé.", "success")
    except InvalidId:
        flash("ID invalide.", "danger")
    return redirect(url_for("head_chefs_liste"))

@app.route("/chef/etudiants")
@login_required
def head_students():
    if current_user.get_role() != "head":
        flash("Accès refusé.", "danger")
        return redirect(url_for("public_index"))
    dept = current_user.get_departement()
    etudiants = list(get_collection("users").find({"role": "student", "departement": dept}).sort("nom", 1))
    for e in etudiants:
        e["_id"] = str(e["_id"])
    return render_template("head/etudiants/liste.html", etudiants=etudiants, departement=dept)

@app.route("/chef/etudiants/creer", methods=["GET", "POST"])
@login_required
def head_student_create():
    if current_user.get_role() != "head":
        flash("Accès refusé.", "danger")
        return redirect(url_for("public_index"))
    dept = current_user.get_departement()

    prefix_map = {"Informatique": "INF", "Gestion": "GES", "Genie Civil": "GC", "Communication": "COM"}
    prefix = prefix_map.get(dept, "ETU")
    count = get_collection("etudiants").count_documents({"departement": dept}) + 1
    auto_matricule = f"{prefix}{count:04d}"

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        if get_collection("users").find_one({"email": email}):
            flash("Cet email est déjà utilisé.", "danger")
            return render_template("head/etudiants/form.html", departement=dept, data=request.form, auto_matricule=auto_matricule)
        password = request.form.get("password", "").strip()
        if len(password) < 4:
            flash("Le mot de passe doit contenir au moins 4 caractères.", "danger")
            return render_template("head/etudiants/form.html", departement=dept, data=request.form, auto_matricule=auto_matricule)
        nom = request.form.get("nom", "").strip().upper()
        prenom = request.form.get("prenom", "").strip().capitalize()
        matricule = request.form.get("matricule", "").strip()
        if not matricule:
            matricule = auto_matricule
        user_doc = {
            "email": email,
            "password": generate_password_hash(password),
            "role": "student",
            "nom": nom,
            "prenom": prenom,
            "departement": dept,
            "matricule": matricule,
            "telephone": request.form.get("telephone", "").strip(),
        }
        user_result = get_collection("users").insert_one(user_doc)
        etu_doc = {
            "matricule": matricule,
            "nom": nom,
            "prenom": prenom,
            "email": email,
            "telephone": request.form.get("telephone", "").strip(),
            "date_naissance": request.form.get("date_naissance", "").strip(),
            "adresse": request.form.get("adresse", "").strip(),
            "departement": dept,
        }
        get_collection("etudiants").insert_one(etu_doc)
        flash(f"Compte étudiant créé avec succès (matricule: {matricule}).", "success")
        return redirect(url_for("head_students"))
    return render_template("head/etudiants/form.html", departement=dept, data=None, auto_matricule=auto_matricule)

@app.route("/chef/etudiants/<id>/supprimer", methods=["POST"])
@login_required
def head_student_delete(id):
    if current_user.get_role() != "head":
        flash("Accès refusé.", "danger")
        return redirect(url_for("public_index"))
    try:
        user_data = get_collection("users").find_one({"_id": ObjectId(id)})
        if user_data and user_data.get("departement") == current_user.get_departement():
            get_collection("users").delete_one({"_id": ObjectId(id)})
            if user_data.get("matricule"):
                etu = get_collection("etudiants").find_one({"matricule": user_data["matricule"]})
                if etu:
                    get_collection("inscriptions").delete_many({"id_etudiant": etu["_id"]})
                    get_collection("notes").delete_many({"id_etudiant": etu["_id"]})
                    get_collection("etudiants").delete_one({"_id": etu["_id"]})
            flash("Étudiant supprimé.", "success")
    except InvalidId:
        flash("ID invalide.", "danger")
    return redirect(url_for("head_students"))

@app.route("/chef/etudiants/<id>/modifier", methods=["GET", "POST"])
@login_required
def head_student_modify(id):
    if current_user.get_role() != "head":
        flash("Accès refusé.", "danger")
        return redirect(url_for("public_index"))
    dept = current_user.get_departement()
    try:
        user = get_collection("users").find_one({"_id": ObjectId(id)})
    except InvalidId:
        flash("ID invalide.", "danger")
        return redirect(url_for("head_students"))
    if not user or user.get("departement") != dept:
        flash("Étudiant introuvable.", "danger")
        return redirect(url_for("head_students"))
    etu = get_collection("etudiants").find_one({"matricule": user.get("matricule", "")})
    if request.method == "POST":
        nom = request.form.get("nom", "").strip().upper()
        prenom = request.form.get("prenom", "").strip().capitalize()
        update_data = {
            "nom": nom,
            "prenom": prenom,
            "telephone": request.form.get("telephone", "").strip(),
        }
        new_pw = request.form.get("password", "").strip()
        if new_pw:
            if len(new_pw) < 4:
                flash("Le mot de passe doit contenir au moins 4 caractères.", "danger")
                return render_template("head/etudiants/form.html", data=user, departement=dept, auto_matricule=user.get("matricule", ""), edit_mode=True)
            update_data["password"] = generate_password_hash(new_pw)
        get_collection("users").update_one({"_id": ObjectId(id)}, {"$set": update_data})
        if etu:
            get_collection("etudiants").update_one(
                {"_id": etu["_id"]},
                {"$set": {"nom": nom, "prenom": prenom, "telephone": request.form.get("telephone", "").strip()}}
            )
        flash("Étudiant modifié avec succès.", "success")
        return redirect(url_for("head_students"))
    return render_template("head/etudiants/form.html", data=user, departement=dept, auto_matricule=user.get("matricule", ""), edit_mode=True)

@app.route("/chef/annonces")
@login_required
def head_annonces():
    if current_user.get_role() != "head":
        flash("Accès refusé.", "danger")
        return redirect(url_for("public_index"))
    dept = current_user.get_departement()
    annonces = list(get_collection("annonces").find({"departement": dept}).sort("date_creation", -1))
    for a in annonces:
        a["_id"] = str(a["_id"])
    return render_template("head/annonces/liste.html", annonces=annonces, departement=dept)

@app.route("/chef/annonces/creer", methods=["GET", "POST"])
@login_required
def head_annonce_create():
    if current_user.get_role() != "head":
        flash("Accès refusé.", "danger")
        return redirect(url_for("public_index"))
    dept = current_user.get_departement()
    if request.method == "POST":
        from datetime import date
        visibilite = request.form.get("visibilite", "departement")
        doc = {
            "titre": request.form.get("titre", "").strip(),
            "contenu": request.form.get("contenu", "").strip(),
            "departement": dept,
            "auteur": ObjectId(current_user.id),
            "date_creation": str(date.today()),
            "publie": True,
            "visibilite": visibilite,
        }
        get_collection("annonces").insert_one(doc)
        flash("Annonce publiée avec succès.", "success")
        return redirect(url_for("head_annonces"))
    return render_template("head/annonces/form.html", departement=dept)

@app.route("/chef/annonces/<id>/supprimer", methods=["POST"])
@login_required
def head_annonce_delete(id):
    if current_user.get_role() != "head":
        flash("Accès refusé.", "danger")
        return redirect(url_for("public_index"))
    try:
        annonce = get_collection("annonces").find_one({"_id": ObjectId(id)})
        if annonce and annonce.get("departement") == current_user.get_departement():
            get_collection("annonces").delete_one({"_id": ObjectId(id)})
            flash("Annonce supprimée.", "success")
    except InvalidId:
        flash("ID invalide.", "danger")
    return redirect(url_for("head_annonces"))

# --- CRUD Cours (Chef département) ---
@app.route("/chef/cours")
@login_required
def head_cours_liste():
    if current_user.get_role() != "head":
        return redirect(url_for("public_index"))
    cours = list(get_collection("cours").find({"departement": current_user.get_departement()}).sort("semestre", 1).sort("code_ue", 1))
    for c in cours:
        c["_id"] = str(c["_id"])
    return render_template("head/cours/liste.html", cours=cours)

@app.route("/chef/cours/ajouter", methods=["GET", "POST"])
@login_required
def head_cours_ajouter():
    if current_user.get_role() != "head":
        return redirect(url_for("public_index"))
    if request.method == "POST":
        code = request.form.get("code", "").strip()
        if get_collection("cours").find_one({"code": code}):
            flash("Ce code existe déjà.", "danger")
            return render_template("head/cours/form.html", cours=request.form)
        get_collection("cours").insert_one({
            "code": code,
            "intitule": request.form.get("intitule", "").strip(),
            "credit": int(request.form.get("credit", 3)),
            "enseignant": request.form.get("enseignant", "").strip().title(),
            "semestre": request.form.get("semestre", "S1"),
            "code_ue": request.form.get("code_ue", "U001"),
            "departement": current_user.get_departement(),
        })
        flash("Cours ajouté.", "success")
        return redirect(url_for("head_cours_liste"))
    return render_template("head/cours/form.html", cours=None, semestres=SEMESTRES, ues=UES)

@app.route("/chef/cours/<id>/modifier", methods=["GET", "POST"])
@login_required
def head_cours_modifier(id):
    if current_user.get_role() != "head":
        return redirect(url_for("public_index"))
    try:
        cours = get_collection("cours").find_one({"_id": ObjectId(id)})
    except InvalidId:
        flash("ID invalide.", "danger")
        return redirect(url_for("head_cours_liste"))
    if not cours:
        flash("Cours introuvable.", "danger")
        return redirect(url_for("head_cours_liste"))
    if request.method == "POST":
        get_collection("cours").update_one({"_id": ObjectId(id)}, {"$set": {
            "code": request.form.get("code", "").strip(),
            "intitule": request.form.get("intitule", "").strip(),
            "credit": int(request.form.get("credit", 3)),
            "enseignant": request.form.get("enseignant", "").strip().title(),
            "semestre": request.form.get("semestre", "S1"),
            "code_ue": request.form.get("code_ue", "U001"),
        }})
        flash("Cours modifié.", "success")
        return redirect(url_for("head_cours_liste"))
    return render_template("head/cours/form.html", cours=cours, semestres=SEMESTRES, ues=UES)

@app.route("/chef/cours/<id>/supprimer", methods=["POST"])
@login_required
def head_cours_supprimer(id):
    if current_user.get_role() != "head":
        return redirect(url_for("public_index"))
    try:
        get_collection("cours").delete_one({"_id": ObjectId(id)})
        get_collection("inscriptions").delete_many({"id_cours": ObjectId(id)})
        get_collection("notes").delete_many({"id_cours": ObjectId(id)})
        flash("Cours supprimé.", "success")
    except InvalidId:
        flash("ID invalide.", "danger")
    return redirect(url_for("head_cours_liste"))

# --- CRUD Inscriptions (Chef département) ---
@app.route("/chef/inscriptions")
@login_required
def head_inscriptions_liste():
    if current_user.get_role() != "head":
        return redirect(url_for("public_index"))
    dept = current_user.get_departement()
    etu_ids = [e["_id"] for e in get_collection("etudiants").find({"departement": dept}, {"_id": 1})]
    inscriptions = []
    for i in get_collection("inscriptions").find({"id_etudiant": {"$in": etu_ids}}).sort("date_inscription", -1):
        i["_id"] = str(i["_id"])
        i["id_etudiant"] = str(i["id_etudiant"])
        i["id_cours"] = str(i["id_cours"])
        etu = get_collection("etudiants").find_one({"_id": ObjectId(i["id_etudiant"])})
        c = get_collection("cours").find_one({"_id": ObjectId(i["id_cours"])})
        i["etudiant_nom"] = f"{etu['prenom']} {etu['nom']}" if etu else "Inconnu"
        i["cours_intitule"] = c["intitule"] if c else "Inconnu"
        inscriptions.append(i)
    return render_template("head/inscriptions/liste.html", inscriptions=inscriptions)

@app.route("/chef/inscriptions/ajouter", methods=["GET", "POST"])
@login_required
def head_inscriptions_ajouter():
    if current_user.get_role() != "head":
        return redirect(url_for("public_index"))
    if request.method == "POST":
        from datetime import date
        try:
            doc = {
                "id_etudiant": ObjectId(request.form.get("id_etudiant", "").strip()),
                "id_cours": ObjectId(request.form.get("id_cours", "").strip()),
                "annee_academique": request.form.get("annee_academique", "").strip(),
                "date_inscription": str(date.today()),
            }
            get_collection("inscriptions").insert_one(doc)
            flash("Inscription ajoutée.", "success")
            return redirect(url_for("head_inscriptions_liste"))
        except InvalidId:
            flash("ID invalide.", "danger")
    dept = current_user.get_departement()
    etudiants = list(get_collection("etudiants").find({"departement": dept}).sort("nom", 1))
    cours = list(get_collection("cours").find({"departement": dept}).sort("intitule", 1))
    for e in etudiants:
        e["_id"] = str(e["_id"])
    for c in cours:
        c["_id"] = str(c["_id"])
    return render_template("head/inscriptions/form.html", etudiants=etudiants, cours=cours)

@app.route("/chef/inscriptions/<id>/supprimer", methods=["POST"])
@login_required
def head_inscriptions_supprimer(id):
    if current_user.get_role() != "head":
        return redirect(url_for("public_index"))
    try:
        get_collection("inscriptions").delete_one({"_id": ObjectId(id)})
        flash("Inscription supprimée.", "success")
    except InvalidId:
        flash("ID invalide.", "danger")
    return redirect(url_for("head_inscriptions_liste"))

# --- CRUD Notes (Chef département) ---
@app.route("/chef/notes")
@login_required
def head_notes_liste():
    if current_user.get_role() != "head":
        return redirect(url_for("public_index"))
    dept = current_user.get_departement()
    etu_ids = [e["_id"] for e in get_collection("etudiants").find({"departement": dept}, {"_id": 1})]
    notes = []
    for n in get_collection("notes").find({"id_etudiant": {"$in": etu_ids}}).sort("date_evaluation", -1):
        n["_id"] = str(n["_id"])
        n["id_etudiant"] = str(n["id_etudiant"])
        n["id_cours"] = str(n["id_cours"])
        etu = get_collection("etudiants").find_one({"_id": ObjectId(n["id_etudiant"])})
        c = get_collection("cours").find_one({"_id": ObjectId(n["id_cours"])})
        n["etudiant_nom"] = f"{etu['prenom']} {etu['nom']}" if etu else "Inconnu"
        n["cours_intitule"] = c["intitule"] if c else "Inconnu"
        n["semestre"] = c.get("semestre", "S1") if c else "S1"
        n["code_ue"] = c.get("code_ue", "") if c else ""
        n["etudiant_id"] = str(etu["_id"]) if etu else ""
        notes.append(n)
    return render_template("head/note/liste.html", notes=notes)

@app.route("/chef/notes/ajouter", methods=["GET", "POST"])
@login_required
def head_notes_ajouter():
    if current_user.get_role() != "head":
        return redirect(url_for("public_index"))
    if request.method == "POST":
        try:
            valeur = float(request.form.get("valeur", 0))
            if valeur < 0 or valeur > 20:
                flash("Note hors limites (0-20).", "danger")
                return redirect(url_for("head_notes_ajouter"))
            from datetime import date
            doc = {
                "id_etudiant": ObjectId(request.form.get("id_etudiant", "").strip()),
                "id_cours": ObjectId(request.form.get("id_cours", "").strip()),
                "valeur": valeur,
                "type_note": request.form.get("type_note", "examen"),
                "date_evaluation": request.form.get("date_evaluation", str(date.today())),
            }
            get_collection("notes").insert_one(doc)
            flash("Note ajoutée.", "success")
            return redirect(url_for("head_notes_liste"))
        except (InvalidId, ValueError):
            flash("Données invalides.", "danger")
    dept = current_user.get_departement()
    etudiants = list(get_collection("etudiants").find({"departement": dept}).sort("nom", 1))
    cours = list(get_collection("cours").find({"departement": dept}).sort("intitule", 1))
    for e in etudiants:
        e["_id"] = str(e["_id"])
    for c in cours:
        c["_id"] = str(c["_id"])
    return render_template("head/note/form.html", etudiants=etudiants, cours=cours, note=None)

@app.route("/chef/notes/<id>/modifier", methods=["GET", "POST"])
@login_required
def head_notes_modifier(id):
    if current_user.get_role() != "head":
        return redirect(url_for("public_index"))
    try:
        note = get_collection("notes").find_one({"_id": ObjectId(id)})
    except InvalidId:
        flash("ID invalide.", "danger")
        return redirect(url_for("head_notes_liste"))
    if not note:
        flash("Note introuvable.", "danger")
        return redirect(url_for("head_notes_liste"))
    if request.method == "POST":
        try:
            valeur = float(request.form.get("valeur", 0))
            if valeur < 0 or valeur > 20:
                flash("Note hors limites.", "danger")
                return render_template("head/note/form.html", etudiants=[], cours=[], note=note)
            get_collection("notes").update_one({"_id": ObjectId(id)}, {"$set": {"valeur": valeur}})
            flash("Note modifiée.", "success")
            return redirect(url_for("head_notes_liste"))
        except ValueError:
            flash("Valeur invalide.", "danger")
    dept = current_user.get_departement()
    etudiants = list(get_collection("etudiants").find({"departement": dept}).sort("nom", 1))
    cours = list(get_collection("cours").find({"departement": dept}).sort("intitule", 1))
    for e in etudiants:
        e["_id"] = str(e["_id"])
    for c in cours:
        c["_id"] = str(c["_id"])
    return render_template("head/note/form.html", etudiants=etudiants, cours=cours, note=note)

@app.route("/chef/notes/<id>/supprimer", methods=["POST"])
@login_required
def head_notes_supprimer(id):
    if current_user.get_role() != "head":
        return redirect(url_for("public_index"))
    try:
        get_collection("notes").delete_one({"_id": ObjectId(id)})
        flash("Note supprimée.", "success")
    except InvalidId:
        flash("ID invalide.", "danger")
    return redirect(url_for("head_notes_liste"))

@app.route("/chef/notes/semestre/<id_etudiant>")
@login_required
def head_notes_semestre(id_etudiant):
    if current_user.get_role() != "head":
        return redirect(url_for("public_index"))
    try:
        etu = get_collection("etudiants").find_one({"_id": ObjectId(id_etudiant)})
    except InvalidId:
        flash("ID invalide.", "danger")
        return redirect(url_for("head_notes_liste"))
    if not etu:
        flash("Étudiant introuvable.", "danger")
        return redirect(url_for("head_notes_liste"))
    if etu.get("departement") != current_user.get_departement():
        flash("Accès refusé.", "danger")
        return redirect(url_for("head_notes_liste"))
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
                    "intitule": c["intitule"],
                    "code": c["code"],
                    "enseignant": c.get("enseignant", ""),
                    "coeff": c.get("credit", 3),
                    "cc": None,
                    "examen": None,
                }
            cours_map[sem][ue][ntype] = n["valeur"]
    semestres = []
    for sem in SEMESTRES:
        if sem in cours_map:
            ues_list = []
            total_coeff = 0
            somme_ponderee = 0
            for ue in UES:
                if ue in cours_map[sem]:
                    d = cours_map[sem][ue]
                    cc = d["cc"]
                    examen = d["examen"]
                    vals = [v for v in (cc, examen) if v is not None]
                    moy = round(sum(vals) / len(vals), 2) if vals else None
                    coeff = d["coeff"]
                    ues_list.append({
                        "code_ue": ue,
                        "code": d["code"],
                        "intitule": d["intitule"],
                        "enseignant": d["enseignant"],
                        "cc": cc,
                        "examen": examen,
                        "moyenne": moy,
                        "coeff": coeff,
                    })
                    if moy is not None:
                        total_coeff += coeff
                        somme_ponderee += moy * coeff
            moyenne_semestre = round(somme_ponderee / total_coeff, 2) if total_coeff > 0 else None
            semestres.append({"semestre": sem, "ues": ues_list, "moyenne": moyenne_semestre})
    nom_etu = f"{etu['prenom']} {etu['nom']}"
    return render_template("head/note/semestre.html", semestres=semestres, etudiant=nom_etu, matricule=etu["matricule"])

@app.route("/chef/notes/<semestre>", methods=["GET", "POST"])
@login_required
def head_notes_par_semestre(semestre):
    if current_user.get_role() != "head":
        return redirect(url_for("public_index"))
    if semestre not in SEMESTRES:
        flash("Semestre invalide.", "danger")
        return redirect(url_for("head_notes_liste"))
    dept = current_user.get_departement()

    if request.method == "POST":
        from datetime import date
        today = str(date.today())
        for key, valeur in request.form.items():
            if key.startswith("note_") and valeur.strip():
                parts = key.split("_", 3)
                if len(parts) == 4:
                    _, s_id, c_id, n_type = parts
                    try:
                        v = float(valeur)
                        if 0 <= v <= 20:
                            existing = get_collection("notes").find_one({
                                "id_etudiant": ObjectId(s_id),
                                "id_cours": ObjectId(c_id),
                                "type_note": n_type,
                            })
                            if existing:
                                get_collection("notes").update_one(
                                    {"_id": existing["_id"]},
                                    {"$set": {"valeur": v, "date_evaluation": today}}
                                )
                            else:
                                get_collection("notes").insert_one({
                                    "id_etudiant": ObjectId(s_id),
                                    "id_cours": ObjectId(c_id),
                                    "valeur": v,
                                    "type_note": n_type,
                                    "date_evaluation": today,
                                })
                    except (ValueError, InvalidId):
                        pass
        flash(f"Notes {semestre} enregistrées.", "success")
        return redirect(url_for("head_notes_par_semestre", semestre=semestre))

    etudiants = list(get_collection("etudiants").find({"departement": dept}).sort("nom", 1))
    cours_sem = list(get_collection("cours").find({"departement": dept, "semestre": semestre}).sort("code_ue", 1))
    ue_order = ["U001", "U002", "U003", "U004", "U005"]
    cours_sem.sort(key=lambda c: ue_order.index(c.get("code_ue", "U000")) if c.get("code_ue", "U000") in ue_order else 99)

    for etu in etudiants:
        etu["_id"] = str(etu["_id"])
        etu["cours_data"] = []
        for c in cours_sem:
            cc = get_collection("notes").find_one({
                "id_etudiant": ObjectId(etu["_id"]), "id_cours": c["_id"], "type_note": "cc"
            })
            ex = get_collection("notes").find_one({
                "id_etudiant": ObjectId(etu["_id"]), "id_cours": c["_id"], "type_note": "examen"
            })
            etu["cours_data"].append({
                "id": str(c["_id"]),
                "code": c["code"],
                "intitule": c["intitule"],
                "enseignant": c.get("enseignant", ""),
                "code_ue": c.get("code_ue", ""),
                "credit": c.get("credit", 3),
                "cc": cc["valeur"] if cc else None,
                "examen": ex["valeur"] if ex else None,
            })

    return render_template("head/note/semestre_edit.html", etudiants=etudiants, departement=dept, semestre=semestre)

@app.route("/chef/moyennes")
@login_required
def head_moyennes():
    if current_user.get_role() != "head":
        return redirect(url_for("public_index"))
    dept = current_user.get_departement()
    etu_ids = [e["_id"] for e in get_collection("etudiants").find({"departement": dept}, {"_id": 1})]
    pipeline = [
        {"$match": {"id_etudiant": {"$in": etu_ids}}},
        {"$group": {"_id": "$id_etudiant", "moyenne": {"$avg": "$valeur"}, "nb_notes": {"$sum": 1}}},
        {"$sort": {"moyenne": -1}}
    ]
    resultats = []
    for r in get_collection("notes").aggregate(pipeline):
        etu = get_collection("etudiants").find_one({"_id": r["_id"]})
        r["_id"] = str(r["_id"])
        r["etudiant_nom"] = f"{etu['prenom']} {etu['nom']}" if etu else "Inconnu"
        r["moyenne"] = round(r["moyenne"], 2)
        resultats.append(r)
    return render_template("head/note/moyennes.html", resultats=resultats)

@app.route("/chef/profil", methods=["GET", "POST"])
@login_required
def head_profile():
    if current_user.get_role() != "head":
        return redirect(url_for("public_index"))
    if request.method == "POST":
        nom = request.form.get("nom", "").strip().upper()
        prenom = request.form.get("prenom", "").strip().capitalize()
        new_pw = request.form.get("new_password", "").strip()
        confirm = request.form.get("confirm_password", "").strip()
        if nom and prenom:
            get_collection("users").update_one(
                {"_id": ObjectId(current_user.id)},
                {"$set": {"nom": nom, "prenom": prenom}}
            )
        if new_pw:
            if new_pw == confirm:
                get_collection("users").update_one(
                    {"_id": ObjectId(current_user.id)},
                    {"$set": {"password": generate_password_hash(new_pw)}}
                )
                flash("Mot de passe modifié.", "success")
            else:
                flash("Les mots de passe ne correspondent pas.", "danger")
                return redirect(url_for("head_profile"))
        flash("Profil mis à jour.", "success")
        return redirect(url_for("head_profile"))
    return render_template("head/profile.html", user=current_user.user_data)

# --- Messagerie Chef (↔ Étudiants) ---
@app.route("/chef/messages")
@login_required
def head_messages():
    if current_user.get_role() != "head":
        flash("Accès refusé.", "danger")
        return redirect(url_for("public_index"))
    dept = current_user.get_departement()
    chef_id = ObjectId(current_user.id)
    pipeline = [
        {"$match": {"id_chef": chef_id}},
        {"$sort": {"date_envoi": -1}},
        {"$group": {
            "_id": "$id_etudiant",
            "dernier_message": {"$first": "$contenu"},
            "dernier_date": {"$first": "$date_envoi"},
            "non_lus": {"$sum": {"$cond": [{"$and": [{"$eq": ["$lu", False]}, {"$eq": ["$expediteur", "etudiant"]}]}, 1, 0]}},
        }},
        {"$sort": {"dernier_date": -1}}
    ]
    conversations = list(get_collection("messages").aggregate(pipeline))
    for conv in conversations:
        etu = get_collection("etudiants").find_one({"_id": conv["_id"]})
        conv["id_etudiant"] = str(conv["_id"])
        conv["etudiant_nom"] = f"{etu['prenom']} {etu['nom']}" if etu else "Inconnu"
        conv["matricule"] = etu["matricule"] if etu else ""
        conv["dernier_date"] = conv["dernier_date"].strftime("%d/%m/%Y %H:%M") if hasattr(conv["dernier_date"], "strftime") else str(conv["dernier_date"])
    return render_template("head/messages/liste.html", conversations=conversations)

@app.route("/chef/messages/<id_etudiant>")
@login_required
def head_messages_conversation(id_etudiant):
    if current_user.get_role() != "head":
        flash("Accès refusé.", "danger")
        return redirect(url_for("public_index"))
    try:
        id_etu = ObjectId(id_etudiant)
    except InvalidId:
        flash("ID invalide.", "danger")
        return redirect(url_for("head_messages"))
    etu = get_collection("etudiants").find_one({"_id": id_etu})
    if not etu:
        flash("Étudiant introuvable.", "danger")
        return redirect(url_for("head_messages"))
    if etu.get("departement") != current_user.get_departement():
        flash("Accès refusé.", "danger")
        return redirect(url_for("head_messages"))
    chef_id = ObjectId(current_user.id)
    messages = list(get_collection("messages").find({
        "id_etudiant": id_etu, "id_chef": chef_id
    }).sort("date_envoi", 1))
    get_collection("messages").update_many(
        {"id_etudiant": id_etu, "id_chef": chef_id, "expediteur": "etudiant", "lu": False},
        {"$set": {"lu": True}}
    )
    for m in messages:
        m["_id"] = str(m["_id"])
    return render_template("head/messages/conversation.html", messages=messages, etudiant=etu)

@app.route("/chef/messages/<id_etudiant>/repondre", methods=["POST"])
@login_required
def head_message_reply(id_etudiant):
    if current_user.get_role() != "head":
        flash("Accès refusé.", "danger")
        return redirect(url_for("public_index"))
    from datetime import datetime
    try:
        id_etu = ObjectId(id_etudiant)
    except InvalidId:
        flash("ID invalide.", "danger")
        return redirect(url_for("head_messages"))
    contenu = request.form.get("contenu", "").strip()
    if not contenu:
        flash("Le message ne peut pas être vide.", "danger")
        return redirect(url_for("head_messages_conversation", id_etudiant=id_etudiant))
    chef_id = ObjectId(current_user.id)
    get_collection("messages").insert_one({
        "id_etudiant": id_etu,
        "id_chef": chef_id,
        "expediteur": "chef",
        "contenu": contenu,
        "date_envoi": datetime.now(),
        "lu": True,
    })
    flash("Réponse envoyée à l'étudiant.", "success")
    return redirect(url_for("head_messages_conversation", id_etudiant=id_etudiant))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, threaded=True)
