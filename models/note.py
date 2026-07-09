from db import get_collection
from bson.objectid import ObjectId
from bson.errors import InvalidId
from datetime import date

class Note:
    @staticmethod
    def collection():
        return get_collection("notes")

    @staticmethod
    def ajouter(id_etudiant, id_cours, valeur, type_note="examen", date_evaluation=None):
        if valeur < 0 or valeur > 20:
            print("La note doit être comprise entre 0 et 20.")
            return False
        if type_note not in ("examen", "devoir", "tp"):
            print("Type de note invalide. Choisissez : examen, devoir, tp.")
            return False
        try:
            data = {
                "id_etudiant": ObjectId(id_etudiant),
                "id_cours": ObjectId(id_cours),
                "valeur": valeur,
                "type_note": type_note,
                "date_evaluation": date_evaluation or str(date.today()),
            }
            result = Note.collection().insert_one(data)
            print(f"Note ajoutée avec l'ID : {result.inserted_id}")
            return True
        except InvalidId:
            print("ID étudiant ou cours invalide.")
            return False

    @staticmethod
    def tous():
        return list(Note.collection().find())

    @staticmethod
    def chercher_par_id(id_):
        try:
            return Note.collection().find_one({"_id": ObjectId(id_)})
        except InvalidId:
            print("ID invalide.")
            return None

    @staticmethod
    def chercher_par_etudiant(id_etudiant):
        try:
            return list(Note.collection().find({"id_etudiant": ObjectId(id_etudiant)}))
        except InvalidId:
            print("ID étudiant invalide.")
            return []

    @staticmethod
    def chercher_par_cours(id_cours):
        try:
            return list(Note.collection().find({"id_cours": ObjectId(id_cours)}))
        except InvalidId:
            print("ID cours invalide.")
            return []

    @staticmethod
    def moyenne_etudiant_par_cours(id_etudiant, id_cours):
        try:
            notes = list(Note.collection().find({
                "id_etudiant": ObjectId(id_etudiant),
                "id_cours": ObjectId(id_cours),
            }))
            if not notes:
                return 0
            return sum(n["valeur"] for n in notes) / len(notes)
        except InvalidId:
            print("ID étudiant ou cours invalide.")
            return 0

    @staticmethod
    def moyenne_generale_etudiant(id_etudiant):
        try:
            notes = list(Note.collection().find({"id_etudiant": ObjectId(id_etudiant)}))
            if not notes:
                return 0
            return sum(n["valeur"] for n in notes) / len(notes)
        except InvalidId:
            print("ID étudiant invalide.")
            return 0

    @staticmethod
    def modifier(id_, valeur):
        if valeur < 0 or valeur > 20:
            print("La note doit être comprise entre 0 et 20.")
            return False
        try:
            result = Note.collection().update_one(
                {"_id": ObjectId(id_)},
                {"$set": {"valeur": valeur}}
            )
            if result.modified_count > 0:
                print("Note modifiée avec succès.")
            else:
                print("Aucune modification effectuée.")
            return result.modified_count > 0
        except InvalidId:
            print("ID invalide.")
            return False

    @staticmethod
    def supprimer(id_):
        try:
            result = Note.collection().delete_one({"_id": ObjectId(id_)})
            if result.deleted_count > 0:
                print("Note supprimée avec succès.")
            else:
                print("Note non trouvée.")
            return result.deleted_count > 0
        except InvalidId:
            print("ID invalide.")
            return False
