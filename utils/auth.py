import streamlit as st
from werkzeug.security import check_password_hash
from db import get_collection

class User:
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

def init_session():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user" not in st.session_state:
        st.session_state.user = None
    if "page" not in st.session_state:
        st.session_state.page = "accueil"
    if "flash" not in st.session_state:
        st.session_state.flash = []

def login(email, password):
    user_data = get_collection("users").find_one({"email": email.strip()})
    if user_data and check_password_hash(user_data["password"], password):
        st.session_state.authenticated = True
        st.session_state.user = User(user_data)
        st.session_state.flash.append(("success", f"Bienvenue, {st.session_state.user.get_nom_complet()} !"))
        return True
    st.session_state.flash.append(("danger", "Email ou mot de passe incorrect."))
    return False

def logout():
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.page = "accueil"
    st.session_state.flash.append(("info", "Vous êtes déconnecté."))
    st.rerun()

def require_role(role):
    if not st.session_state.authenticated:
        st.session_state.page = "login"
        st.rerun()
    if st.session_state.user.get_role() != role:
        st.session_state.flash.append(("danger", f"Accès réservé aux {role}."))
        st.session_state.page = "accueil"
        st.rerun()

def show_flash():
    for cat, msg in st.session_state.flash:
        if cat == "success":
            st.success(msg)
        elif cat == "danger":
            st.error(msg)
        elif cat == "info":
            st.info(msg)
        elif cat == "warning":
            st.warning(msg)
    st.session_state.flash = []
