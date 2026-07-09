from db import get_collection
from bson.objectid import ObjectId
from bson.errors import InvalidId

class Cours:
    @staticmethod
    def collection():
        return get_collection("cours")

    @staticmethod
    def creer(code, intitule, credit, enseignant):
        existe = Cours.collection().find_one({"code": code})
        if existe:
            print(f"Un cours avec le code '{code}' existe déjà.")
            return False
        cours = {
            "code": code,
            "intitule": intitule,
            "credit": credit,
            "enseignant": enseignant,
        }
        result = Cours.collection().insert_one(cours)
        print(f"Cours créé avec l'ID : {result.inserted_id}")
        return True

    @staticmethod
    def tous():
        return list(Cours.collection().find())

    @staticmethod
    def chercher_par_id(id_):
        try:
            return Cours.collection().find_one({"_id": ObjectId(id_)})
        except InvalidId:
            print("ID invalide.")
            return None

    @staticmethod
    def chercher_par_code(code):
        return Cours.collection().find_one({"code": code})

    @staticmethod
    def modifier(id_, data):
        try:
            result = Cours.collection().update_one(
                {"_id": ObjectId(id_)},
                {"$set": data}
            )
            if result.modified_count > 0:
                print("Cours modifié avec succès.")
            else:
                print("Aucune modification effectuée.")
            return result.modified_count > 0
        except InvalidId:
            print("ID invalide.")
            return False

    @staticmethod
    def supprimer(id_):
        try:
            result = Cours.collection().delete_one({"_id": ObjectId(id_)})
            if result.deleted_count > 0:
                print("Cours supprimé avec succès.")
            else:
                print("Cours non trouvé.")
            return result.deleted_count > 0
        except InvalidId:
            print("ID invalide.")
            return False
