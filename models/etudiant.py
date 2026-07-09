from db import get_collection
from bson.objectid import ObjectId
from bson.errors import InvalidId

class Etudiant:
    @staticmethod
    def collection():
        return get_collection("etudiants")

    @staticmethod
    def creer(matricule, nom, prenom, email, telephone, date_naissance, adresse):
        existe = Etudiant.collection().find_one({"matricule": matricule})
        if existe:
            print(f"Un étudiant avec le matricule '{matricule}' existe déjà.")
            return False
        etudiant = {
            "matricule": matricule,
            "nom": nom,
            "prenom": prenom,
            "email": email,
            "telephone": telephone,
            "date_naissance": date_naissance,
            "adresse": adresse,
        }
        result = Etudiant.collection().insert_one(etudiant)
        print(f"Étudiant créé avec l'ID : {result.inserted_id}")
        return True

    @staticmethod
    def tous():
        return list(Etudiant.collection().find())

    @staticmethod
    def chercher_par_id(id_):
        try:
            return Etudiant.collection().find_one({"_id": ObjectId(id_)})
        except InvalidId:
            print("ID invalide.")
            return None

    @staticmethod
    def chercher_par_matricule(matricule):
        return Etudiant.collection().find_one({"matricule": matricule})

    @staticmethod
    def modifier(id_, data):
        try:
            result = Etudiant.collection().update_one(
                {"_id": ObjectId(id_)},
                {"$set": data}
            )
            if result.modified_count > 0:
                print("Étudiant modifié avec succès.")
            else:
                print("Aucune modification effectuée.")
            return result.modified_count > 0
        except InvalidId:
            print("ID invalide.")
            return False

    @staticmethod
    def supprimer(id_):
        try:
            result = Etudiant.collection().delete_one({"_id": ObjectId(id_)})
            if result.deleted_count > 0:
                print("Étudiant supprimé avec succès.")
            else:
                print("Étudiant non trouvé.")
            return result.deleted_count > 0
        except InvalidId:
            print("ID invalide.")
            return False
