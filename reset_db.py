from website import create_app, db
import os

def reset_database():
    app = create_app()
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'website', 'database.db')
    
    print(f"Chemin de la base de données: {db_path}")  # Debug
    print(f"Permissions d'écriture sur le dossier: {os.access(os.path.dirname(db_path), os.W_OK)}")  # Debug
    
    with app.app_context():
        # Supprimer la base de données existante
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
                print(f"Ancienne base de données supprimée: {db_path}")
            except Exception as e:
                print(f"Erreur lors de la suppression: {e}")
        
        # Créer une nouvelle base de données
        try:
            db.create_all()
            print("Nouvelle base de données créée avec succès!")
            return True
        except Exception as e:
            print(f"Erreur lors de la création: {e}")
            return False

if __name__ == "__main__":
    reset_database()
