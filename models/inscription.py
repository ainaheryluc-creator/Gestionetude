from db import get_collection
from bson.objectid import ObjectId
from bson.errors import InvalidId
from datetime import date

class Inscription:
    @staticmethod
    def collection():
        return get_collection("inscriptions")

    @staticmethod
    def creer(id_etudiant, id_cours, annee_academique, date_inscription=None):
        try:
            data = {
                "id_etudiant": ObjectId(id_etudiant),
                "id_cours": ObjectId(id_cours),
                "annee_academique": annee_academique,
                "date_inscription": date_inscription or str(date.today()),
            }
            result = Inscription.collection().insert_one(data)
            print(f"Inscription créée avec l'ID : {result.inserted_id}")
            return True
        except InvalidId:
            print("ID étudiant ou cours invalide.")
            return False

    @staticmethod
    def tous():
        return list(Inscription.collection().find())

    @staticmethod
    def chercher_par_id(id_):
        try:
            return Inscription.collection().find_one({"_id": ObjectId(id_)})
        except InvalidId:
            print("ID invalide.")
            return None

    @staticmethod
    def chercher_par_etudiant(id_etudiant):
        try:
            return list(Inscription.collection().find({"id_etudiant": ObjectId(id_etudiant)}))
        except InvalidId:
            print("ID étudiant invalide.")
            return []

    @staticmethod
    def chercher_par_cours(id_cours):
        try:
            return list(Inscription.collection().find({"id_cours": ObjectId(id_cours)}))
        except InvalidId:
            print("ID cours invalide.")
            return []

    @staticmethod
    def supprimer(id_):
        try:
            result = Inscription.collection().delete_one({"_id": ObjectId(id_)})
            if result.deleted_count > 0:
                print("Inscription supprimée avec succès.")
            else:
                print("Inscription non trouvée.")
            return result.deleted_count > 0
        except InvalidId:
            print("ID invalide.")
            return False
